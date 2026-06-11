import os
import tempfile

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SERVICEFLOW_DB_PATH", os.path.join(tempfile.gettempdir(), "serviceflow-agent-console-test.db"))
os.environ.setdefault("AUTH_SECRET", "test-auth-secret-with-at-least-32-characters")
os.environ.setdefault("DEMO_AUTH_ENABLED", "false")
os.environ.setdefault("ADMIN_PASSWORD_HASH", "pbkdf2_sha256$120000$serviceflow-admin-salt$9832057a930d7a670efdbaf1dde200756c0939784f2f496104189bcdabbe5e91")
os.environ.setdefault("AGENT_PASSWORD_HASH", "pbkdf2_sha256$120000$serviceflow-agent-salt$5bcc3a94b739763d9ab67aa08fd2bfc5c8e5aad24cacb6be499b3f9ecca6a28f")

from app.seed import seed_database
from app.rate_limit import reset_rate_limit_buckets
from main import app


@pytest.fixture()
def client():
    # 每个测试重置临时 SQLite 文件，避免污染 data/serviceflow.db。
    seed_database(reset=True)
    reset_rate_limit_buckets()
    return TestClient(app)


@pytest.fixture()
def admin_headers(client):
    login = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture()
def chat(client):
    def _post(message: str, conversation_id: str | None = None, user_id: str = "U1001"):
        response = client.post("/api/chat", json={"message": message, "conversation_id": conversation_id, "user_id": user_id})
        assert response.status_code == 200
        return response.json()

    return _post
