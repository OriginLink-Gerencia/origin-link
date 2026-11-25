"""Tipos compartidos por los schemas de la API."""

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

# Pydantic serializa Decimal como texto en JSON; el contrato usa números.
Kg = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2), PlainSerializer(float, return_type=float)]
Soles = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2), PlainSerializer(float, return_type=float)]
KgConSigno = Annotated[Decimal, Field(max_digits=10, decimal_places=2), PlainSerializer(float, return_type=float)]


class Esquema(BaseModel):
    """Base de las respuestas: permite construirlas desde objetos ORM."""

    model_config = ConfigDict(from_attributes=True)
