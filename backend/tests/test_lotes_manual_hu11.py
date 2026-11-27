"""HU-11 Registrar un lote de un proveedor sin cuenta (lo carga el tostador en su directorio)."""

import pytest
from sqlalchemy import select

from app.models import Lote, Proveedor
from app.models.enums import EstadoVinculo

LOTES = "/api/v1/lotes"

LOTE = {
    "codigo": "FM-01", "region": "San Martín", "variedad": "Catimor", "proceso": "NATURAL", "cosecha": "2026",
    "altitud_msnm": 1300, "cantidad_disponible_kg": 80, "precio_kg": 24,
}  # fmt: skip


@pytest.fixture
def ficha(db, usuarios):
    f = Proveedor(tostador_id=usuarios["a"].organizacion_id, nombre="Finca sin cuenta")
    db.add(f)
    db.commit()
    return f


def test_escenario1_lote_manual_aparece_marcado_como_registrado_por_el_tostador(como, db, ficha):
    r = como("a").post(LOTES, json={**LOTE, "proveedor_id": ficha.id})
    assert r.status_code == 201
    lote = r.json()
    assert lote["registrado_por_tostador"] is True and lote["proveedor_nombre"] == "Finca sin cuenta"
    guardado = db.scalar(select(Lote).where(Lote.id == lote["id"]))
    assert guardado.proveedor_id == ficha.id and guardado.organizacion_proveedora_id is None  # un solo origen
    lista = como("a").get(LOTES).json()
    assert [(item["codigo"], item["registrado_por_tostador"]) for item in lista] == [("FM-01", True)]


def test_el_lote_manual_es_privado_del_tostador(como, ficha):
    como("a").post(LOTES, json={**LOTE, "proveedor_id": ficha.id})
    assert como("b").get(LOTES).json() == []
    assert como("coop").get(LOTES).json() == []


def test_el_tostador_puede_actualizar_la_disponibilidad_de_su_lote_manual(como, ficha):
    lote_id = como("a").post(LOTES, json={**LOTE, "proveedor_id": ficha.id}).json()["id"]
    r = como("a").patch(f"{LOTES}/{lote_id}/disponibilidad", json={"cantidad_disponible_kg": 0})
    assert r.status_code == 200 and r.json()["agotado"] is True


def test_proveedor_de_otro_tostador_es_404(como, db, ficha):
    assert como("b").post(LOTES, json={**LOTE, "proveedor_id": ficha.id}).status_code == 404
    assert db.scalars(select(Lote)).all() == []


def test_proveedor_ya_vinculado_publica_sus_propios_lotes(como, db, ficha):
    ficha.estado_vinculo = EstadoVinculo.VINCULADO
    db.commit()
    assert como("a").post(LOTES, json={**LOTE, "proveedor_id": ficha.id}).status_code == 409


def test_el_tostador_debe_indicar_el_proveedor(como):
    assert como("a").post(LOTES, json=LOTE).status_code == 400


def test_valores_negativos_no_se_registran(como, db, ficha):
    r = como("a").post(LOTES, json={**LOTE, "proveedor_id": ficha.id, "cantidad_disponible_kg": -1})
    assert r.status_code == 422
    assert db.scalars(select(Lote)).all() == []
