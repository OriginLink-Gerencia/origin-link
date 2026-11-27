"""Pruebas del backend.

Se ejecuta antes que cualquier conftest o módulo de prueba, para que la configuración (con caché) ya tenga
la clave JWT de pruebas cuando se importa la app. No es una clave real.
"""

import os

os.environ.setdefault("JWT_SECRET_KEY", "test-key-only-DO-NOT-USE-IN-PRODUCTION-123456789")
