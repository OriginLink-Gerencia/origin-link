"""Reglas compartidas de lotes: conversión a la respuesta del contrato."""

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

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


def fichas_de_cooperativas(db: Session, usuario: Usuario) -> dict[int, int]:
    """{organización de la cooperativa: ficha vinculada} del tostador. Vacío para una cooperativa."""
    if usuario.organizacion.tipo != TipoOrganizacion.TOSTADOR:
        return {}
    fichas = db.execute(
        select(Proveedor.organizacion_proveedora_id, Proveedor.id).where(
            Proveedor.tostador_id == usuario.organizacion_id,
            Proveedor.estado_vinculo == EstadoVinculo.VINCULADO,
            Proveedor.organizacion_proveedora_id.is_not(None),
        )
    )
    return {organizacion: ficha for organizacion, ficha in fichas}


def lote_a_out(lote: Lote, fichas: dict[int, int] | None = None) -> LoteOut:
    """Arma `LoteOut`: proveedor (ficha del directorio, si la hay), su nombre y la bandera de agotado.

    `fichas` es el resultado de `fichas_de_cooperativas`; sin él, los lotes de cooperativa no indican ficha.
    """
    registrado_por_tostador = lote.proveedor_id is not None
    origen = lote.proveedor if registrado_por_tostador else lote.organizacion_proveedora
    return LoteOut(
        id=lote.id,
        proveedor_id=lote.proveedor_id or (fichas or {}).get(lote.organizacion_proveedora_id),
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
