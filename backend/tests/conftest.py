"""Fixtures compartidas: base SQLite en memoria, usuarios de prueba y clientes autenticados.

La autenticación real (JWT) llega con HU-01/02; aquí `get_usuario_actual` se sustituye por un usuario de prueba.
"""

import datetime as dt
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.deps import get_hoy, get_usuario_actual
from app.db.session import get_db
from app.main import app
from app.models import Base, Lote, Organizacion, Proveedor, Usuario
from app.models.enums import EstadoVinculo, ProcesoCafe, TipoOrganizacion

# Fecha fija de las pruebas: miércoles. La última semana completa con consumo empieza el lunes 16/11.
HOY = dt.date(2026, 11, 25)


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    event.listen(engine, "connect", lambda con, _: con.execute("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as s:  # igual que SessionLocal: los valores no se releen tras commit
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
        app.dependency_overrides[get_hoy] = lambda: HOY
        return TestClient(app)

    yield _cliente
    app.dependency_overrides.clear()


@pytest.fixture
def vincular(db):
    """Vincula una cooperativa con un tostador (como lo deja HU-03): una ficha de proveedor VINCULADA."""

    def _vincular(tostador_id: int, coop_id: int, nombre: str = "Coop. X") -> Proveedor:
        prov = Proveedor(
            tostador_id=tostador_id,
            organizacion_proveedora_id=coop_id,
            nombre=nombre,
            estado_vinculo=EstadoVinculo.VINCULADO,
        )
        db.add(prov)
        db.commit()
        return prov

    return _vincular


@pytest.fixture
def crear_lote(db):
    """Crea un lote de la cooperativa (`coop_id`) o de la ficha del directorio de un tostador (`proveedor_id`)."""

    def _crear(*, coop_id: int | None = None, proveedor_id: int | None = None, **extra) -> Lote:
        datos = dict(
            codigo="L-1", region="Cajamarca", variedad="Caturra", proceso=ProcesoCafe.LAVADO, cosecha="2026",
            altitud_msnm=1600, cantidad_disponible_kg=Decimal("200"), precio_kg=Decimal("28.5"),
        )  # fmt: skip
        lote = Lote(organizacion_proveedora_id=coop_id, proveedor_id=proveedor_id, **{**datos, **extra})
        db.add(lote)
        db.commit()
        return lote

    return _crear
