"""EP-03 Gestión colaborativa de lotes."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base_mixins import Timestamps
from app.models.enums import ProcesoCafe
from app.models.identidad import Organizacion
from app.models.proveedores import Proveedor


class Lote(Timestamps, Base):
    """Lote de café verde.

    - Publicado por una cooperativa (HU-08): `organizacion_proveedora_id` = la cooperativa. Lo ven todos
      los tostadores vinculados con ella.
    - Registrado por el tostador para un proveedor sin cuenta (HU-11): `proveedor_id` = ficha del
      directorio del tostador. Solo lo ve ese tostador.
    """

    __tablename__ = "lotes"
    __table_args__ = (
        CheckConstraint(
            "organizacion_proveedora_id IS NOT NULL OR proveedor_id IS NOT NULL", name="ck_lote_tiene_proveedor"
        ),
        CheckConstraint("cantidad_disponible_kg >= 0", name="ck_lote_cantidad_no_negativa"),
        CheckConstraint("altitud_msnm IS NULL OR altitud_msnm >= 0", name="ck_lote_altitud_no_negativa"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organizacion_proveedora_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizaciones.id", ondelete="CASCADE"), index=True
    )
    proveedor_id: Mapped[int | None] = mapped_column(ForeignKey("proveedores.id", ondelete="CASCADE"), index=True)

    codigo: Mapped[str] = mapped_column(String(40))  # código interno del proveedor, ej. "JAEN-2026-07"
    region: Mapped[str] = mapped_column(String(100))  # procedencia: departamento / provincia
    finca: Mapped[str | None] = mapped_column(String(120))
    variedad: Mapped[str] = mapped_column(String(80))
    proceso: Mapped[ProcesoCafe] = mapped_column(Enum(ProcesoCafe, native_enum=False, length=20))
    cosecha: Mapped[str] = mapped_column(String(20))  # ej. "2026" o "2026-A"
    altitud_msnm: Mapped[int | None] = mapped_column(Integer)
    caracteristicas: Mapped[str | None] = mapped_column(Text)  # notas sensoriales, puntaje declarado, etc.

    # Disponibilidad y condiciones de abastecimiento (HU-10)
    cantidad_disponible_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    precio_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2))  # soles por kg
    cantidad_minima_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, server_default="0")
    plazo_entrega_dias: Mapped[int] = mapped_column(Integer, default=7, server_default="7")
    publicado: Mapped[bool] = mapped_column(default=True, server_default="true")

    organizacion_proveedora: Mapped[Organizacion | None] = relationship()
    proveedor: Mapped[Proveedor | None] = relationship()
