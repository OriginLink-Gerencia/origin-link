"""HU-04 Restringir el acceso según el rol y el vínculo: pruebas transversales a todas las rutas."""

import re

import pytest
from fastapi.testclient import TestClient

from app.main import app

API = "/api/v1"

# Rutas abiertas sin sesión (HU-01, HU-02 y HU-03). Cualquier ruta pública nueva debe agregarse aquí a propósito.
PUBLICAS: set[tuple[str, str]] = {
    ("POST", f"{API}/auth/registro"),
    ("POST", f"{API}/auth/login"),
    ("POST", f"{API}/auth/registro-invitacion"),
    ("GET", f"{API}/invitaciones/1"),
}


def _rutas() -> list[tuple[str, str]]:
    """(método, ruta) de cada endpoint de negocio, leídos del esquema OpenAPI (no depende de la versión de FastAPI)."""
    rutas = []
    for ruta, operaciones in app.openapi()["paths"].items():
        if ruta.startswith(API):
            for metodo in sorted(operaciones):
                rutas.append((metodo.upper(), re.sub(r"\{[^}]+\}", "1", ruta)))
    return rutas


RUTAS = _rutas()
SOLO_COOPERATIVA = {("GET", f"{API}/vinculos")}
SOLO_TOSTADOR = [
    (m, r)
    for m, r in RUTAS
    if (m, r) not in SOLO_COOPERATIVA
    and r.split("/")[3]
    in {
        "proveedores",
        "compras",
        "movimientos",
        "existencias",
        "consumo-historico",
        "pronostico",
        "recomendaciones",
        "alertas",
    }  # fmt: skip
]


def test_se_detectaron_las_rutas_de_negocio():
    assert len(RUTAS) >= 19 and len(SOLO_TOSTADOR) >= 14  # si baja, la enumeración dejó de funcionar


@pytest.mark.parametrize(("metodo", "ruta"), [r for r in RUTAS if r not in PUBLICAS])
def test_sin_sesion_ninguna_ruta_de_negocio_responde(metodo, ruta):
    """Sin token todo es 401: ninguna ruta queda abierta por olvido."""
    r = TestClient(app).request(metodo, ruta, json={})
    assert r.status_code == 401, f"{metodo} {ruta} respondió {r.status_code} sin sesión"


@pytest.mark.parametrize(("metodo", "ruta"), SOLO_TOSTADOR)
def test_la_cooperativa_recibe_403_en_las_rutas_del_tostador(como, metodo, ruta):
    r = como("coop").request(metodo, ruta, json={})
    assert r.status_code == 403, f"{metodo} {ruta} respondió {r.status_code}"


@pytest.mark.parametrize(("metodo", "ruta"), sorted(SOLO_COOPERATIVA))
def test_el_tostador_recibe_403_en_las_rutas_de_la_cooperativa(como, metodo, ruta):
    assert como("a").request(metodo, ruta).status_code == 403


COMPRAS = f"{API}/compras"
MOVS = f"{API}/movimientos"


@pytest.fixture
def dos_tostadores(como, usuarios, vincular, crear_lote):
    """A y B compran cada uno a la misma cooperativa y reciben café."""
    coop = usuarios["coop"].organizacion_id
    lotes = {}
    for clave in ("a", "b"):
        vincular(usuarios[clave].organizacion_id, coop)
    lotes["a"] = crear_lote(coop_id=coop, codigo="LOTE-A")
    for clave, kg in (("a", 30), ("b", 70)):
        c = como(clave)
        compra = c.post(
            COMPRAS,
            json={"lote_id": lotes["a"].id, "cantidad_kg": kg, "precio_kg": 10, "fecha_compra": "2026-11-01",
                  "fecha_entrega_acordada": "2026-11-05"},
        ).json()  # fmt: skip
        c.post(
            f"{COMPRAS}/{compra['id']}/recepcion", json={"fecha_recepcion": "2026-11-05", "cantidad_recibida_kg": kg}
        )
    return lotes


def test_escenario1_cada_tostador_solo_ve_registros_de_su_empresa(como, dos_tostadores):
    for clave, kg in (("a", 30), ("b", 70)):
        c = como(clave)
        assert [x["cantidad_kg"] for x in c.get(COMPRAS).json()] == [kg]
        assert [x["cantidad_kg"] for x in c.get(MOVS).json()] == [kg]
        assert c.get(f"{API}/existencias").json()["total_kg"] == kg


def test_escenario2_una_cooperativa_no_vinculada_no_ve_nada_del_tostador(como, db, dos_tostadores):
    from app.models import Organizacion, Usuario
    from app.models.enums import TipoOrganizacion

    otra = Organizacion(tipo=TipoOrganizacion.PROVEEDOR, nombre="Coop. sin vínculo")
    db.add(otra)
    db.flush()
    u = Usuario(organizacion_id=otra.id, nombre="Z", email="z@x.pe", password_hash="x")
    db.add(u)
    db.commit()
    como("coop")  # prepara el override de la base de datos
    from app.api.deps import get_usuario_actual

    app.dependency_overrides[get_usuario_actual] = lambda: u
    c = TestClient(app)
    for ruta in (COMPRAS, MOVS, f"{API}/existencias", f"{API}/proveedores"):
        assert c.get(ruta).status_code == 403  # no usa las rutas del tostador
    assert c.get(f"{API}/lotes").json() == []  # solo ve lotes propios
    assert (
        c.get(f"{API}/lotes/{dos_tostadores['a'].id}").status_code == 404
    )  # el lote de otra cooperativa no existe para ella


def test_un_tostador_no_ve_los_lotes_de_una_cooperativa_con_la_que_no_esta_vinculado(como, usuarios, crear_lote):
    lote = crear_lote(coop_id=usuarios["coop"].organizacion_id, codigo="SIN-VINCULO")
    assert como("a").get(f"{API}/lotes/{lote.id}").status_code == 404
    assert como("a").get(f"{API}/lotes").json() == []
