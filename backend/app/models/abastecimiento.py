"""EP-04 Compras y recepciones · EP-05 Inventario y existencias."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base_mixins import Timestamps
from app.models.enums import EstadoCompra, OrigenConsumo, TipoMovimiento
from app.models.lotes import Lote
from app.models.proveedores import Proveedor


class Compra(Timestamps, Base):
    __tablename__ = "compras"
    __table_args__ = (CheckConstraint("cantidad_kg > 0", name="ck_compra_cantidad_positiva"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tostador_id: Mapped[int] = mapped_column(ForeignKey("organizaciones.id", ondelete="CASCADE"), index=True)
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedores.id"), index=True)  # para el historial (HU-15)
    lote_id: Mapped[int] = mapped_column(ForeignKey("lotes.id"), index=True)
    cantidad_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    precio_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    fecha_compra: Mapped[date] = mapped_column(Date)
    fecha_entrega_acordada: Mapped[date] = mapped_column(Date)
    estado: Mapped[EstadoCompra] = mapped_column(
        Enum(EstadoCompra, native_enum=False, length=20),
        default=EstadoCompra.PENDIENTE,
        server_default=EstadoCompra.PENDIENTE.value,
    )
    observaciones: Mapped[str | None] = mapped_column(Text)

    lote: Mapped[Lote] = relationship()
    proveedor: Mapped[Proveedor] = relationship()
    recepcion: Mapped[Recepcion | None] = relationship(back_populates="compra", uselist=False)


class Recepcion(Base):
    """Recepción de una compra (HU-14). Genera un movimiento ENTRADA por la cantidad recibida."""

    __tablename__ = "recepciones"
    __table_args__ = (
        UniqueConstraint("compra_id", name="uq_recepcion_compra"),
        CheckConstraint("cantidad_recibida_kg >= 0", name="ck_recepcion_cantidad_no_negativa"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    compra_id: Mapped[int] = mapped_column(ForeignKey("compras.id", ondelete="CASCADE"))
    fecha_recepcion: Mapped[date] = mapped_column(Date)
    cantidad_recibida_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    observaciones: Mapped[str | None] = mapped_column(Text)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    compra: Mapped[Compra] = relationship(back_populates="recepcion")


class MovimientoInventario(Base):
    """Entradas, consumos, mermas y ajustes de café verde (HU-16).

    Existencias de un lote = Σ ENTRADA − Σ CONSUMO − Σ MERMA + Σ AJUSTE (HU-17).
    ENTRADA, CONSUMO y MERMA se guardan con cantidad positiva; AJUSTE con signo (+/−).
    """

    __tablename__ = "movimientos_inventario"
    __table_args__ = (
        CheckConstraint(
            "(tipo = 'AJUSTE' AND cantidad_kg <> 0) OR (tipo <> 'AJUSTE' AND cantidad_kg > 0)",
            name="ck_movimiento_cantidad",
        ),
        CheckConstraint("tipo <> 'AJUSTE' OR motivo IS NOT NULL", name="ck_ajuste_con_motivo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tostador_id: Mapped[int] = mapped_column(ForeignKey("organizaciones.id", ondelete="CASCADE"), index=True)
    lote_id: Mapped[int] = mapped_column(ForeignKey("lotes.id"), index=True)
    recepcion_id: Mapped[int | None] = mapped_column(ForeignKey("recepciones.id", ondelete="CASCADE"))
    tipo: Mapped[TipoMovimiento] = mapped_column(Enum(TipoMovimiento, native_enum=False, length=20))
    cantidad_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    fecha: Mapped[date] = mapped_column(Date, index=True)
    motivo: Mapped[str | None] = mapped_column(String(200))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lote: Mapped[Lote] = relationship()


class ConsumoHistorico(Base):
    """Historial semanal de consumo importado desde CSV/Excel (HU-18).

    La serie semanal que usa el pronóstico = consumo_historico + movimientos CONSUMO agregados por semana.
    `semana` es siempre el lunes de la semana.
    """

    __tablename__ = "consumo_historico"
    __table_args__ = (
        UniqueConstraint("tostador_id", "semana", name="uq_consumo_semana"),
        CheckConstraint("kg_consumidos >= 0", name="ck_consumo_no_negativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tostador_id: Mapped[int] = mapped_column(ForeignKey("organizaciones.id", ondelete="CASCADE"), index=True)
    semana: Mapped[date] = mapped_column(Date)
    kg_consumidos: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    origen: Mapped[OrigenConsumo] = mapped_column(
        Enum(OrigenConsumo, native_enum=False, length=20),
        default=OrigenConsumo.IMPORTADO,
        server_default=OrigenConsumo.IMPORTADO.value,
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
