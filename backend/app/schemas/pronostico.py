"""EP-06 Pronóstico (HU-20) · EP-07 Recomendaciones y alertas (HU-21, HU-22). Contrato preliminar (Sprint B)."""

import datetime as dt
from typing import Literal

from pydantic import BaseModel

from app.schemas.comunes import Kg


class PuntoSerie(BaseModel):
    semana: dt.date  # lunes de la semana
    kg: Kg


class PronosticoOut(BaseModel):
    metodo: Literal["TCN", "PROMEDIO_MOVIL"]
    motivo_metodo: str | None  # ej. "Historial insuficiente (10 semanas; mínimo 24)"
    historial: list[PuntoSerie]  # consumo real (importado + registrado)
    pronostico: list[PuntoSerie]  # próximas 4 semanas
    mape_referencia: float | None  # MAPE del modelo en el conjunto de prueba, si existe


class FactoresRecomendacion(BaseModel):
    existencias_kg: Kg
    consumo_semanal_pronosticado_kg: list[PuntoSerie]
    plazo_entrega_dias: int
    semanas_cobertura: int
    cantidad_minima_kg: Kg
    metodo_pronostico: Literal["TCN", "PROMEDIO_MOVIL"]


class RecomendacionOut(BaseModel):
    """HU-21. No recomienda proveedor: solo cuánto y cuándo."""

    fecha_limite_compra: dt.date
    cantidad_sugerida_kg: Kg
    semanas_cobertura_actual: float  # existencias / consumo semanal pronosticado
    dias_cobertura_actual: int | None  # días que alcanzan las existencias; None si no hay consumo pronosticado
    factores: FactoresRecomendacion
    explicacion: str  # texto legible con el cálculo


class AlertaOut(BaseModel):
    """HU-22."""

    tipo: Literal["STOCK_BAJO", "COMPRA_PROXIMA"]
    mensaje: str
    semanas_cobertura_restantes: float
    fecha_limite_compra: dt.date
