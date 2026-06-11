import httpx

from app.llm.client import LLMClient


def test_chat_completion_retries_transient_http_errors(monkeypatch):
    request = httpx.Request("POST", "https://llm.example/v1/chat/completions")
    calls = {"count": 0}

    def fake_post(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise httpx.TimeoutException("slow", request=request)
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]}, request=request)

    monkeypatch.setattr("app.llm.client.httpx.post", fake_post)
    monkeypatch.setattr("app.llm.client.sleep", lambda _: None)

    client = LLMClient(api_key="token", base_url="https://llm.example/v1", retry_attempts=2, retry_delay_seconds=0)

    assert client.chat_completion([{"role": "user", "content": "hi"}]) == "ok"
    assert calls["count"] == 2
