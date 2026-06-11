import pytest

from app.agent.graph import traced_node
from app.agent.input_routing_nodes import parse_input_node
from app.config import settings


def test_parse_input_preserves_previous_evidence_for_current_turn():
    state = {
        "user_message": "继续看看这个问题",
        "slots": {},
        "route_trace": [],
        "tool_calls": [{"name": "get_order_status"}],
        "retrieved_docs": [{"title": "SmartRouter X1"}],
        "citations": [{"source_file": "knowledge_base/tech/smart_router_wifi.md"}],
        "evaluation_result": {"answer_relevance": 1.0},
        "missing_slots": ["order_id"],
        "awaiting_user_input": True,
        "need_human": True,
        "ticket_id": "T1",
        "order_info": {"order_id": "10001"},
        "return_result": {"success": True},
        "final_answer": "上一轮回答",
    }

    result = parse_input_node(state)

    assert result["tool_calls"] == state["tool_calls"]
    assert result["retrieved_docs"] == state["retrieved_docs"]
    assert result["citations"] == state["citations"]
    assert result["evaluation_result"] == state["evaluation_result"]
    assert result["order_info"] == state["order_info"]


def test_traced_node_uses_configured_retry_delay(monkeypatch):
    attempts = {"count": 0}
    delays: list[float] = []

    monkeypatch.setattr(settings, "agent_node_retry_delay_seconds", 0.123)
    monkeypatch.setattr("app.agent.graph.sleep", delays.append)
    monkeypatch.setattr("app.agent.graph._safe_write_agent_trace", lambda **kwargs: None)

    def flaky_node(state):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("temporary")
        return {**state, "conversation_id": "C1"}

    result = traced_node("load_conversation_node", flaky_node)({"trace_id": "TR1", "tenant_id": "T1001", "conversation_id": "C1"})

    assert result["conversation_id"] == "C1"
    assert delays == [pytest.approx(0.123)]
