"""Preparación del historial de consumo semanal para entrenar la TCN."""

import numpy as np
import pandas as pd


def cargar_consumo_semanal(ruta_csv: str) -> pd.DataFrame:
    """Lee un CSV con columnas: tostador_id, fecha, kg_consumidos.

    Agrega a semanas (lunes) por tostador y rellena con 0 las semanas sin consumo.
    """
    df = pd.read_csv(ruta_csv, parse_dates=["fecha"])
    df["semana"] = df["fecha"].dt.to_period("W-SUN").dt.start_time
    semanal = df.groupby(["tostador_id", "semana"], as_index=False)["kg_consumidos"].sum()
    completas = []
    for tid, g in semanal.groupby("tostador_id"):
        idx = pd.date_range(g["semana"].min(), g["semana"].max(), freq="W-MON")
        g = g.set_index("semana").reindex(idx, fill_value=0).rename_axis("semana").reset_index()
        g["tostador_id"] = tid
        completas.append(g)
    return pd.concat(completas, ignore_index=True)


def ventanas(serie: np.ndarray, window: int, horizon: int) -> tuple[np.ndarray, np.ndarray]:
    """Convierte una serie en pares (X: `window` semanas previas, y: `horizon` semanas siguientes)."""
    X, y = [], []
    for t in range(window, len(serie) - horizon + 1):
        X.append(serie[t - window : t])
        y.append(serie[t : t + horizon])
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


def particion_temporal(serie: np.ndarray, semanas_prueba: int) -> tuple[np.ndarray, np.ndarray]:
    """Separa las últimas `semanas_prueba` semanas como conjunto de prueba (sin mezclar el orden).

    El conjunto de prueba se fija ANTES de entrenar (protocolo de evaluación, EDT 1.3.4.2).
    """
    return serie[:-semanas_prueba], serie[-semanas_prueba:]
