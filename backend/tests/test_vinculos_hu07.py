"""HU-07 Ver mis vínculos: lista del tostador (estado de cada proveedor) y de la cooperativa."""

from datetime import UTC, datetime

from app.models import Invitacion, Organizacion, Proveedor
from app.models.enums import EstadoVinculo, TipoOrganizacion

PROVEEDORES = "/api/v1/proveedores"
VINCULOS = "/api/v1/vinculos"


def _vincular(db, tostador_id: int, coop_id: int, desde: datetime | None = None) -> Proveedor:
    prov = Proveedor(
        tostador_id=tostador_id,
        organizacion_proveedora_id=coop_id,
        nombre="Coop. X",
        estado_vinculo=EstadoVinculo.VINCULADO,
    )
    db.add(prov)
    db.flush()
    if desde:
        db.add(Invitacion(proveedor_id=prov.id, token=f"t{prov.id}", creado_en=desde, expira_en=desde, usada_en=desde))
    db.commit()
    return prov


def test_escenario1_tostador_ve_el_estado_de_cada_proveedor(como):
    c = como("a")
    sin = c.post(PROVEEDORES, json={"nombre": "Sin invitar"}).json()["id"]
    inv = c.post(PROVEEDORES, json={"nombre": "Invitado"}).json()["id"]
    c.post(f"{PROVEEDORES}/{inv}/invitaciones")
    estados = {p["id"]: p["estado_vinculo"] for p in c.get(PROVEEDORES).json()}
    assert estados == {sin: "SIN_VINCULAR", inv: "INVITADO"}


def test_escenario2_cooperativa_ve_los_dos_tostadores_vinculados(como, db, usuarios):
    coop = usuarios["coop"].organizacion_id
    desde = datetime(2026, 11, 19, 15, 0, tzinfo=UTC)
    _vincular(db, usuarios["a"].organizacion_id, coop, desde)
    _vincular(db, usuarios["b"].organizacion_id, coop)
    r = como("coop").get(VINCULOS)
    assert r.status_code == 200
    vinculos = {v["tostador"]: v for v in r.json()}
    assert set(vinculos) == {"Tostaduría A", "Tostaduría B"}
    assert vinculos["Tostaduría A"]["tostador_id"] == usuarios["a"].organizacion_id
    assert vinculos["Tostaduría A"]["vinculado_desde"].startswith("2026-11-19T15:00")


def test_solo_cuentan_los_proveedores_ya_vinculados(como, db, usuarios):
    coop = usuarios["coop"].organizacion_id
    db.add(
        Proveedor(
            tostador_id=usuarios["a"].organizacion_id,
            organizacion_proveedora_id=coop,
            nombre="Pendiente",
            estado_vinculo=EstadoVinculo.INVITADO,
        )
    )
    db.commit()
    assert como("coop").get(VINCULOS).json() == []


def test_cooperativa_no_ve_vinculos_de_otra_cooperativa(como, db, usuarios):
    otra = Organizacion(tipo=TipoOrganizacion.PROVEEDOR, nombre="Coop. Y")
    db.add(otra)
    db.flush()
    _vincular(db, usuarios["a"].organizacion_id, otra.id)
    assert como("coop").get(VINCULOS).json() == []


def test_el_tostador_no_usa_la_ruta_de_la_cooperativa(como):
    assert como("a").get(VINCULOS).status_code == 403
