"""Modelos ORM de Origin Link.

Cada modelo nuevo debe importarse aquí para que Alembic lo detecte al generar migraciones.
Luego: alembic revision --autogenerate -m "descripción del cambio"

Diagrama y diccionario de datos: docs/arquitectura/modelo-de-datos.md
"""

from app.db.base import Base
from app.models.abastecimiento import Compra, ConsumoHistorico, MovimientoInventario, Recepcion
from app.models.identidad import Organizacion, Usuario
from app.models.lotes import Lote
from app.models.proveedores import Invitacion, Proveedor

__all__ = [
    "Base",
    "Compra",
    "ConsumoHistorico",
    "Invitacion",
    "Lote",
    "MovimientoInventario",
    "Organizacion",
    "Proveedor",
    "Recepcion",
    "Usuario",
]
