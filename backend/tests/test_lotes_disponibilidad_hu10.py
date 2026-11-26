"""HU-10 Actualizar disponibilidad y condiciones de abastecimiento de un lote."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.models import Lote
from app.models.enums import ProcesoCafe

LOTES = "/api/v1/lotes"


@pytest.fixture
def lote(db, usuarios, vincular):
    vincular(usuarios["a"].organizacion_id, usuarios["coop"].organizacion_id)
    obj = Lote(
        organizacion_proveedora_id=usuarios["coop"].organizacion_id, codigo="X-1", region="Cajamarca",
        variedad="Caturra", proceso=ProcesoCafe.LAVADO, cosecha="2026", cantidad_disponible_kg=Decimal("200"),
        precio_kg=Decimal("28.5"), cantidad_minima_kg=Decimal("30"), plazo_entrega_dias=10,
        actualizado_en=datetime(2026, 1, 1, tzinfo=UTC),
    )  # fmt: skip
    db.add(obj)
    db.commit()
    return obj


def _url(lote) -> str:
    return f"{LOTES}/{lote.id}/disponibilidad"


def test_escenario1_actualiza_cantidad_y_plazo_y_el_tostador_ve_el_dato_nuevo(como, lote):
    r = como("coop").patch(_url(lote), json={"cantidad_disponible_kg": 120.5, "plazo_entrega_dias": 5})
    assert r.status_code == 200
    assert r.json()["cantidad_disponible_kg"] == 120.5 and r.json()["plazo_entrega_dias"] == 5
    assert r.json()["precio_kg"] == 28.5  # lo no enviado no cambia
    visto = como("a").get(f"{LOTES}/{lote.id}").json()
    assert visto["cantidad_disponible_kg"] == 120.5
    assert datetime.fromisoformat(visto["actualizado_en"]).year >= 2026


def test_la_fecha_de_ultima_actualizacion_cambia(como, db, lote):
    antes = lote.actualizado_en
    como("coop").patch(_url(lote), json={"precio_kg": 30})
    db.refresh(lote)
    assert lote.actualizado_en.replace(tzinfo=None) > antes.replace(tzinfo=None)


def test_escenario2_cantidad_cero_marca_el_lote_como_agotado(como, lote):
    r = como("coop").patch(_url(lote), json={"cantidad_disponible_kg": 0})
    assert r.status_code == 200 and r.json()["agotado"] is True
    assert como("coop").patch(_url(lote), json={"cantidad_disponible_kg": 10}).json()["agotado"] is False


def test_despublicar_oculta_el_lote_al_tostador(como, lote):
    como("coop").patch(_url(lote), json={"publicado": False})
    assert como("a").get(f"{LOTES}/{lote.id}").status_code == 404


@pytest.mark.parametrize("cuerpo", [{"cantidad_disponible_kg": -1}, {"precio_kg": -2}, {"plazo_entrega_dias": -3}])
def test_valores_negativos_se_rechazan_y_no_cambian_el_lote(como, db, lote, cuerpo):
    assert como("coop").patch(_url(lote), json=cuerpo).status_code == 422
    db.refresh(lote)
    assert lote.cantidad_disponible_kg == Decimal("200") and lote.plazo_entrega_dias == 10


def test_un_campo_obligatorio_no_puede_ser_nulo(como, lote):
    assert como("coop").patch(_url(lote), json={"precio_kg": None}).status_code == 422


def test_otra_cooperativa_no_ve_ni_edita_el_lote(como, db, lote):
    from app.models import Organizacion, Usuario
    from app.models.enums import TipoOrganizacion

    otra = Organizacion(tipo=TipoOrganizacion.PROVEEDOR, nombre="Coop. Otra")
    db.add(otra)
    db.flush()
    u = Usuario(organizacion_id=otra.id, nombre="O", email="o@x.pe", password_hash="x")
    db.add(u)
    db.commit()
    from app.api.deps import get_usuario_actual
    from app.main import app

    como("coop")  # deja listo el override de la base
    app.dependency_overrides[get_usuario_actual] = lambda: u
    from fastapi.testclient import TestClient

    assert TestClient(app).patch(_url(lote), json={"precio_kg": 1}).status_code == 404


def test_el_tostador_no_puede_editar_un_lote_de_la_cooperativa(como, lote):
    assert como("a").patch(_url(lote), json={"precio_kg": 1}).status_code == 403
    assert como("b").patch(_url(lote), json={"precio_kg": 1}).status_code == 404  # ni siquiera lo ve


def test_lote_inexistente_es_404(como):
    assert como("coop").patch(f"{LOTES}/999/disponibilidad", json={"precio_kg": 1}).status_code == 404
