"""Valores permitidos (se guardan como texto en la base de datos)."""

import enum


class TipoOrganizacion(enum.StrEnum):
    TOSTADOR = "TOSTADOR"
    PROVEEDOR = "PROVEEDOR"  # empresa productora o cooperativa


class EstadoVinculo(enum.StrEnum):
    SIN_VINCULAR = "SIN_VINCULAR"
    INVITADO = "INVITADO"
    VINCULADO = "VINCULADO"


class ProcesoCafe(enum.StrEnum):
    LAVADO = "LAVADO"
    NATURAL = "NATURAL"
    HONEY = "HONEY"
    ANAEROBICO = "ANAEROBICO"
    OTRO = "OTRO"


class EstadoCompra(enum.StrEnum):
    PENDIENTE = "PENDIENTE"  # pendiente de recepción
    RECIBIDA = "RECIBIDA"
    ANULADA = "ANULADA"


class TipoMovimiento(enum.StrEnum):
    ENTRADA = "ENTRADA"  # se genera al registrar una recepción
    CONSUMO = "CONSUMO"  # café verde usado en el tostado
    MERMA = "MERMA"
    AJUSTE = "AJUSTE"  # conteo físico; cantidad con signo y motivo obligatorio


class OrigenConsumo(enum.StrEnum):
    IMPORTADO = "IMPORTADO"  # HU-18: cargado desde CSV/Excel
