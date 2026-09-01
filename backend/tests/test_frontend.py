from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app, mount_frontend

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


def test_root_serves_index_html():
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "今日の三賢者" in response.text


def test_static_assets_are_served():
    client = TestClient(app)
    for path, content_type in (
        ("/app.js", "javascript"),
        ("/api.js", "javascript"),
        ("/store.js", "javascript"),
        ("/i18n.js", "javascript"),
        ("/styles.css", "text/css"),
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert content_type in response.headers["content-type"]


def test_api_routes_are_not_shadowed_by_frontend():
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/systems").status_code == 200


def test_unknown_frontend_path_returns_404():
    response = TestClient(app).get("/does-not-exist")
    assert response.status_code == 404


def test_missing_static_directory_skips_mount(monkeypatch):
    missing = str(FRONTEND_DIR / "not-present")
    monkeypatch.setenv("MAGI_STATIC_DIR", missing)
    application = FastAPI()

    @application.get("/health")
    def health():
        return {"status": "ok"}

    mount_frontend(application)
    client = TestClient(application)
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/").status_code == 404
