"""HU-08 Publicar un lote de café verde (cooperativa vinculada con al menos un tostador)."""

import pytest
from sqlalchemy import select

from app.models import Lote

LOTES = "/api/v1/lotes"

LOTE = {
    "codigo": "JAEN-2026-07", "region": "Cajamarca - Jaén", "finca": "El Mirador", "variedad": "Caturra",
    "proceso": "LAVADO", "cosecha": "2026", "altitud_msnm": 1650,
    "caracteristicas": "Notas a chocolate y panela. Puntaje declarado 84",
    "cantidad_disponible_kg": 200, "precio_kg": 28.5, "cantidad_minima_kg": 30, "plazo_entrega_dias": 10,
}  # fmt: skip


@pytest.fixture
def coop_vinculada(usuarios, vincular):
    vincular(usuarios["a"].organizacion_id, usuarios["coop"].organizacion_id)


def test_escenario1_publicacion_exitosa(como, db, usuarios, coop_vinculada):
    r = como("coop").post(LOTES, json=LOTE)
    assert r.status_code == 201
    lote = r.json()
    assert lote["proveedor_nombre"] == "Coop. X"
    assert lote["registrado_por_tostador"] is False
    assert lote["agotado"] is False
    assert lote["cantidad_disponible_kg"] == 200 and lote["precio_kg"] == 28.5
    guardado = db.scalar(select(Lote).where(Lote.id == lote["id"]))
    assert guardado.organizacion_proveedora_id == usuarios["coop"].organizacion_id
    assert guardado.proveedor_id is None and guardado.publicado is True


def test_sin_vinculo_con_ningun_tostador_no_puede_publicar(como, db):
    r = como("coop").post(LOTES, json=LOTE)
    assert r.status_code == 400
    assert db.scalars(select(Lote)).all() == []


@pytest.mark.parametrize(
    ("campo", "valor"),
    [("altitud_msnm", -10), ("cantidad_disponible_kg", -1), ("precio_kg", -5), ("cantidad_minima_kg", -1)],
)
def test_escenario2_valores_negativos_no_se_publican(como, db, coop_vinculada, campo, valor):
    r = como("coop").post(LOTES, json={**LOTE, campo: valor})
    assert r.status_code == 422
    assert campo in str(r.json()["detail"])  # el error indica el campo
    assert db.scalars(select(Lote)).all() == []


def test_proceso_desconocido_se_rechaza(como, coop_vinculada):
    assert como("coop").post(LOTES, json={**LOTE, "proceso": "MAGICO"}).status_code == 422


def test_la_cooperativa_no_puede_registrar_a_nombre_de_un_proveedor_del_tostador(como, coop_vinculada):
    assert como("coop").post(LOTES, json={**LOTE, "proveedor_id": 1}).status_code == 400


def test_el_tostador_no_publica_lotes_de_cooperativa(como):
    assert como("a").post(LOTES, json=LOTE).status_code == 403
