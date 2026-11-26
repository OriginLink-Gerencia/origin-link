"""EP-05 Inventario: movimientos de café verde (HU-16)."""

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.api.deps import exigir_tostador
from app.db.session import get_db
from app.models.abastecimiento import MovimientoInventario
from app.models.enums import TipoMovimiento
from app.models.identidad import Usuario
from app.models.lotes import Lote
from app.schemas.abastecimiento import MovimientoIn, MovimientoOut
from app.services.inventario import existencias_lote
from app.services.lotes import lotes_visibles

router = APIRouter(prefix="/movimientos", tags=["inventario"])


def _lote_del_tostador(db: Session, usuario: Usuario, lote_id: int) -> None:
    """El lote debe ser visible para el tostador o tener ya movimientos suyos (p. ej. se despublicó tras comprarlo)."""
    visible = db.scalar(lotes_visibles(usuario).where(Lote.id == lote_id).with_only_columns(Lote.id))
    con_movimientos = db.scalar(
        select(
            exists().where(
                MovimientoInventario.tostador_id == usuario.organizacion_id, MovimientoInventario.lote_id == lote_id
            )
        )
    )
    if visible is None and not con_movimientos:
        raise HTTPException(status_code=404, detail="Lote no encontrado")


@router.post("", response_model=MovimientoOut, status_code=status.HTTP_201_CREATED)
def registrar(
    datos: MovimientoIn, usuario: Usuario = Depends(exigir_tostador), db: Session = Depends(get_db)
) -> MovimientoInventario:
    """HU-16: consumo, merma o ajuste. Nunca se permite dejar las existencias de un lote por debajo de 0."""
    _lote_del_tostador(db, usuario, datos.lote_id)
    efecto = datos.cantidad_kg if datos.tipo == TipoMovimiento.AJUSTE else -datos.cantidad_kg
    if efecto < 0 and existencias_lote(db, usuario.organizacion_id, datos.lote_id) + efecto < 0:
        raise HTTPException(status_code=400, detail="La cantidad supera las existencias del lote")
    movimiento = MovimientoInventario(tostador_id=usuario.organizacion_id, **datos.model_dump())
    db.add(movimiento)
    db.commit()
    db.refresh(movimiento)
    return movimiento


@router.get("", response_model=list[MovimientoOut])
def listar(
    lote_id: int | None = None,
    tipo: TipoMovimiento | None = None,
    desde: dt.date | None = None,
    hasta: dt.date | None = None,
    usuario: Usuario = Depends(exigir_tostador),
    db: Session = Depends(get_db),
) -> list[MovimientoInventario]:
    consulta = select(MovimientoInventario).where(MovimientoInventario.tostador_id == usuario.organizacion_id)
    if lote_id is not None:
        consulta = consulta.where(MovimientoInventario.lote_id == lote_id)
    if tipo is not None:
        consulta = consulta.where(MovimientoInventario.tipo == tipo)
    if desde is not None:
        consulta = consulta.where(MovimientoInventario.fecha >= desde)
    if hasta is not None:
        consulta = consulta.where(MovimientoInventario.fecha <= hasta)
    return list(db.scalars(consulta.order_by(MovimientoInventario.fecha.desc(), MovimientoInventario.id.desc())))
