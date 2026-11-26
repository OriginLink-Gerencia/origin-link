"""HU-14 Registrar la recepción de una compra: cambia el estado y crea la ENTRADA de inventario."""

import pytest
from sqlalchemy import select

from app.models import Compra, MovimientoInventario, Recepcion
from app.models.enums import EstadoCompra, TipoMovimiento

COMPRAS = "/api/v1/compras"


@pytest.fixture
def compra(como, usuarios, vincular, crear_lote) -> dict:
    vincular(usuarios["a"].organizacion_id, usuarios["coop"].organizacion_id)
    lote = crear_lote(coop_id=usuarios["coop"].organizacion_id, codigo="X-1")
    r = como("a").post(
        COMPRAS,
        json={"lote_id": lote.id, "cantidad_kg": 60, "precio_kg": 28.5, "fecha_compra": "2026-11-19",
              "fecha_entrega_acordada": "2026-11-29"},
    )  # fmt: skip
    return r.json()


def _recibir(c, compra_id: int, kg: float, **extra):
    return c.post(
        f"{COMPRAS}/{compra_id}/recepcion", json={"fecha_recepcion": "2026-11-29", "cantidad_recibida_kg": kg, **extra}
    )


def test_escenario1_recepcion_completa_pasa_a_recibida_y_crea_la_entrada(como, db, compra):
    r = _recibir(como("a"), compra["id"], 60)
    assert r.status_code == 201
    c = r.json()
    assert c["estado"] == "RECIBIDA"
    assert c["recepcion"]["cantidad_recibida_kg"] == 60 and c["recepcion"]["diferencia_kg"] == 0
    mov = db.scalars(select(MovimientoInventario)).all()
    assert len(mov) == 1
    assert mov[0].tipo == TipoMovimiento.ENTRADA and mov[0].cantidad_kg == 60
    assert mov[0].lote_id == compra["lote_id"] and mov[0].recepcion_id == c["recepcion"]["id"]


def test_escenario2_recepcion_con_diferencia_registra_el_faltante(como, db, compra):
    r = _recibir(como("a"), compra["id"], 55, observaciones="Un saco con humedad")
    assert r.status_code == 201
    assert r.json()["recepcion"]["diferencia_kg"] == -5
    assert r.json()["recepcion"]["observaciones"] == "Un saco con humedad"
    assert db.scalar(select(MovimientoInventario)).cantidad_kg == 55  # entra lo realmente recibido


def test_recibir_dos_veces_responde_409_y_no_duplica_la_entrada(como, db, compra):
    assert _recibir(como("a"), compra["id"], 60).status_code == 201
    assert _recibir(como("a"), compra["id"], 60).status_code == 409
    assert len(db.scalars(select(MovimientoInventario)).all()) == 1
    assert len(db.scalars(select(Recepcion)).all()) == 1


def test_una_compra_anulada_no_se_puede_recibir(como, db, compra):
    db.get(Compra, compra["id"]).estado = EstadoCompra.ANULADA
    db.commit()
    assert _recibir(como("a"), compra["id"], 60).status_code == 409


@pytest.mark.parametrize("kg", [0, -3])
def test_cantidad_recibida_debe_ser_positiva(como, db, compra, kg):
    assert _recibir(como("a"), compra["id"], kg).status_code == 422
    assert db.scalars(select(MovimientoInventario)).all() == []
    assert db.get(Compra, compra["id"]).estado == EstadoCompra.PENDIENTE


def test_compra_ajena_o_inexistente_es_404(como, compra):
    assert _recibir(como("b"), compra["id"], 60).status_code == 404
    assert _recibir(como("a"), 9999, 60).status_code == 404


def test_la_cooperativa_no_registra_recepciones(como, compra):
    assert _recibir(como("coop"), compra["id"], 60).status_code == 403


def test_la_compra_listada_muestra_la_diferencia(como, compra):
    _recibir(como("a"), compra["id"], 55)
    listada = como("a").get(COMPRAS, params={"estado": "RECIBIDA"}).json()
    assert [c["recepcion"]["diferencia_kg"] for c in listada] == [-5]
