"""HU-05 Registrar un proveedor: directorio de proveedores de cada tostador."""

import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import exigir_tostador
from app.core.config import get_settings
from app.db.session import get_db
from app.models.abastecimiento import Compra
from app.models.enums import EstadoVinculo
from app.models.identidad import Usuario
from app.models.proveedores import Invitacion, Proveedor
from app.schemas.abastecimiento import CompraOut
from app.schemas.proveedores import InvitacionOut, ProveedorIn, ProveedorOut, ProveedorUpdate
from app.services.compras import compra_a_out

router = APIRouter(prefix="/proveedores", tags=["proveedores"])

VIGENCIA_INVITACION = timedelta(days=7)


def _del_tostador(db: Session, usuario: Usuario, proveedor_id: int) -> Proveedor:
    """HU-04: solo se ve lo de la propia organización; lo ajeno responde 404 (no revela que existe)."""
    proveedor = db.scalar(
        select(Proveedor).where(Proveedor.id == proveedor_id, Proveedor.tostador_id == usuario.organizacion_id)
    )
    if proveedor is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return proveedor


@router.get("", response_model=list[ProveedorOut])
def listar(usuario: Usuario = Depends(exigir_tostador), db: Session = Depends(get_db)) -> list[Proveedor]:
    consulta = select(Proveedor).where(Proveedor.tostador_id == usuario.organizacion_id).order_by(Proveedor.nombre)
    return list(db.scalars(consulta))


@router.post("", response_model=ProveedorOut, status_code=status.HTTP_201_CREATED)
def crear(datos: ProveedorIn, usuario: Usuario = Depends(exigir_tostador), db: Session = Depends(get_db)) -> Proveedor:
    # estado_vinculo nace en SIN_VINCULAR (valor por defecto del modelo); no lo decide el cliente.
    proveedor = Proveedor(tostador_id=usuario.organizacion_id, **datos.model_dump())
    db.add(proveedor)
    db.commit()
    db.refresh(proveedor)
    return proveedor


@router.get("/{proveedor_id}", response_model=ProveedorOut)
def detalle(proveedor_id: int, usuario: Usuario = Depends(exigir_tostador), db: Session = Depends(get_db)) -> Proveedor:
    return _del_tostador(db, usuario, proveedor_id)


@router.patch("/{proveedor_id}", response_model=ProveedorOut)
def actualizar(
    proveedor_id: int,
    datos: ProveedorUpdate,
    usuario: Usuario = Depends(exigir_tostador),
    db: Session = Depends(get_db),
) -> Proveedor:
    proveedor = _del_tostador(db, usuario, proveedor_id)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(proveedor, campo, valor)
    db.commit()
    db.refresh(proveedor)
    return proveedor


@router.post("/{proveedor_id}/invitaciones", response_model=InvitacionOut, status_code=status.HTTP_201_CREATED)
def invitar(
    proveedor_id: int, usuario: Usuario = Depends(exigir_tostador), db: Session = Depends(get_db)
) -> InvitacionOut:
    """HU-06: enlace único, de un solo uso y con vigencia de 7 días; el proveedor pasa a INVITADO."""
    proveedor = _del_tostador(db, usuario, proveedor_id)
    if proveedor.estado_vinculo == EstadoVinculo.VINCULADO:
        raise HTTPException(status_code=409, detail="El proveedor ya está vinculado")
    ahora = datetime.now(UTC)
    # Una sola invitación vigente por proveedor: al generar otra, las anteriores sin usar vencen.
    for previa in proveedor.invitaciones:
        if previa.usada_en is None and _aware(previa.expira_en) > ahora:
            previa.expira_en = ahora
    invitacion = Invitacion(
        proveedor_id=proveedor.id,
        token=secrets.token_urlsafe(32),
        creado_en=ahora,
        expira_en=ahora + VIGENCIA_INVITACION,
    )
    proveedor.estado_vinculo = EstadoVinculo.INVITADO
    db.add(invitacion)
    db.commit()
    url = f"{get_settings().frontend_url.rstrip('/')}/invitacion/{invitacion.token}"
    return InvitacionOut(token=invitacion.token, url=url, expira_en=invitacion.expira_en)


def _aware(fecha: datetime) -> datetime:
    """SQLite devuelve fechas sin zona; PostgreSQL con zona. Se asume UTC cuando falta."""
    return fecha if fecha.tzinfo else fecha.replace(tzinfo=UTC)


@router.get("/{proveedor_id}/compras", response_model=list[CompraOut])
def historial_de_compras(
    proveedor_id: int, usuario: Usuario = Depends(exigir_tostador), db: Session = Depends(get_db)
) -> list[CompraOut]:
    """HU-15: compras y recepciones de un proveedor, de la más reciente a la más antigua."""
    proveedor = _del_tostador(db, usuario, proveedor_id)
    consulta = (
        select(Compra)
        .where(Compra.tostador_id == usuario.organizacion_id, Compra.proveedor_id == proveedor.id)
        .order_by(Compra.fecha_compra.desc(), Compra.id.desc())
    )
    return [compra_a_out(c) for c in db.scalars(consulta)]
