"""Modelo TCN global para el pronóstico de consumo semanal (HU-19).

Diferencias frente a `train.py` (un modelo por tostador, solo la serie de consumo):

1. **Modelo global**: una sola red aprende de todos los tostadores a la vez. Cada serie se normaliza
   con las estadísticas de su propio tramo de entrenamiento, así que se multiplican los ejemplos sin
   mezclar escalas (6 kg/semana frente a 12 kg/semana).
2. **Calendario como entrada**: el mes del año (codificación cíclica seno/coseno con resolución semanal)
   de cada semana de la ventana y de las semanas que se van a pronosticar. Permite aprender la
   estacionalidad (Fiestas Patrias, agosto, diciembre).
3. **Evaluación honesta**: partición temporal en entrenamiento / validación / prueba. La prueba (últimas
   `semanas_prueba` semanas de cada tostador) se aparta antes de entrenar y solo se usa para informar.
   La validación se usa para elegir el número de épocas y, por tostador, el método (ADR-0003).
4. **Origen rodante** a 1 y a 4 semanas, que es el horizonte que usa la recomendación de compra.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd
import torch
from torch import nn

from originlink_ml.baseline import mape, promedio_movil
from originlink_ml.data import cargar_consumo_semanal
from originlink_ml.tcn import TCN

TCN_METODO = "TCN"
PM_METODO = "PROMEDIO_MOVIL"


@dataclass(frozen=True)
class Config:
    ventana: int = 12
    horizonte: int = 4
    semanas_prueba: int = 6  # Charter M4: últimas 6 semanas de cada tostador
    semanas_validacion: int = 12
    calendario: bool = True
    norm_ventana: bool = False  # True: se divide cada ventana entre su propio promedio
    perdida: str = "mse"  # "mse" | "l1"
    epocas: int = 300
    lr: float = 5e-3
    decaimiento: float = 1e-4
    semillas: int = 5
    canales: tuple[int, ...] = (16, 16, 16)
    dropout: float = 0.1
    paciencia: int = 40

    @property
    def minimo_semanas(self) -> int:
        """Historial mínimo por tostador para entrenar (M3 del Charter pide además >= 26 semanas)."""
        return max(26, self.ventana + self.horizonte + self.semanas_prueba + self.semanas_validacion)


@dataclass
class Serie:
    id: str
    fechas: pd.DatetimeIndex  # lunes de cada semana
    kg: np.ndarray


def cargar_series(ruta_csv: str) -> list[Serie]:
    """Lee `tostador_id, fecha, kg_consumidos` y devuelve una serie semanal por tostador."""
    df = cargar_consumo_semanal(ruta_csv)
    series = []
    for tid, g in df.groupby("tostador_id"):
        g = g.sort_values("semana")
        series.append(Serie(str(tid), pd.DatetimeIndex(g["semana"]), g["kg_consumidos"].to_numpy(dtype=float)))
    return series


def calendario(fechas: pd.DatetimeIndex, horizonte: int) -> np.ndarray:
    """Seno/coseno del día del año de cada semana, extendido `horizonte` semanas hacia el futuro."""
    extra = pd.date_range(fechas[-1] + pd.Timedelta(days=7), periods=horizonte, freq="7D")
    todas = fechas.append(extra)
    ang = 2 * np.pi * (todas.dayofyear.to_numpy() - 1) / 365.25
    return np.stack([np.sin(ang), np.cos(ang)], axis=1).astype(np.float32)


def _estadisticas(serie: Serie, n_entrenamiento: int) -> tuple[float, float]:
    tramo = serie.kg[:n_entrenamiento]
    return float(tramo.mean()), float(tramo.std() or 1.0)


def _muestra(kg: np.ndarray, cal: np.ndarray, t: int, cfg: Config, stats: tuple[float, float]):
    """Ventana de `cfg.ventana` semanas previas a `t` y las `cfg.horizonte` semanas que le siguen."""
    w, h = cfg.ventana, cfg.horizonte
    x = kg[t - w : t]
    if cfg.norm_ventana:
        a = b = max(float(x.mean()), 1e-6)
        xn = x / a - 1.0
        yn = (kg[t : t + h] / a - 1.0) if t + h <= len(kg) else np.zeros(h)
    else:
        a, b = stats
        xn = (x - a) / b
        yn = ((kg[t : t + h] - a) / b) if t + h <= len(kg) else np.zeros(h)
    canales = [xn[None, :]]
    if cfg.calendario:
        canales.append(cal[t - w : t].T)
    futuro = cal[t : t + h].reshape(-1) if cfg.calendario else np.zeros(0)
    return (
        np.concatenate(canales, axis=0).astype(np.float32),
        futuro.astype(np.float32),
        yn.astype(np.float32),
        a,
        b,
    )


def construir_conjunto(series: list[Serie], cfg: Config, objetivo_desde: int | None, objetivo_hasta: int):
    """Muestras cuyo objetivo cae en [objetivo_desde, objetivo_hasta) *relativo al final de cada serie*.

    Los índices son offsets desde el final (negativos), p. ej. el entrenamiento usa objetivos hasta
    `-(prueba + validacion)`. Así ninguna muestra de entrenamiento ve semanas de validación ni de prueba.
    """
    X, F, Y = [], [], []
    for s in series:
        n = len(s.kg)
        fin = n + objetivo_hasta
        ini = cfg.ventana if objetivo_desde is None else n + objetivo_desde
        stats = _estadisticas(s, n - cfg.semanas_prueba - cfg.semanas_validacion)
        cal = calendario(s.fechas, cfg.horizonte)
        for t in range(max(ini, cfg.ventana), fin - cfg.horizonte + 1):
            x, f, y, _, _ = _muestra(s.kg, cal, t, cfg, stats)
            X.append(x)
            F.append(f)
            Y.append(y)
    return (
        torch.from_numpy(np.stack(X)),
        torch.from_numpy(np.stack(F)),
        torch.from_numpy(np.stack(Y)),
    )


class TCNGlobal(nn.Module):
    """TCN (convoluciones causales dilatadas) + cabeza que además recibe el calendario futuro."""

    def __init__(self, cfg: Config):
        super().__init__()
        n_in = 1 + (2 if cfg.calendario else 0)
        base = TCN(n_features=n_in, channels=cfg.canales, dropout=cfg.dropout, horizon=cfg.horizonte)
        self.tcn = base.tcn
        n_futuro = cfg.horizonte * 2 if cfg.calendario else 0
        self.cabeza = nn.Sequential(
            nn.Linear(cfg.canales[-1] + n_futuro, 32), nn.ReLU(), nn.Linear(32, cfg.horizonte)
        )

    def forward(self, x: torch.Tensor, futuro: torch.Tensor) -> torch.Tensor:
        h = self.tcn(x)[:, :, -1]
        if futuro.shape[1]:
            h = torch.cat([h, futuro], dim=1)
        return self.cabeza(h)


def entrenar_modelo(train, val, cfg: Config, semilla: int) -> TCNGlobal:
    """Entrena una red y devuelve la de menor pérdida de validación (parada temprana)."""
    torch.manual_seed(semilla)
    np.random.seed(semilla)
    modelo = TCNGlobal(cfg)
    opt = torch.optim.Adam(modelo.parameters(), lr=cfg.lr, weight_decay=cfg.decaimiento)
    fn = nn.MSELoss() if cfg.perdida == "mse" else nn.L1Loss()
    (Xt, Ft, Yt), (Xv, Fv, Yv) = train, val
    mejor, mejor_estado, sin_mejora = float("inf"), None, 0
    for _ in range(cfg.epocas):
        modelo.train()
        opt.zero_grad()
        fn(modelo(Xt, Ft), Yt).backward()
        opt.step()
        modelo.eval()
        with torch.no_grad():
            perdida_val = float(fn(modelo(Xv, Fv), Yv))
        if perdida_val < mejor - 1e-6:
            mejor, sin_mejora = perdida_val, 0
            mejor_estado = {k: v.detach().clone() for k, v in modelo.state_dict().items()}
        else:
            sin_mejora += 1
            if sin_mejora >= cfg.paciencia:
                break
    modelo.load_state_dict(mejor_estado)
    return modelo.eval()


def entrenar_conjunto(series: list[Serie], cfg: Config) -> list[TCNGlobal]:
    """Entrena `cfg.semillas` redes con distinta inicialización; el pronóstico es el promedio."""
    series = [s for s in series if len(s.kg) >= cfg.minimo_semanas]
    if not series:
        return []  # nadie tiene historial suficiente: no hay nada que entrenar (ver entrenar_y_elegir)
    corte_val = -(cfg.semanas_prueba + cfg.semanas_validacion)
    train = construir_conjunto(series, cfg, None, corte_val)
    val = construir_conjunto(series, cfg, corte_val, -cfg.semanas_prueba)
    return [entrenar_modelo(train, val, cfg, semilla=42 + i) for i in range(cfg.semillas)]


def entrenar_y_elegir(series: list[Serie], cfg: Config) -> tuple[list[TCNGlobal], dict[str, str]]:
    """Entrena y decide el método de cada tostador (ADR-0003).

    Si ningún tostador alcanza el mínimo de semanas, devuelve ([], {id: PROMEDIO_MOVIL}) sin fallar:
    el mecanismo alternativo se ejecuta para todos y el sistema sigue pudiendo recomendar.
    """
    modelos = entrenar_conjunto(series, cfg)
    return modelos, elegir_metodo_por_tostador(series, modelos, cfg)


def pronosticar(modelos: list[TCNGlobal], serie: Serie, origen: int, cfg: Config) -> np.ndarray:
    """Pronóstico (kg) de las `horizonte` semanas siguientes a la semana `origen` (exclusive).

    Solo usa `serie.kg[:origen]` como historia. Con `origen == len(serie.kg)` pronostica el futuro.
    """
    n_entrenamiento = len(serie.kg) - cfg.semanas_prueba - cfg.semanas_validacion
    stats = _estadisticas(serie, n_entrenamiento)
    cal = calendario(serie.fechas, cfg.horizonte)
    historia = serie.kg[:origen]
    x, f, _, a, b = _muestra(np.concatenate([historia, np.zeros(cfg.horizonte)]), cal, origen, cfg, stats)
    with torch.no_grad():
        salidas = [m(torch.from_numpy(x)[None], torch.from_numpy(f)[None])[0].numpy() for m in modelos]
    return np.clip(np.mean(salidas, axis=0) * b + a, 0, None)


def errores(series: list[Serie], modelos: list[TCNGlobal], cfg: Config, region: str) -> pd.DataFrame:
    """Origen rodante sobre `region` ("prueba" o "validacion"). Una fila por (tostador, origen, paso)."""
    filas = []
    for s in series:
        n = len(s.kg)
        if region == "prueba":
            ini, limite = n - cfg.semanas_prueba, n
        else:
            ini, limite = n - cfg.semanas_prueba - cfg.semanas_validacion, n - cfg.semanas_prueba
        for t in range(ini, limite):
            pasos = min(cfg.horizonte, limite - t)
            tcn = pronosticar(modelos, s, t, cfg)
            pm = promedio_movil(s.kg[:t], 4, cfg.horizonte)
            for k in range(pasos):
                filas.append((s.id, t, k + 1, s.kg[t + k], tcn[k], pm[k], pasos == cfg.horizonte))
    return pd.DataFrame(filas, columns=["tostador", "origen", "paso", "real", "tcn", "pm", "origen_completo"])


def resumen_mape(df: pd.DataFrame) -> pd.DataFrame:
    """MAPE (%) por tostador y global, a 1 semana (primer paso) y a 4 semanas (todos los pasos)."""
    def fila(g1: pd.DataFrame, g4: pd.DataFrame) -> dict:
        return {
            "mape_tcn_1s": mape(g1.real, g1.tcn),
            "mape_pm_1s": mape(g1.real, g1.pm),
            "mape_tcn_4s": mape(g4.real, g4.tcn),
            "mape_pm_4s": mape(g4.real, g4.pm),
            "n_1s": len(g1),
            "n_4s": len(g4),
        }

    d1 = df[df.paso == 1]
    d4 = df[df.origen_completo]
    filas = {t: fila(d1[d1.tostador == t], d4[d4.tostador == t]) for t in sorted(df.tostador.unique())}
    filas["GLOBAL"] = fila(d1, d4)
    return pd.DataFrame(filas).T


def elegir_metodo_por_tostador(series: list[Serie], modelos: list[TCNGlobal], cfg: Config) -> dict[str, str]:
    """ADR-0003: usa la TCN solo si su MAPE de validación (4 semanas) es menor que el del promedio móvil.

    Un tostador con menos historial que `cfg.minimo_semanas` usa siempre el promedio móvil.
    """
    elegido: dict[str, str] = {}
    suficientes = [s for s in series if len(s.kg) >= cfg.minimo_semanas]
    for s in series:
        if len(s.kg) < cfg.minimo_semanas:
            elegido[s.id] = PM_METODO
    if suficientes:
        val = resumen_mape(errores(suficientes, modelos, cfg, "validacion"))
        for s in suficientes:
            r = val.loc[s.id]
            elegido[s.id] = TCN_METODO if r.mape_tcn_4s < r.mape_pm_4s else PM_METODO
    return elegido


def config_a_dict(cfg: Config) -> dict:
    return {k: (list(v) if isinstance(v, tuple) else v) for k, v in asdict(cfg).items()}
