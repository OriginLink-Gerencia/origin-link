"""EP-01 Identidad y acceso: organizaciones (tostadores y proveedores) y sus usuarios."""

from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base_mixins import Timestamps
from app.models.enums import TipoOrganizacion


class Organizacion(Timestamps, Base):
    """Empresa tostadora o empresa productora/cooperativa."""

    __tablename__ = "organizaciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[TipoOrganizacion] = mapped_column(Enum(TipoOrganizacion, native_enum=False, length=20))
    nombre: Mapped[str] = mapped_column(String(150))
    ruc: Mapped[str | None] = mapped_column(String(11))
    region: Mapped[str | None] = mapped_column(String(100))
    # Solo tostadores: semanas de consumo que debe cubrir cada compra (HU-21).
    semanas_cobertura: Mapped[int] = mapped_column(Integer, default=2, server_default="2")

    usuarios: Mapped[list[Usuario]] = relationship(back_populates="organizacion")


class Usuario(Timestamps, Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    organizacion_id: Mapped[int] = mapped_column(ForeignKey("organizaciones.id", ondelete="CASCADE"), index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    activo: Mapped[bool] = mapped_column(default=True, server_default="true")

    organizacion: Mapped[Organizacion] = relationship(back_populates="usuarios")
