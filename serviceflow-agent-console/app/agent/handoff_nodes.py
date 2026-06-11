from __future__ import annotations

from app.agent.nodes_helpers import tool_call as _tool_call
from app.agent.nodes_helpers import trace_step as _trace
from app.agent.nodes_support import create_human_ticket as _create_human_ticket
from app.agent.state import AgentState


def human_handoff_node(state: AgentState) -> AgentState:
    answer = "人工客服正在处理中，请等待客服回复。"
    # 人工接管期间不再自动调用业务工具，但仍回到统一 final/evaluation/save 链路。
    return {
        **state,
        "sender": "system",
        "final_answer": answer,
        "intent": state.get("current_intent") or "HUMAN_TRANSFER",
        "confidence": 1.0,
        "route_trace": _trace(state, "human_handoff_node"),
        "tool_calls": [],
        "retrieved_docs": [],
        "citations": [],
        "evaluation_result": {},
        "need_human": True,
    }


def human_ticket_node(state: AgentState) -> AgentState:
    output = _create_human_ticket(state)
    return {
        **state,
        "need_human": True,
        "ticket_id": output.get("ticket_id"),
        "conversation_status": "WAITING_HUMAN",
        "handoff_status": "REQUESTED",
        "final_answer": f"该问题已转交人工客服，工单号为 {output.get('ticket_id')}。",
        "tool_calls": [
            *state.get("tool_calls", []),
            _tool_call("create_ticket", {"user_id": state.get("user_id", "U1001"), "issue_type": state.get("intent")}, output),
        ],
        "route_trace": _trace(state, "human_ticket_node"),
    }

