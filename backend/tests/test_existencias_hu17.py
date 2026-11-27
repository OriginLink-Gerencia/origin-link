"""HU-17 Ver mis existencias actuales: por lote y total, calculadas desde los movimientos."""

import pytest

COMPRAS = "/api/v1/compras"
MOVS = "/api/v1/movimientos"
EXISTENCIAS = "/api/v1/existencias"


@pytest.fixture
def stock(como, usuarios, vincular, crear_lote):
    vincular(usuarios["a"].organizacion_id, usuarios["coop"].organizacion_id)

    def _stock(kg: float, codigo: str):
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


def _mov(c, lote, tipo, kg, **extra):
    r = c.post(MOVS, json={"lote_id": lote.id, "tipo": tipo, "cantidad_kg": kg, "fecha": "2026-11-10", **extra})
    assert r.status_code == 201, r.text


def test_sin_movimientos_las_existencias_son_cero(como):
    r = como("a").get(EXISTENCIAS)
    assert r.status_code == 200 and r.json() == {"total_kg": 0, "lotes": []}


def test_escenario1_existencias_son_entradas_menos_salidas_mas_ajustes(como, stock):
    lote = stock(100, "X-1")
    c = como("a")
    _mov(c, lote, "CONSUMO", 30)
    _mov(c, lote, "MERMA", 5)
    _mov(c, lote, "AJUSTE", -2.5, motivo="Conteo")
    _mov(c, lote, "AJUSTE", 1, motivo="Sobrante")
    r = c.get(EXISTENCIAS).json()
    assert r["lotes"] == [
        {"lote_id": lote.id, "lote_codigo": "X-1", "proveedor_nombre": "Coop. X", "existencias_kg": 63.5}
    ]
    assert r["total_kg"] == 63.5


def test_escenario2_total_es_la_suma_y_el_lote_agotado_no_aparece(como, stock):
    stock(40, "X-1")
    stock(25, "X-2")
    l3 = stock(10, "X-3")
    c = como("a")
    _mov(c, l3, "CONSUMO", 10)  # consumido por completo
    r = c.get(EXISTENCIAS).json()
    assert {item["lote_codigo"] for item in r["lotes"]} == {"X-1", "X-2"}
    assert r["total_kg"] == 65
    assert sum(item["existencias_kg"] for item in r["lotes"]) == r["total_kg"]


def test_cada_tostador_ve_solo_las_suyas(como, stock):
    stock(40, "X-1")
    assert como("b").get(EXISTENCIAS).json() == {"total_kg": 0, "lotes": []}


def test_una_compra_pendiente_aun_no_cuenta(como, usuarios, vincular, crear_lote):
    vincular(usuarios["a"].organizacion_id, usuarios["coop"].organizacion_id)
    lote = crear_lote(coop_id=usuarios["coop"].organizacion_id)
    como("a").post(
        COMPRAS,
        json={"lote_id": lote.id, "cantidad_kg": 60, "precio_kg": 28.5, "fecha_compra": "2026-11-01",
              "fecha_entrega_acordada": "2026-11-05"},
    )  # fmt: skip
    assert como("a").get(EXISTENCIAS).json()["total_kg"] == 0


def test_la_cooperativa_no_ve_existencias(como):
    assert como("coop").get(EXISTENCIAS).status_code == 403
