from fastapi.testclient import TestClient

from app.api.deps import get_usuario_actual
from app.main import app


def test_flujo_integrado_proveedor_invitacion_registro_vinculo(como):
    tostador = como("a")

    proveedor = tostador.post(
        "/api/v1/proveedores",
        json={"nombre": "Cooperativa de Integracion"},
    )
    assert proveedor.status_code == 201, proveedor.text
    pid = proveedor.json()["id"]

    invitacion = tostador.post(f"/api/v1/proveedores/{pid}/invitaciones")
    assert invitacion.status_code == 201, invitacion.text
    token = invitacion.json()["token"]

    app.dependency_overrides.pop(get_usuario_actual, None)
    cliente = TestClient(app)

    info = cliente.get(f"/api/v1/invitaciones/{token}")
    assert info.status_code == 200, info.text
    assert info.json()["vigente"] is True

    registro = cliente.post(
        "/api/v1/auth/registro-invitacion",
        json={
            "token": token,
            "empresa": "Cooperativa de Integracion",
            "region": "Cajamarca",
            "nombre": "Ana Prueba",
            "email": "ana.integracion@example.com",
            "password": "ClaveSegura123",
        },
    )
    assert registro.status_code == 201, registro.text

    jwt = registro.json()["access_token"]
    vinculos = cliente.get(
        "/api/v1/vinculos",
        headers={"Authorization": f"Bearer {jwt}"},
    )
    assert vinculos.status_code == 200, vinculos.text
    assert len(vinculos.json()) == 1
    assert vinculos.json()[0]["tostador"] == "Tostaduría A"

    assert cliente.get(f"/api/v1/invitaciones/{token}").json()["vigente"] is False
