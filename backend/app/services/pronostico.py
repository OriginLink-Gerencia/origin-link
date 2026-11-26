"""Pronóstico de consumo semanal (HU-20): TCN si hay modelo e historial suficiente; si no, promedio móvil (ADR-0003)."""

import datetime as dt
import logging
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.schemas.pronostico import PuntoSerie
from app.services.consumo import serie_semanal
from app.services.modelo_tcn import cargar_modelo

log = logging.getLogger(__name__)

HORIZONTE = 4
VENTANA_PM = 4
SEMANAS_BACKTEST = 6  # el MAPE de referencia se mide sobre las últimas 6 semanas (Charter M4)
SEMANAS_EN_RESPUESTA = 104


class HistorialInsuficiente(Exception):
    pass


@dataclass
class Resultado:
    metodo: str
    motivo: str | None
    historial: list[PuntoSerie]
    pronostico: list[PuntoSerie]
    mape: float | None


def promedio_movil(kg: list[float], ventana: int = VENTANA_PM, horizonte: int = HORIZONTE) -> list[float]:
    return [sum(kg[-ventana:]) / ventana] * horizonte


def _mape(reales: list[float], predichos: list[float]) -> float | None:
    pares = [(r, p) for r, p in zip(reales, predichos, strict=True) if r != 0]
    if not pares:
        return None
    return sum(abs(r - p) / r for r, p in pares) / len(pares) * 100


def _backtest(kg: list[float], predecir, minimo_previo: int) -> float | None:
    """MAPE a 1 semana sobre las últimas semanas, usando solo lo que se sabía antes de cada una."""
    inicio = max(minimo_previo, len(kg) - SEMANAS_BACKTEST)
    reales, predichos = [], []
    for i in range(inicio, len(kg)):
        reales.append(kg[i])
        predichos.append(predecir(i)[0])
    return _mape(reales, predichos) if reales else None


def _redondear(valor: float, decimales: int = 2) -> Decimal:
    return Decimal(str(valor)).quantize(Decimal(1).scaleb(-decimales), rounding=ROUND_HALF_UP)


def calcular(db: Session, tostador_id: int, hoy: dt.date) -> Resultado:
    serie = serie_semanal(db, tostador_id, hoy)
    if not serie:
        raise HistorialInsuficiente("Aún no hay historial de consumo. Importa tu consumo semanal (CSV o Excel) primero")
    if len(serie) < VENTANA_PM:
        raise HistorialInsuficiente(
            f"Se necesitan al menos {VENTANA_PM} semanas de consumo para pronosticar (hay {len(serie)})"
        )
    semanas = [s for s, _ in serie]
    kg = [float(v) for _, v in serie]

    metodo, motivo = "PROMEDIO_MOVIL", None
    modelo = cargar_modelo()
    prediccion: list[float] | None = None
    if modelo is None:
        motivo = "El modelo TCN no está disponible; se usa el promedio móvil de 4 semanas"
    elif len(kg) < modelo.minimo_semanas:
        motivo = f"Historial insuficiente ({len(kg)} semanas; el modelo necesita al menos {modelo.minimo_semanas})"
    else:
        try:
            prediccion = [max(0.0, float(x)) for x in modelo.pronosticar(semanas, kg)][:HORIZONTE]
            metodo = "TCN"
        except Exception:
            log.exception("La TCN falló; se usa el promedio móvil")
            motivo = "El modelo TCN falló; se usa el promedio móvil de 4 semanas"
    if prediccion is None:
        prediccion = promedio_movil(kg)

    if metodo == "TCN":
        mape = _backtest(kg, lambda i: modelo.pronosticar(semanas[:i], kg[:i]), modelo.minimo_semanas)
    else:
        mape = _backtest(kg, lambda i: promedio_movil(kg[:i]), VENTANA_PM)

    primera = semanas[-1] + dt.timedelta(weeks=1)
    return Resultado(
        metodo=metodo,
        motivo=motivo,
        historial=[PuntoSerie(semana=s, kg=v) for s, v in serie[-SEMANAS_EN_RESPUESTA:]],
        pronostico=[
            PuntoSerie(semana=primera + dt.timedelta(weeks=i), kg=_redondear(v)) for i, v in enumerate(prediccion)
        ],
        mape=None if mape is None else round(mape, 1),
    )
