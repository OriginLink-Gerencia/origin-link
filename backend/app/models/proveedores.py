"""EP-02 Proveedores y relaciones privadas."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base_mixins import Timestamps
from app.models.enums import EstadoVinculo
from app.models.identidad import Organizacion


class Proveedor(Timestamps, Base):
    """Proveedor en el directorio de UN tostador.

    El tostador lo registra (HU-05). Cuando el proveedor acepta la invitación (HU-03), se completa
    `organizacion_proveedora_id` y el estado pasa a VINCULADO. Una misma cooperativa puede estar en el
    directorio de varios tostadores (una fila por tostador).
    """

    __tablename__ = "proveedores"
    __table_args__ = (UniqueConstraint("tostador_id", "organizacion_proveedora_id", name="uq_proveedor_vinculo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tostador_id: Mapped[int] = mapped_column(ForeignKey("organizaciones.id", ondelete="CASCADE"), index=True)
    organizacion_proveedora_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizaciones.id", ondelete="SET NULL"), index=True
    )
    nombre: Mapped[str] = mapped_column(String(150))
    region: Mapped[str | None] = mapped_column(String(100))
    contacto_nombre: Mapped[str | None] = mapped_column(String(120))
    contacto_telefono: Mapped[str | None] = mapped_column(String(30))
    contacto_email: Mapped[str | None] = mapped_column(String(254))
    estado_vinculo: Mapped[EstadoVinculo] = mapped_column(
        Enum(EstadoVinculo, native_enum=False, length=20),
        default=EstadoVinculo.SIN_VINCULAR,
        server_default=EstadoVinculo.SIN_VINCULAR.value,
    )

    tostador: Mapped[Organizacion] = relationship(foreign_keys=[tostador_id])
    organizacion_proveedora: Mapped[Organizacion | None] = relationship(foreign_keys=[organizacion_proveedora_id])
    invitaciones: Mapped[list[Invitacion]] = relationship(back_populates="proveedor")

    @property
    def invitacion_vigente(self) -> Invitacion | None:
        """Enlace sin usar y sin vencer (HU-06), para que el tostador pueda volver a copiarlo."""
        ahora = datetime.now(UTC)
        vigentes = [
            i
            for i in self.invitaciones
            if i.usada_en is None and (i.expira_en if i.expira_en.tzinfo else i.expira_en.replace(tzinfo=UTC)) > ahora
        ]
        return max(vigentes, key=lambda i: i.creado_en, default=None)


class Invitacion(Base):
    """Enlace único y de un solo uso para que un proveedor se vincule con un tostador (HU-06)."""

    __tablename__ = "invitaciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedores.id", ondelete="CASCADE"), index=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))  # creado_en + 7 días
    usada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    proveedor: Mapped[Proveedor] = relationship(back_populates="invitaciones")
