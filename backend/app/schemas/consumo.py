"""EP-06 Historial de consumo (HU-18)."""

import datetime as dt

from pydantic import BaseModel


class ErrorFila(BaseModel):
    fila: int  # número de fila en el archivo (la 1 es el encabezado)
    error: str


class ImportacionOut(BaseModel):
    semanas_importadas: int
    desde: dt.date | None
    hasta: dt.date | None
    errores: list[ErrorFila]
