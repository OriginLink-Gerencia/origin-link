"""Coherencia de los datos sintéticos: inventario nunca negativo y consumo de la app = serie."""

from datetime import date, timedelta

import numpy as np
import pandas as pd

from generar_datos import maestros_demo, simular

SIGNO = {"ENTRADA": 1, "AJUSTE": 1, "CONSUMO": -1, "MERMA": -1}


def _generar(semilla=42):
    prov, lotes = maestros_demo(np.random.default_rng(semilla))
    return simular(prov, lotes, semanas_total=60, semanas_app=8, fin=date(2026, 11, 16), semilla=semilla)


def test_existencias_nunca_negativas():
    tablas, _, _ = _generar()
    m = tablas["movimientos"].copy()
    m["s"] = m["tipo"].map(SIGNO) * m["cantidad_kg"]
    m = m.sort_values(["fecha", "movimiento_id"])
    assert (m.groupby(["tostador_id", "lote_id"])["s"].cumsum() >= -0.01).all()


def test_consumo_registrado_coincide_con_la_serie():
    tablas, _, inicio_app = _generar()
    m = tablas["movimientos"]
    cons = m[m["tipo"] == "CONSUMO"].copy()
    cons["semana"] = pd.to_datetime(cons["fecha"]) - timedelta(days=4)
    reg = cons.groupby(["tostador_id", "semana"])["cantidad_kg"].sum().round(2)
    serie = tablas["consumo_semanal_completo"].assign(semana=lambda d: pd.to_datetime(d["fecha"]))
    serie = serie.set_index(["tostador_id", "semana"])["kg_consumidos"]
    comunes = reg.index.intersection(serie.index)
    assert len(comunes) > 0
    assert np.allclose(reg.loc[comunes], serie.loc[comunes], atol=0.02)


def test_historial_y_app_no_se_superponen():
    tablas, _, inicio_app = _generar()
    hist = pd.to_datetime(tablas["consumo_historico"]["semana"])
    assert (hist < pd.Timestamp(inicio_app)).all()


def test_serie_no_depende_de_los_maestros():
    a, _, _ = _generar(semilla=42)
    prov, lotes = maestros_demo(np.random.default_rng(999))  # otros maestros, misma semilla de la serie
    b, _, _ = simular(prov, lotes, semanas_total=60, semanas_app=8, fin=date(2026, 11, 16), semilla=42)
    pd.testing.assert_frame_equal(a["consumo_semanal_completo"], b["consumo_semanal_completo"])
