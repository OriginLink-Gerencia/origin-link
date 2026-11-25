"""HU-03: registro por invitación y aceptación de vínculos."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.auth_security import hash_password
from app.models.enums import EstadoVinculo, TipoOrganizacion
from app.models.identidad import Organizacion, Usuario
from app.models.proveedores import Invitacion, Proveedor
from app.schemas.auth import RegistroPorInvitacionIn
from app.services.auth_service import CorreoDuplicado


class InvitacionInvalida(Exception):
    pass


class VinculoExistente(Exception):
    pass


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


def _buscar(db: Session, token: str, bloquear: bool = False) -> Invitacion | None:
    query = select(Invitacion).where(Invitacion.token == token)
    if bloquear:
        query = query.with_for_update()
    return db.scalar(query)


def es_vigente(inv: Invitacion) -> bool:
    return inv.usada_en is None and _aware(inv.expira_en) > datetime.now(UTC)


def informacion(db: Session, token: str) -> dict | None:
    inv = _buscar(db, token)
    if inv is None:
        return None
    proveedor = db.get(Proveedor, inv.proveedor_id)
    tostador = db.get(Organizacion, proveedor.tostador_id)
    return {
        "tostador": tostador.nombre,
        "proveedor": proveedor.nombre,
        "vigente": es_vigente(inv) and proveedor.estado_vinculo != EstadoVinculo.VINCULADO,
        "expira_en": inv.expira_en,
    }


def registrar_cooperativa(db: Session, datos: RegistroPorInvitacionIn) -> Usuario:
    """Una transacción: crear organización+usuario, vincular y consumir token."""
    inv = _buscar(db, datos.token, bloquear=True)
    if inv is None or not es_vigente(inv):
        raise InvitacionInvalida
    proveedor = db.get(Proveedor, inv.proveedor_id)
    if proveedor is None or proveedor.estado_vinculo == EstadoVinculo.VINCULADO:
        raise InvitacionInvalida
    correo = str(datos.email).strip().lower()
    if db.scalar(select(Usuario.id).where(Usuario.email == correo)) is not None:
        raise CorreoDuplicado
    organizacion = Organizacion(
        tipo=TipoOrganizacion.PROVEEDOR,
        nombre=datos.empresa.strip(),
        ruc=datos.ruc,
        region=datos.region.strip() if datos.region else None,
    )
    usuario = Usuario(
        nombre=datos.nombre.strip(),
        email=correo,
        password_hash=hash_password(datos.password),
        activo=True,
        organizacion=organizacion,
    )
    db.add(usuario)
    db.flush()
    proveedor.organizacion_proveedora_id = organizacion.id
    proveedor.estado_vinculo = EstadoVinculo.VINCULADO
    inv.usada_en = datetime.now(UTC)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if db.scalar(select(Usuario.id).where(Usuario.email == correo)) is not None:
            raise CorreoDuplicado from exc
        raise VinculoExistente from exc
    return db.scalar(select(Usuario).options(joinedload(Usuario.organizacion)).where(Usuario.id == usuario.id))


def aceptar_por_usuario(db: Session, token: str, usuario: Usuario) -> dict:
    """Vincula una cooperativa existente con el tostador que invitó."""
    if usuario.organizacion.tipo != TipoOrganizacion.PROVEEDOR:
        raise PermissionError
    inv = _buscar(db, token, bloquear=True)
    if inv is None or not es_vigente(inv):
        raise InvitacionInvalida
    proveedor = db.get(Proveedor, inv.proveedor_id)
    if proveedor is None or proveedor.estado_vinculo == EstadoVinculo.VINCULADO:
        raise InvitacionInvalida
    ya = db.scalar(
        select(Proveedor.id).where(
            Proveedor.tostador_id == proveedor.tostador_id,
            Proveedor.organizacion_proveedora_id == usuario.organizacion_id,
        )
    )
    if ya is not None:
        raise VinculoExistente
    proveedor.organizacion_proveedora_id = usuario.organizacion_id
    proveedor.estado_vinculo = EstadoVinculo.VINCULADO
    inv.usada_en = datetime.now(UTC)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise VinculoExistente from exc
    tostador = db.get(Organizacion, proveedor.tostador_id)
    return {"tostador_id": tostador.id, "tostador": tostador.nombre, "vinculado_desde": inv.usada_en}
