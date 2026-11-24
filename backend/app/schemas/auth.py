"""EP-01 Identidad y acceso (HU-01 a HU-04)."""

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import TipoOrganizacion
from app.schemas.comunes import Esquema


class RegistroTostadorIn(BaseModel):
    empresa: str = Field(min_length=2, max_length=150)
    ruc: str | None = Field(default=None, pattern=r"^\d{11}$")
    nombre: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegistroPorInvitacionIn(BaseModel):
    """HU-03: la cooperativa crea su cuenta con el token de la invitación."""

    token: str
    empresa: str = Field(min_length=2, max_length=150)
    ruc: str | None = Field(default=None, pattern=r"^\d{11}$")
    region: str | None = Field(default=None, max_length=100)
    nombre: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class OrganizacionOut(Esquema):
    id: int
    tipo: TipoOrganizacion
    nombre: str
    ruc: str | None
    region: str | None


class UsuarioOut(Esquema):
    id: int
    nombre: str
    email: EmailStr
    organizacion: OrganizacionOut


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut
