from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.agent.intents import Intent
from app.agent.router import classify_intent
from app.agent.state import AgentState
from app.config import settings
from app.llm.client import get_llm_client
from app.llm.prompts import HUMAN_SUMMARY_PROMPT, RAG_ANSWER_PROMPT
from app.tools.customer_tools import create_ticket


def should_continue_return_flow(state: AgentState) -> bool:
    if state.get("current_intent") != Intent.RETURN_REQUEST.value:
        return False
    slots = state.get("slots", {})
    missing = [slot for slot in ["order_id", "return_reason"] if not slots.get(slot)]
    extracted = state.get("extracted_slots", {})
    return bool(missing or {"order_id", "return_reason"} & set(extracted))


def looks_like_new_intent(message: str) -> bool:
    result = classify_intent(message)
    return result.intent not in {Intent.UNKNOWN.value, Intent.RETURN_REQUEST.value} and result.confidence >= settings.clarify_confidence_threshold


def parse_confirm_decision(message: str, cancel_words: set[str], confirm_words: set[str]) -> str | None:
    compact = message.strip().lower()
    if any(word.lower() in compact for word in cancel_words):
        return "CANCELLED"
    if any(word.lower() in compact for word in confirm_words):
        return "CONFIRMED"
    return None


def generate_rag_answer(question: str, docs: list[dict[str, Any]]) -> dict[str, Any]:
    if not docs:
        return {"answer": "暂未找到相关资料，建议转人工客服进一步确认。", "citations": []}

    client = get_llm_client()
    if client.available:
        result = client.json_completion(RAG_ANSWER_PROMPT.format(question=question, docs=json.dumps(docs, ensure_ascii=False)))
        if result and isinstance(result.get("answer"), str):
            return {
                "answer": result["answer"],
                "citations": normalize_citations(result.get("citations") or docs),
            }

    bullets = [f"- 参考《{doc.get('title', '知识库文档')}》：{doc.get('snippet', '')}" for doc in docs[:2]]
    return {
        "answer": "根据知识库，我找到这些信息：\n"
        + "\n".join(bullets)
        + f"\n\n针对你的问题“{question}”，建议先按上述资料核对；如果仍无法解决，我可以继续帮你转人工。",
        "citations": normalize_citations(docs),
    }


def normalize_citations(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    citations = []
    for index, item in enumerate(items[:3], start=1):
        source = item.get("source_file") or item.get("source") or "unknown.md"
        source_name = Path(source).name
        citations.append(
            {
                "source_file": source_name,
                "chunk_id": item.get("chunk_id") or f"{item.get('category', 'doc')}_{index:03d}",
                "score": float(item.get("score", 0.0) or 0.0),
            }
        )
    return citations


def create_human_ticket(state: AgentState) -> dict[str, Any]:
    summary_payload = build_human_summary(state)
    return create_ticket(
        user_id=state.get("user_id", "U1001"),
        issue_type=summary_payload["issue_type"],
        priority=summary_payload["priority"],
        summary=summary_payload["summary"],
        chat_history=[*state.get("history", []), {"role": "user", "content": state.get("user_message", "")}],
    )


def build_human_summary(state: AgentState) -> dict[str, str]:
    client = get_llm_client()
    if client.available:
        result = client.json_completion(
            HUMAN_SUMMARY_PROMPT.format(
                user_id=state.get("user_id", "U1001"),
                intent=state.get("intent", Intent.HUMAN_TRANSFER.value),
                history=json.dumps([*state.get("history", []), {"role": "user", "content": state.get("user_message", "")}], ensure_ascii=False),
            )
        )
        if result and result.get("summary"):
            return {
                "summary": str(result.get("summary")),
                "priority": str(result.get("priority") or "HIGH").upper(),
                "issue_type": str(result.get("issue_type") or state.get("intent") or Intent.HUMAN_TRANSFER.value),
                "suggested_action": str(result.get("suggested_action") or "建议客服尽快跟进。"),
            }

    message = state.get("user_message", "")
    priority = "HIGH" if any(keyword in message for keyword in ["投诉", "差评", "举报", "人工"]) else "MEDIUM"
    if len(message.strip()) < 8:
        priority = "LOW"
    return {
        "summary": f"用户反馈：{message}。当前意图为 {state.get('intent', Intent.HUMAN_TRANSFER.value)}，需要人工客服介入处理。",
        "priority": priority,
        "issue_type": state.get("intent", Intent.HUMAN_TRANSFER.value),
        "suggested_action": "建议客服查看完整会话并主动联系用户。",
    }
