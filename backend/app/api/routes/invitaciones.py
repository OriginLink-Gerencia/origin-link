"""HU-03: información pública de invitaciones y aceptación por cuenta existente."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.db.session import get_db
from app.models.identidad import Usuario
from app.services.invitaciones_service import (
    InvitacionInvalida,
    VinculoExistente,
    aceptar_por_usuario,
    informacion,
)

router = APIRouter(prefix="/invitaciones", tags=["invitaciones"])


class InvitacionInfoOut(BaseModel):
    tostador: str
    proveedor: str
    vigente: bool
    expira_en: datetime


class VinculoAceptadoOut(BaseModel):
    tostador_id: int
    tostador: str
    vinculado_desde: datetime


@router.get("/{token}", response_model=InvitacionInfoOut)
def consultar(token: str, db: Session = Depends(get_db)) -> InvitacionInfoOut:
    info = informacion(db, token)
    if info is None:
        raise HTTPException(status_code=404, detail="Invitación no encontrada")
    return InvitacionInfoOut(**info)


@router.post("/{token}/aceptar", response_model=VinculoAceptadoOut)
def aceptar(
    token: str, usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)
) -> VinculoAceptadoOut:
    try:
        return VinculoAceptadoOut(**aceptar_por_usuario(db, token, usuario))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail="Solo las cooperativas pueden aceptar invitaciones") from exc
    except InvitacionInvalida as exc:
        raise HTTPException(status_code=400, detail="Invitación no válida") from exc
    except VinculoExistente as exc:
        raise HTTPException(status_code=409, detail="La cooperativa ya está vinculada con este tostador") from exc
