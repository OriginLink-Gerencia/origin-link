"""HU-20 Pronóstico de consumo de las próximas 4 semanas (TCN, con promedio móvil de respaldo: ADR-0003)."""

import datetime as dt
from decimal import Decimal

import pytest

from app.models.abastecimiento import ConsumoHistorico, MovimientoInventario
from app.models.enums import TipoMovimiento
from app.services import pronostico as servicio

URL = "/api/v1/pronostico"
ULTIMA_SEMANA = dt.date(2026, 11, 16)  # lunes de la última semana completa antes de HOY (25/11)


def cargar(db, tostador_id, kgs, ultima=ULTIMA_SEMANA):
    """Guarda `kgs` como semanas consecutivas que terminan en `ultima`."""
    for i, kg in enumerate(kgs):
        semana = ultima - dt.timedelta(weeks=len(kgs) - 1 - i)
        db.add(ConsumoHistorico(tostador_id=tostador_id, semana=semana, kg_consumidos=Decimal(str(kg))))
    db.commit()


@pytest.fixture(autouse=True)
def sin_modelo(monkeypatch):
    """Por defecto no hay modelo TCN entrenado: se usa el respaldo."""
    monkeypatch.setattr(servicio, "cargar_modelo", lambda: None)


def test_escenario2_sin_modelo_usa_el_promedio_movil_de_4_semanas(como, db, usuarios):
    cargar(db, usuarios["a"].organizacion_id, [5, 5, 5, 5, 5, 5, 4, 6, 8, 10])  # últimas 4: promedio 7
    r = como("a").get(URL)
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["metodo"] == "PROMEDIO_MOVIL"
    assert "no está disponible" in cuerpo["motivo_metodo"]
    assert [p["semana"] for p in cuerpo["pronostico"]] == ["2026-11-23", "2026-11-30", "2026-12-07", "2026-12-14"]
    assert [p["kg"] for p in cuerpo["pronostico"]] == [7.0, 7.0, 7.0, 7.0]
    assert len(cuerpo["historial"]) == 10
    assert cuerpo["historial"][-1] == {"semana": "2026-11-16", "kg": 10.0}


def test_el_mape_de_referencia_se_calcula_con_las_ultimas_semanas(como, db, usuarios):
    cargar(db, usuarios["a"].organizacion_id, [10] * 10)  # el promedio acierta siempre
    assert como("a").get(URL).json()["mape_referencia"] == 0.0


def test_mape_de_referencia_con_error(como, db, usuarios):
    cargar(db, usuarios["a"].organizacion_id, [10, 10, 10, 10, 20])  # predice 10 para una semana real de 20: 50 %
    assert como("a").get(URL).json()["mape_referencia"] == 50.0


def test_con_menos_de_4_semanas_no_se_puede_pronosticar(como, db, usuarios):
    cargar(db, usuarios["a"].organizacion_id, [5, 6, 7])
    r = como("a").get(URL)
    assert r.status_code == 409
    assert "al menos 4 semanas" in r.json()["detail"]


def test_sin_historial_se_pide_importarlo(como):
    r = como("a").get(URL)
    assert r.status_code == 409 and "Importa" in r.json()["detail"]


def test_el_historial_suma_el_consumo_registrado_y_rellena_semanas_vacias_con_cero(como, db, usuarios, crear_lote):
    tostador = usuarios["a"].organizacion_id
    cargar(db, tostador, [6, 6, 6], ultima=dt.date(2026, 11, 2))  # semanas 19/10, 26/10 y 2/11
    lote = crear_lote(coop_id=usuarios["coop"].organizacion_id)
    # 9/11 sin datos; el consumo registrado el 18/11 (miércoles) cae en la semana del 16/11
    db.add(MovimientoInventario(tostador_id=tostador, lote_id=lote.id, tipo=TipoMovimiento.CONSUMO,
                                cantidad_kg=Decimal("4"), fecha=dt.date(2026, 11, 18)))  # fmt: skip
    db.commit()
    historial = como("a").get(URL).json()["historial"]
    assert [(p["semana"], p["kg"]) for p in historial][-3:] == [
        ("2026-11-02", 6.0),
        ("2026-11-09", 0.0),
        ("2026-11-16", 4.0),
    ]


def test_escenario1_usa_la_tcn_cuando_hay_modelo_e_historial_suficiente(como, db, usuarios, monkeypatch):
    cargar(db, usuarios["a"].organizacion_id, list(range(1, 41)))

    class Falso:
        minimo_semanas = 34

        def pronosticar(self, semanas, kg):
            return [11.5, 12.0, 12.5, 13.0]

    monkeypatch.setattr(servicio, "cargar_modelo", lambda: Falso())
    cuerpo = como("a").get(URL).json()
    assert cuerpo["metodo"] == "TCN" and cuerpo["motivo_metodo"] is None
    assert [p["kg"] for p in cuerpo["pronostico"]] == [11.5, 12.0, 12.5, 13.0]
    assert cuerpo["mape_referencia"] is not None


def test_con_historial_insuficiente_para_la_tcn_se_usa_el_respaldo_y_se_explica(como, db, usuarios, monkeypatch):
    cargar(db, usuarios["a"].organizacion_id, [8] * 10)

    class Falso:
        minimo_semanas = 34

        def pronosticar(self, semanas, kg):
            raise AssertionError("no debe llamarse con historial corto")

    monkeypatch.setattr(servicio, "cargar_modelo", lambda: Falso())
    cuerpo = como("a").get(URL).json()
    assert cuerpo["metodo"] == "PROMEDIO_MOVIL"
    assert cuerpo["motivo_metodo"] == "Historial insuficiente (10 semanas; el modelo necesita al menos 34)"


def test_si_la_tcn_falla_se_usa_el_respaldo_sin_error(como, db, usuarios, monkeypatch):
    cargar(db, usuarios["a"].organizacion_id, [8] * 40)

    class Roto:
        minimo_semanas = 34

        def pronosticar(self, semanas, kg):
            raise RuntimeError("modelo corrupto")

    monkeypatch.setattr(servicio, "cargar_modelo", lambda: Roto())
    r = como("a").get(URL)
    assert r.status_code == 200 and r.json()["metodo"] == "PROMEDIO_MOVIL"
    assert "falló" in r.json()["motivo_metodo"]


def test_cada_tostador_ve_solo_su_pronostico(como, db, usuarios):
    cargar(db, usuarios["a"].organizacion_id, [8] * 10)
    assert como("a").get(URL).status_code == 200
    assert como("b").get(URL).status_code == 409  # B no importó nada
    assert como("coop").get(URL).status_code == 403
