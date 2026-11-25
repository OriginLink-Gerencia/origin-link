"""Reglas compartidas de lotes: conversión a la respuesta del contrato."""

from app.models.lotes import Lote
from app.schemas.lotes import LoteOut


def lote_a_out(lote: Lote) -> LoteOut:
    """Arma `LoteOut`: nombre del proveedor (cooperativa o ficha del directorio) y bandera de agotado."""
    registrado_por_tostador = lote.proveedor_id is not None
    origen = lote.proveedor if registrado_por_tostador else lote.organizacion_proveedora
    return LoteOut(
        id=lote.id,
        proveedor_nombre=origen.nombre,
        registrado_por_tostador=registrado_por_tostador,
        codigo=lote.codigo,
        region=lote.region,
        finca=lote.finca,
        variedad=lote.variedad,
        proceso=lote.proceso,
        cosecha=lote.cosecha,
        altitud_msnm=lote.altitud_msnm,
        caracteristicas=lote.caracteristicas,
        cantidad_disponible_kg=lote.cantidad_disponible_kg,
        precio_kg=lote.precio_kg,
        cantidad_minima_kg=lote.cantidad_minima_kg,
        plazo_entrega_dias=lote.plazo_entrega_dias,
        agotado=lote.cantidad_disponible_kg == 0,
        actualizado_en=lote.actualizado_en,
    )
