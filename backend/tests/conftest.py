"""Fixtures compartidas: base SQLite en memoria, usuarios de prueba y clientes autenticados.

La autenticación real (JWT) llega con HU-01/02; aquí `get_usuario_actual` se sustituye por un usuario de prueba.
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
