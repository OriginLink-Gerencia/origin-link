"""HU-06 Invitar a un proveedor a vincularse: enlace único de un solo uso con vigencia de 7 días."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.models import Invitacion, Proveedor
from app.models.enums import EstadoVinculo

BASE = "/api/v1/proveedores"


def _crear(c, nombre="Coop. Jaén") -> int:
    return c.post(BASE, json={"nombre": nombre}).json()["id"]


def _aware(fecha: datetime) -> datetime:
    return fecha if fecha.tzinfo else fecha.replace(tzinfo=UTC)


def test_escenario1_genera_enlace_unico_con_vigencia_de_7_dias(como, db):
    c = como("a")
    pid = _crear(c)
    r = c.post(f"{BASE}/{pid}/invitaciones")
    assert r.status_code == 201
    cuerpo = r.json()
    assert len(cuerpo["token"]) >= 40  # secrets.token_urlsafe(32)
    assert cuerpo["url"].endswith(f"/invitacion/{cuerpo['token']}")
    expira = _aware(datetime.fromisoformat(cuerpo["expira_en"]))
    assert timedelta(days=6, hours=23) < expira - datetime.now(UTC) <= timedelta(days=7)
    assert c.get(f"{BASE}/{pid}").json()["estado_vinculo"] == "INVITADO"


def test_cada_invitacion_tiene_un_token_distinto(como):
    c = como("a")
    a, b = _crear(c, "Coop. A"), _crear(c, "Coop. B")
    assert c.post(f"{BASE}/{a}/invitaciones").json()["token"] != c.post(f"{BASE}/{b}/invitaciones").json()["token"]


def test_reinvitar_invalida_el_enlace_anterior(como, db):
    c = como("a")
    pid = _crear(c)
    primero = c.post(f"{BASE}/{pid}/invitaciones").json()["token"]
    segundo = c.post(f"{BASE}/{pid}/invitaciones").json()["token"]
    assert primero != segundo
    viejo = db.scalar(select(Invitacion).where(Invitacion.token == primero))
    nuevo = db.scalar(select(Invitacion).where(Invitacion.token == segundo))
    assert _aware(viejo.expira_en) <= datetime.now(UTC)  # el anterior deja de ser vigente
    assert _aware(nuevo.expira_en) > datetime.now(UTC)


def test_escenario2_proveedor_ya_vinculado_responde_409(como, db):
    c = como("a")
    pid = _crear(c)
    db.get(Proveedor, pid).estado_vinculo = EstadoVinculo.VINCULADO
    db.commit()
    r = c.post(f"{BASE}/{pid}/invitaciones")
    assert r.status_code == 409
    assert db.scalars(select(Invitacion)).all() == []


def test_proveedor_ajeno_es_404_y_no_crea_invitacion(como, db):
    pid = _crear(como("a"))
    assert como("b").post(f"{BASE}/{pid}/invitaciones").status_code == 404
    assert db.scalars(select(Invitacion)).all() == []


def test_cooperativa_no_puede_invitar(como):
    pid = _crear(como("a"))
    assert como("coop").post(f"{BASE}/{pid}/invitaciones").status_code == 403
