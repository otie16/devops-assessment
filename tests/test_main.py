from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
non_raising_client = TestClient(app, raise_server_exceptions=False)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "app" in data
    assert "version" in data
    assert "environment" in data


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_ready():
    response = client.get("/ready")
    assert response.status_code in [200, 503]
    body = response.json()
    assert "status" in body


def test_info():
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert "app_name" in data
    assert "version" in data
    assert "environment" in data
    assert "uptime_seconds" in data


def test_sample_endpoint():
    response = client.get("/api/v1/sample")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "Sample endpoint is working"


def test_error_endpoint():
    response = client.get("/api/v1/error")
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Intentional test error"


def test_crash_endpoint():
    response = non_raising_client.get("/api/v1/crash")
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert (
        "http_requests_total" in response.text
        or "python_gc_objects_collected_total" in response.text
    )
