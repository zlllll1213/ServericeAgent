from __future__ import annotations

import json
from typing import Any

from app.llm.client import get_llm_client
from app.llm.prompts import ANSWER_EVALUATION_PROMPT


DEFAULT_EVALUATION = {
    "intent_correctness": 0.8,
    "answer_relevance": 0.8,
    "tool_call_correctness": 1.0,
    "citation_quality": 1.0,
    "safety_risk": "LOW",
    "need_human_review": False,
    "comment": "规则评估：回复已完成基础流程校验。",
}


def evaluate_response(state: dict[str, Any]) -> dict[str, Any]:
    client = get_llm_client()
    if client.available:
        prompt = ANSWER_EVALUATION_PROMPT.format(
            user_message=state.get("user_message", ""),
            answer=state.get("final_answer", ""),
            intent=state.get("intent", "UNKNOWN"),
            tool_calls=json.dumps(state.get("tool_calls", []), ensure_ascii=False),
            retrieved_docs=json.dumps(state.get("retrieved_docs", []), ensure_ascii=False),
            citations=json.dumps(state.get("citations", []), ensure_ascii=False),
        )
        result = client.json_completion(prompt)
        if result:
            return _normalize_evaluation(result)
    return _rule_based_evaluation(state)


def _rule_based_evaluation(state: dict[str, Any]) -> dict[str, Any]:
    result = dict(DEFAULT_EVALUATION)
    intent = state.get("intent", "UNKNOWN")
    citations = state.get("citations", [])
    retrieved_docs = state.get("retrieved_docs", [])
    tool_calls = state.get("tool_calls", [])

    if intent == "UNKNOWN":
        result["intent_correctness"] = 0.55
        result["answer_relevance"] = 0.65
        result["comment"] = "规则评估：意图仍不明确，建议继续追问。"

    if intent in {"TECH_SUPPORT", "POLICY_QA", "PRODUCT_QA"}:
        result["citation_quality"] = 0.85 if citations and retrieved_docs else 0.35
        if not citations:
            result["comment"] = "规则评估：知识库回答缺少可追溯引用。"

    if state.get("pending_action") in {"CREATE_RETURN_REQUEST", "CREATE_TICKET"}:
        # 等待用户确认时没有执行变更工具，这是符合第三阶段安全要求的。
        mutating_calls = {call.get("name") for call in tool_calls} & {"create_return_request", "create_ticket"}
        result["tool_call_correctness"] = 0.4 if mutating_calls else 1.0

    if state.get("need_human"):
        result["need_human_review"] = True
        result["comment"] = "规则评估：已进入人工处理流程，需要客服查看。"

    return result


def _normalize_evaluation(result: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(DEFAULT_EVALUATION)
    normalized.update(result)
    for key in ["intent_correctness", "answer_relevance", "tool_call_correctness", "citation_quality"]:
        try:
            normalized[key] = max(0.0, min(1.0, float(normalized[key])))
        except (TypeError, ValueError):
            normalized[key] = DEFAULT_EVALUATION[key]
    normalized["safety_risk"] = str(normalized.get("safety_risk") or "LOW").upper()
    normalized["need_human_review"] = bool(normalized.get("need_human_review"))
    normalized["comment"] = str(normalized.get("comment") or DEFAULT_EVALUATION["comment"])
    return normalized
