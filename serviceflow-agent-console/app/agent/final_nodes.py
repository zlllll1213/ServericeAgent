from __future__ import annotations

from app.agent.nodes_helpers import trace_step as _trace
from app.agent.persistence import save_conversation_state, write_chat_log
from app.agent.state import AgentState
from app.evaluation import evaluate_response


def clarify_node(state: AgentState) -> AgentState:
    return {
        **state,
        "awaiting_user_input": True,
        "final_answer": "我还没能明确识别你的需求，请补充你要查询订单、申请退货、咨询技术问题、了解政策，还是需要人工客服。",
        "route_trace": _trace(state, "clarify_node"),
    }


def final_response_node(state: AgentState) -> AgentState:
    return {
        **state,
        "final_answer": state.get("final_answer") or "我已经收到你的问题，但还需要更多信息才能继续处理。",
        "route_trace": _trace(state, "final_response_node"),
    }


def evaluation_node(state: AgentState) -> AgentState:
    evaluation = evaluate_response(dict(state))
    return {**state, "evaluation_result": evaluation, "route_trace": _trace(state, "evaluation_node")}


def save_conversation_node(state: AgentState) -> AgentState:
    saved = save_conversation_state(dict(state))
    logged = write_chat_log({**state, "route_trace": _trace(state, "save_conversation_node")})
    return {
        **state,
        "history": saved.get("history", state.get("history", [])),
        "chat_log_id": logged.get("id"),
        "route_trace": _trace(state, "save_conversation_node"),
    }
