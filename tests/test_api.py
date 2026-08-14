from fastapi.testclient import TestClient

from web.main import app


def test_api_docs_and_health_load() -> None:
    client = TestClient(app)

    assert client.get("/openapi.json").status_code == 200
    assert client.get("/api/health").status_code == 200
