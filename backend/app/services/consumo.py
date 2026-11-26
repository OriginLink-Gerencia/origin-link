"""Historial semanal de consumo: lectura de CSV/Excel (HU-18) y serie que alimenta el pronóstico (HU-20).

La serie semanal de un tostador = consumo importado + consumo registrado en movimientos (CONSUMO), por semana
(lunes a domingo, identificada por su lunes). Las semanas sin dato entre la primera y la última cuentan como 0.
"""

import csv
import datetime as dt
import io
from collections import defaultdict
from decimal import Decimal, InvalidOperation

from openpyxl import load_workbook
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.abastecimiento import ConsumoHistorico, MovimientoInventario
from app.models.enums import OrigenConsumo, TipoMovimiento
from app.schemas.consumo import ErrorFila

MAX_FILAS = 20_000
MAX_BYTES = 2_000_000
COLUMNAS = ("fecha", "kg_consumidos")


class ArchivoInvalido(Exception):
    """El archivo no se puede leer como historial (formato, columnas o contenido vacío)."""


class ArchivoDemasiadoGrande(Exception):
    pass


def lunes(dia: dt.date) -> dt.date:
    return dia - dt.timedelta(days=dia.weekday())


def _filas_csv(contenido: bytes) -> list[list[str]]:
    try:
        texto = contenido.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = contenido.decode("latin-1")  # Excel en español suele guardar así
    primera = texto.splitlines()[0] if texto.strip() else ""
    delimitador = max(",;\t", key=primera.count) if primera else ","
    return [fila for fila in csv.reader(io.StringIO(texto), delimiter=delimitador)]


def _filas_xlsx(contenido: bytes) -> list[list[str]]:
    try:
        libro = load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
    except Exception as e:  # archivo corrupto o no es un .xlsx real
        raise ArchivoInvalido("No se pudo abrir el archivo Excel") from e
    filas = []
    for fila in libro.active.iter_rows(values_only=True):
        filas.append(
            ["" if c is None else (c.date().isoformat() if isinstance(c, dt.datetime) else str(c)) for c in fila]
        )
    return filas


def _fecha(texto: str) -> dt.date | None:
    texto = texto.strip()
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return dt.datetime.strptime(texto[:10] if formato == "%Y-%m-%d" else texto, formato).date()
        except ValueError:
            continue
    return None


def leer_archivo(nombre: str, contenido: bytes) -> tuple[dict[dt.date, Decimal], list[ErrorFila]]:
    """Devuelve el consumo por semana (lunes) y los errores por fila. Si hay errores no se debe guardar nada."""
    extension = nombre.lower().rsplit(".", 1)[-1] if "." in nombre else ""
    if extension not in {"csv", "xlsx"}:
        raise ArchivoInvalido("El archivo debe ser .csv o .xlsx")
    if len(contenido) > MAX_BYTES:
        raise ArchivoDemasiadoGrande
    filas = _filas_xlsx(contenido) if extension == "xlsx" else _filas_csv(contenido)
    if not filas:
        raise ArchivoInvalido("El archivo está vacío")
    if len(filas) - 1 > MAX_FILAS:
        raise ArchivoDemasiadoGrande

    encabezado = [c.strip().lower() for c in filas[0]]
    faltan = [c for c in COLUMNAS if c not in encabezado]
    if faltan:
        raise ArchivoInvalido(f"Faltan las columnas: {', '.join(faltan)}. Se esperan fecha y kg_consumidos")
    i_fecha, i_kg = encabezado.index("fecha"), encabezado.index("kg_consumidos")
    datos = [(n, f) for n, f in enumerate(filas[1:], start=2) if any(c.strip() for c in f)]
    if not datos:
        raise ArchivoInvalido("El archivo no tiene filas de datos")

    semanas: dict[dt.date, Decimal] = defaultdict(Decimal)
    errores: list[ErrorFila] = []
    for n, fila in datos:
        celda_fecha = fila[i_fecha] if i_fecha < len(fila) else ""
        celda_kg = (fila[i_kg] if i_kg < len(fila) else "").strip()
        dia = _fecha(celda_fecha)
        if dia is None:
            errores.append(ErrorFila(fila=n, error="fecha no válida"))
            continue
        if not celda_kg:
            errores.append(ErrorFila(fila=n, error="kg_consumidos vacío"))
            continue
        try:
            kg = Decimal(celda_kg.replace(",", "."))
        except InvalidOperation:
            errores.append(ErrorFila(fila=n, error="kg_consumidos no es un número"))
            continue
        if not kg.is_finite():
            errores.append(ErrorFila(fila=n, error="kg_consumidos no es un número"))
        elif kg < 0:
            errores.append(ErrorFila(fila=n, error="kg_consumidos negativo"))
        elif kg >= Decimal("1e8"):
            errores.append(ErrorFila(fila=n, error="kg_consumidos demasiado grande"))
        else:
            semanas[lunes(dia)] += kg
    return dict(semanas), errores


def guardar_semanas(db: Session, tostador_id: int, semanas: dict[dt.date, Decimal]) -> None:
    """Reemplaza las semanas del archivo y conserva las demás (reimportar corrige, no duplica)."""
    db.execute(
        delete(ConsumoHistorico).where(
            ConsumoHistorico.tostador_id == tostador_id, ConsumoHistorico.semana.in_(list(semanas))
        )
    )
    db.add_all(
        ConsumoHistorico(tostador_id=tostador_id, semana=s, kg_consumidos=kg, origen=OrigenConsumo.IMPORTADO)
        for s, kg in semanas.items()
    )
    db.commit()


def serie_semanal(db: Session, tostador_id: int) -> list[tuple[dt.date, Decimal]]:
    """Consumo semanal (importado + registrado) ordenado por semana, sin huecos."""
    total: dict[dt.date, Decimal] = defaultdict(Decimal)
    for semana, kg in db.execute(
        select(ConsumoHistorico.semana, ConsumoHistorico.kg_consumidos).where(
            ConsumoHistorico.tostador_id == tostador_id
        )
    ):
        total[semana] += Decimal(kg)
    for fecha, kg in db.execute(
        select(MovimientoInventario.fecha, MovimientoInventario.cantidad_kg).where(
            MovimientoInventario.tostador_id == tostador_id, MovimientoInventario.tipo == TipoMovimiento.CONSUMO
        )
    ):
        total[lunes(fecha)] += Decimal(kg)
    if not total:
        return []
    primera, ultima = min(total), max(total)
    semanas = (primera + dt.timedelta(weeks=i) for i in range((ultima - primera).days // 7 + 1))
    return [(s, total.get(s, Decimal(0))) for s in semanas]
