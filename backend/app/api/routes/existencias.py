"""EP-05 Inventario: existencias actuales (HU-17)."""

from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import exigir_tostador
from app.db.session import get_db
from app.models.identidad import Usuario
from app.models.lotes import Lote
from app.schemas.abastecimiento import ExistenciaLoteOut, ExistenciasOut
from app.services.inventario import existencias_por_lote
from app.services.lotes import lote_a_out

router = APIRouter(prefix="/existencias", tags=["inventario"])


@router.get("", response_model=ExistenciasOut)
def ver(usuario: Usuario = Depends(exigir_tostador), db: Session = Depends(get_db)) -> ExistenciasOut:
    """HU-17: kg por lote y total. Los lotes consumidos por completo no aparecen en la lista."""
    con_stock = {lote_id: kg for lote_id, kg in existencias_por_lote(db, usuario.organizacion_id).items() if kg > 0}
    if not con_stock:
        return ExistenciasOut(total_kg=Decimal(0), lotes=[])
    lotes = db.scalars(select(Lote).where(Lote.id.in_(con_stock)).order_by(Lote.codigo, Lote.id))
    items = [
        ExistenciaLoteOut(
            lote_id=lote.id,
            lote_codigo=lote.codigo,
            proveedor_nombre=lote_a_out(lote).proveedor_nombre,
            existencias_kg=con_stock[lote.id],
        )
        for lote in lotes
    ]
    return ExistenciasOut(total_kg=sum((i.existencias_kg for i in items), Decimal(0)), lotes=items)
