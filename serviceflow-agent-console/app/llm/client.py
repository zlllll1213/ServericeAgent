from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 12.0,
    ):
        self.api_key = api_key if api_key is not None else settings.openai_api_key
        self.base_url = (base_url or settings.openai_base_url).rstrip("/")
        self.model = model or settings.openai_model
        self.timeout = timeout
        self.last_error: str | None = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def chat_completion(self, messages: list[dict[str, str]], json_output: bool = False) -> str | None:
        self.last_error = None
        if not self.available:
            self.last_error = "OPENAI_API_KEY 未配置"
            return None

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }
        if json_output:
            payload["response_format"] = {"type": "json_object"}

        try:
            # 使用 OpenAI-compatible Chat Completions 协议，base_url 可指向第三方兼容服务。
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            body = response.json()
            return body["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as exc:
            self.last_error = f"LLM HTTP {exc.response.status_code}"
            logger.warning("llm_http_status_error status=%s model=%s", exc.response.status_code, self.model)
            return None
        except httpx.TimeoutException:
            self.last_error = "LLM 请求超时"
            logger.warning("llm_timeout model=%s timeout=%s", self.model, self.timeout)
            return None
        except httpx.HTTPError as exc:
            self.last_error = exc.__class__.__name__
            logger.warning("llm_http_error type=%s model=%s", exc.__class__.__name__, self.model)
            return None
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            self.last_error = "LLM 响应结构异常"
            logger.warning("llm_response_parse_error type=%s model=%s", exc.__class__.__name__, self.model)
            return None

    def json_completion(self, prompt: str) -> dict[str, Any] | None:
        content = self.chat_completion(
            [
                {"role": "system", "content": "你只输出严格 JSON。"},
                {"role": "user", "content": prompt},
            ],
            json_output=True,
        )
        if not content:
            return None
        try:
            parsed = json.loads(content)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError as exc:
            self.last_error = "LLM JSON 解析失败"
            logger.warning("llm_json_decode_error error=%s", str(exc))
            return None


def get_llm_client() -> LLMClient:
    return LLMClient()
