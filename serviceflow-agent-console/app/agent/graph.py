import logging
from time import sleep
from time import perf_counter
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from app.agent.persistence import write_agent_trace
from app.agent.nodes import (
    after_load_decision,
    clarify_node,
    confirm_decision,
    confirm_node,
    evaluation_node,
    final_response_node,
    human_handoff_node,
    human_ticket_node,
    intent_router_node,
    load_conversation_node,
    order_query_node,
    parse_input_node,
    rag_node,
    refund_status_node,
    route_decision,
    save_conversation_node,
    slot_filling_node,
    tool_execute_node,
)
from app.agent.state import AgentState
from app.config import settings

logger = logging.getLogger(__name__)
RETRYABLE_NODES = {"load_conversation_node", "save_conversation_node"}


def _safe_write_agent_trace(**kwargs) -> None:
    try:
        write_agent_trace(**kwargs)
    except Exception:
        logger.exception("agent_trace_write_failed node=%s trace_id=%s", kwargs.get("node_name"), kwargs.get("trace_id"))


def _recover_node_error(node_name: str, state: AgentState, exc: Exception) -> AgentState | None:
    if node_name == "evaluation_node":
        # 质检失败不应阻断用户回复；保留错误信息，后续人工或日志排查即可。
        return {
            **state,
            "evaluation_result": {
                "intent_correctness": 0.0,
                "answer_relevance": 0.0,
                "tool_call_correctness": 0.0,
                "citation_quality": 0.0,
                "safety_risk": "UNKNOWN",
                "need_human_review": True,
                "error": str(exc),
            },
            "route_trace": [*state.get("route_trace", []), "evaluation_node"],
        }
    return None


def traced_node(node_name: str, fn):
    def wrapped(state: AgentState) -> AgentState:
        max_attempts = 2 if node_name in RETRYABLE_NODES else 1
        for attempt in range(max_attempts):
            started = perf_counter()
            try:
                output = fn(state)
                latency_ms = round((perf_counter() - started) * 1000, 3)
                _safe_write_agent_trace(
                    tenant_id=state.get("tenant_id", "T1001"),
                    conversation_id=output.get("conversation_id") or state.get("conversation_id"),
                    trace_id=state.get("trace_id", "TR_UNKNOWN"),
                    node_name=node_name,
                    input_state=dict(state),
                    output_state=dict(output),
                    latency_ms=latency_ms,
                    success=True,
                )
                return output
            except Exception as exc:
                latency_ms = round((perf_counter() - started) * 1000, 3)
                _safe_write_agent_trace(
                    tenant_id=state.get("tenant_id", "T1001"),
                    conversation_id=state.get("conversation_id"),
                    trace_id=state.get("trace_id", "TR_UNKNOWN"),
                    node_name=node_name,
                    input_state=dict(state),
                    output_state={},
                    latency_ms=latency_ms,
                    success=False,
                    error_message=str(exc),
                )
                if attempt + 1 < max_attempts:
                    sleep(settings.agent_node_retry_delay_seconds)
                    continue
                recovered = _recover_node_error(node_name, state, exc)
                if recovered is not None:
                    return recovered
                raise
        raise RuntimeError(f"{node_name} 执行失败")

    return wrapped


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("load_conversation_node", traced_node("load_conversation_node", load_conversation_node))
    graph.add_node("human_handoff_node", traced_node("human_handoff_node", human_handoff_node))
    graph.add_node("parse_input_node", traced_node("parse_input_node", parse_input_node))
    graph.add_node("intent_router_node", traced_node("intent_router_node", intent_router_node))
    graph.add_node("order_query_node", traced_node("order_query_node", order_query_node))
    graph.add_node("slot_filling_node", traced_node("slot_filling_node", slot_filling_node))
    graph.add_node("confirm_node", traced_node("confirm_node", confirm_node))
    graph.add_node("tool_execute_node", traced_node("tool_execute_node", tool_execute_node))
    graph.add_node("refund_status_node", traced_node("refund_status_node", refund_status_node))
    graph.add_node("rag_node", traced_node("rag_node", rag_node))
    graph.add_node("human_ticket_node", traced_node("human_ticket_node", human_ticket_node))
    graph.add_node("clarify_node", traced_node("clarify_node", clarify_node))
    graph.add_node("final_response_node", traced_node("final_response_node", final_response_node))
    graph.add_node("evaluation_node", traced_node("evaluation_node", evaluation_node))
    graph.add_node("save_conversation_node", traced_node("save_conversation_node", save_conversation_node))

    graph.add_edge(START, "load_conversation_node")
    graph.add_conditional_edges(
        "load_conversation_node",
        after_load_decision,
        {
            "parse_input_node": "parse_input_node",
            "human_handoff_node": "human_handoff_node",
        },
    )
    graph.add_edge("human_handoff_node", "final_response_node")
    graph.add_edge("parse_input_node", "intent_router_node")
    graph.add_conditional_edges(
        "intent_router_node",
        route_decision,
        {
            "order_query_node": "order_query_node",
            "slot_filling_node": "slot_filling_node",
            "confirm_node": "confirm_node",
            "refund_status_node": "refund_status_node",
            "rag_node": "rag_node",
            "human_ticket_node": "human_ticket_node",
            "clarify_node": "clarify_node",
        },
    )
    graph.add_conditional_edges(
        "confirm_node",
        confirm_decision,
        {
            "tool_execute_node": "tool_execute_node",
            "final_response_node": "final_response_node",
        },
    )
    for node in [
        "order_query_node",
        "slot_filling_node",
        "tool_execute_node",
        "refund_status_node",
        "rag_node",
        "human_ticket_node",
        "clarify_node",
    ]:
        graph.add_edge(node, "final_response_node")
    graph.add_edge("final_response_node", "evaluation_node")
    graph.add_edge("evaluation_node", "save_conversation_node")
    graph.add_edge("save_conversation_node", END)
    return graph.compile()


AGENT_GRAPH = build_graph()


def run_agent(user_message: str, user_id: str = "U1001", conversation_id: str | None = None) -> dict:
    trace_id = f"TR_{uuid4().hex[:16]}"
    initial_state: AgentState = {
        "trace_id": trace_id,
        "tenant_id": "T1001",
        "conversation_id": conversation_id,
        "user_message": user_message,
        "user_id": user_id,
        "current_intent": None,
        "conversation_status": "ACTIVE",
        "handoff_status": "NONE",
        "assigned_agent_id": None,
        "pending_action": "NONE",
        "slots": {},
        "missing_slots": [],
        "history": [],
        "awaiting_user_input": False,
        "confirm_decision": None,
        "intent": "UNKNOWN",
        "confidence": 0.0,
        "reason": None,
        "extracted_slots": {},
        "route_trace": [],
        "route_debug": {},
        "tool_calls": [],
        "retrieved_docs": [],
        "citations": [],
        "evaluation_result": {},
        "final_answer": "",
        "sender": "agent",
        "need_human": False,
        "ticket_id": None,
        "order_info": None,
        "return_result": None,
    }
    state = AGENT_GRAPH.invoke(initial_state)
    slots = _response_slots(state)
    return {
        "conversation_id": state["conversation_id"],
        "trace_id": state.get("trace_id"),
        "answer": state["final_answer"],
        "intent": state.get("intent", "UNKNOWN"),
        "confidence": state.get("confidence", 0),
        "reason": state.get("reason"),
        "slots": slots,
        "missing_slots": state.get("missing_slots", []),
        "pending_action": None if state.get("pending_action") == "NONE" else state.get("pending_action"),
        "awaiting_user_input": state.get("awaiting_user_input", False),
        "extracted_slots": state.get("extracted_slots", {}),
        "route_trace": state.get("route_trace", []),
        "route_debug": state.get("route_debug", {}),
        "tool_calls": state.get("tool_calls", []),
        "retrieved_docs": state.get("retrieved_docs", []),
        "citations": state.get("citations", []),
        "evaluation_result": state.get("evaluation_result", {}),
        "need_human": state.get("need_human", False),
        "ticket_id": state.get("ticket_id"),
        "order_info": state.get("order_info"),
        "return_result": state.get("return_result"),
    }


def _response_slots(state: AgentState) -> dict:
    slots = dict(state.get("slots", {}))
    if state.get("intent") == "RETURN_REQUEST" or state.get("current_intent") == "RETURN_REQUEST":
        # 退货流程的必填槽位固定返回，前端无需猜测键是否存在。
        slots.setdefault("order_id", None)
        slots.setdefault("return_reason", None)
    return slots
