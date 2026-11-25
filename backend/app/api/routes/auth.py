"""Endpoints de identidad (HU-01/HU-02) según el contrato aprobado."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.auth_security import decode_user_id, make_access_token
from app.db.session import get_db
from app.models.identidad import Usuario
from app.schemas.auth import LoginIn, RegistroTostadorIn, TokenOut, UsuarioOut
from app.services.auth_service import CorreoDuplicado, autenticar, registrar_tostador

router = APIRouter(prefix="/auth", tags=["auth"])
_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer), db: Session = Depends(get_db)
) -> Usuario:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401, detail="Se requiere iniciar sesión", headers={"WWW-Authenticate": "Bearer"}
        )
    user_id = decode_user_id(credentials.credentials)
    usuario = db.scalar(select(Usuario).options(joinedload(Usuario.organizacion)).where(Usuario.id == user_id))
    if usuario is None or not usuario.activo:
        raise HTTPException(status_code=401, detail="Sesión inválida o vencida", headers={"WWW-Authenticate": "Bearer"})
    return usuario


def _respuesta(usuario: Usuario) -> TokenOut:
    return TokenOut(
        access_token=make_access_token(usuario.id), token_type="bearer", usuario=UsuarioOut.model_validate(usuario)
    )


@router.post("/registro", status_code=status.HTTP_201_CREATED, response_model=TokenOut)
def registro(datos: RegistroTostadorIn, db: Session = Depends(get_db)) -> TokenOut:
    try:
        usuario = registrar_tostador(db, datos)
    except CorreoDuplicado as exc:
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con este correo") from exc
    return _respuesta(usuario)


@router.post("/login", response_model=TokenOut)
def login(datos: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    usuario = autenticar(db, str(datos.email), datos.password)
    if usuario is None:
        raise HTTPException(
            status_code=401, detail="Correo o contraseña incorrectos", headers={"WWW-Authenticate": "Bearer"}
        )
    return _respuesta(usuario)


@router.get("/me", response_model=UsuarioOut)
def me(usuario: Usuario = Depends(get_current_user)) -> UsuarioOut:
    return UsuarioOut.model_validate(usuario)
