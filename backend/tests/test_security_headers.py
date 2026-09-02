from fastapi.testclient import TestClient

from app.main import CONTENT_SECURITY_POLICY, app

client = TestClient(app)


def assert_security_headers(response):
    assert response.headers["content-security-policy"] == CONTENT_SECURITY_POLICY
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_static_response_has_security_headers():
    response = client.get("/")
    assert response.status_code == 200
    assert_security_headers(response)
    assert response.headers["cache-control"] == "no-cache"


def test_json_api_response_has_security_headers():
    response = client.get("/api/v1/systems?lang=ja")
    assert response.status_code == 200
    assert_security_headers(response)


def test_error_response_has_security_headers():
    response = client.post("/api/v1/readings", json={})
    assert response.status_code == 422
    assert_security_headers(response)


def test_interactive_docs_are_disabled_but_openapi_remains_available():
    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 200


def test_content_security_policy_does_not_allow_inline_code():
    assert "'unsafe-inline'" not in CONTENT_SECURITY_POLICY
    assert "'unsafe-eval'" not in CONTENT_SECURITY_POLICY
