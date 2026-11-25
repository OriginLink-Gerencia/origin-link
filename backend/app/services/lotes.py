"""Reglas compartidas de lotes: conversión a la respuesta del contrato."""

from sqlalchemy import Select, or_, select

from app.models.enums import EstadoVinculo, TipoOrganizacion
from app.models.identidad import Usuario
from app.models.lotes import Lote
from app.models.proveedores import Proveedor
from app.schemas.lotes import LoteOut


def lotes_visibles(usuario: Usuario) -> Select[tuple[Lote]]:
    """Lotes que el usuario puede ver (HU-04): toda consulta de lotes parte de aquí.

    - Cooperativa: solo los suyos (publicados o no).
    - Tostador: los publicados por cooperativas con las que está VINCULADO, más los que registró
      él mismo para proveedores de su directorio. Nunca los de cooperativas sin vínculo.
    """
    consulta = select(Lote).order_by(Lote.id.desc())
    if usuario.organizacion.tipo == TipoOrganizacion.PROVEEDOR:
        return consulta.where(Lote.organizacion_proveedora_id == usuario.organizacion_id)
    mis_fichas = select(Proveedor.id).where(Proveedor.tostador_id == usuario.organizacion_id)
    mis_cooperativas = select(Proveedor.organizacion_proveedora_id).where(
        Proveedor.tostador_id == usuario.organizacion_id,
        Proveedor.estado_vinculo == EstadoVinculo.VINCULADO,
        Proveedor.organizacion_proveedora_id.is_not(None),
    )
    return consulta.where(
        or_(
            Lote.proveedor_id.in_(mis_fichas),
            (Lote.organizacion_proveedora_id.in_(mis_cooperativas)) & Lote.publicado.is_(True),
        )
    )


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
