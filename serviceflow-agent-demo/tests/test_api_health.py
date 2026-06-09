def test_health_reports_core_dependency_status(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert "redis" in body
    assert "qdrant" in body
    assert "minio" in body
