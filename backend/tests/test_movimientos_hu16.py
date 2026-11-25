"""HU-16 Registrar consumos, mermas y ajustes; las existencias salen de los movimientos."""

from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import MovimientoInventario
from app.services.inventario import existencias_lote

COMPRAS = "/api/v1/compras"
MOVS = "/api/v1/movimientos"


@pytest.fixture
def stock(como, db, usuarios, vincular, crear_lote):
    """Devuelve una función que deja `kg` kg de un lote en el inventario del tostador A (compra + recepción)."""
    vincular(usuarios["a"].organizacion_id, usuarios["coop"].organizacion_id)

    def _stock(kg: float, codigo: str = "X-1"):
        lote = crear_lote(coop_id=usuarios["coop"].organizacion_id, codigo=codigo)
        compra = como("a").post(
            COMPRAS,
            json={"lote_id": lote.id, "cantidad_kg": kg, "precio_kg": 28.5, "fecha_compra": "2026-11-01",
                  "fecha_entrega_acordada": "2026-11-05"},
        ).json()  # fmt: skip
        como("a").post(
            f"{COMPRAS}/{compra['id']}/recepcion", json={"fecha_recepcion": "2026-11-05", "cantidad_recibida_kg": kg}
        )
        return lote

    return _stock


def _mov(lote_id, tipo, kg, fecha="2026-11-10", **extra) -> dict:
    return {"lote_id": lote_id, "tipo": tipo, "cantidad_kg": kg, "fecha": fecha, **extra}


def test_escenario1_consumo_descuenta_de_las_existencias(como, db, usuarios, stock):
    lote = stock(40)
    r = como("a").post(MOVS, json=_mov(lote.id, "CONSUMO", 8))
    assert r.status_code == 201 and r.json()["tipo"] == "CONSUMO" and r.json()["cantidad_kg"] == 8
    assert existencias_lote(db, usuarios["a"].organizacion_id, lote.id) == Decimal("32")


def test_escenario2_consumo_mayor_a_las_existencias_no_se_registra(como, db, usuarios, stock):
    lote = stock(5)
    r = como("a").post(MOVS, json=_mov(lote.id, "CONSUMO", 8))
    assert r.status_code == 400
    assert len(db.scalars(select(MovimientoInventario)).all()) == 1  # solo la ENTRADA
    assert existencias_lote(db, usuarios["a"].organizacion_id, lote.id) == Decimal("5")


def test_se_puede_consumir_exactamente_lo_que_hay(como, db, usuarios, stock):
    lote = stock(10)
    assert como("a").post(MOVS, json=_mov(lote.id, "CONSUMO", 10)).status_code == 201
    assert existencias_lote(db, usuarios["a"].organizacion_id, lote.id) == 0


def test_la_merma_tambien_descuenta_y_no_puede_exceder_lo_que_hay(como, db, usuarios, stock):
    lote = stock(10)
    assert como("a").post(MOVS, json=_mov(lote.id, "MERMA", 2.5, motivo="Humedad")).status_code == 201
    assert como("a").post(MOVS, json=_mov(lote.id, "MERMA", 8)).status_code == 400
    assert existencias_lote(db, usuarios["a"].organizacion_id, lote.id) == Decimal("7.5")


def test_escenario3_el_ajuste_exige_motivo(como, db, usuarios, stock):
    lote = stock(10)
    r = como("a").post(MOVS, json=_mov(lote.id, "AJUSTE", -2))
    assert r.status_code == 422 and "motivo" in str(r.json()["detail"]).lower()
    ok = como("a").post(MOVS, json=_mov(lote.id, "AJUSTE", -2, motivo="Conteo físico"))
    assert ok.status_code == 201 and ok.json()["cantidad_kg"] == -2
    assert existencias_lote(db, usuarios["a"].organizacion_id, lote.id) == Decimal("8")


def test_el_ajuste_puede_sumar_y_no_puede_dejar_existencias_negativas(como, db, usuarios, stock):
    lote = stock(10)
    assert como("a").post(MOVS, json=_mov(lote.id, "AJUSTE", 1.5, motivo="Sobrante")).status_code == 201
    assert como("a").post(MOVS, json=_mov(lote.id, "AJUSTE", -20, motivo="Error")).status_code == 400
    assert como("a").post(MOVS, json=_mov(lote.id, "AJUSTE", 0, motivo="Nada")).status_code == 422


def test_las_entradas_no_se_registran_a_mano(como, stock):
    lote = stock(10)
    assert como("a").post(MOVS, json=_mov(lote.id, "ENTRADA", 5)).status_code == 422


@pytest.mark.parametrize("kg", [0, -1])
def test_consumo_con_cantidad_no_positiva_es_422(como, stock, kg):
    lote = stock(10)
    assert como("a").post(MOVS, json=_mov(lote.id, "CONSUMO", kg)).status_code == 422


def test_lote_que_no_es_mio_es_404(como, stock):
    lote = stock(10)
    assert como("b").post(MOVS, json=_mov(lote.id, "CONSUMO", 1)).status_code == 404
    assert como("a").post(MOVS, json=_mov(9999, "CONSUMO", 1)).status_code == 404


def test_la_cooperativa_no_registra_movimientos(como, stock):
    lote = stock(10)  # primero el stock: `stock` autentica como el tostador
    assert como("coop").post(MOVS, json=_mov(lote.id, "CONSUMO", 1)).status_code == 403
    assert como("coop").get(MOVS).status_code == 403


def test_listado_con_filtros_y_aislamiento(como, stock):
    l1, l2 = stock(40, "X-1"), stock(40, "X-2")
    c = como("a")
    c.post(MOVS, json=_mov(l1.id, "CONSUMO", 8, "2026-11-10"))
    c.post(MOVS, json=_mov(l1.id, "MERMA", 1, "2026-11-12"))
    c.post(MOVS, json=_mov(l2.id, "CONSUMO", 3, "2026-11-15"))
    assert len(c.get(MOVS).json()) == 5  # 2 entradas + 3 movimientos
    assert len(c.get(MOVS, params={"lote_id": l1.id}).json()) == 3
    assert len(c.get(MOVS, params={"tipo": "CONSUMO"}).json()) == 2
    assert len(c.get(MOVS, params={"desde": "2026-11-11", "hasta": "2026-11-14"}).json()) == 1
    assert como("b").get(MOVS).json() == []
