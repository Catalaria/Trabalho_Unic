"""
Teste básico das rotas /health.
(Placeholder para expansão — não inclui instruções de execução.)
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "mqtt" in data
    assert "counts" in data
