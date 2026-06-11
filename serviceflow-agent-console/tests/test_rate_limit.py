import pytest

from app.config import settings
from app.rate_limit import _BUCKETS, check_chat_rate_limit, reset_rate_limit_buckets


def test_health_exposes_redis_or_demo_rate_limit_status(client):
    body = client.get("/api/health").json()

    assert "redis" in body
    assert body["rate_limit"] == "in_memory_single_process"


def test_chat_rate_limit_blocks_excessive_requests(client, monkeypatch):
    monkeypatch.setattr(settings, "chat_rate_limit_requests", 1)
    monkeypatch.setattr(settings, "chat_rate_limit_window_seconds", 60)

    payload = {"message": "帮我查一下订单 10001", "user_id": "RATE_LIMIT_USER"}
    first = client.post("/api/chat", json=payload)
    second = client.post("/api/chat", json=payload)

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["error_code"] == "RATE_LIMITED"


def test_rate_limit_ignores_user_id_spoofing(client, monkeypatch):
    monkeypatch.setattr(settings, "chat_rate_limit_requests", 1)
    monkeypatch.setattr(settings, "chat_rate_limit_window_seconds", 60)

    first = client.post("/api/chat", json={"message": "帮我查一下订单 10001", "user_id": "USER_A"})
    second = client.post("/api/chat", json={"message": "帮我查一下订单 10001", "user_id": "USER_B"})

    assert first.status_code == 200
    assert second.status_code == 429


def test_rate_limit_uses_forwarded_ip_as_identity(client, monkeypatch):
    monkeypatch.setattr(settings, "chat_rate_limit_requests", 1)
    monkeypatch.setattr(settings, "chat_rate_limit_window_seconds", 60)

    payload = {"message": "帮我查一下订单 10001", "user_id": "FORWARDED_USER"}
    first = client.post("/api/chat", json=payload, headers={"X-Forwarded-For": "10.0.0.1"})
    second = client.post("/api/chat", json=payload, headers={"X-Forwarded-For": "10.0.0.2"})

    assert first.status_code == 200
    assert second.status_code == 200


def test_rate_limit_prunes_empty_identity_buckets(monkeypatch):
    reset_rate_limit_buckets()
    monkeypatch.setattr(settings, "chat_rate_limit_requests", 10)
    monkeypatch.setattr(settings, "chat_rate_limit_window_seconds", 0)

    check_chat_rate_limit("ip:127.0.0.1")
    check_chat_rate_limit("ip:127.0.0.2")

    assert list(_BUCKETS) == ["ip:127.0.0.2"]


def test_redis_rate_limit_backend_requires_configuration(monkeypatch):
    reset_rate_limit_buckets()
    monkeypatch.setattr(settings, "rate_limit_backend", "redis")
    monkeypatch.setattr(settings, "redis_url", None)

    with pytest.raises(Exception):
        check_chat_rate_limit("ip:127.0.0.1")


def test_redis_rate_limit_backend_counts_with_shared_key(monkeypatch):
    calls = []

    def fake_redis_command(*parts):
        calls.append(parts)
        if parts[0] == "INCR":
            return sum(1 for call in calls if call[0] == "INCR")
        return "OK"

    monkeypatch.setattr(settings, "rate_limit_backend", "redis")
    monkeypatch.setattr(settings, "redis_url", "redis://127.0.0.1:6379/0")
    monkeypatch.setattr(settings, "chat_rate_limit_requests", 1)
    monkeypatch.setattr(settings, "chat_rate_limit_window_seconds", 60)
    monkeypatch.setattr("app.rate_limit._redis_command", fake_redis_command)

    check_chat_rate_limit("ip:127.0.0.1")
    with pytest.raises(Exception):
        check_chat_rate_limit("ip:127.0.0.1")

    assert ("INCR", "serviceflow:rate_limit:chat:ip:127.0.0.1") in calls
    assert ("EXPIRE", "serviceflow:rate_limit:chat:ip:127.0.0.1", "60") in calls


@pytest.mark.skip(reason="当前本地 Demo 未启用 Redis 限流中间件，CI 先覆盖健康检查契约。")
def test_redis_rate_limit_blocks_excessive_requests():
    pass
