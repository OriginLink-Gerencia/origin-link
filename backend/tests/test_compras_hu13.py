"""HU-13 Registrar una compra de un lote."""

from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import Compra, Organizacion, Proveedor
from app.models.enums import TipoOrganizacion

COMPRAS = "/api/v1/compras"


@pytest.fixture
def mundo(db, usuarios, vincular, crear_lote):
    """Tostador A vinculado con Coop. X, que tiene un lote de 200 kg; Coop. Z no está vinculada."""
    a, coop = usuarios["a"].organizacion_id, usuarios["coop"].organizacion_id
    ficha = vincular(a, coop)
    z = Organizacion(tipo=TipoOrganizacion.PROVEEDOR, nombre="Coop. Z")
    db.add(z)
    db.commit()
    return {
        "ficha": ficha,
        "lote": crear_lote(coop_id=coop, codigo="X-1"),
        "lote_chico": crear_lote(coop_id=coop, codigo="X-2", cantidad_disponible_kg=Decimal("50")),
        "lote_z": crear_lote(coop_id=z.id, codigo="Z-1"),
    }


def _compra(lote_id: int, **extra) -> dict:
    return {
        "lote_id": lote_id, "cantidad_kg": 60, "precio_kg": 28.5, "fecha_compra": "2026-11-19",
        "fecha_entrega_acordada": "2026-11-29", **extra,
    }  # fmt: skip


def test_escenario1_compra_queda_pendiente_de_recepcion(como, db, mundo):
    r = como("a").post(COMPRAS, json=_compra(mundo["lote"].id))
    assert r.status_code == 201
    c = r.json()
    assert c["estado"] == "PENDIENTE" and c["recepcion"] is None and c["advertencia"] is None
    assert c["total"] == 1710 and c["fecha_entrega_acordada"] == "2026-11-29"
    assert c["lote_codigo"] == "X-1" and c["proveedor_nombre"] == "Coop. X"
    assert c["proveedor_id"] == mundo["ficha"].id
    assert db.scalar(select(Compra)).tostador_id is not None


def test_escenario2_cantidad_mayor_a_la_disponible_advierte_pero_registra(como, db, mundo):
    r = como("a").post(COMPRAS, json=_compra(mundo["lote_chico"].id, cantidad_kg=80))
    assert r.status_code == 201
    assert r.json()["advertencia"] == "La cantidad supera lo disponible en el lote"
    assert len(db.scalars(select(Compra)).all()) == 1


def test_compra_de_un_lote_del_directorio_usa_esa_ficha(como, db, usuarios, crear_lote):
    ficha = Proveedor(tostador_id=usuarios["a"].organizacion_id, nombre="Finca sin cuenta")
    db.add(ficha)
    db.commit()
    lote = crear_lote(proveedor_id=ficha.id, codigo="D-1")
    r = como("a").post(COMPRAS, json=_compra(lote.id))
    assert r.status_code == 201 and r.json()["proveedor_id"] == ficha.id


def test_no_se_puede_comprar_un_lote_que_no_se_ve(como, db, mundo):
    assert como("a").post(COMPRAS, json=_compra(mundo["lote_z"].id)).status_code == 404  # sin vínculo
    assert como("b").post(COMPRAS, json=_compra(mundo["lote"].id)).status_code == 404  # otro tostador
    assert como("a").post(COMPRAS, json=_compra(9999)).status_code == 404
    assert db.scalars(select(Compra)).all() == []


@pytest.mark.parametrize(
    "cambio",
    [{"cantidad_kg": 0}, {"cantidad_kg": -5}, {"precio_kg": -1}, {"fecha_entrega_acordada": "2026-11-01"}],
)
def test_datos_invalidos_se_rechazan(como, db, mundo, cambio):
    assert como("a").post(COMPRAS, json=_compra(mundo["lote"].id, **cambio)).status_code == 422
    assert db.scalars(select(Compra)).all() == []


def test_la_cooperativa_no_registra_compras(como, mundo):
    assert como("coop").post(COMPRAS, json=_compra(mundo["lote"].id)).status_code == 403
    assert como("coop").get(COMPRAS).status_code == 403


def test_listado_solo_de_mis_compras_con_filtros(como, mundo):
    c = como("a")
    c.post(COMPRAS, json=_compra(mundo["lote"].id))
    c.post(COMPRAS, json=_compra(mundo["lote_chico"].id, cantidad_kg=10))
    assert len(c.get(COMPRAS).json()) == 2
    assert len(c.get(COMPRAS, params={"estado": "PENDIENTE"}).json()) == 2
    assert c.get(COMPRAS, params={"estado": "RECIBIDA"}).json() == []
    assert len(c.get(COMPRAS, params={"proveedor_id": mundo["ficha"].id}).json()) == 2
    assert c.get(COMPRAS, params={"proveedor_id": 9999}).json() == []
    assert como("b").get(COMPRAS).json() == []
