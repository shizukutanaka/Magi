from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.main as main
from app.main import ConfigError, app, mount_frontend

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


def test_static_files_revalidate_without_disabling_storage():
    client = TestClient(app)

    for path in ("/", "/app.js"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-cache"

    response = client.get("/app.js")
    conditional = client.get("/app.js", headers={"If-None-Match": response.headers["etag"]})
    assert conditional.status_code == 304
    assert conditional.headers["cache-control"] == "no-cache"


def test_static_files_prevent_referrer_leaks():
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert response.headers["referrer-policy"] == "no-referrer"


def test_api_routes_are_not_shadowed_by_frontend():
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    systems = client.get("/api/v1/systems")
    assert systems.status_code == 200
    assert systems.headers.get("cache-control") is None


def test_unknown_frontend_path_returns_404():
    response = TestClient(app).get("/does-not-exist")
    assert response.status_code == 404


def test_missing_explicit_static_directory_fails(monkeypatch):
    missing = str(FRONTEND_DIR / "not-present")
    monkeypatch.setenv("MAGI_STATIC_DIR", missing)
    application = FastAPI()

    @application.get("/health")
    def health():
        return {"status": "ok"}

    with pytest.raises(ConfigError, match=missing):
        mount_frontend(application)


def test_missing_default_static_directory_starts_api_only(monkeypatch, caplog):
    monkeypatch.delenv("MAGI_STATIC_DIR", raising=False)
    missing = FRONTEND_DIR / "not-present"
    monkeypatch.setattr(main, "DEFAULT_STATIC_DIR", missing)
    application = FastAPI()

    @application.get("/health")
    def health():
        return {"status": "ok"}

    with caplog.at_level("WARNING", logger="app.main"):
        mount_frontend(application)

    client = TestClient(application)
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/").status_code == 404
    assert "API-only" in caplog.text
