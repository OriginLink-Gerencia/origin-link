"""HU-05 Registrar un proveedor: escenarios del backlog y aislamiento por organización (HU-04).

La autenticación real llega con HU-01/02; aquí se sustituye `get_usuario_actual` por un usuario de prueba.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.deps import get_usuario_actual
from app.db.session import get_db
from app.main import app
from app.models import Base, Organizacion, Usuario
from app.models.enums import TipoOrganizacion

BASE = "/api/v1/proveedores"


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    event.listen(engine, "connect", lambda con, _: con.execute("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def usuarios(db):
    """Dos tostadores y una cooperativa, cada uno con un usuario."""
    orgs = [
        Organizacion(tipo=TipoOrganizacion.TOSTADOR, nombre="Tostaduría A"),
        Organizacion(tipo=TipoOrganizacion.TOSTADOR, nombre="Tostaduría B"),
        Organizacion(tipo=TipoOrganizacion.PROVEEDOR, nombre="Coop. X"),
    ]
    db.add_all(orgs)
    db.flush()
    us = [
        Usuario(organizacion_id=o.id, nombre=f"U{i}", email=f"u{i}@x.pe", password_hash="x") for i, o in enumerate(orgs)
    ]
    db.add_all(us)
    db.commit()
    return {"a": us[0], "b": us[1], "coop": us[2]}


@pytest.fixture
def como(db, usuarios):
    """Devuelve un cliente autenticado como el usuario indicado ("a", "b" o "coop")."""

    def _cliente(clave: str) -> TestClient:
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_usuario_actual] = lambda: usuarios[clave]
        return TestClient(app)

    yield _cliente
    app.dependency_overrides.clear()


DATOS = {"nombre": "Coop. Jaén", "region": "Cajamarca", "contacto_nombre": "Ana Pérez",
         "contacto_telefono": "987654321", "contacto_email": "ana@coopjaen.pe"}  # fmt: skip


def test_escenario1_proveedor_nuevo_aparece_sin_vincular(como):
    c = como("a")
    r = c.post(BASE, json=DATOS)
    assert r.status_code == 201
    creado = r.json()
    assert creado["nombre"] == "Coop. Jaén"
    assert creado["estado_vinculo"] == "SIN_VINCULAR"
    assert creado["organizacion_proveedora_id"] is None
    lista = c.get(BASE).json()
    assert [p["id"] for p in lista] == [creado["id"]]
    assert lista[0]["estado_vinculo"] == "SIN_VINCULAR"


@pytest.mark.parametrize("nombre", ["", "   ", "A"])
def test_escenario2_nombre_obligatorio_no_se_guarda(como, nombre):
    c = como("a")
    r = c.post(BASE, json={**DATOS, "nombre": nombre})
    assert r.status_code == 422
    assert c.get(BASE).json() == []


def test_nombre_se_guarda_sin_espacios_sobrantes(como):
    r = como("a").post(BASE, json={"nombre": "  Coop. Jaén  "})
    assert r.status_code == 201 and r.json()["nombre"] == "Coop. Jaén"


def test_solo_nombre_es_obligatorio(como):
    r = como("a").post(BASE, json={"nombre": "Finca El Mirador"})
    assert r.status_code == 201
    assert r.json()["region"] is None and r.json()["contacto_email"] is None


def test_correo_de_contacto_invalido_se_rechaza(como):
    assert como("a").post(BASE, json={**DATOS, "contacto_email": "no-es-correo"}).status_code == 422


def test_cada_tostador_ve_solo_sus_proveedores(como):
    como("a").post(BASE, json=DATOS)
    assert len(como("a").get(BASE).json()) == 1
    assert como("b").get(BASE).json() == []


def test_detalle_de_proveedor_de_otro_tostador_es_404(como):
    pid = como("a").post(BASE, json=DATOS).json()["id"]
    assert como("a").get(f"{BASE}/{pid}").status_code == 200
    r = como("b").get(f"{BASE}/{pid}")
    assert r.status_code == 404  # no revela que existe


def test_proveedor_inexistente_es_404(como):
    assert como("a").get(f"{BASE}/999").status_code == 404


def test_cooperativa_no_puede_usar_las_rutas_del_tostador(como):
    c = como("coop")
    assert c.get(BASE).status_code == 403
    assert c.post(BASE, json=DATOS).status_code == 403


def test_sin_sesion_es_401(db):
    app.dependency_overrides[get_db] = lambda: db
    try:
        assert TestClient(app).get(BASE).status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_patch_actualiza_solo_lo_enviado(como):
    c = como("a")
    pid = c.post(BASE, json=DATOS).json()["id"]
    r = c.patch(f"{BASE}/{pid}", json={"region": "San Martín"})
    assert r.status_code == 200
    assert r.json()["region"] == "San Martín"
    assert r.json()["nombre"] == "Coop. Jaén"  # sin tocar
    assert r.json()["estado_vinculo"] == "SIN_VINCULAR"


def test_patch_no_permite_dejar_el_nombre_vacio(como):
    c = como("a")
    pid = c.post(BASE, json=DATOS).json()["id"]
    assert c.patch(f"{BASE}/{pid}", json={"nombre": " "}).status_code == 422
    assert c.patch(f"{BASE}/{pid}", json={"nombre": None}).status_code == 422
    assert c.get(f"{BASE}/{pid}").json()["nombre"] == "Coop. Jaén"


def test_patch_de_proveedor_ajeno_es_404(como):
    pid = como("a").post(BASE, json=DATOS).json()["id"]
    assert como("b").patch(f"{BASE}/{pid}", json={"region": "X"}).status_code == 404
    assert como("a").get(f"{BASE}/{pid}").json()["region"] == "Cajamarca"
