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