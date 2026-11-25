"""Dependencias compartidas de las rutas: usuario actual y control de rol (HU-04)."""

from fastapi import Depends, HTTPException

from app.models.enums import TipoOrganizacion
from app.models.identidad import Usuario


def get_usuario_actual() -> Usuario:
    """Usuario autenticado a partir del JWT del header Authorization.

    La lectura real del token se implementa en HU-01/HU-02 (`feature/HU-01-registro`), que reemplaza el
    cuerpo de esta función conservando su firma. Mientras tanto, toda ruta protegida responde 401 y las
    pruebas la sustituyen con `app.dependency_overrides`.
    """
    raise HTTPException(status_code=401, detail="Se requiere iniciar sesión", headers={"WWW-Authenticate": "Bearer"})


def exigir_tostador(usuario: Usuario = Depends(get_usuario_actual)) -> Usuario:
    """Rutas 🟤 del contrato: solo usuarios de una organización tostadora."""
    if usuario.organizacion.tipo != TipoOrganizacion.TOSTADOR:
        raise HTTPException(status_code=403, detail="Esta acción es solo para tostadores")
    return usuario
