from __future__ import annotations

from typing import Any

from app.agent.nodes_helpers import (
    CANCEL_WORDS,
    CONFIRM_WORDS,
    ORDER_PATTERN,
    REASON_PATTERN,
    RETURN_PATTERN,
    RETURN_REASONS,
    pending_action as _pending_action,
    trace_step as _trace,
)
from app.agent.nodes_support import looks_like_new_intent as _looks_like_new_intent
from app.agent.nodes_support import parse_confirm_decision, should_continue_return_flow as _should_continue_return_flow
from app.agent.router import classify_intent_hybrid
from app.agent.state import AgentState
from app.config import settings


def parse_input_node(state: AgentState) -> AgentState:
    message = state["user_message"].strip()
    slots = {**state.get("slots", {})}
    extracted_slots: dict[str, Any] = {}
    order_match = ORDER_PATTERN.search(message)
    return_match = RETURN_PATTERN.search(message)
    reason_match = REASON_PATTERN.search(message)

    if order_match:
        extracted_slots["order_id"] = next(group for group in order_match.groups() if group)
    if return_match:
        extracted_slots["return_id"] = return_match.group(1)
    if reason_match:
        extracted_slots["return_reason"] = reason_match.group(1).strip()
    else:
        for reason in RETURN_REASONS:
            if reason in message:
                extracted_slots["return_reason"] = reason
                break

    confirm_decision = parse_confirm_decision(message, CANCEL_WORDS, CONFIRM_WORDS)
    if (
        state.get("current_intent") == "RETURN_REQUEST"
        and not confirm_decision
        and "return_reason" not in extracted_slots
        and not order_match
        and not any(keyword in message for keyword in ["退货", "退款", "订单"])
        and not _looks_like_new_intent(message)
    ):
        # 用户在退货流程里只回复“买错了”这类短句时，应视为上一轮缺失的退货原因。
        extracted_slots["return_reason"] = message

    slots.update({key: value for key, value in extracted_slots.items() if value})
    return {
        **state,
        "slots": slots,
        "extracted_slots": extracted_slots,
        "confirm_decision": confirm_decision,
        "route_trace": _trace(state, "parse_input_node"),
        "tool_calls": state.get("tool_calls", []),
        "retrieved_docs": state.get("retrieved_docs", []),
        "citations": state.get("citations", []),
        "evaluation_result": state.get("evaluation_result", {}),
        "missing_slots": [],
        "awaiting_user_input": False,
        "need_human": False,
        "ticket_id": state.get("ticket_id"),
        "order_info": state.get("order_info"),
        "return_result": state.get("return_result"),
        "final_answer": "",
    }


def intent_router_node(state: AgentState) -> AgentState:
    pending = _pending_action(state.get("pending_action"))
    if pending != "NONE":
        intent = state.get("current_intent") or "UNKNOWN"
        return {
            **state,
            "intent": intent,
            "confidence": 0.9,
            "reason": f"会话中存在待确认动作 {pending}，优先进入确认节点。",
            "route_debug": {
                "rule_result": None,
                "llm_result": None,
                "final_intent": intent,
                "conflict": False,
                "decision_reason": "pending_action 优先级高于新一轮意图识别。",
            },
            "route_trace": _trace(state, "intent_router_node"),
        }

    if _should_continue_return_flow(state):
        return {
            **state,
            "intent": "RETURN_REQUEST",
            "current_intent": "RETURN_REQUEST",
            "confidence": 0.88,
            "reason": "根据会话状态继续退货槽位补全流程。",
            "route_debug": {
                "rule_result": None,
                "llm_result": None,
                "final_intent": "RETURN_REQUEST",
                "conflict": False,
                "decision_reason": "用户正在补充退货流程必填槽位，沿用 current_intent。",
            },
            "route_trace": _trace(state, "intent_router_node"),
        }

    result, route_debug = classify_intent_hybrid(state["user_message"])
    slots = {**state.get("slots", {}), **{key: value for key, value in result.slots.items() if value}}
    return {
        **state,
        "intent": result.intent,
        "current_intent": result.intent if result.intent != "UNKNOWN" else state.get("current_intent"),
        "confidence": result.confidence,
        "reason": result.reason,
        "slots": slots,
        "route_debug": route_debug,
        "route_trace": _trace(state, "intent_router_node"),
    }


def route_decision(state: AgentState) -> str:
    if _pending_action(state.get("pending_action")) != "NONE":
        return "confirm_node"
    if state.get("confidence", 0) < settings.clarify_confidence_threshold:
        return "clarify_node"
    return {
        "ORDER_QUERY": "order_query_node",
        "RETURN_REQUEST": "slot_filling_node",
        "REFUND_STATUS": "refund_status_node",
        "TECH_SUPPORT": "rag_node",
        "POLICY_QA": "rag_node",
        "PRODUCT_QA": "rag_node",
        "COMPLAINT": "human_ticket_node",
        "HUMAN_TRANSFER": "human_ticket_node",
        "UNKNOWN": "clarify_node",
    }.get(state.get("intent", "UNKNOWN"), "clarify_node")
