"""TT-01 Datos de demostración para el prototipo y la presentación.

Uso (desde backend/, con la base migrada):  python -m app.seed_demo

Crea, solo si no existen:
  - Tostaduría Demo (demo@originlink.pe) con 60 semanas de consumo importado (~14 kg/semana con estacionalidad),
    existencias bajas (12 kg) para que se vea la alerta, y una compra recibida.
  - Cooperativa Jaén (coop@originlink.pe) vinculada a esa tostaduría, con un lote publicado.
  - Una ficha del directorio del tostador (Finca Don Pepe, sin vincular) con un lote cargado a mano.
Las cuentas usan una contraseña de demostración: no sembrar en una base real de producción.
"""

import datetime as dt
import math
import random
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_security import hash_password
from app.models import Compra, Lote, Organizacion, Proveedor, Usuario
from app.models.abastecimiento import ConsumoHistorico, MovimientoInventario, Recepcion
from app.models.enums import EstadoCompra, EstadoVinculo, OrigenConsumo, ProcesoCafe, TipoMovimiento, TipoOrganizacion
from app.services.consumo import lunes

DEMO_EMAIL_TOSTADOR = "demo@originlink.pe"
DEMO_EMAIL_COOP = "coop@originlink.pe"
DEMO_PASSWORD = "OriginLink2026!"  # solo para la demostración
SEMANAS_DE_HISTORIAL = 60


def _consumo_semanal(semana: int) -> Decimal:
    """~14 kg/semana con una onda anual (más consumo a mitad de año) y ruido reproducible."""
    ruido = random.Random(1000 + semana).uniform(-1.2, 1.2)
    return Decimal(str(round(14 + 3 * math.sin(2 * math.pi * semana / 52) + ruido, 1)))


def sembrar(db: Session, hoy: dt.date | None = None) -> bool:
    """Devuelve False (sin tocar nada) si los datos de demostración ya existen."""
    hoy = hoy or dt.date.today()
    if db.scalar(select(Usuario.id).where(Usuario.email == DEMO_EMAIL_TOSTADOR)):
        return False

    tostador = Organizacion(
        tipo=TipoOrganizacion.TOSTADOR, nombre="Tostaduría Demo", region="Lima", semanas_cobertura=2
    )
    coop = Organizacion(tipo=TipoOrganizacion.PROVEEDOR, nombre="Cooperativa Cafetalera Jaén", region="Cajamarca")
    db.add_all([tostador, coop])
    db.flush()
    clave = hash_password(DEMO_PASSWORD)
    db.add_all(
        [
            Usuario(organizacion_id=tostador.id, nombre="Ana Demo", email=DEMO_EMAIL_TOSTADOR, password_hash=clave),
            Usuario(organizacion_id=coop.id, nombre="Luis Demo", email=DEMO_EMAIL_COOP, password_hash=clave),
        ]
    )
    vinculada = Proveedor(
        tostador_id=tostador.id,
        organizacion_proveedora_id=coop.id,
        nombre=coop.nombre,
        region="Cajamarca",
        estado_vinculo=EstadoVinculo.VINCULADO,
    )
    don_pepe = Proveedor(
        tostador_id=tostador.id, nombre="Finca Don Pepe", region="Junín", estado_vinculo=EstadoVinculo.SIN_VINCULAR
    )
    db.add_all([vinculada, don_pepe])
    db.flush()

    lote_coop = Lote(
        organizacion_proveedora_id=coop.id, codigo="JAEN-2026-07", region="Cajamarca", finca="Finca El Mirador",
        variedad="Caturra", proceso=ProcesoCafe.LAVADO, cosecha="2026", altitud_msnm=1650,
        cantidad_disponible_kg=Decimal(300), precio_kg=Decimal("28.5"), cantidad_minima_kg=Decimal(30),
        plazo_entrega_dias=10, caracteristicas="Notas a panela y cacao; 84 puntos declarados",
    )  # fmt: skip
    lote_pepe = Lote(
        proveedor_id=don_pepe.id, codigo="DONPEPE-2026-01", region="Junín", variedad="Catimor",
        proceso=ProcesoCafe.NATURAL, cosecha="2026", altitud_msnm=1400,
        cantidad_disponible_kg=Decimal(120), precio_kg=Decimal(24), plazo_entrega_dias=5,
    )  # fmt: skip
    db.add_all([lote_coop, lote_pepe])
    db.flush()

    ultima = lunes(hoy) - dt.timedelta(weeks=1)  # última semana completa
    db.add_all(
        ConsumoHistorico(
            tostador_id=tostador.id,
            semana=ultima - dt.timedelta(weeks=SEMANAS_DE_HISTORIAL - 1 - i),
            kg_consumidos=_consumo_semanal(i),
            origen=OrigenConsumo.IMPORTADO,
        )
        for i in range(SEMANAS_DE_HISTORIAL)
    )

    compra = Compra(
        tostador_id=tostador.id, proveedor_id=vinculada.id, lote_id=lote_coop.id, cantidad_kg=Decimal(40),
        precio_kg=Decimal("28.5"), fecha_compra=hoy - dt.timedelta(days=30),
        fecha_entrega_acordada=hoy - dt.timedelta(days=20), estado=EstadoCompra.RECIBIDA,
    )  # fmt: skip
    db.add(compra)
    db.flush()
    recepcion = Recepcion(
        compra_id=compra.id, fecha_recepcion=hoy - dt.timedelta(days=20), cantidad_recibida_kg=Decimal(40)
    )
    db.add(recepcion)
    db.flush()
    db.add_all(
        [
            MovimientoInventario(
                tostador_id=tostador.id, lote_id=lote_coop.id, recepcion_id=recepcion.id,
                tipo=TipoMovimiento.ENTRADA, cantidad_kg=Decimal(40), fecha=recepcion.fecha_recepcion,
            ),
            # El tostado de las últimas semanas ya está en el historial importado; el conteo físico deja 12 kg
            MovimientoInventario(
                tostador_id=tostador.id, lote_id=lote_coop.id, tipo=TipoMovimiento.AJUSTE,
                cantidad_kg=Decimal(-28), motivo="Conteo físico", fecha=hoy - dt.timedelta(days=1),
            ),
        ]
    )  # fmt: skip
    db.commit()
    return True


def main() -> None:
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        creado = sembrar(db)
    if creado:
        print(
            f"Datos de demostración creados.\n  Tostador:     {DEMO_EMAIL_TOSTADOR}\n  Cooperativa:  {DEMO_EMAIL_COOP}"
        )
        print(f"  Contraseña:   {DEMO_PASSWORD}")
    else:
        print("Los datos de demostración ya existían; no se cambió nada.")


if __name__ == "__main__":
    main()
