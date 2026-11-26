"""EP-03 Gestión colaborativa de lotes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_usuario_actual
from app.db.session import get_db
from app.models.enums import EstadoVinculo, ProcesoCafe, TipoOrganizacion
from app.models.identidad import Usuario
from app.models.lotes import Lote
from app.models.proveedores import Proveedor
from app.schemas.lotes import DisponibilidadUpdate, LoteIn, LoteOut
from app.services.lotes import fichas_de_cooperativas, lote_a_out, lotes_visibles

router = APIRouter(prefix="/lotes", tags=["lotes"])


@router.post("", response_model=LoteOut, status_code=status.HTTP_201_CREATED)
def publicar(datos: LoteIn, usuario: Usuario = Depends(get_usuario_actual), db: Session = Depends(get_db)) -> LoteOut:
    """HU-08: la cooperativa publica un lote. HU-11: el tostador registra uno a nombre de un proveedor sin cuenta."""
    if usuario.organizacion.tipo == TipoOrganizacion.TOSTADOR:
        lote = _lote_manual(datos, usuario, db)
    else:
        lote = _lote_de_cooperativa(datos, usuario, db)
    db.add(lote)
    db.commit()
    db.refresh(lote)
    return lote_a_out(lote, fichas_de_cooperativas(db, usuario))


def _lote_de_cooperativa(datos: LoteIn, usuario: Usuario, db: Session) -> Lote:
    """Lo ven solo los tostadores con los que la cooperativa está vinculada."""
    if datos.proveedor_id is not None:
        raise HTTPException(status_code=400, detail="Solo un tostador puede registrar un lote a nombre de un proveedor")
    vinculado = db.scalar(
        select(Proveedor.id)
        .where(
            Proveedor.organizacion_proveedora_id == usuario.organizacion_id,
            Proveedor.estado_vinculo == EstadoVinculo.VINCULADO,
        )
        .limit(1)
    )
    if vinculado is None:
        raise HTTPException(status_code=400, detail="Para publicar un lote debes estar vinculado con un tostador")
    return Lote(organizacion_proveedora_id=usuario.organizacion_id, **datos.model_dump(exclude={"proveedor_id"}))


def _lote_manual(datos: LoteIn, usuario: Usuario, db: Session) -> Lote:
    """Lote privado del tostador, asociado a una ficha de su directorio que aún no está vinculada."""
    if datos.proveedor_id is None:
        raise HTTPException(status_code=400, detail="Indica el proveedor de tu directorio al que pertenece el lote")
    ficha = db.scalar(
        select(Proveedor).where(Proveedor.id == datos.proveedor_id, Proveedor.tostador_id == usuario.organizacion_id)
    )
    if ficha is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    if ficha.estado_vinculo == EstadoVinculo.VINCULADO:
        raise HTTPException(status_code=409, detail="El proveedor ya está vinculado: publica sus propios lotes")
    return Lote(proveedor_id=ficha.id, **datos.model_dump(exclude={"proveedor_id"}))


@router.get("", response_model=list[LoteOut])
def listar(
    proveedor_id: int | None = None,
    proceso: ProcesoCafe | None = None,
    disponibles: bool = False,
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
) -> list[LoteOut]:
    """HU-09: lotes visibles para el usuario, con filtros por proveedor, proceso y disponibilidad."""
    consulta = lotes_visibles(usuario)
    if proveedor_id is not None and usuario.organizacion.tipo == TipoOrganizacion.TOSTADOR:
        ficha = db.scalar(
            select(Proveedor).where(Proveedor.id == proveedor_id, Proveedor.tostador_id == usuario.organizacion_id)
        )
        if ficha is None:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        # La ficha puede ser de una cooperativa vinculada (lotes publicados) o del directorio (lotes propios).
        condiciones = [Lote.proveedor_id == ficha.id]
        if ficha.organizacion_proveedora_id is not None:
            condiciones.append(Lote.organizacion_proveedora_id == ficha.organizacion_proveedora_id)
        consulta = consulta.where(or_(*condiciones))
    if proceso is not None:
        consulta = consulta.where(Lote.proceso == proceso)
    if disponibles:
        consulta = consulta.where(Lote.cantidad_disponible_kg > 0)
    fichas = fichas_de_cooperativas(db, usuario)
    return [lote_a_out(lote, fichas) for lote in db.scalars(consulta)]


@router.get("/{lote_id}", response_model=LoteOut)
def detalle(lote_id: int, usuario: Usuario = Depends(get_usuario_actual), db: Session = Depends(get_db)) -> LoteOut:
    lote = db.scalar(lotes_visibles(usuario).where(Lote.id == lote_id))
    if lote is None:
        raise HTTPException(status_code=404, detail="Lote no encontrado")  # no revela si existe (HU-04)
    return lote_a_out(lote, fichas_de_cooperativas(db, usuario))


@router.patch("/{lote_id}/disponibilidad", response_model=LoteOut)
def actualizar_disponibilidad(
    lote_id: int,
    datos: DisponibilidadUpdate,
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
) -> LoteOut:
    """HU-10: el dueño del lote actualiza cantidad, mínimo, precio, plazo o publicación.

    Con cantidad 0 el lote se muestra como agotado. `actualizado_en` se renueva solo (onupdate).
    """
    lote = db.scalar(lotes_visibles(usuario).where(Lote.id == lote_id))
    if lote is None:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    if not _es_dueno(usuario, lote):
        raise HTTPException(status_code=403, detail="Solo quien registró el lote puede modificarlo")
    cambios = datos.model_dump(exclude_unset=True)
    if any(valor is None for valor in cambios.values()):
        raise HTTPException(status_code=422, detail="Los campos enviados no pueden ser nulos")
    for campo, valor in cambios.items():
        setattr(lote, campo, valor)
    db.commit()
    db.refresh(lote)
    return lote_a_out(lote, fichas_de_cooperativas(db, usuario))


def _es_dueno(usuario: Usuario, lote: Lote) -> bool:
    """Cooperativa: sus lotes publicados. Tostador: los que registró para su directorio (HU-11)."""
    if usuario.organizacion.tipo == TipoOrganizacion.PROVEEDOR:
        return lote.organizacion_proveedora_id == usuario.organizacion_id
    return lote.proveedor_id is not None and lote.proveedor.tostador_id == usuario.organizacion_id
