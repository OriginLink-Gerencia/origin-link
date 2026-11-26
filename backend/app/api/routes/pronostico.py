"""EP-06 Pronóstico de consumo (HU-20)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import exigir_tostador
from app.db.session import get_db
from app.models.identidad import Usuario
from app.schemas.pronostico import PronosticoOut
from app.services import pronostico as pronostico_servicio
from app.services.pronostico import HistorialInsuficiente

router = APIRouter(tags=["pronostico"])


@router.get("/pronostico", response_model=PronosticoOut)
def pronostico(usuario: Usuario = Depends(exigir_tostador), db: Session = Depends(get_db)) -> PronosticoOut:
    """HU-20: consumo de las próximas 4 semanas. `metodo` indica si es la TCN o el promedio móvil de respaldo."""
    try:
        r = pronostico_servicio.calcular(db, usuario.organizacion_id)
    except HistorialInsuficiente as e:
        raise HTTPException(status_code=409, detail=str(e)) from None
    return PronosticoOut(
        metodo=r.metodo, motivo_metodo=r.motivo, historial=r.historial, pronostico=r.pronostico, mape_referencia=r.mape
    )
