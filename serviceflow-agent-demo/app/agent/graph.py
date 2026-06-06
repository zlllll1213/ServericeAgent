from langgraph.graph import END, START, StateGraph

from app.agent.nodes import (
    clarify_node,
    confirm_decision,
    confirm_node,
    evaluation_node,
    final_response_node,
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


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("load_conversation_node", load_conversation_node)
    graph.add_node("parse_input_node", parse_input_node)
    graph.add_node("intent_router_node", intent_router_node)
    graph.add_node("order_query_node", order_query_node)
    graph.add_node("slot_filling_node", slot_filling_node)
    graph.add_node("confirm_node", confirm_node)
    graph.add_node("tool_execute_node", tool_execute_node)
    graph.add_node("refund_status_node", refund_status_node)
    graph.add_node("rag_node", rag_node)
    graph.add_node("human_ticket_node", human_ticket_node)
    graph.add_node("clarify_node", clarify_node)
    graph.add_node("final_response_node", final_response_node)
    graph.add_node("evaluation_node", evaluation_node)
    graph.add_node("save_conversation_node", save_conversation_node)

    graph.add_edge(START, "load_conversation_node")
    graph.add_edge("load_conversation_node", "parse_input_node")
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
    initial_state: AgentState = {
        "conversation_id": conversation_id,
        "user_message": user_message,
        "user_id": user_id,
        "current_intent": None,
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
        "need_human": False,
        "ticket_id": None,
        "order_info": None,
        "return_result": None,
    }
    state = AGENT_GRAPH.invoke(initial_state)
    slots = _response_slots(state)
    return {
        "conversation_id": state["conversation_id"],
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
