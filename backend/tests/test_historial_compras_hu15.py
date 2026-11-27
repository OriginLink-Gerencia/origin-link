"""HU-15 Historial de compras y recepciones de un proveedor."""

import pytest

COMPRAS = "/api/v1/compras"
PROVEEDORES = "/api/v1/proveedores"


@pytest.fixture
def historial(como, usuarios, vincular, crear_lote):
    """Tostador A compró 3 veces a Coop. X (una recibida con diferencia) y 1 vez a otra ficha."""
    coop = usuarios["coop"].organizacion_id
    ficha = vincular(usuarios["a"].organizacion_id, coop)
    lote = crear_lote(coop_id=coop, codigo="X-1")
    c = como("a")
    ids = []
    for kg, fecha in [(60, "2026-10-01"), (40, "2026-10-15"), (20, "2026-11-01")]:
        ids.append(
            c.post(
                COMPRAS,
                json={"lote_id": lote.id, "cantidad_kg": kg, "precio_kg": 28.5, "fecha_compra": fecha,
                      "fecha_entrega_acordada": "2026-11-20"},
            ).json()["id"]
        )  # fmt: skip
    c.post(f"{COMPRAS}/{ids[0]}/recepcion", json={"fecha_recepcion": "2026-10-08", "cantidad_recibida_kg": 55})
    return ficha, ids


def test_escenario1_historial_con_fechas_kilos_acordados_recibidos_y_diferencias(como, historial):
    ficha, ids = historial
    r = como("a").get(f"{PROVEEDORES}/{ficha.id}/compras")
    assert r.status_code == 200
    por_id = {c["id"]: c for c in r.json()}
    assert set(por_id) == set(ids)
    recibida = por_id[ids[0]]
    assert recibida["cantidad_kg"] == 60 and recibida["fecha_compra"] == "2026-10-01"
    assert recibida["recepcion"]["cantidad_recibida_kg"] == 55 and recibida["recepcion"]["diferencia_kg"] == -5
    assert por_id[ids[1]]["recepcion"] is None and por_id[ids[1]]["estado"] == "PENDIENTE"


def test_orden_de_la_mas_reciente_a_la_mas_antigua(como, historial):
    ficha, _ = historial
    fechas = [c["fecha_compra"] for c in como("a").get(f"{PROVEEDORES}/{ficha.id}/compras").json()]
    assert fechas == sorted(fechas, reverse=True)


def test_proveedor_sin_compras_devuelve_lista_vacia(como, db, usuarios):
    from app.models import Proveedor

    f = Proveedor(tostador_id=usuarios["a"].organizacion_id, nombre="Nuevo")
    db.add(f)
    db.commit()
    assert como("a").get(f"{PROVEEDORES}/{f.id}/compras").json() == []


def test_proveedor_de_otro_tostador_es_404(como, historial):
    ficha, _ = historial
    assert como("b").get(f"{PROVEEDORES}/{ficha.id}/compras").status_code == 404
    assert como("a").get(f"{PROVEEDORES}/9999/compras").status_code == 404


def test_la_cooperativa_no_ve_historiales(como, historial):
    ficha, _ = historial
    assert como("coop").get(f"{PROVEEDORES}/{ficha.id}/compras").status_code == 403
