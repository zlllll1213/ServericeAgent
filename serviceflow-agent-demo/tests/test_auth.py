from app.config import settings
from app.database import SessionLocal
from app.models import AdminUser


def test_correct_account_can_login_and_token_reads_me(client):
    login = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})

    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["role"] == "admin"


def test_admin_user_password_hash_is_seeded(client):
    with SessionLocal() as db:
        admin = db.query(AdminUser).filter(AdminUser.username == "admin").first()

    assert admin is not None
    assert admin.password_hash.startswith("pbkdf2_sha256$")


def test_wrong_password_and_bad_token_are_rejected(client):
    bad_login = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    bad_token = client.get("/api/auth/me", headers={"Authorization": "Bearer broken"})

    assert bad_login.status_code == 401
    assert bad_token.status_code == 401


def test_admin_api_requires_token_by_default(client):
    response = client.get("/api/admin/conversations")
    forged = client.get("/api/admin/conversations", headers={"X-User-Role": "admin"})

    assert response.status_code == 401
    assert response.json()["error_code"] == "AUTH_FAILED"
    assert forged.status_code == 401


def test_demo_role_header_only_works_when_explicitly_enabled(client, monkeypatch):
    monkeypatch.setattr(settings, "demo_auth_enabled", True)
    response = client.get("/api/admin/conversations", headers={"X-User-Role": "admin"})
    monkeypatch.setattr(settings, "demo_auth_enabled", False)

    assert response.status_code == 200


def test_password_hash_must_be_configured_outside_demo_mode(client, monkeypatch):
    monkeypatch.setattr(settings, "demo_auth_enabled", False)
    monkeypatch.setattr(settings, "admin_password_hash", None)
    monkeypatch.setattr(settings, "agent_password_hash", None)
    with SessionLocal() as db:
        for user in db.query(AdminUser).all():
            user.password_hash = None
        db.commit()

    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})

    assert response.status_code == 401
    assert response.json()["error_code"] == "AUTH_FAILED"
