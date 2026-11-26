"""Pedidos que reciben las cooperativas: compras de los tostadores sobre los lotes que ellas publicaron."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import exigir_cooperativa
from app.db.session import get_db
from app.models.abastecimiento import Compra
from app.models.identidad import Usuario
from app.models.lotes import Lote
from app.schemas.abastecimiento import PedidoRecibidoOut

router = APIRouter(prefix="/pedidos-recibidos", tags=["pedidos"])


@router.get("", response_model=list[PedidoRecibidoOut])
def listar(usuario: Usuario = Depends(exigir_cooperativa), db: Session = Depends(get_db)) -> list[PedidoRecibidoOut]:
    """Solo lectura: de la compra más reciente a la más antigua. No incluye precios ni datos internos del tostador."""
    compras = db.scalars(
        select(Compra)
        .join(Lote, Compra.lote_id == Lote.id)
        .where(Lote.organizacion_proveedora_id == usuario.organizacion_id)
        .order_by(Compra.id.desc())
    )
    return [
        PedidoRecibidoOut(
            id=c.id,
            tostador=c.tostador.nombre,
            lote_id=c.lote_id,
            lote_codigo=c.lote.codigo,
            cantidad_kg=c.cantidad_kg,
            recibido_kg=c.recepcion.cantidad_recibida_kg if c.recepcion else 0,
            fecha_compra=c.fecha_compra,
            fecha_entrega_acordada=c.fecha_entrega_acordada,
            estado=c.estado,
        )
        for c in compras
    ]
