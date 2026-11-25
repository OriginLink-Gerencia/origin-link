"""HU-04: pruebas adicionales de acceso y aislamiento."""

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app


def test_rutas_privadas_sin_autenticacion(db):
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = lambda: db
    try:
        cliente = TestClient(app)
        assert cliente.get("/api/v1/proveedores").status_code == 401
        assert cliente.get("/api/v1/vinculos").status_code == 401
        assert cliente.post("/api/v1/proveedores", json={"nombre": "Prueba"}).status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_tostador_no_accede_a_proveedor_ajeno(como):
    propietario = como("a")
    pid = propietario.post("/api/v1/proveedores", json={"nombre": "Proveedor privado"}).json()["id"]

    ajeno = como("b")
    assert ajeno.get(f"/api/v1/proveedores/{pid}").status_code == 404
    assert ajeno.patch(f"/api/v1/proveedores/{pid}", json={"region": "Lima"}).status_code == 404
    assert ajeno.post(f"/api/v1/proveedores/{pid}/invitaciones").status_code == 404


def test_cooperativa_no_administra_proveedores(como):
    cooperativa = como("coop")
    assert cooperativa.get("/api/v1/proveedores").status_code == 403
    assert cooperativa.post("/api/v1/proveedores", json={"nombre": "Prohibido"}).status_code == 403


def test_tostador_no_consulta_vinculos_de_cooperativa(como):
    assert como("a").get("/api/v1/vinculos").status_code == 403
