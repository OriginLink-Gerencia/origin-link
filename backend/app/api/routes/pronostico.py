"""EP-06 Pronóstico (HU-20) · EP-07 Recomendaciones y alertas (HU-21, HU-22)."""

import datetime as dt
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import exigir_tostador, get_hoy
from app.db.session import get_db
from app.models.identidad import Usuario
from app.schemas.pronostico import AlertaOut, PronosticoOut, RecomendacionOut
from app.services import pronostico as pronostico_servicio
from app.services import recomendacion as servicio
from app.services.pronostico import HistorialInsuficiente

router = APIRouter(tags=["pronostico"])


@router.get("/pronostico", response_model=PronosticoOut)
def pronostico(
    usuario: Usuario = Depends(exigir_tostador), db: Session = Depends(get_db), hoy: dt.date = Depends(get_hoy)
) -> PronosticoOut:
    """HU-20: consumo de las próximas 4 semanas. `metodo` indica si es la TCN o el promedio móvil de respaldo."""
    try:
        r = pronostico_servicio.calcular(db, usuario.organizacion_id, hoy)
    except HistorialInsuficiente as e:
        raise HTTPException(status_code=409, detail=str(e)) from None
    return PronosticoOut(
        metodo=r.metodo, motivo_metodo=r.motivo, historial=r.historial, pronostico=r.pronostico, mape_referencia=r.mape
    )


@router.get("/recomendaciones", response_model=RecomendacionOut)
def recomendacion(
    plazo_entrega_dias: int | None = Query(default=None, ge=0, le=180),
    cantidad_minima_kg: Decimal | None = Query(default=None, ge=0, max_digits=10, decimal_places=2),
    usuario: Usuario = Depends(exigir_tostador),
    db: Session = Depends(get_db),
    hoy: dt.date = Depends(get_hoy),
) -> RecomendacionOut:
    """HU-21: cuánto comprar y hasta cuándo. No recomienda proveedor.

    Sin parámetros usa el plazo y el mínimo de la última compra. Con `plazo_entrega_dias` y `cantidad_minima_kg`
    simula las condiciones de otro lote.
    """
    try:
        return servicio.recomendar(
            servicio.calcular_situacion(db, usuario, hoy, plazo_entrega_dias, cantidad_minima_kg), hoy
        )
    except HistorialInsuficiente as e:
        raise HTTPException(status_code=409, detail=str(e)) from None


@router.get("/alertas", response_model=list[AlertaOut])
def alertas(
    usuario: Usuario = Depends(exigir_tostador), db: Session = Depends(get_db), hoy: dt.date = Depends(get_hoy)
) -> list[AlertaOut]:
    """HU-22: stock bajo o compra próxima. Sin historial suficiente no hay alertas (lista vacía)."""
    try:
        return servicio.alertas(servicio.calcular_situacion(db, usuario, hoy), hoy)
    except HistorialInsuficiente:
        return []
