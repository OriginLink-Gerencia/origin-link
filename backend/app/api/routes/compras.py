"""EP-04 Compras y recepciones."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import exigir_tostador
from app.db.session import get_db
from app.models.abastecimiento import Compra
from app.models.enums import EstadoCompra, EstadoVinculo
from app.models.identidad import Usuario
from app.models.lotes import Lote
from app.models.proveedores import Proveedor
from app.schemas.abastecimiento import CompraIn, CompraOut
from app.services.compras import ADVERTENCIA_CANTIDAD, compra_a_out
from app.services.lotes import lotes_visibles

router = APIRouter(prefix="/compras", tags=["compras"])


def _ficha_del_lote(db: Session, usuario: Usuario, lote: Lote) -> Proveedor:
    """Ficha del directorio del tostador a la que se le compra: la del lote o la de la cooperativa vinculada."""
    if lote.proveedor_id is not None:
        return lote.proveedor
    ficha = db.scalar(
        select(Proveedor).where(
            Proveedor.tostador_id == usuario.organizacion_id,
            Proveedor.organizacion_proveedora_id == lote.organizacion_proveedora_id,
            Proveedor.estado_vinculo == EstadoVinculo.VINCULADO,
        )
    )
    if ficha is None:  # no debería ocurrir: el lote es visible solo si hay vínculo
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    return ficha


@router.post("", response_model=CompraOut, status_code=status.HTTP_201_CREATED)
def registrar(datos: CompraIn, usuario: Usuario = Depends(exigir_tostador), db: Session = Depends(get_db)) -> CompraOut:
    """HU-13: compra de un lote visible para el tostador. Si pide más de lo disponible, se registra con advertencia."""
    lote = db.scalar(lotes_visibles(usuario).where(Lote.id == datos.lote_id))
    if lote is None:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    ficha = _ficha_del_lote(db, usuario, lote)
    compra = Compra(tostador_id=usuario.organizacion_id, proveedor_id=ficha.id, **datos.model_dump())
    db.add(compra)
    db.commit()
    db.refresh(compra)
    advertencia = ADVERTENCIA_CANTIDAD if datos.cantidad_kg > lote.cantidad_disponible_kg else None
    return compra_a_out(compra, advertencia)


@router.get("", response_model=list[CompraOut])
def listar(
    estado: EstadoCompra | None = None,
    proveedor_id: int | None = None,
    usuario: Usuario = Depends(exigir_tostador),
    db: Session = Depends(get_db),
) -> list[CompraOut]:
    consulta = select(Compra).where(Compra.tostador_id == usuario.organizacion_id).order_by(Compra.id.desc())
    if estado is not None:
        consulta = consulta.where(Compra.estado == estado)
    if proveedor_id is not None:
        consulta = consulta.where(Compra.proveedor_id == proveedor_id)
    return [compra_a_out(c) for c in db.scalars(consulta)]
