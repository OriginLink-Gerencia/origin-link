"""Casos de uso de identidad. La API gestiona transporte; el servicio, reglas y transacciones."""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.auth_security import hash_password, verify_password
from app.models.enums import TipoOrganizacion
from app.models.identidad import Organizacion, Usuario
from app.schemas.auth import RegistroTostadorIn


class CorreoDuplicado(Exception):
    pass


def registrar_tostador(db: Session, datos: RegistroTostadorIn) -> Usuario:
    correo = str(datos.email).strip().lower()
    if db.scalar(select(Usuario.id).where(Usuario.email == correo)) is not None:
        raise CorreoDuplicado

    organizacion = Organizacion(tipo=TipoOrganizacion.TOSTADOR,
                                nombre=datos.empresa.strip(), ruc=datos.ruc, region=None)
    usuario = Usuario(nombre=datos.nombre.strip(), email=correo,
                      password_hash=hash_password(datos.password), activo=True,
                      organizacion=organizacion)
    db.add(usuario)
    try:
        db.commit()  # transacción atómica: organización y usuario juntos
    except IntegrityError as exc:
        db.rollback()
        # La restricción UNIQUE prevalece ante registros concurrentes.
        if db.scalar(select(Usuario.id).where(Usuario.email == correo)) is not None:
            raise CorreoDuplicado from exc
        raise
    registrado = db.scalar(
        select(Usuario).options(joinedload(Usuario.organizacion)).where(Usuario.id == usuario.id)
    )
    if registrado is None:
        raise RuntimeError("No fue posible recuperar el usuario registrado")
    return registrado


def autenticar(db: Session, email: str, password: str) -> Usuario | None:
    usuario = db.scalar(select(Usuario).options(joinedload(Usuario.organizacion))
                        .where(Usuario.email == email.strip().lower()))
    # Verifica un hash ficticio incluso cuando el usuario no existe, para reducir
    # diferencias temporales de respuesta que revelen existencia de cuentas.
    if usuario is None:
        verify_password(password, _DUMMY_HASH)
        return None
    if not verify_password(password, usuario.password_hash) or not usuario.activo:
        return None
    return usuario


# Hash Argon2 estable de una contraseña ficticia; no representa una credencial real.
_DUMMY_HASH = hash_password('origin-link-dummy-password-not-a-secret')
