"""Recorrido completo con autenticación real (sin sustituir usuarios): lo que hará el frontend de punta a punta.

registro del tostador -> proveedor -> invitación -> registro de la cooperativa -> lote -> compra -> recepción
-> existencias -> consumo -> historial.
"""

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app

API = "/api/v1"


@pytest.fixture
def api(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_flujo_completo_de_abastecimiento_con_jwt(api):
    # 1. El tostador crea su cuenta e inicia sesión
    r = api.post(
        f"{API}/auth/registro",
        json={"empresa": "Tostaduría Raúl", "nombre": "Raúl", "email": "raul@cafe.pe", "password": "clave-segura-1"},
    )
    assert r.status_code == 201
    login = api.post(f"{API}/auth/login", json={"email": "raul@cafe.pe", "password": "clave-segura-1"})
    assert login.status_code == 200
    tostador = _auth(login.json()["access_token"])
    assert api.get(f"{API}/auth/me", headers=tostador).json()["organizacion"]["tipo"] == "TOSTADOR"

    # 2. Registra a su proveedor y lo invita
    prov = api.post(f"{API}/proveedores", json={"nombre": "Coop. Jaén", "region": "Cajamarca"}, headers=tostador).json()
    assert prov["estado_vinculo"] == "SIN_VINCULAR"
    inv = api.post(f"{API}/proveedores/{prov['id']}/invitaciones", headers=tostador)
    assert inv.status_code == 201
    token = inv.json()["token"]
    assert api.get(f"{API}/proveedores/{prov['id']}", headers=tostador).json()["estado_vinculo"] == "INVITADO"

    # 3. La cooperativa abre el enlace (público) y crea su cuenta con la invitación
    info = api.get(f"{API}/invitaciones/{token}").json()
    assert info["vigente"] is True and info["tostador"] == "Tostaduría Raúl"
    reg = api.post(
        f"{API}/auth/registro-invitacion",
        json={
            "token": token,
            "empresa": "Coop. Jaén",
            "region": "Cajamarca",
            "nombre": "Ana",
            "email": "ana@coopjaen.pe",
            "password": "clave-segura-2",
        },
    )
    assert reg.status_code == 201
    coop = _auth(reg.json()["access_token"])
    assert api.get(f"{API}/proveedores/{prov['id']}", headers=tostador).json()["estado_vinculo"] == "VINCULADO"
    assert [v["tostador"] for v in api.get(f"{API}/vinculos", headers=coop).json()] == ["Tostaduría Raúl"]

    # 4. La cooperativa publica un lote y el tostador lo ve
    lote = api.post(
        f"{API}/lotes",
        headers=coop,
        json={
            "codigo": "JAEN-2026-07",
            "region": "Cajamarca - Jaén",
            "variedad": "Caturra",
            "proceso": "LAVADO",
            "cosecha": "2026",
            "altitud_msnm": 1650,
            "cantidad_disponible_kg": 200,
            "precio_kg": 28.5,
        },
    )
    assert lote.status_code == 201
    visibles = api.get(f"{API}/lotes", headers=tostador).json()
    assert [item["codigo"] for item in visibles] == ["JAEN-2026-07"]

    # 5. El tostador compra, recibe con diferencia y ve sus existencias
    compra = api.post(
        f"{API}/compras",
        headers=tostador,
        json={
            "lote_id": lote.json()["id"],
            "cantidad_kg": 60,
            "precio_kg": 28.5,
            "fecha_compra": "2026-11-19",
            "fecha_entrega_acordada": "2026-11-29",
        },
    )
    assert compra.status_code == 201 and compra.json()["total"] == 1710
    rec = api.post(
        f"{API}/compras/{compra.json()['id']}/recepcion",
        headers=tostador,
        json={"fecha_recepcion": "2026-11-29", "cantidad_recibida_kg": 55},
    )
    assert rec.status_code == 201 and rec.json()["recepcion"]["diferencia_kg"] == -5
    assert api.get(f"{API}/existencias", headers=tostador).json()["total_kg"] == 55

    # 6. Consume café y las existencias bajan; el historial del proveedor muestra la diferencia
    mov = api.post(
        f"{API}/movimientos",
        headers=tostador,
        json={"lote_id": lote.json()["id"], "tipo": "CONSUMO", "cantidad_kg": 8, "fecha": "2026-12-01"},
    )
    assert mov.status_code == 201
    assert api.get(f"{API}/existencias", headers=tostador).json()["total_kg"] == 47
    historial = api.get(f"{API}/proveedores/{prov['id']}/compras", headers=tostador).json()
    assert [c["recepcion"]["diferencia_kg"] for c in historial] == [-5]

    # 7. Aislamiento: la cooperativa no entra al inventario del tostador y sin token no hay acceso
    assert api.get(f"{API}/existencias", headers=coop).status_code == 403
    assert api.get(f"{API}/existencias").status_code == 401
    assert api.get(f"{API}/existencias", headers=_auth("token-falso")).status_code == 401
