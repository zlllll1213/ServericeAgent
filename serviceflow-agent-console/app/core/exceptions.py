from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ServiceFlowException(Exception):
    error_code = "SERVICEFLOW_ERROR"
    status_code = 500

    def __init__(self, message: str = "服务异常"):
        self.message = message
        super().__init__(message)


class AuthException(ServiceFlowException):
    error_code = "AUTH_FAILED"
    status_code = 401


class PermissionDeniedException(ServiceFlowException):
    error_code = "PERMISSION_DENIED"
    status_code = 403


class TenantAccessDeniedException(ServiceFlowException):
    error_code = "TENANT_ACCESS_DENIED"
    status_code = 403


class ToolExecutionException(ServiceFlowException):
    error_code = "TOOL_EXECUTION_FAILED"


class RetrieverException(ServiceFlowException):
    error_code = "RETRIEVER_FAILED"


class LLMException(ServiceFlowException):
    error_code = "LLM_FAILED"


class ValidationException(ServiceFlowException):
    error_code = "VALIDATION_FAILED"
    status_code = 422


class RateLimitException(ServiceFlowException):
    error_code = "RATE_LIMITED"
    status_code = 429


def request_id() -> str:
    return f"REQ_{uuid4().hex[:12]}"


async def serviceflow_exception_handler(request: Request, exc: ServiceFlowException):
    logger.info("serviceflow_exception path=%s code=%s message=%s", request.url.path, exc.error_code, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message, "request_id": request_id()},
    )


async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled_exception path=%s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error_code": "INTERNAL_ERROR", "message": "服务内部错误", "request_id": request_id()},
    )
