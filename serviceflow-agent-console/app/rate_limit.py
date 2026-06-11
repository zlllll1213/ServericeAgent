from __future__ import annotations

import time
import socket
from collections import defaultdict, deque
from typing import Deque
from urllib.parse import urlparse

from fastapi import Request

from app.config import settings
from app.core.exceptions import RateLimitException

_BUCKETS: dict[str, Deque[float]] = defaultdict(deque)


def client_identity_from_request(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    real_ip = request.headers.get("x-real-ip", "")
    client_host = request.client.host if request.client else "unknown"
    # 反向代理后优先使用代理透传的真实 IP；生产环境应只在可信代理处写入这些头。
    ip = forwarded_for.split(",", 1)[0].strip() or real_ip.strip() or client_host
    return f"ip:{ip}"


def check_chat_rate_limit(identity: str) -> None:
    if not settings.chat_rate_limit_enabled:
        return
    if settings.rate_limit_backend == "redis":
        _check_redis_rate_limit(identity)
        return

    now = time.monotonic()
    window = settings.chat_rate_limit_window_seconds
    limit = settings.chat_rate_limit_requests
    _prune_empty_buckets(now, window)
    bucket = _BUCKETS[identity]

    # 使用滑动窗口记录最近请求时间，先满足 Demo 的单进程防刷需求；多 worker 场景应替换为 Redis。
    while bucket and now - bucket[0] >= window:
        bucket.popleft()

    if len(bucket) >= limit:
        raise RateLimitException(f"请求过于频繁，请稍后再试。当前限制为 {window} 秒内 {limit} 次。")

    bucket.append(now)


def _prune_empty_buckets(now: float, window: int) -> None:
    for identity in list(_BUCKETS):
        bucket = _BUCKETS[identity]
        while bucket and now - bucket[0] >= window:
            bucket.popleft()
        if not bucket:
            del _BUCKETS[identity]


def reset_rate_limit_buckets() -> None:
    _BUCKETS.clear()


def _check_redis_rate_limit(identity: str) -> None:
    if not settings.redis_url:
        raise RateLimitException("Redis 限流后端未配置 REDIS_URL。")

    key = f"serviceflow:rate_limit:chat:{identity}"
    try:
        count = int(_redis_command("INCR", key))
        if count == 1:
            _redis_command("EXPIRE", key, str(settings.chat_rate_limit_window_seconds))
    except RateLimitException:
        raise
    except Exception as exc:
        raise RateLimitException(f"Redis 限流后端不可用：{exc}") from exc

    if count > settings.chat_rate_limit_requests:
        raise RateLimitException(
            f"请求过于频繁，请稍后再试。当前限制为 {settings.chat_rate_limit_window_seconds} 秒内 {settings.chat_rate_limit_requests} 次。"
        )


def _redis_command(*parts: str) -> int | str:
    parsed = urlparse(settings.redis_url or "")
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 6379
    database = (parsed.path or "/0").lstrip("/") or "0"
    timeout = 1.0

    with socket.create_connection((host, port), timeout=timeout) as sock:
        file = sock.makefile("rb")
        if parsed.password:
            _send_resp(sock, ["AUTH", parsed.password])
            _read_resp(file)
        if database != "0":
            _send_resp(sock, ["SELECT", database])
            _read_resp(file)
        _send_resp(sock, list(parts))
        return _read_resp(file)


def _send_resp(sock: socket.socket, parts: list[str]) -> None:
    payload = f"*{len(parts)}\r\n".encode()
    for part in parts:
        raw = part.encode()
        payload += f"${len(raw)}\r\n".encode() + raw + b"\r\n"
    sock.sendall(payload)


def _read_resp(file) -> int | str:
    prefix = file.read(1)
    if prefix == b":":
        return int(file.readline().decode().strip())
    if prefix == b"+":
        return file.readline().decode().strip()
    if prefix == b"$":
        length = int(file.readline().decode().strip())
        if length < 0:
            return ""
        data = file.read(length)
        file.read(2)
        return data.decode()
    if prefix == b"-":
        raise RateLimitException(file.readline().decode().strip())
    raise RateLimitException("无法解析 Redis 响应")
