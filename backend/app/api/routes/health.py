from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Verifica que la API responde (lo usa Cloud Run y el pipeline)."""
    s = get_settings()
    return {"status": "ok", "app": s.app_name, "environment": s.environment}


@router.get("/health/db")
def health_db(db: Session = Depends(get_db)) -> dict[str, str]:
    """Verifica la conexión con PostgreSQL (Neon en el ambiente de validación)."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "reachable"}
