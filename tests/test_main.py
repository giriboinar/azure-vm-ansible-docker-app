from fastapi.testclient import TestClient

from app.main import app, services

client = TestClient(app)


def setup_function():
    services.clear()


def test_root():
    assert client.get("/").json()["service"] == "Service Health API"


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_create_and_get_service():
    created = client.post("/api/services", json={"name": "api", "url": "https://example.com/health"}).json()
    assert created["status"] == "unknown"
    fetched = client.get(f"/api/services/{created['id']}").json()
    assert fetched["name"] == "api"


def test_list_services():
    client.post("/api/services", json={"name": "a", "url": "https://a.example"})
    client.post("/api/services", json={"name": "b", "url": "https://b.example"})
    assert len(client.get("/api/services").json()) == 2


def test_get_missing_returns_404():
    assert client.get("/api/services/nope").status_code == 404


def test_delete_service():
    created = client.post("/api/services", json={"name": "x", "url": "https://x.example"}).json()
    assert client.delete(f"/api/services/{created['id']}").status_code == 204
    assert client.get(f"/api/services/{created['id']}").status_code == 404


def test_validation_rejects_empty_name():
    assert client.post("/api/services", json={"name": "", "url": "https://x.example"}).status_code == 422


def test_metrics_exposes_counters():
    client.post("/api/services", json={"name": "m", "url": "https://m.example"})
    body = client.get("/metrics").text
    assert "services_created_total" in body
    assert "services_total" in body
