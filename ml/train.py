"""Entrena la TCN con el historial de consumo y la compara con el promedio móvil de 4 semanas.

Uso:
    python train.py --csv data/consumo.csv --tostador T01 --semanas-prueba 8
    python train.py --demo            # con datos sintéticos, para probar que todo funciona

Guarda el modelo en models/tcn.pt (copiarlo a backend/models/ para servirlo desde la API).
"""

import argparse
from pathlib import Path

import numpy as np
import torch
from torch import nn

from originlink_ml.baseline import mape, promedio_movil
from originlink_ml.data import cargar_consumo_semanal, particion_temporal, ventanas
from originlink_ml.tcn import TCN

WINDOW = 12  # semanas de historia que recibe el modelo
HORIZON = 4  # semanas que pronostica


def serie_demo(n: int = 104, seed: int = 7) -> np.ndarray:
    """Consumo semanal sintético (kg): tendencia + estacionalidad + ruido. Solo para pruebas."""
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    return (7 + 0.02 * t + 1.5 * np.sin(2 * np.pi * t / 26) + rng.normal(0, 0.5, n)).clip(min=0)


def entrenar(train: np.ndarray, epochs: int = 300, lr: float = 1e-2, seed: int = 42) -> tuple[TCN, float, float]:
    torch.manual_seed(seed)
    media, desv = float(train.mean()), float(train.std() or 1.0)
    X, y = ventanas((train - media) / desv, WINDOW, HORIZON)
    X_t, y_t = torch.from_numpy(X).unsqueeze(1), torch.from_numpy(y)

    modelo = TCN(n_features=1, horizon=HORIZON)
    opt = torch.optim.Adam(modelo.parameters(), lr=lr)
    loss_fn = nn.MSELoss()
    modelo.train()
    for _ in range(epochs):
        opt.zero_grad()
        loss = loss_fn(modelo(X_t), y_t)
        loss.backward()
        opt.step()
    return modelo, media, desv


def pronosticar(modelo: TCN, historia: np.ndarray, media: float, desv: float) -> np.ndarray:
    modelo.eval()
    x = torch.tensor((historia[-WINDOW:] - media) / desv, dtype=torch.float32).view(1, 1, -1)
    with torch.no_grad():
        return modelo(x).numpy().ravel() * desv + media


def evaluar(serie: np.ndarray, semanas_prueba: int, modelo: TCN, media: float, desv: float) -> tuple[float, float]:
    """Pronóstico rodante sobre el conjunto de prueba: TCN vs promedio móvil (MAPE a 1 semana)."""
    inicio = len(serie) - semanas_prueba
    real, p_tcn, p_pm = [], [], []
    for t in range(inicio, len(serie)):
        historia = serie[:t]
        real.append(serie[t])
        p_tcn.append(pronosticar(modelo, historia, media, desv)[0])
        p_pm.append(promedio_movil(historia, ventana=4, horizon=1)[0])
    return mape(real, p_tcn), mape(real, p_pm)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", help="CSV con columnas tostador_id, fecha, kg_consumidos")
    parser.add_argument("--tostador", help="ID del tostador a modelar")
    parser.add_argument("--semanas-prueba", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=300)
    parser.add_argument("--demo", action="store_true", help="Usar datos sintéticos")
    parser.add_argument("--salida", default="models/tcn.pt")
    args = parser.parse_args()

    if args.demo:
        serie = serie_demo()
    else:
        df = cargar_consumo_semanal(args.csv)
        serie = df.loc[df["tostador_id"] == args.tostador, "kg_consumidos"].to_numpy(dtype=float)

    minimo = WINDOW + HORIZON + args.semanas_prueba
    if len(serie) < minimo:
        raise SystemExit(f"Historial insuficiente: {len(serie)} semanas (mínimo {minimo}). Usar el promedio móvil.")

    train, _ = particion_temporal(serie, args.semanas_prueba)
    modelo, media, desv = entrenar(train, epochs=args.epochs)
    mape_tcn, mape_pm = evaluar(serie, args.semanas_prueba, modelo, media, desv)

    print(f"Semanas de historial: {len(serie)} | prueba: {args.semanas_prueba}")
    print(f"MAPE TCN:             {mape_tcn:.2f} %  (meta OE3-I1: <= 25 %)")
    print(f"MAPE promedio móvil:  {mape_pm:.2f} %")
    print("La TCN supera al promedio móvil (OE4-I3)" if mape_tcn < mape_pm else "La TCN NO supera al promedio móvil")

    Path(args.salida).parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {"state_dict": modelo.state_dict(), "media": media, "desv": desv, "window": WINDOW, "horizon": HORIZON},
        args.salida,
    )
    print(f"Modelo guardado en {args.salida}")


if __name__ == "__main__":
    main()
