"""Tipos compartidos por los schemas de la API."""

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

# Pydantic serializa Decimal como texto en JSON; el contrato usa números. Solo en JSON: al guardar en la base
# (`model_dump()`) los montos siguen siendo Decimal y no se mezclan con float.
Kg = Annotated[
    Decimal, Field(ge=0, max_digits=10, decimal_places=2), PlainSerializer(float, return_type=float, when_used="json")
]
Soles = Annotated[
    Decimal, Field(ge=0, max_digits=10, decimal_places=2), PlainSerializer(float, return_type=float, when_used="json")
]
KgConSigno = Annotated[
    Decimal, Field(max_digits=10, decimal_places=2), PlainSerializer(float, return_type=float, when_used="json")
]


class Esquema(BaseModel):
    """Base de las respuestas: permite construirlas desde objetos ORM."""

    model_config = ConfigDict(from_attributes=True)
