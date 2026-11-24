"""Reglas de integridad del modelo de datos que debe garantizar la base de datos (revisión H04).

Se prueban sobre SQLite en memoria para no depender de PostgreSQL en el CI; las restricciones CHECK y
UNIQUE son SQL estándar y se comportan igual en ambos motores.
"""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Base, Compra, Lote, MovimientoInventario, Organizacion, Proveedor, Recepcion
from app.models.enums import ProcesoCafe, TipoMovimiento, TipoOrganizacion


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    event.listen(engine, "connect", lambda con, _: con.execute("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def base(db):
    """Tostador, cooperativa vinculada, proveedor del directorio, lote, compra y recepción."""
    tostador = Organizacion(tipo=TipoOrganizacion.TOSTADOR, nombre="Tostaduría Demo")
    coop = Organizacion(tipo=TipoOrganizacion.PROVEEDOR, nombre="Coop. Demo")
    db.add_all([tostador, coop])
    db.flush()
    prov = Proveedor(tostador_id=tostador.id, nombre="Coop. Demo", organizacion_proveedora_id=coop.id)
    db.add(prov)
    db.flush()
    lote = _lote(organizacion_proveedora_id=coop.id)
    db.add(lote)
    db.flush()
    compra = Compra(
        tostador_id=tostador.id, proveedor_id=prov.id, lote_id=lote.id, cantidad_kg=Decimal("60"),
        precio_kg=Decimal("28.5"), fecha_compra=date(2026, 11, 19), fecha_entrega_acordada=date(2026, 11, 29),
    )  # fmt: skip
    db.add(compra)
    db.flush()
    rec = Recepcion(compra_id=compra.id, fecha_recepcion=date(2026, 11, 29), cantidad_recibida_kg=Decimal("55"))
    db.add(rec)
    db.commit()
    return {"tostador": tostador, "coop": coop, "prov": prov, "lote": lote, "rec": rec}


def _lote(**origen) -> Lote:
    return Lote(
        codigo="J-01", region="Cajamarca - Jaén", variedad="Caturra", proceso=ProcesoCafe.LAVADO, cosecha="2026",
        cantidad_disponible_kg=Decimal("200"), precio_kg=Decimal("28.5"), **origen,
    )  # fmt: skip


def _mov(b, tipo, recepcion_id=None, cantidad="55", motivo=None) -> MovimientoInventario:
    return MovimientoInventario(
        tostador_id=b["tostador"].id, lote_id=b["lote"].id, recepcion_id=recepcion_id, tipo=tipo,
        cantidad_kg=Decimal(cantidad), fecha=date(2026, 11, 29), motivo=motivo,
    )  # fmt: skip


def _falla(db, obj):
    db.add(obj)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


# ----------------------------------------------------------------- lotes: un solo origen


def test_lote_de_cooperativa_es_valido(db, base):
    db.add(_lote(organizacion_proveedora_id=base["coop"].id))
    db.commit()


def test_lote_registrado_por_tostador_es_valido(db, base):
    db.add(_lote(proveedor_id=base["prov"].id))
    db.commit()


def test_lote_sin_origen_es_rechazado(db, base):
    _falla(db, _lote())


def test_lote_con_dos_origenes_es_rechazado(db, base):
    _falla(db, _lote(organizacion_proveedora_id=base["coop"].id, proveedor_id=base["prov"].id))


# ----------------------------------------------------------------- movimientos: ENTRADA 1:1 con recepción


def test_entrada_con_recepcion_es_valida(db, base):
    db.add(_mov(base, TipoMovimiento.ENTRADA, recepcion_id=base["rec"].id))
    db.commit()


def test_segunda_entrada_para_la_misma_recepcion_es_rechazada(db, base):
    db.add(_mov(base, TipoMovimiento.ENTRADA, recepcion_id=base["rec"].id))
    db.commit()
    _falla(db, _mov(base, TipoMovimiento.ENTRADA, recepcion_id=base["rec"].id))


def test_entrada_sin_recepcion_es_rechazada(db, base):
    _falla(db, _mov(base, TipoMovimiento.ENTRADA))


def test_consumo_ligado_a_una_recepcion_es_rechazado(db, base):
    _falla(db, _mov(base, TipoMovimiento.CONSUMO, recepcion_id=base["rec"].id, cantidad="8"))


def test_consumo_y_ajuste_sin_recepcion_son_validos(db, base):
    db.add_all([
        _mov(base, TipoMovimiento.CONSUMO, cantidad="8"),
        _mov(base, TipoMovimiento.AJUSTE, cantidad="-1", motivo="Conteo físico"),
    ])  # fmt: skip
    db.commit()
