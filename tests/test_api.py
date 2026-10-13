import pytest

from fastapi.testclient import TestClient
from backend.main import create_app

app = create_app(auto_clock=False)

def test_crear_y_consultar_simulacion():
    with TestClient(app) as client:
        res = client.post("/api/simulations", json={"numero_trabajos": 4, "seed": 123})
        assert res.status_code == 201
        data = res.json()
        sim_id = data["simulacion_id"]

        res_get = client.get(f"/api/simulations/{sim_id}")
        assert res_get.status_code == 200
        assert res_get.json()["simulacion_id"] == sim_id

@pytest.mark.parametrize("cantidad", [0, -1, 2.5, 2.0, True, "3"])
def test_rechaza_cantidades_invalidas(cantidad):
    with TestClient(create_app(auto_clock=False)) as client:
        respuesta = client.post(
            "/api/simulations",
            json={"numero_trabajos": cantidad},
        )
        assert respuesta.status_code == 422


def test_id_inexistente():
    with TestClient(create_app(auto_clock=False)) as client:
        assert client.get("/api/simulations/no-existe").status_code == 404

        respuesta = client.post(
            "/api/simulations/no-existe/actions",
            json={"accion": "pause"},
        )
        assert respuesta.status_code == 404


def test_consultar_no_avanza_el_reloj():
    with TestClient(create_app(auto_clock=False)) as client:
        inicial = client.post(
            "/api/simulations",
            json={"numero_trabajos": 3, "seed": 123},
        ).json()

        ruta = f"/api/simulations/{inicial['simulacion_id']}"

        for _ in range(5):
            assert client.get(ruta).json() == inicial


def test_acciones_y_estados():
    with TestClient(create_app(auto_clock=False)) as client:
        inicial = client.post(
            "/api/simulations",
            json={"numero_trabajos": 3, "seed": 123},
        ).json()

        ruta = f"/api/simulations/{inicial['simulacion_id']}/actions"

        respuesta = client.post(ruta, json={"accion": "pause"})
        assert respuesta.status_code == 200
        assert respuesta.json()["estado"] == "paused"

        for accion in ("interrupt", "error"):
            respuesta = client.post(ruta, json={"accion": accion})
            assert respuesta.status_code == 409

        respuesta = client.post(ruta, json={"accion": "continue"})
        assert respuesta.status_code == 200
        assert respuesta.json()["estado"] == "running"

        respuesta = client.post(ruta, json={"accion": "interrupt"})
        assert respuesta.status_code == 200
        estado = respuesta.json()
        assert estado["en_ejecucion"]["id"] == 2
        assert [p["id"] for p in estado["en_espera"]] == [3, 1]
        assert estado["reloj"] == 0

        respuesta = client.post(ruta, json={"accion": "error"})
        assert respuesta.status_code == 200
        estado = respuesta.json()
        terminado = estado["terminados"][-1]
        assert terminado["id"] == 2
        assert terminado["estado"] == "error"
        assert terminado["resultado"] is None
        assert terminado["restante"] == 0
        assert estado["reloj"] == 0

        # Terminar los dos procesos restantes mediante E.
        for _ in range(2):
            assert client.post(
                ruta, json={"accion": "error"}
            ).status_code == 200

        for accion in ("interrupt", "error", "pause", "continue"):
            respuesta = client.post(ruta, json={"accion": accion})
            assert respuesta.status_code == 409


def test_rechaza_accion_desconocida():
    with TestClient(create_app(auto_clock=False)) as client:
        inicial = client.post(
            "/api/simulations",
            json={"numero_trabajos": 1},
        ).json()

        respuesta = client.post(
            f"/api/simulations/{inicial['simulacion_id']}/actions",
            json={"accion": "reiniciar"},
        )
        assert respuesta.status_code == 422