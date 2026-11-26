"""Configuración de la aplicación, leída desde variables de entorno (o backend/.env en local)."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Origin Link API"
    environment: str = "local"  # local | validacion
    api_prefix: str = "/api/v1"

    # Local: Postgres de docker-compose. En Cloud Run: connection string de Neon.
    database_url: str = "postgresql+psycopg://originlink:originlink@localhost:5432/originlink"

    # Orígenes permitidos para CORS, separados por coma (ej. la URL de Firebase Hosting).
    cors_origins: str = "http://localhost:5173"

    # Se exige en autenticación; no se asigna una clave predeterminada en producción.
    jwt_secret_key: str = ""

    # URL pública del frontend; se usa para armar los enlaces de invitación (HU-06).
    frontend_url: str = "http://localhost:5173"

    # Modelo TCN global entrenado (`python train_global.py` en ml/ lo deja en ml/models/tcn_global.pt).
    # Sin el archivo, sin PyTorch o con historial corto, el pronóstico usa el promedio móvil de 4 semanas (ADR-0003).
    model_path: str = "../ml/models/tcn_global.pt"
    # Carpeta que contiene el paquete `originlink_ml`; vacío = la carpeta `ml/` hermana de `backend/`.
    ml_path: str = ""

    @field_validator("database_url")
    @classmethod
    def usar_driver_psycopg(cls, v: str) -> str:
        # Neon entrega "postgresql://..." o "postgres://..."; SQLAlchemy necesita el driver explícito.
        if v.startswith("postgres://"):
            v = "postgresql://" + v.removeprefix("postgres://")
        if v.startswith("postgresql://"):
            v = "postgresql+psycopg://" + v.removeprefix("postgresql://")
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
