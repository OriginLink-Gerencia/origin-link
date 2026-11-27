"""Pruebas del contrato de la API: validaciones de entrada y formato de salida."""

import datetime as dt
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.enums import TipoMovimiento
from app.schemas.abastecimiento import CompraIn, MovimientoIn
from app.schemas.auth import RegistroTostadorIn
from app.schemas.lotes import LoteIn


def test_registro_rechaza_password_corta():
    with pytest.raises(ValidationError):
        RegistroTostadorIn(empresa="Tostaduría", nombre="Raúl", email="raul@cafe.pe", password="123")


def test_lote_rechaza_cantidad_y_altitud_negativas():
    base = dict(codigo="J-01", region="Jaén", variedad="Caturra", proceso="LAVADO", cosecha="2026", precio_kg=28)
    with pytest.raises(ValidationError):
        LoteIn(**base, cantidad_disponible_kg=-5)
    with pytest.raises(ValidationError):
        LoteIn(**base, cantidad_disponible_kg=100, altitud_msnm=-10)


def test_kg_se_serializa_como_numero():
    lote = LoteIn(
        codigo="J-01", region="Jaén", variedad="Caturra", proceso="LAVADO", cosecha="2026",
        cantidad_disponible_kg=Decimal("200.50"), precio_kg=Decimal("28.5"),
    )  # fmt: skip
    datos = lote.model_dump(mode="json")
    assert datos["cantidad_disponible_kg"] == 200.5
    assert isinstance(datos["precio_kg"], float)


def test_compra_rechaza_entrega_anterior_a_compra():
    with pytest.raises(ValidationError):
        CompraIn(
            lote_id=1, cantidad_kg=60, precio_kg=28,
            fecha_compra=dt.date(2026, 11, 20), fecha_entrega_acordada=dt.date(2026, 11, 10),
        )  # fmt: skip


def test_compra_rechaza_cantidad_cero():
    with pytest.raises(ValidationError):
        CompraIn(
            lote_id=1, cantidad_kg=0, precio_kg=28,
            fecha_compra=dt.date(2026, 11, 20), fecha_entrega_acordada=dt.date(2026, 11, 30),
        )  # fmt: skip


@pytest.mark.parametrize(
    "tipo,cantidad,motivo",
    [
        (TipoMovimiento.ENTRADA, 10, None),  # las entradas las genera la recepción
        (TipoMovimiento.AJUSTE, 2, None),  # ajuste sin motivo
        (TipoMovimiento.CONSUMO, -3, None),  # consumo negativo
    ],
)
def test_movimiento_invalido(tipo, cantidad, motivo):
    with pytest.raises(ValidationError):
        MovimientoIn(lote_id=1, tipo=tipo, cantidad_kg=cantidad, fecha=dt.date(2026, 11, 20), motivo=motivo)


def test_ajuste_negativo_con_motivo_es_valido():
    m = MovimientoIn(lote_id=1, tipo="AJUSTE", cantidad_kg=-1.5, fecha=dt.date(2026, 11, 20), motivo="Conteo físico")
    assert m.cantidad_kg == Decimal("-1.5")
