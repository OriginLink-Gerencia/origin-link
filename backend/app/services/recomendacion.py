"""Recomendación de compra (HU-21) y alertas (HU-22).

Con el consumo pronosticado y las existencias se calcula cuántos días alcanzan; el proveedor tarda `plazo` días en
entregar, así que la compra debe hacerse `plazo` días antes de quedarse sin café. No se elige proveedor: el plazo y
el mínimo de compra salen del último lote comprado (o 7 días y 0 kg si todavía no hay compras).

Simplificación: la primera semana pronosticada se toma como la semana que empieza hoy.
"""

import datetime as dt
import math
from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.abastecimiento import Compra
from app.models.enums import EstadoCompra
from app.schemas.pronostico import AlertaOut, FactoresRecomendacion, RecomendacionOut
from app.services.inventario import existencias_por_lote
from app.services.pronostico import Resultado, calcular

PLAZO_POR_DEFECTO = 7
DIAS_AVISO_COMPRA = 7  # COMPRA_PROXIMA: la fecha límite está a una semana o menos


@dataclass
class Calculo:
    pronostico: Resultado
    existencias: Decimal
    plazo: int
    minimo: Decimal
    semanas_cobertura: int
    dias_alcanza: float  # días que cubren las existencias (inf si no hay consumo)
    consumo_semanal: float  # promedio semanal pronosticado


def _tasa_diaria(semanal: list[float], dia: int) -> float:
    """Consumo por día del día `dia` (0 = hoy); pasado el horizonte se mantiene el promedio pronosticado."""
    return semanal[dia // 7] / 7 if dia // 7 < len(semanal) else sum(semanal) / len(semanal) / 7


def consumo_en(semanal: list[float], dias: int) -> float:
    return sum(_tasa_diaria(semanal, d) for d in range(dias))


def dias_que_alcanza(existencias: float, semanal: list[float]) -> float:
    restante, dias = existencias, 0.0
    if sum(semanal) <= 0:
        return math.inf
    while True:
        tasa = _tasa_diaria(semanal, int(dias))
        dias_en_semana = 7 - (int(dias) % 7)
        if tasa > 0 and restante <= tasa * dias_en_semana:
            return dias + restante / tasa
        restante -= tasa * dias_en_semana
        dias += dias_en_semana


def _datos_de_compra(db: Session, tostador_id: int) -> tuple[int, Decimal]:
    ultima = db.scalars(
        select(Compra)
        .where(Compra.tostador_id == tostador_id, Compra.estado != EstadoCompra.ANULADA)
        .order_by(Compra.fecha_compra.desc(), Compra.id.desc())
        .limit(1)
    ).first()
    if ultima is None:
        return PLAZO_POR_DEFECTO, Decimal(0)
    return ultima.lote.plazo_entrega_dias, Decimal(ultima.lote.cantidad_minima_kg)


def calcular_situacion(
    db: Session, usuario, hoy: dt.date, plazo_simulado: int | None = None, minimo_simulado: Decimal | None = None
) -> Calculo:
    """Reúne pronóstico, existencias y datos de compra. Lanza `HistorialInsuficiente` si no se puede pronosticar."""
    org = usuario.organizacion
    pronostico = calcular(db, org.id, hoy)
    existencias = sum(existencias_por_lote(db, org.id).values(), Decimal(0))
    plazo, minimo = _datos_de_compra(db, org.id)
    # Con las condiciones de otro lote (plazo y mínimo) se simula la compra sin tocar nada.
    plazo = plazo if plazo_simulado is None else plazo_simulado
    minimo = minimo if minimo_simulado is None else minimo_simulado
    semanal = [float(p.kg) for p in pronostico.pronostico]
    return Calculo(
        pronostico=pronostico,
        existencias=max(existencias, Decimal(0)),
        plazo=plazo,
        minimo=minimo,
        semanas_cobertura=org.semanas_cobertura,
        dias_alcanza=dias_que_alcanza(float(max(existencias, Decimal(0))), semanal),
        consumo_semanal=sum(semanal) / len(semanal),
    )


def _fecha_limite(c: Calculo, hoy: dt.date) -> dt.date:
    if math.isinf(c.dias_alcanza):
        return hoy + dt.timedelta(days=365)
    return hoy + dt.timedelta(days=max(0, math.floor(c.dias_alcanza - c.plazo)))


def _semanas(c: Calculo) -> float:
    return 0.0 if c.consumo_semanal <= 0 else float(c.existencias) / c.consumo_semanal


def recomendar(c: Calculo, hoy: dt.date) -> RecomendacionOut:
    semanal = [float(p.kg) for p in c.pronostico.pronostico]
    horizonte_dias = c.plazo + c.semanas_cobertura * 7
    necesario = Decimal(str(consumo_en(semanal, horizonte_dias))) - c.existencias
    if necesario <= 0:
        cantidad = Decimal(0)
    else:
        cantidad = max(necesario.to_integral_value(rounding=ROUND_CEILING), c.minimo)
    fecha = _fecha_limite(c, hoy)
    semanas = round(_semanas(c), 2)
    existencias = c.existencias.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if cantidad == 0:
        explicacion = (
            f"Tus {float(existencias):g} kg alcanzan para el consumo pronosticado de los próximos "
            f"{horizonte_dias} días "
            f"(entrega de {c.plazo} días y {c.semanas_cobertura} semanas de cobertura). Por ahora no necesitas comprar."
        )
    else:
        explicacion = (
            f"Tus {float(existencias):g} kg alcanzan ~{semanas:.1f} semanas. El proveedor tarda {c.plazo} días, "
            "así que "
            f"conviene comprar antes del {fecha.strftime('%d/%m/%Y')}. Para cubrir {c.plazo} días de entrega más "
            f"{c.semanas_cobertura} semanas de cobertura necesitas ~{float(necesario):.1f} kg"
            + (
                f"; el proveedor pide al menos {float(c.minimo):g} kg."
                if cantidad > necesario and cantidad == c.minimo
                else "."
            )
        )
    return RecomendacionOut(
        fecha_limite_compra=fecha,
        cantidad_sugerida_kg=cantidad,
        semanas_cobertura_actual=semanas,
        dias_cobertura_actual=None if math.isinf(c.dias_alcanza) else math.floor(c.dias_alcanza),
        factores=FactoresRecomendacion(
            existencias_kg=existencias,
            consumo_semanal_pronosticado_kg=c.pronostico.pronostico,
            plazo_entrega_dias=c.plazo,
            semanas_cobertura=c.semanas_cobertura,
            cantidad_minima_kg=c.minimo,
            metodo_pronostico=c.pronostico.metodo,
        ),
        explicacion=explicacion,
    )


def alertas(c: Calculo, hoy: dt.date) -> list[AlertaOut]:
    fecha = _fecha_limite(c, hoy)
    semanas = round(_semanas(c), 2)
    if c.dias_alcanza < c.plazo:
        return [
            AlertaOut(
                tipo="STOCK_BAJO",
                mensaje=f"Tus existencias cubren {semanas:.1f} semanas y la entrega tarda {c.plazo} días",
                semanas_cobertura_restantes=semanas,
                fecha_limite_compra=fecha,
            )
        ]
    if (fecha - hoy).days <= DIAS_AVISO_COMPRA:
        return [
            AlertaOut(
                tipo="COMPRA_PROXIMA",
                mensaje=f"Conviene comprar antes del {fecha.strftime('%d/%m/%Y')}: la entrega tarda {c.plazo} días",
                semanas_cobertura_restantes=semanas,
                fecha_limite_compra=fecha,
            )
        ]
    return []
