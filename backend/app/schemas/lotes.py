"""EP-03 Gestión colaborativa de lotes (HU-08 a HU-11)."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ProcesoCafe
from app.schemas.comunes import Esquema, Kg, Soles


class LoteIn(BaseModel):
    """HU-08 (cooperativa) y HU-11 (tostador, indicando `proveedor_id` de su directorio)."""

    proveedor_id: int | None = None  # solo HU-11
    codigo: str = Field(min_length=1, max_length=40)
    region: str = Field(min_length=2, max_length=100)
    finca: str | None = Field(default=None, max_length=120)
    variedad: str = Field(min_length=2, max_length=80)
    proceso: ProcesoCafe
    cosecha: str = Field(min_length=4, max_length=20)
    altitud_msnm: int | None = Field(default=None, ge=0, le=5000)
    caracteristicas: str | None = None
    cantidad_disponible_kg: Kg
    precio_kg: Soles
    cantidad_minima_kg: Kg = 0
    plazo_entrega_dias: int = Field(default=7, ge=0, le=180)


class DisponibilidadUpdate(BaseModel):
    """HU-10: solo se envían los campos que cambian."""

    cantidad_disponible_kg: Kg | None = None
    precio_kg: Soles | None = None
    cantidad_minima_kg: Kg | None = None
    plazo_entrega_dias: int | None = Field(default=None, ge=0, le=180)
    publicado: bool | None = None


class LoteOut(Esquema):
    id: int
    proveedor_nombre: str  # nombre de la cooperativa o del proveedor del directorio
    registrado_por_tostador: bool  # True en HU-11
    codigo: str
    region: str
    finca: str | None
    variedad: str
    proceso: ProcesoCafe
    cosecha: str
    altitud_msnm: int | None
    caracteristicas: str | None
    cantidad_disponible_kg: Kg
    precio_kg: Soles
    cantidad_minima_kg: Kg
    plazo_entrega_dias: int
    agotado: bool  # cantidad_disponible_kg == 0
    actualizado_en: datetime
