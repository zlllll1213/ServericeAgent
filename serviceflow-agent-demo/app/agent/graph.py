from langgraph.graph import END, START, StateGraph

from app.agent.nodes import (
    clarify_node,
    final_response_node,
    human_ticket_node,
    intent_router_node,
    order_query_node,
    parse_input_node,
    rag_policy_node,
    rag_product_node,
    rag_tech_node,
    refund_status_node,
    return_request_node,
    route_decision,
)
from app.agent.state import AgentState


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("parse_input_node", parse_input_node)
    graph.add_node("intent_router_node", intent_router_node)
    graph.add_node("order_query_node", order_query_node)
    graph.add_node("return_request_node", return_request_node)
    graph.add_node("refund_status_node", refund_status_node)
    graph.add_node("rag_tech_node", rag_tech_node)
    graph.add_node("rag_policy_node", rag_policy_node)
    graph.add_node("rag_product_node", rag_product_node)
    graph.add_node("human_ticket_node", human_ticket_node)
    graph.add_node("clarify_node", clarify_node)
    graph.add_node("final_response_node", final_response_node)

    graph.add_edge(START, "parse_input_node")
    graph.add_edge("parse_input_node", "intent_router_node")
    graph.add_conditional_edges(
        "intent_router_node",
        route_decision,
        {
            "order_query_node": "order_query_node",
            "return_request_node": "return_request_node",
            "refund_status_node": "refund_status_node",
            "rag_tech_node": "rag_tech_node",
            "rag_policy_node": "rag_policy_node",
            "rag_product_node": "rag_product_node",
            "human_ticket_node": "human_ticket_node",
            "clarify_node": "clarify_node",
        },
    )
    for node in [
        "order_query_node",
        "return_request_node",
        "refund_status_node",
        "rag_tech_node",
        "rag_policy_node",
        "rag_product_node",
        "human_ticket_node",
        "clarify_node",
    ]:
        graph.add_edge(node, "final_response_node")
    graph.add_edge("final_response_node", END)
    return graph.compile()


AGENT_GRAPH = build_graph()


def run_agent(user_message: str, user_id: str = "U1001") -> dict:
    initial_state: AgentState = {
        "user_message": user_message,
        "user_id": user_id,
        "intent": "UNKNOWN",
        "confidence": 0.0,
        "reason": None,
        "extracted_slots": {},
        "route_trace": [],
        "tool_calls": [],
        "retrieved_docs": [],
        "final_answer": "",
        "need_human": False,
        "ticket_id": None,
        "order_info": None,
        "return_result": None,
    }
    state = AGENT_GRAPH.invoke(initial_state)
    return {
        "answer": state["final_answer"],
        "intent": state.get("intent", "UNKNOWN"),
        "confidence": state.get("confidence", 0),
        "reason": state.get("reason"),
        "extracted_slots": state.get("extracted_slots", {}),
        "route_trace": state.get("route_trace", []),
        "tool_calls": state.get("tool_calls", []),
        "retrieved_docs": state.get("retrieved_docs", []),
        "need_human": state.get("need_human", False),
        "ticket_id": state.get("ticket_id"),
        "order_info": state.get("order_info"),
        "return_result": state.get("return_result"),
    }
