"""EP-03 Gestión colaborativa de lotes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import exigir_cooperativa
from app.db.session import get_db
from app.models.enums import EstadoVinculo
from app.models.identidad import Usuario
from app.models.lotes import Lote
from app.models.proveedores import Proveedor
from app.schemas.lotes import LoteIn, LoteOut
from app.services.lotes import lote_a_out

router = APIRouter(prefix="/lotes", tags=["lotes"])


@router.post("", response_model=LoteOut, status_code=status.HTTP_201_CREATED)
def publicar(datos: LoteIn, usuario: Usuario = Depends(exigir_cooperativa), db: Session = Depends(get_db)) -> LoteOut:
    """HU-08: la cooperativa publica un lote; lo ven solo los tostadores con los que está vinculada."""
    if datos.proveedor_id is not None:
        raise HTTPException(status_code=400, detail="Solo un tostador puede registrar un lote a nombre de un proveedor")
    vinculado = db.scalar(
        select(Proveedor.id)
        .where(
            Proveedor.organizacion_proveedora_id == usuario.organizacion_id,
            Proveedor.estado_vinculo == EstadoVinculo.VINCULADO,
        )
        .limit(1)
    )
    if vinculado is None:
        raise HTTPException(status_code=400, detail="Para publicar un lote debes estar vinculado con un tostador")
    lote = Lote(organizacion_proveedora_id=usuario.organizacion_id, **datos.model_dump(exclude={"proveedor_id"}))
    db.add(lote)
    db.commit()
    db.refresh(lote)
    return lote_a_out(lote)
