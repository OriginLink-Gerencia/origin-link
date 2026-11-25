"""HU-07 Ver mis vínculos (vista de la cooperativa). La vista del tostador es GET /proveedores."""

from datetime import UTC

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import exigir_cooperativa
from app.db.session import get_db
from app.models.enums import EstadoVinculo
from app.models.identidad import Usuario
from app.models.proveedores import Proveedor
from app.schemas.proveedores import VinculoOut

router = APIRouter(prefix="/vinculos", tags=["vinculos"])


@router.get("", response_model=list[VinculoOut])
def listar(usuario: Usuario = Depends(exigir_cooperativa), db: Session = Depends(get_db)) -> list[VinculoOut]:
    """Tostadores con los que la cooperativa comparte lotes (solo los ya VINCULADOS)."""
    consulta = (
        select(Proveedor)
        .where(
            Proveedor.organizacion_proveedora_id == usuario.organizacion_id,
            Proveedor.estado_vinculo == EstadoVinculo.VINCULADO,
        )
        .order_by(Proveedor.id)
    )
    vinculos = []
    for prov in db.scalars(consulta):
        usos = [i.usada_en for i in prov.invitaciones if i.usada_en is not None]
        desde = max(usos) if usos else prov.actualizado_en  # sin invitación (vínculo directo): última actualización
        vinculos.append(
            VinculoOut(
                tostador_id=prov.tostador_id,
                tostador=prov.tostador.nombre,
                vinculado_desde=desde if desde.tzinfo else desde.replace(tzinfo=UTC),
            )
        )
    return vinculos
