"""Punto de entrada de la API de Origin Link."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import compras, health, lotes, movimientos, proveedores, vinculos
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API de Origin Link: abastecimiento colaborativo de café verde y pronóstico de demanda (TCN).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(proveedores.router, prefix=settings.api_prefix)
app.include_router(vinculos.router, prefix=settings.api_prefix)
app.include_router(lotes.router, prefix=settings.api_prefix)
app.include_router(compras.router, prefix=settings.api_prefix)
app.include_router(movimientos.router, prefix=settings.api_prefix)
# Registrar aquí los routers de cada módulo, por ejemplo:
