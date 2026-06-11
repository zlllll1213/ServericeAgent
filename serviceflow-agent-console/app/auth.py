from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import AuthException, PermissionDeniedException, ServiceFlowException
from app.database import get_db
from app.models import AdminUser

router = APIRouter()

JWT_HEADER = {"alg": "HS256", "typ": "JWT"}
PASSWORD_HASH_ITERATIONS = 120000


class LoginRequest(BaseModel):
    username: str
    password: str


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode())


def _auth_secret() -> str:
    if not settings.auth_secret:
        raise AuthException("AUTH_SECRET 未配置，请使用稳定的强随机密钥，避免服务重启后 token 全部失效")
    if len(settings.auth_secret) < 32:
        raise AuthException("AUTH_SECRET 长度不足，请至少使用 32 个字符")
    return settings.auth_secret


def _sign(message: str) -> str:
    return _base64url_encode(hmac.new(_auth_secret().encode(), message.encode(), hashlib.sha256).digest())


def hash_password(password: str, salt: str | None = None, iterations: int = PASSWORD_HASH_ITERATIONS) -> str:
    resolved_salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), resolved_salt.encode(), iterations).hex()
    return f"pbkdf2_sha256${iterations}${resolved_salt}${digest}"


def _password_hash_matches(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt, digest = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            raise AuthException("不支持的密码哈希算法")
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations)).hex()
        return hmac.compare_digest(candidate, digest)
    except ServiceFlowException:
        raise
    except Exception as exc:
        raise AuthException("密码哈希配置无效") from exc


def _configured_users() -> dict[str, dict[str, str]]:
    admin_hash = settings.admin_password_hash
    agent_hash = settings.agent_password_hash
    if not admin_hash or not agent_hash:
        raise AuthException("后台密码哈希未配置，请设置 ADMIN_PASSWORD_HASH 和 AGENT_PASSWORD_HASH")
    return {
        settings.admin_username: {"password_hash": admin_hash, "user_id": "A1001", "role": "admin"},
        settings.agent_username: {"password_hash": agent_hash, "user_id": "S1001", "role": "agent"},
    }


def _admin_user_from_db(username: str, db: Session) -> dict[str, str] | None:
    admin_user = db.query(AdminUser).filter(AdminUser.username == username).first()
    if admin_user is None:
        return None
    return {"user_id": admin_user.user_id, "role": admin_user.role, "password_hash": admin_user.password_hash or ""}


def create_token(payload: dict[str, Any], ttl_seconds: int = 3600) -> str:
    now = int(time.time())
    body = {
        **payload,
        "iss": settings.auth_issuer,
        "aud": settings.auth_audience,
        "iat": now,
        "exp": now + ttl_seconds,
        "jti": uuid4().hex,
    }
    encoded_header = _base64url_encode(json.dumps(JWT_HEADER, separators=(",", ":"), ensure_ascii=False).encode())
    encoded_body = _base64url_encode(json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode())
    signature = _sign(f"{encoded_header}.{encoded_body}")
    return f"{encoded_header}.{encoded_body}.{signature}"


def decode_token(token: str) -> dict[str, Any]:
    try:
        encoded_header, encoded_body, signature = token.split(".", 2)
        expected = _sign(f"{encoded_header}.{encoded_body}")
        if not hmac.compare_digest(signature, expected):
            raise AuthException("无效 token")
        header = json.loads(_base64url_decode(encoded_header).decode())
        payload = json.loads(_base64url_decode(encoded_body).decode())
        if header.get("alg") != "HS256" or header.get("typ") != "JWT":
            raise AuthException("无效 token")
        if payload.get("iss") != settings.auth_issuer or payload.get("aud") != settings.auth_audience:
            raise AuthException("token 签发方或受众不匹配")
        if int(payload.get("exp", 0)) < int(time.time()):
            raise AuthException("token 已过期")
        return payload
    except ServiceFlowException:
        raise
    except Exception as exc:
        raise AuthException("无效 token") from exc


def user_from_headers(authorization: str | None = None, x_user_role: str | None = None) -> dict[str, Any]:
    if authorization and authorization.startswith("Bearer "):
        return decode_token(authorization.removeprefix("Bearer ").strip())
    if x_user_role and settings.demo_auth_enabled:
        # X-User-Role 只保留给本地演示；默认关闭，避免把可伪造请求头误当成生产认证。
        role = "agent" if x_user_role == "service_agent" else x_user_role
        return {"user_id": "S1001" if role == "agent" else "A1001", "role": role}
    raise AuthException("缺少认证信息")


def require_admin_access(
    authorization: str | None = Header(default=None),
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
) -> dict[str, Any]:
    user = user_from_headers(authorization, x_user_role)
    if user.get("role") not in {"agent", "admin", "tenant_admin", "super_admin"}:
        raise PermissionDeniedException("没有权限访问后台资源")
    return user


@router.post("/auth/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = _admin_user_from_db(request.username, db) or _configured_users().get(request.username)
    if not user or not user.get("password_hash") or not _password_hash_matches(request.password, user["password_hash"]):
        raise AuthException("账号或密码错误")
    token = create_token(
        {"user_id": user["user_id"], "username": request.username, "role": user["role"]},
        ttl_seconds=settings.auth_token_ttl_seconds,
    )
    return {"access_token": token, "token_type": "bearer", "role": user["role"], "user_id": user["user_id"]}


@router.get("/auth/me")
def me(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthException("缺少 token")
    return decode_token(authorization.removeprefix("Bearer ").strip())
