"""HU-21 Recomendación de cuánto y cuándo comprar · HU-22 Alertas de stock bajo y de compra próxima."""

import datetime as dt
from decimal import Decimal

import pytest

from app.models import Compra, Proveedor
from app.models.abastecimiento import ConsumoHistorico, MovimientoInventario
from app.models.enums import EstadoCompra, EstadoVinculo, TipoMovimiento
from app.services import pronostico as servicio
from tests.conftest import HOY

RECOMENDACION = "/api/v1/recomendaciones"
ALERTAS = "/api/v1/alertas"


@pytest.fixture(autouse=True)
def sin_modelo(monkeypatch):
    monkeypatch.setattr(servicio, "cargar_modelo", lambda: None)


@pytest.fixture
def escenario(db, usuarios, crear_lote):
    """Tostador A consume 7 kg por semana (1 kg por día) y puede tener existencias y una compra previa."""
    tostador = usuarios["a"].organizacion_id
    for i in range(10):
        db.add(ConsumoHistorico(tostador_id=tostador, semana=dt.date(2026, 11, 16) - dt.timedelta(weeks=i),
                                kg_consumidos=Decimal(7)))  # fmt: skip
    prov = Proveedor(tostador_id=tostador, nombre="Finca Don Pepe", estado_vinculo=EstadoVinculo.SIN_VINCULAR)
    db.add(prov)
    db.commit()

    class Esc:
        def existencias(self, kg, lote=None):
            lote = lote or crear_lote(proveedor_id=prov.id, codigo="STOCK")
            db.add(MovimientoInventario(tostador_id=tostador, lote_id=lote.id, tipo=TipoMovimiento.AJUSTE,
                                        cantidad_kg=Decimal(str(kg)), motivo="Conteo inicial", fecha=HOY))  # fmt: skip
            db.commit()

        def compra(self, plazo, minimo, fecha=dt.date(2026, 11, 1), estado=EstadoCompra.RECIBIDA):
            lote = crear_lote(proveedor_id=prov.id, codigo=f"C-{plazo}-{fecha}", plazo_entrega_dias=plazo,
                              cantidad_minima_kg=Decimal(str(minimo)))  # fmt: skip
            db.add(
                Compra(
                    tostador_id=tostador, proveedor_id=prov.id, lote_id=lote.id, cantidad_kg=Decimal(50),
                    precio_kg=Decimal(10), fecha_compra=fecha, fecha_entrega_acordada=fecha, estado=estado,
                )
            )  # fmt: skip
            db.commit()

    return Esc()


def test_escenario1_calcula_cuando_y_cuanto_comprar(como, escenario):
    escenario.existencias(15)
    escenario.compra(plazo=10, minimo=30)
    r = como("a").get(RECOMENDACION)
    assert r.status_code == 200
    c = r.json()
    # Alcanza 15 días y el proveedor tarda 10: hay que comprar en 5 días (30/11)
    assert c["fecha_limite_compra"] == "2026-11-30"
    # Consumo de 24 días (10 de entrega + 2 semanas de cobertura) = 24 kg, menos 15 en bodega = 9, y el mínimo es 30
    assert c["cantidad_sugerida_kg"] == 30
    assert c["semanas_cobertura_actual"] == 2.14
    f = c["factores"]
    assert (f["existencias_kg"], f["plazo_entrega_dias"], f["semanas_cobertura"], f["cantidad_minima_kg"]) == (
        15,
        10,
        2,
        30,
    )
    assert f["metodo_pronostico"] == "PROMEDIO_MOVIL" and len(f["consumo_semanal_pronosticado_kg"]) == 4
    assert "15" in c["explicacion"] and "10 días" in c["explicacion"]


def test_la_cantidad_se_redondea_hacia_arriba_y_respeta_el_minimo(como, escenario):
    escenario.existencias(4.5)  # faltan 24 − 4.5 = 19.5 → 20 kg
    escenario.compra(plazo=10, minimo=5)
    assert como("a").get(RECOMENDACION).json()["cantidad_sugerida_kg"] == 20


def test_sin_compras_previas_usa_7_dias_y_sin_minimo(como, escenario):
    escenario.existencias(15)  # 7 + 14 = 21 kg de consumo − 15 = 6; alcanza 15 días − 7 de entrega = 8 días
    c = como("a").get(RECOMENDACION).json()
    assert c["cantidad_sugerida_kg"] == 6
    assert c["fecha_limite_compra"] == "2026-12-03"
    assert c["factores"]["plazo_entrega_dias"] == 7 and c["factores"]["cantidad_minima_kg"] == 0


def test_usa_los_datos_de_la_ultima_compra_no_anulada(como, escenario):
    escenario.existencias(15)
    escenario.compra(plazo=20, minimo=100, fecha=dt.date(2026, 10, 1))
    escenario.compra(plazo=10, minimo=30, fecha=dt.date(2026, 11, 1))
    escenario.compra(plazo=3, minimo=1, fecha=dt.date(2026, 11, 10), estado=EstadoCompra.ANULADA)
    f = como("a").get(RECOMENDACION).json()["factores"]
    assert (f["plazo_entrega_dias"], f["cantidad_minima_kg"]) == (10, 30)


def test_si_las_existencias_alcanzan_no_se_sugiere_comprar(como, escenario):
    escenario.existencias(200)
    c = como("a").get(RECOMENDACION).json()
    assert c["cantidad_sugerida_kg"] == 0
    assert "no necesitas comprar" in c["explicacion"].lower()


def test_sin_existencias_la_fecha_limite_es_hoy(como, escenario):
    c = como("a").get(RECOMENDACION).json()
    assert c["fecha_limite_compra"] == HOY.isoformat() and c["semanas_cobertura_actual"] == 0


def test_cuenta_las_existencias_de_todos_los_lotes(como, escenario, crear_lote, usuarios, db):
    escenario.existencias(10)
    escenario.existencias(5, lote=crear_lote(coop_id=usuarios["coop"].organizacion_id, codigo="OTRO"))
    assert como("a").get(RECOMENDACION).json()["factores"]["existencias_kg"] == 15


def test_usa_las_semanas_de_cobertura_configuradas_de_la_organizacion(como, escenario, db, usuarios):
    usuarios["a"].organizacion.semanas_cobertura = 4
    db.commit()
    escenario.existencias(15)
    escenario.compra(plazo=10, minimo=0)
    c = como("a").get(RECOMENDACION).json()
    assert c["cantidad_sugerida_kg"] == 23  # (10 + 28) − 15


def test_sin_historial_suficiente_no_hay_recomendacion(como):
    r = como("b").get(RECOMENDACION)
    assert r.status_code == 409


def test_la_cooperativa_no_ve_recomendaciones(como):
    assert como("coop").get(RECOMENDACION).status_code == 403


# ---- HU-22 ----


def test_alerta_de_stock_bajo_cuando_no_alcanza_para_el_plazo_de_entrega(como, escenario):
    escenario.existencias(8)
    escenario.compra(plazo=10, minimo=0)
    alertas = como("a").get(ALERTAS).json()
    assert [a["tipo"] for a in alertas] == ["STOCK_BAJO"]
    assert alertas[0]["semanas_cobertura_restantes"] == 1.14
    assert alertas[0]["fecha_limite_compra"] == HOY.isoformat()
    assert "1.1 semanas" in alertas[0]["mensaje"] and "10 días" in alertas[0]["mensaje"]


def test_alerta_de_compra_proxima_si_el_limite_es_en_una_semana_o_menos(como, escenario):
    escenario.existencias(15)
    escenario.compra(plazo=10, minimo=0)  # fecha límite: 30/11, a 5 días
    alertas = como("a").get(ALERTAS).json()
    assert [a["tipo"] for a in alertas] == ["COMPRA_PROXIMA"]
    assert alertas[0]["fecha_limite_compra"] == "2026-11-30"


def test_sin_alertas_si_hay_stock_de_sobra(como, escenario):
    escenario.existencias(100)
    assert como("a").get(ALERTAS).json() == []


def test_sin_historial_las_alertas_van_vacias_en_lugar_de_fallar(como):
    r = como("b").get(ALERTAS)
    assert r.status_code == 200 and r.json() == []


def test_la_cooperativa_no_ve_alertas(como):
    assert como("coop").get(ALERTAS).status_code == 403
