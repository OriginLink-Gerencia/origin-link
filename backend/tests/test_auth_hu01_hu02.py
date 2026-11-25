"""Pruebas aisladas de Registro/Login, sin conexión a Neon.

Requiere modelos y esquemas aprobados de PR #35 y sqlite (incluido en Python).
"""

import os

os.environ.setdefault("JWT_SECRET_KEY", "test-key-only-DO-NOT-USE-IN-PRODUCTION-123456789")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.identidad import Organizacion, Usuario


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, connection_record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine, tables=[Organizacion.__table__, Usuario.__table__])

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine, tables=[Usuario.__table__, Organizacion.__table__])
        engine.dispose()


REGISTRO = {
    "empresa": "Tostaduría Raúl",
    "ruc": "20123456789",
    "nombre": "Raúl Tello",
    "email": "raul@cafe.pe",
    "password": "PasswordSegura123!",
}


def test_registro_y_me(client):
    respuesta = client.post("/api/v1/auth/registro", json=REGISTRO)
    assert respuesta.status_code == 201, respuesta.text
    payload = respuesta.json()
    assert payload["usuario"]["organizacion"]["tipo"] == "TOSTADOR"
    assert payload["usuario"]["email"] == "raul@cafe.pe"
    assert payload["token_type"] == "bearer"
    perfil = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {payload['access_token']}"})
    assert perfil.status_code == 200
    assert perfil.json()["email"] == "raul@cafe.pe"


def test_correo_duplicado_no_crea_otra_cuenta(client):
    assert client.post("/api/v1/auth/registro", json=REGISTRO).status_code == 201
    r = client.post("/api/v1/auth/registro", json=REGISTRO)
    assert r.status_code == 409
    assert r.json()["detail"] == "Ya existe una cuenta con este correo"


def test_password_corta(client):
    r = client.post("/api/v1/auth/registro", json={**REGISTRO, "password": "123"})
    assert r.status_code == 422


def test_login_correcto_incorrecto_y_sin_token(client):
    assert client.post("/api/v1/auth/registro", json=REGISTRO).status_code == 201
    ok = client.post("/api/v1/auth/login", json={"email": REGISTRO["email"], "password": REGISTRO["password"]})
    assert ok.status_code == 200
    bad = client.post("/api/v1/auth/login", json={"email": REGISTRO["email"], "password": "incorrecta"})
    assert bad.status_code == 401
    assert bad.json()["detail"] == "Correo o contraseña incorrectos"
    assert client.get("/api/v1/auth/me").status_code == 401


def test_token_invalido(client):
    r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer token-invalido"})
    assert r.status_code == 401


def test_registro_normaliza_email_y_exige_ruc_valido(client):
    r = client.post("/api/v1/auth/registro", json={**REGISTRO, "email": "RAUL@CAFE.PE"})
    assert r.status_code == 201, r.text
    assert r.json()["usuario"]["email"] == "raul@cafe.pe"
    dup = client.post("/api/v1/auth/registro", json=REGISTRO)
    assert dup.status_code == 409
    bad_ruc = client.post("/api/v1/auth/registro", json={**REGISTRO, "email": "otro@cafe.pe", "ruc": "1234"})
    assert bad_ruc.status_code == 422


def test_logout_no_tiene_endpoint_por_contrato(client):
    assert client.post("/api/v1/auth/logout").status_code == 404
