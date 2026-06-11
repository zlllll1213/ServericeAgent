import pytest

from app.auth import create_token
from app.config import settings
from app.core.exceptions import AuthException
from app.database import SessionLocal
from app.models import AdminUser


def test_order_lookup_treats_suspicious_order_id_as_data(client):
    response = client.get("/api/orders/10001%27%20OR%20%271%27=%271")

    assert response.status_code == 200
    body = response.json()
    assert body["error"] == "订单不存在"
    assert body["order_id"] == "10001' OR '1'='1"
    assert body["product_name"] is None


def test_token_creation_requires_configured_auth_secret(monkeypatch):
    monkeypatch.setattr(settings, "auth_secret", None)

    with pytest.raises(AuthException, match="AUTH_SECRET"):
        create_token({"user_id": "A1001", "role": "admin"})


def test_demo_mode_does_not_fallback_to_embedded_password_hashes(client, monkeypatch):
    monkeypatch.setattr(settings, "demo_auth_enabled", True)
    monkeypatch.setattr(settings, "admin_password_hash", None)
    monkeypatch.setattr(settings, "agent_password_hash", None)
    with SessionLocal() as db:
        for user in db.query(AdminUser).all():
            user.password_hash = None
        db.commit()

    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})

    assert response.status_code == 401
    assert response.json()["error_code"] == "AUTH_FAILED"
