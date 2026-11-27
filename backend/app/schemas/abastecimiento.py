"""EP-04 Compras y recepciones (HU-13 a HU-15) · EP-05 Inventario (HU-16 a HU-18)."""

import datetime as dt

from pydantic import BaseModel, Field, model_validator

from app.models.enums import EstadoCompra, TipoMovimiento
from app.schemas.comunes import Esquema, Kg, KgConSigno, Soles


class CompraIn(BaseModel):
    lote_id: int
    cantidad_kg: Kg = Field(gt=0)
    precio_kg: Soles
    fecha_compra: dt.date
    fecha_entrega_acordada: dt.date
    observaciones: str | None = None

    @model_validator(mode="after")
    def entrega_posterior(self):
        if self.fecha_entrega_acordada < self.fecha_compra:
            raise ValueError("La fecha de entrega no puede ser anterior a la fecha de compra")
        return self


class RecepcionIn(BaseModel):
    fecha_recepcion: dt.date
    cantidad_recibida_kg: Kg = Field(gt=0)  # una recepción sin nada recibido no genera entrada de inventario
    observaciones: str | None = None


class RecepcionOut(Esquema):
    id: int
    fecha_recepcion: dt.date
    cantidad_recibida_kg: Kg
    diferencia_kg: KgConSigno  # recibida - acordada (negativo = faltante)
    observaciones: str | None


class CompraOut(Esquema):
    id: int
    lote_id: int
    lote_codigo: str
    proveedor_id: int
    proveedor_nombre: str
    cantidad_kg: Kg
    precio_kg: Soles
    total: Soles
    fecha_compra: dt.date
    fecha_entrega_acordada: dt.date
    estado: EstadoCompra
    observaciones: str | None
    recepcion: RecepcionOut | None
    advertencia: str | None = None  # HU-13: "La cantidad supera lo disponible en el lote"


class PedidoRecibidoOut(Esquema):
    """Vista de la cooperativa de una compra hecha sobre uno de sus lotes."""

    id: int
    tostador: str
    lote_id: int
    lote_codigo: str
    cantidad_kg: Kg
    recibido_kg: Kg
    fecha_compra: dt.date
    fecha_entrega_acordada: dt.date
    estado: EstadoCompra


class MovimientoIn(BaseModel):
    """HU-16. ENTRADA no se registra a mano: la genera la recepción (HU-14)."""

    lote_id: int
    tipo: TipoMovimiento
    cantidad_kg: KgConSigno  # positiva; con signo solo en AJUSTE
    fecha: dt.date
    motivo: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def reglas(self):
        if self.tipo == TipoMovimiento.ENTRADA:
            raise ValueError("Las entradas se generan al registrar una recepción")
        if self.tipo == TipoMovimiento.AJUSTE:
            if not self.motivo:
                raise ValueError("El ajuste requiere un motivo")
            if self.cantidad_kg == 0:
                raise ValueError("El ajuste no puede ser 0")
        elif self.cantidad_kg <= 0:
            raise ValueError("La cantidad debe ser mayor que 0")
        return self


class MovimientoOut(Esquema):
    id: int
    lote_id: int
    tipo: TipoMovimiento
    cantidad_kg: KgConSigno
    fecha: dt.date
    motivo: str | None
    creado_en: dt.datetime


class ExistenciaLoteOut(BaseModel):
    lote_id: int
    lote_codigo: str
    proveedor_nombre: str
    existencias_kg: Kg


class ExistenciasOut(BaseModel):
    """HU-17."""

    total_kg: Kg
    lotes: list[ExistenciaLoteOut]


class ErrorFila(BaseModel):
    fila: int
    error: str


class ImportacionOut(BaseModel):
    """HU-18: si `errores` no está vacío, no se importó ninguna fila."""

    semanas_importadas: int
    desde: dt.date | None
    hasta: dt.date | None
    errores: list[ErrorFila]
