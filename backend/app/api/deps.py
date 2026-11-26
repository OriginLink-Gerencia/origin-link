"""Dependencias compartidas de las rutas: usuario actual y control de rol (HU-04)."""

import datetime as dt

from fastapi import Depends, HTTPException

from app.api.routes.auth import get_current_user as get_usuario_actual  # JWT de HU-01/02 (Authorization: Bearer)
from app.models.enums import TipoOrganizacion
from app.models.identidad import Usuario


def exigir_tostador(usuario: Usuario = Depends(get_usuario_actual)) -> Usuario:
    """Rutas 🟤 del contrato: solo usuarios de una organización tostadora."""
    if usuario.organizacion.tipo != TipoOrganizacion.TOSTADOR:
        raise HTTPException(status_code=403, detail="Esta acción es solo para tostadores")
    return usuario


def exigir_cooperativa(usuario: Usuario = Depends(get_usuario_actual)) -> Usuario:
    """Rutas 🟢 del contrato: solo usuarios de una empresa productora o cooperativa."""
    if usuario.organizacion.tipo != TipoOrganizacion.PROVEEDOR:
        raise HTTPException(status_code=403, detail="Esta acción es solo para cooperativas")
    return usuario


def get_hoy() -> dt.date:
    """Fecha de hoy; es una dependencia para fijarla en las pruebas (recomendaciones y alertas dependen de ella)."""
    return dt.date.today()
