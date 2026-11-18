"""Método de referencia (promedio móvil de 4 semanas) y métrica MAPE.

El promedio móvil cumple dos funciones del proyecto:
1. Línea base para el indicador OE4-I3 (la TCN debe tener menor MAPE).
2. Mecanismo de respaldo (EDT 1.5.2.2) si el modelo TCN no está disponible.
"""

import numpy as np


def promedio_movil(serie: np.ndarray, ventana: int = 4, horizon: int = 4) -> np.ndarray:
    """Pronostica las próximas `horizon` semanas como el promedio de las últimas `ventana`."""
    serie = np.asarray(serie, dtype=float)
    if len(serie) < ventana:
        raise ValueError(f"Se necesitan al menos {ventana} semanas de historial")
    return np.full(horizon, serie[-ventana:].mean())


def mape(real: np.ndarray, pronostico: np.ndarray) -> float:
    """Error porcentual absoluto medio (%). Ignora semanas con consumo real 0."""
    real = np.asarray(real, dtype=float)
    pronostico = np.asarray(pronostico, dtype=float)
    mask = real != 0
    if not mask.any():
        raise ValueError("No hay semanas con consumo distinto de cero para calcular el MAPE")
    return float(np.mean(np.abs((real[mask] - pronostico[mask]) / real[mask])) * 100)
