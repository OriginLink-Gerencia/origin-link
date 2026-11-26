"""Reglas compartidas de compras y recepciones."""

from app.models.abastecimiento import Compra
from app.schemas.abastecimiento import CompraOut, RecepcionOut

ADVERTENCIA_CANTIDAD = "La cantidad supera lo disponible en el lote"


def compra_a_out(compra: Compra, advertencia: str | None = None) -> CompraOut:
    recepcion = None
    if compra.recepcion is not None:
        r = compra.recepcion
        recepcion = RecepcionOut(
            id=r.id,
            fecha_recepcion=r.fecha_recepcion,
            cantidad_recibida_kg=r.cantidad_recibida_kg,
            diferencia_kg=r.cantidad_recibida_kg - compra.cantidad_kg,  # negativo = faltante
            observaciones=r.observaciones,
        )
    return CompraOut(
        id=compra.id,
        lote_id=compra.lote_id,
        lote_codigo=compra.lote.codigo,
        proveedor_id=compra.proveedor_id,
        proveedor_nombre=compra.proveedor.nombre,
        cantidad_kg=compra.cantidad_kg,
        precio_kg=compra.precio_kg,
        total=compra.cantidad_kg * compra.precio_kg,
        fecha_compra=compra.fecha_compra,
        fecha_entrega_acordada=compra.fecha_entrega_acordada,
        estado=compra.estado,
        observaciones=compra.observaciones,
        recepcion=recepcion,
        advertencia=advertencia,
    )
