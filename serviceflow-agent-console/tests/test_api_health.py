def test_health_reports_core_dependency_status(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert "redis" in body
    assert "qdrant" in body
    assert "minio" in body


def test_static_html_routes_load_module_entrypoints(client):
    routes = {
        "/": "/static/chat/index.js",
        "/admin": "/static/admin/index.js",
        "/login": "/static/login.js",
    }

    for route, module_path in routes.items():
        response = client.get(route)

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert 'type="module"' in response.text
        assert module_path in response.text
