"""TT-01 Datos de demostración: un tostador con historial, una cooperativa vinculada y existencias bajas."""

import datetime as dt

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.main import app
from app.models import Organizacion, Usuario
from app.models.abastecimiento import ConsumoHistorico
from app.seed_demo import DEMO_EMAIL_COOP, DEMO_EMAIL_TOSTADOR, DEMO_PASSWORD, sembrar
from app.services import pronostico as servicio

HOY = dt.date(2026, 11, 25)


def test_siembra_los_datos_y_se_puede_iniciar_sesion_y_pronosticar(db, monkeypatch):
    monkeypatch.setattr(servicio, "cargar_modelo", lambda: None)
    sembrar(db, hoy=HOY)
    assert db.scalar(select(func.count()).select_from(ConsumoHistorico)) == 60

    from app.api.deps import get_hoy
    from app.db.session import get_db

    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_hoy] = lambda: HOY
    try:
        c = TestClient(app)
        token = c.post("/api/v1/auth/login", json={"email": DEMO_EMAIL_TOSTADOR, "password": DEMO_PASSWORD}).json()
        cabecera = {"Authorization": f"Bearer {token['access_token']}"}
        p = c.get("/api/v1/pronostico", headers=cabecera).json()
        assert p["metodo"] == "PROMEDIO_MOVIL" and len(p["pronostico"]) == 4 and len(p["historial"]) == 60
        assert c.get("/api/v1/existencias", headers=cabecera).json()["total_kg"] > 0
        assert [a["tipo"] for a in c.get("/api/v1/alertas", headers=cabecera).json()] == ["STOCK_BAJO"]
        assert c.get("/api/v1/recomendaciones", headers=cabecera).json()["cantidad_sugerida_kg"] > 0
        assert len(c.get("/api/v1/lotes", headers=cabecera).json()) >= 2
        assert (
            c.post("/api/v1/auth/login", json={"email": DEMO_EMAIL_COOP, "password": DEMO_PASSWORD}).status_code == 200
        )
    finally:
        app.dependency_overrides.clear()


def test_sembrar_dos_veces_no_duplica(db):
    sembrar(db, hoy=HOY)
    sembrar(db, hoy=HOY)
    assert db.scalar(select(func.count()).select_from(Usuario).where(Usuario.email == DEMO_EMAIL_TOSTADOR)) == 1
    assert db.scalar(select(func.count()).select_from(Organizacion)) == 2
