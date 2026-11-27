"""HU-09 Consultar los lotes de mis proveedores: visibilidad por vínculo, filtros y detalle."""

from decimal import Decimal

import pytest

from app.models import Lote, Organizacion, Proveedor
from app.models.enums import ProcesoCafe, TipoOrganizacion

LOTES = "/api/v1/lotes"


def _lote(db, *, coop_id=None, proveedor_id=None, **extra) -> Lote:
    datos = dict(
        codigo="L-1", region="Cajamarca", variedad="Caturra", proceso=ProcesoCafe.LAVADO, cosecha="2026",
        altitud_msnm=1600, cantidad_disponible_kg=Decimal("100"), precio_kg=Decimal("28.5"),
    )  # fmt: skip
    lote = Lote(organizacion_proveedora_id=coop_id, proveedor_id=proveedor_id, **{**datos, **extra})
    db.add(lote)
    db.commit()
    return lote


@pytest.fixture
def escenario(db, usuarios, vincular):
    """Tostador A vinculado con Coop. X (lote publicado, otro sin publicar, uno agotado natural)
    y con una segunda cooperativa; Coop. Z no está vinculada con A."""
    a, coop = usuarios["a"].organizacion_id, usuarios["coop"].organizacion_id
    vincular(a, coop)
    y = Organizacion(tipo=TipoOrganizacion.PROVEEDOR, nombre="Coop. Y")
    z = Organizacion(tipo=TipoOrganizacion.PROVEEDOR, nombre="Coop. Z")
    db.add_all([y, z])
    db.commit()
    prov_y = vincular(a, y.id, "Coop. Y")
    return {
        "x_lavado": _lote(db, coop_id=coop, codigo="X-1"),
        "x_natural": _lote(db, coop_id=coop, codigo="X-2", proceso=ProcesoCafe.NATURAL),
        "x_oculto": _lote(db, coop_id=coop, codigo="X-3", publicado=False),
        "x_agotado": _lote(db, coop_id=coop, codigo="X-4", cantidad_disponible_kg=Decimal("0")),
        "y": _lote(db, coop_id=y.id, codigo="Y-1"),
        "z": _lote(db, coop_id=z.id, codigo="Z-1"),
        "prov_y": prov_y,
    }


def _codigos(r) -> set[str]:
    assert r.status_code == 200
    return {lote["codigo"] for lote in r.json()}


def test_escenario1_tostador_ve_lotes_de_sus_proveedores_vinculados_con_sus_datos(como, escenario):
    r = como("a").get(LOTES)
    assert _codigos(r) == {"X-1", "X-2", "X-4", "Y-1"}  # sin el no publicado ni los de Coop. Z
    lote = next(item for item in r.json() if item["codigo"] == "X-1")
    for campo in ("proveedor_nombre", "region", "altitud_msnm", "proceso", "cantidad_disponible_kg", "precio_kg"):
        assert lote[campo] is not None
    assert lote["proveedor_nombre"] == "Coop. X" and lote["agotado"] is False


def test_otro_tostador_no_ve_lotes_de_una_cooperativa_con_la_que_no_esta_vinculado(como, escenario):
    assert como("b").get(LOTES).json() == []


def test_el_tostador_ve_los_lotes_de_su_propio_directorio(como, db, usuarios, escenario):
    prov = Proveedor(tostador_id=usuarios["a"].organizacion_id, nombre="Finca sin cuenta")
    db.add(prov)
    db.commit()
    _lote(db, proveedor_id=prov.id, codigo="D-1")
    lotes = como("a").get(LOTES).json()
    propio = next(item for item in lotes if item["codigo"] == "D-1")
    assert propio["registrado_por_tostador"] is True and propio["proveedor_nombre"] == "Finca sin cuenta"
    assert "D-1" not in _codigos(como("b").get(LOTES))


def test_escenario2_filtro_por_proveedor(como, escenario):
    # proveedor_id es el de la ficha del directorio del tostador
    r = como("a").get(LOTES, params={"proveedor_id": escenario["prov_y"].id})
    assert _codigos(r) == {"Y-1"}


def test_filtro_por_proveedor_ajeno_es_404(como, escenario):
    assert como("b").get(LOTES, params={"proveedor_id": escenario["prov_y"].id}).status_code == 404


def test_filtro_por_proceso(como, escenario):
    assert _codigos(como("a").get(LOTES, params={"proceso": "NATURAL"})) == {"X-2"}


def test_filtro_solo_disponibles_excluye_agotados(como, escenario):
    assert "X-4" not in _codigos(como("a").get(LOTES, params={"disponibles": "true"}))


def test_proceso_invalido_es_422(como, escenario):
    assert como("a").get(LOTES, params={"proceso": "MAGICO"}).status_code == 422


def test_la_cooperativa_ve_solo_sus_lotes_incluidos_los_no_publicados(como, escenario):
    assert _codigos(como("coop").get(LOTES)) == {"X-1", "X-2", "X-3", "X-4"}


def test_detalle_visible_y_no_visible(como, escenario):
    assert como("a").get(f"{LOTES}/{escenario['x_lavado'].id}").json()["codigo"] == "X-1"
    assert como("a").get(f"{LOTES}/{escenario['z'].id}").status_code == 404  # cooperativa sin vínculo
    assert como("a").get(f"{LOTES}/{escenario['x_oculto'].id}").status_code == 404
    assert como("b").get(f"{LOTES}/{escenario['x_lavado'].id}").status_code == 404
    assert como("coop").get(f"{LOTES}/{escenario['x_oculto'].id}").status_code == 200
    assert como("a").get(f"{LOTES}/9999").status_code == 404


def test_filtro_por_ficha_del_directorio_no_mezcla_otras_fichas(como, db, usuarios, escenario):
    a = usuarios["a"].organizacion_id
    f1, f2 = Proveedor(tostador_id=a, nombre="Finca 1"), Proveedor(tostador_id=a, nombre="Finca 2")
    db.add_all([f1, f2])
    db.commit()
    _lote(db, proveedor_id=f1.id, codigo="F1-1")
    _lote(db, proveedor_id=f2.id, codigo="F2-1")
    assert _codigos(como("a").get(LOTES, params={"proveedor_id": f1.id})) == {"F1-1"}
