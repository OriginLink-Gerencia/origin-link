"""Datos que necesita el frontend: proveedor de cada lote, enlace de invitación vigente, pedidos de la cooperativa
y recomendación con las condiciones de un lote elegido."""

import datetime as dt
from decimal import Decimal

from app.models import Compra, Proveedor
from app.models.abastecimiento import ConsumoHistorico, MovimientoInventario
from app.models.enums import EstadoVinculo, TipoMovimiento
from app.services import pronostico as servicio
from tests.conftest import HOY

API = "/api/v1"


# ---- Lotes: a qué proveedor del directorio pertenecen ----


def test_cada_lote_indica_la_ficha_del_directorio_a_la_que_pertenece(como, usuarios, vincular, crear_lote):
    tostador, coop = usuarios["a"].organizacion_id, usuarios["coop"].organizacion_id
    ficha_coop = vincular(tostador, coop)
    de_coop = crear_lote(coop_id=coop, codigo="DE-COOP")
    ficha_pepe = como("a").post(f"{API}/proveedores", json={"nombre": "Finca Don Pepe"}).json()["id"]
    manual = como("a").post(
        f"{API}/lotes",
        json={"proveedor_id": ficha_pepe, "codigo": "MANUAL", "region": "Junín", "variedad": "Catimor",
              "proceso": "NATURAL", "cosecha": "2026", "cantidad_disponible_kg": 50, "precio_kg": 20},
    ).json()  # fmt: skip
    assert manual.get("codigo") == "MANUAL", manual
    lotes = {x["codigo"]: x for x in como("a").get(f"{API}/lotes").json()}
    assert lotes["DE-COOP"]["proveedor_id"] == ficha_coop.id
    assert lotes["MANUAL"]["proveedor_id"] == ficha_pepe == manual["proveedor_id"]
    assert como("a").get(f"{API}/lotes/{de_coop.id}").json()["proveedor_id"] == ficha_coop.id


def test_la_cooperativa_no_recibe_proveedor_id(como, usuarios, vincular, crear_lote):
    vincular(usuarios["a"].organizacion_id, usuarios["coop"].organizacion_id)
    crear_lote(coop_id=usuarios["coop"].organizacion_id)
    assert como("coop").get(f"{API}/lotes").json()[0]["proveedor_id"] is None


# ---- Proveedores: enlace de invitación vigente ----


def test_el_proveedor_invitado_trae_su_enlace_vigente(como):
    c = como("a")
    pid = c.post(f"{API}/proveedores", json={"nombre": "Coop. Nueva"}).json()["id"]
    assert c.get(f"{API}/proveedores/{pid}").json()["invitacion_vigente"] is None
    invitacion = c.post(f"{API}/proveedores/{pid}/invitaciones").json()
    vigente = c.get(f"{API}/proveedores").json()[0]["invitacion_vigente"]
    assert vigente["token"] == invitacion["token"] and vigente["expira_en"][:19] == invitacion["expira_en"][:19]


def test_una_invitacion_vencida_ya_no_se_muestra(como, db):
    c = como("a")
    pid = c.post(f"{API}/proveedores", json={"nombre": "Coop. Nueva"}).json()["id"]
    c.post(f"{API}/proveedores/{pid}/invitaciones")
    db.get(Proveedor, pid).invitaciones[0].expira_en = dt.datetime(2020, 1, 1, tzinfo=dt.UTC)
    db.commit()
    prov = c.get(f"{API}/proveedores/{pid}").json()
    assert prov["estado_vinculo"] == "INVITADO" and prov["invitacion_vigente"] is None


# ---- Pedidos recibidos por la cooperativa ----


def _comprar(db, tostador_id, ficha, lote, kg, recibido=None):
    compra = Compra(tostador_id=tostador_id, proveedor_id=ficha.id, lote_id=lote.id, cantidad_kg=Decimal(kg),
                    precio_kg=Decimal(10), fecha_compra=dt.date(2026, 11, 1),
                    fecha_entrega_acordada=dt.date(2026, 11, 8))  # fmt: skip
    db.add(compra)
    db.commit()
    return compra


def test_la_cooperativa_ve_los_pedidos_de_sus_tostadoras(como, db, usuarios, vincular, crear_lote):
    coop = usuarios["coop"].organizacion_id
    ficha_a = vincular(usuarios["a"].organizacion_id, coop)
    lote = crear_lote(coop_id=coop, codigo="L-COOP")
    _comprar(db, usuarios["a"].organizacion_id, ficha_a, lote, 40)
    recibida = como("a").post(
        f"{API}/compras",
        json={"lote_id": lote.id, "cantidad_kg": 25, "precio_kg": 10, "fecha_compra": "2026-11-10",
              "fecha_entrega_acordada": "2026-11-15"},
    ).json()  # fmt: skip
    como("a").post(
        f"{API}/compras/{recibida['id']}/recepcion", json={"fecha_recepcion": "2026-11-15", "cantidad_recibida_kg": 24}
    )
    pedidos = como("coop").get(f"{API}/pedidos-recibidos").json()
    assert [(p["tostador"], p["lote_codigo"], p["cantidad_kg"], p["recibido_kg"], p["estado"]) for p in pedidos] == [
        ("Tostaduría A", "L-COOP", 25, 24, "RECIBIDA"),
        ("Tostaduría A", "L-COOP", 40, 0, "PENDIENTE"),
    ]
    assert {"id", "fecha_compra", "fecha_entrega_acordada", "lote_id"} <= set(pedidos[0])


def test_cada_cooperativa_ve_solo_los_pedidos_de_sus_lotes(como, db, usuarios, vincular, crear_lote):
    coop = usuarios["coop"].organizacion_id
    ficha = vincular(usuarios["a"].organizacion_id, coop)
    ajeno = crear_lote(proveedor_id=ficha.id, codigo="MANUAL")  # lote manual del tostador: no es de la cooperativa
    _comprar(db, usuarios["a"].organizacion_id, ficha, ajeno, 10)
    assert como("coop").get(f"{API}/pedidos-recibidos").json() == []


def test_el_tostador_no_ve_pedidos_recibidos(como):
    assert como("a").get(f"{API}/pedidos-recibidos").status_code == 403


# ---- Recomendación con las condiciones de un lote elegido ----


def _escenario_recomendacion(db, usuarios, crear_lote):
    tostador = usuarios["a"].organizacion_id
    for i in range(10):
        db.add(ConsumoHistorico(tostador_id=tostador, semana=dt.date(2026, 11, 16) - dt.timedelta(weeks=i),
                                kg_consumidos=Decimal(7)))  # fmt: skip
    prov = Proveedor(tostador_id=tostador, nombre="Finca", estado_vinculo=EstadoVinculo.SIN_VINCULAR)
    db.add(prov)
    db.commit()
    lote = crear_lote(proveedor_id=prov.id, codigo="S")
    db.add(MovimientoInventario(tostador_id=tostador, lote_id=lote.id, tipo=TipoMovimiento.AJUSTE,
                                cantidad_kg=Decimal(15), motivo="Conteo", fecha=HOY))  # fmt: skip
    db.commit()


def test_la_recomendacion_informa_los_dias_de_cobertura(como, db, usuarios, crear_lote, monkeypatch):
    monkeypatch.setattr(servicio, "cargar_modelo", lambda: None)
    _escenario_recomendacion(db, usuarios, crear_lote)
    c = como("a").get(f"{API}/recomendaciones").json()
    assert c["dias_cobertura_actual"] == 15
    assert c["factores"]["plazo_entrega_dias"] == 7  # sin compras previas


def test_se_pueden_simular_las_condiciones_de_otro_lote(como, db, usuarios, crear_lote, monkeypatch):
    monkeypatch.setattr(servicio, "cargar_modelo", lambda: None)
    _escenario_recomendacion(db, usuarios, crear_lote)
    c = como("a").get(f"{API}/recomendaciones", params={"plazo_entrega_dias": 20, "cantidad_minima_kg": 50}).json()
    assert c["factores"]["plazo_entrega_dias"] == 20 and c["factores"]["cantidad_minima_kg"] == 50
    assert c["fecha_limite_compra"] == HOY.isoformat()  # alcanza 15 días y la entrega tarda 20
    assert c["cantidad_sugerida_kg"] == 50  # (20 + 14) − 15 = 19, pero el mínimo es 50


def test_las_condiciones_simuladas_se_validan(como):
    assert como("a").get(f"{API}/recomendaciones", params={"plazo_entrega_dias": -1}).status_code == 422
