from fastapi.testclient import TestClient

from backend.main import app


def test_health():
    with TestClient(app) as client:
        respuesta = client.get("/api/health")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}


def test_frontend():
    with TestClient(app) as client:
        respuesta = client.get("/")

    assert respuesta.status_code == 200
    assert "text/html" in respuesta.headers["content-type"]
    assert '<script src="/app.js"></script>' in respuesta.text


def test_frontend_javascript():
    with TestClient(app) as client:
        respuesta = client.get("/app.js")

    assert respuesta.status_code == 200
    assert "/api/health" in respuesta.text
