"""Existencias de café verde: se calculan desde los movimientos, nunca se guardan (HU-16, HU-17).

Existencias de un lote = Σ ENTRADA − Σ CONSUMO − Σ MERMA + Σ AJUSTE (el ajuste ya viene con signo).
"""

from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.abastecimiento import MovimientoInventario as Mov
from app.models.enums import TipoMovimiento

# Signo con el que cada tipo afecta las existencias. AJUSTE se guarda con su propio signo.
_EFECTO = case(
    (Mov.tipo == TipoMovimiento.ENTRADA, Mov.cantidad_kg),
    (Mov.tipo == TipoMovimiento.AJUSTE, Mov.cantidad_kg),
    else_=-Mov.cantidad_kg,  # CONSUMO y MERMA
)


def existencias_por_lote(db: Session, tostador_id: int) -> dict[int, Decimal]:
    """Existencias de cada lote con movimientos del tostador (incluye los que quedaron en 0)."""
    filas = db.execute(
        select(Mov.lote_id, func.sum(_EFECTO)).where(Mov.tostador_id == tostador_id).group_by(Mov.lote_id)
    )
    return {lote_id: Decimal(total) for lote_id, total in filas}


def existencias_lote(db: Session, tostador_id: int, lote_id: int) -> Decimal:
    total = db.scalar(select(func.sum(_EFECTO)).where(Mov.tostador_id == tostador_id, Mov.lote_id == lote_id))
    return Decimal(total or 0)
