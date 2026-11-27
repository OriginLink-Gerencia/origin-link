"""Pruebas HU-03 con SQLite aislado; no toca Neon."""

import os
from datetime import UTC, datetime, timedelta

os.environ.setdefault("JWT_SECRET_KEY", "test-key-only-DO-NOT-USE-IN-PRODUCTION-123456789")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.auth_security import hash_password, make_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import EstadoVinculo, TipoOrganizacion
from app.models.identidad import Organizacion, Usuario
from app.models.proveedores import Invitacion, Proveedor

TABLAS = [Organizacion.__table__, Usuario.__table__, Proveedor.__table__, Invitacion.__table__]


@pytest.fixture
def contexto():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def fk(dbapi_connection, connection_record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine, tables=TABLAS)

    def override():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override
    try:
        yield TestClient(app), engine
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine, tables=list(reversed(TABLAS)))
        engine.dispose()


def crear_invitacion(engine, token="token-prueba", vencida=False):
    with Session(engine) as db:
        tostador = Organizacion(tipo=TipoOrganizacion.TOSTADOR, nombre="Tostadora Uno")
        db.add(tostador)
        db.flush()
        prov = Proveedor(tostador_id=tostador.id, nombre="Cooperativa Jaén", estado_vinculo=EstadoVinculo.INVITADO)
        db.add(prov)
        db.flush()
        inv = Invitacion(
            proveedor_id=prov.id,
            token=token,
            creado_en=datetime.now(UTC) - timedelta(days=1),
            expira_en=datetime.now(UTC) - timedelta(seconds=1) if vencida else datetime.now(UTC) + timedelta(days=6),
        )
        db.add(inv)
        db.commit()
        return prov.id


DATOS = {
    "token": "token-prueba",
    "empresa": "Cooperativa Jaén",
    "ruc": None,
    "region": "Cajamarca",
    "nombre": "Ana",
    "email": "ana@cooperativa.pe",
    "password": "ClaveSegura123",
}


def test_invitacion_publica_y_registro_completo(contexto):
    client, engine = contexto
    proveedor_id = crear_invitacion(engine)
    info = client.get("/api/v1/invitaciones/token-prueba")
    assert info.status_code == 200 and info.json()["vigente"] is True
    r = client.post("/api/v1/auth/registro-invitacion", json=DATOS)
    assert r.status_code == 201, r.text
    assert r.json()["usuario"]["organizacion"]["tipo"] == "PROVEEDOR"
    token = r.json()["access_token"]
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    with Session(engine) as db:
        proveedor = db.get(Proveedor, proveedor_id)
        assert proveedor.estado_vinculo == EstadoVinculo.VINCULADO
        assert proveedor.organizacion_proveedora_id is not None
        assert db.scalar(select(Invitacion).where(Invitacion.token == "token-prueba")).usada_en is not None
    assert client.get("/api/v1/invitaciones/token-prueba").json()["vigente"] is False
    assert client.post("/api/v1/auth/registro-invitacion", json={**DATOS, "email": "otra@coop.pe"}).status_code == 400


def test_invitacion_vencida_y_token_inexistente(contexto):
    client, engine = contexto
    crear_invitacion(engine, vencida=True)
    assert client.get("/api/v1/invitaciones/token-prueba").json()["vigente"] is False
    assert client.post("/api/v1/auth/registro-invitacion", json=DATOS).status_code == 400
    assert client.get("/api/v1/invitaciones/inexistente").status_code == 404


def test_correo_duplicado_no_consume_invitacion(contexto):
    client, engine = contexto
    crear_invitacion(engine)
    with Session(engine) as db:
        org = Organizacion(tipo=TipoOrganizacion.PROVEEDOR, nombre="Otra coop")
        db.add(Usuario(organizacion=org, nombre="Ana", email="ana@cooperativa.pe", password_hash=hash_password("test")))
        db.commit()
    assert client.post("/api/v1/auth/registro-invitacion", json=DATOS).status_code == 409
    assert client.get("/api/v1/invitaciones/token-prueba").json()["vigente"] is True


def test_cooperativa_existente_acepta_invitacion(contexto):
    client, engine = contexto
    proveedor_id = crear_invitacion(engine)
    with Session(engine) as db:
        org = Organizacion(tipo=TipoOrganizacion.PROVEEDOR, nombre="Coop existente")
        user = Usuario(
            organizacion=org, nombre="María", email="maria@coop.pe", password_hash=hash_password("segura123")
        )
        db.add(user)
        db.commit()
        token = make_access_token(user.id)
        org_id = org.id
    resp = client.post("/api/v1/invitaciones/token-prueba/aceptar", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["tostador"] == "Tostadora Uno"
    with Session(engine) as db:
        proveedor = db.get(Proveedor, proveedor_id)
        assert proveedor.organizacion_proveedora_id == org_id
    assert (
        client.post(
            "/api/v1/invitaciones/token-prueba/aceptar", headers={"Authorization": f"Bearer {token}"}
        ).status_code
        == 400
    )
