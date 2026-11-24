"""Pruebas del modelo TCN global (HU-19)."""

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
import torch

from originlink_ml.global_model import (
    PM_METODO,
    Config,
    Serie,
    calendario,
    construir_conjunto,
    elegir_metodo_por_tostador,
    entrenar_conjunto,
    errores,
    pronosticar,
    resumen_mape,
)

CFG = Config(epocas=15, semillas=2, paciencia=5)


def serie_sintetica(id_: str, n: int = 80, nivel: float = 8.0, seed: int = 0) -> Serie:
    rng = np.random.default_rng(seed)
    fechas = pd.date_range("2025-01-06", periods=n, freq="W-MON")
    t = np.arange(n)
    kg = nivel + 1.5 * np.sin(2 * np.pi * t / 52) + rng.normal(0, 0.4, n)
    return Serie(id_, fechas, kg.clip(min=0.1))


@pytest.fixture(scope="module")
def series():
    return [serie_sintetica("A", nivel=6, seed=1), serie_sintetica("B", nivel=12, seed=2)]


def test_calendario_cubre_el_futuro_y_esta_acotado():
    s = serie_sintetica("A", n=30)
    cal = calendario(s.fechas, 4)
    assert cal.shape == (34, 2)
    assert np.all(np.abs(cal) <= 1.0)


def test_entrenamiento_no_ve_semanas_de_validacion_ni_de_prueba(series):
    """Cambiar los kg de las últimas semanas (validación y prueba) no altera las muestras de entrenamiento."""
    corte = -(CFG.semanas_prueba + CFG.semanas_validacion)
    original = construir_conjunto(series, CFG, None, corte)
    alteradas = []
    for s in series:
        kg = s.kg.copy()
        kg[corte:] += 100.0
        alteradas.append(Serie(s.id, s.fechas, kg))
    # las estadísticas de normalización también usan solo el tramo de entrenamiento
    despues = construir_conjunto(alteradas, CFG, None, corte)
    for a, b in zip(original, despues):
        assert torch.equal(a, b)


def test_cantidad_de_muestras_de_entrenamiento(series):
    corte = -(CFG.semanas_prueba + CFG.semanas_validacion)
    X, F, Y = construir_conjunto(series, CFG, None, corte)
    por_serie = 80 + corte - CFG.horizonte - CFG.ventana + 1
    assert X.shape == (2 * por_serie, 3, CFG.ventana)  # consumo + seno + coseno
    assert F.shape == (2 * por_serie, 2 * CFG.horizonte)
    assert Y.shape == (2 * por_serie, CFG.horizonte)


def test_pronostico_tiene_horizonte_y_no_es_negativo(series):
    modelos = entrenar_conjunto(series, CFG)
    p = pronosticar(modelos, series[0], len(series[0].kg), CFG)  # futuro, más allá de la última semana
    assert p.shape == (CFG.horizonte,)
    assert np.all(p >= 0)


def test_pronostico_solo_usa_la_historia_previa_al_origen(series):
    modelos = entrenar_conjunto(series, CFG)
    s = series[0]
    origen = len(s.kg) - 5
    kg = s.kg.copy()
    kg[origen:] += 50.0  # el futuro cambia; el pronóstico desde `origen` no debe cambiar
    otra = Serie(s.id, s.fechas, kg)
    assert np.allclose(pronosticar(modelos, s, origen, CFG), pronosticar(modelos, otra, origen, CFG))


def test_errores_de_prueba_usan_las_mismas_semanas_para_ambos_metodos(series):
    modelos = entrenar_conjunto(series, CFG)
    df = errores(series, modelos, CFG, "prueba")
    assert {"real", "tcn", "pm"} <= set(df.columns)
    por_tostador = df[df.paso == 1].groupby("tostador").size()
    assert (por_tostador == CFG.semanas_prueba).all()
    completos = df[df.origen_completo].groupby("tostador").origen.nunique()
    assert (completos == CFG.semanas_prueba - CFG.horizonte + 1).all()
    res = resumen_mape(df)
    assert "GLOBAL" in res.index
    assert res.loc["GLOBAL", ["mape_tcn_1s", "mape_pm_1s", "mape_tcn_4s", "mape_pm_4s"]].notna().all()


def test_historial_insuficiente_usa_promedio_movil(series):
    """Escenario 2 de HU-19: el tostador con pocas semanas queda documentado con promedio móvil."""
    corta = serie_sintetica("C", n=CFG.minimo_semanas - 1)
    modelos = entrenar_conjunto(series + [corta], CFG)  # la serie corta se ignora al entrenar
    metodos = elegir_metodo_por_tostador(series + [corta], modelos, CFG)
    assert metodos["C"] == PM_METODO
    assert set(metodos) == {"A", "B", "C"}


def test_minimo_de_semanas_respeta_el_charter():
    assert Config().minimo_semanas >= 26
    assert replace(Config(), semanas_prueba=6).semanas_prueba == 6
