"""JWT HS256 y hash de contraseñas Argon2. Sin claves hardcodeadas."""

from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException
from pwdlib import PasswordHash

from app.core.config import get_settings

_hasher = PasswordHash.recommended()
_ALGORITHM = "HS256"
_TTL = timedelta(hours=8)


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        return _hasher.verify(password, stored_hash)
    except (ValueError, TypeError):
        return False


def _secret() -> str:
    secret = get_settings().jwt_secret_key
    if len(secret) < 32:
        raise RuntimeError("Configurar JWT_SECRET_KEY seguro (mínimo 32 caracteres) en backend/.env")
    return secret


def make_access_token(user_id: int) -> str:
    now = datetime.now(UTC)
    return jwt.encode({"sub": str(user_id), "iat": now, "exp": now + _TTL}, _secret(), algorithm=_ALGORITHM)


def decode_user_id(token: str) -> int:
    try:
        claims = jwt.decode(token, _secret(), algorithms=[_ALGORITHM], options={"require": ["sub", "exp", "iat"]})
        user_id = int(claims["sub"])
        if user_id <= 0:
            raise ValueError("Id inválido")
        return user_id
    except (jwt.PyJWTError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=401, detail="Sesión inválida o vencida", headers={"WWW-Authenticate": "Bearer"}
        ) from exc
