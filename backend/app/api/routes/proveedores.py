"""HU-05 Registrar un proveedor: directorio de proveedores de cada tostador."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import exigir_tostador
from app.db.session import get_db
from app.models.identidad import Usuario
from app.models.proveedores import Proveedor
from app.schemas.proveedores import ProveedorIn, ProveedorOut, ProveedorUpdate

router = APIRouter(prefix="/proveedores", tags=["proveedores"])


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
