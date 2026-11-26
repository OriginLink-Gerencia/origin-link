"""EP-02 Proveedores y relaciones privadas (HU-05 a HU-07)."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import EstadoVinculo
from app.schemas.comunes import Esquema


def _nombre_valido(v: str | None) -> str:
    """El nombre es obligatorio: sin espacios sobrantes y con al menos 2 caracteres (HU-05, escenario 2)."""
    if v is None or len(v.strip()) < 2:
        raise ValueError("El nombre es obligatorio (mínimo 2 caracteres)")
    return v.strip()


class ProveedorIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    region: str | None = Field(default=None, max_length=100)
    contacto_nombre: str | None = Field(default=None, max_length=120)
    contacto_telefono: str | None = Field(default=None, max_length=30)
    contacto_email: EmailStr | None = None

    _normalizar_nombre = field_validator("nombre")(_nombre_valido)


class ProveedorUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=150)
    region: str | None = Field(default=None, max_length=100)
    contacto_nombre: str | None = Field(default=None, max_length=120)
    contacto_telefono: str | None = Field(default=None, max_length=30)
    contacto_email: EmailStr | None = None

    _normalizar_nombre = field_validator("nombre")(_nombre_valido)  # no admite null ni vacío si se envía


class InvitacionVigenteOut(Esquema):
    token: str
    expira_en: datetime


class ProveedorOut(Esquema):
    id: int
    nombre: str
    region: str | None
    contacto_nombre: str | None
    contacto_telefono: str | None
    contacto_email: str | None
    estado_vinculo: EstadoVinculo
    organizacion_proveedora_id: int | None
    invitacion_vigente: InvitacionVigenteOut | None = None  # solo mientras el proveedor está INVITADO
    creado_en: datetime


class InvitacionOut(BaseModel):
    """HU-06: respuesta al generar una invitación."""

    token: str
    url: str  # ej. https://<frontend>/invitacion/<token>
    expira_en: datetime


class InvitacionInfoOut(BaseModel):
    """Información pública de una invitación (pantalla de registro de la cooperativa)."""

    tostador: str
    proveedor: str
    vigente: bool
    expira_en: datetime


class VinculoOut(BaseModel):
    """HU-07, vista de la cooperativa: tostadores con los que comparte lotes."""

    tostador_id: int
    tostador: str
    vinculado_desde: datetime
