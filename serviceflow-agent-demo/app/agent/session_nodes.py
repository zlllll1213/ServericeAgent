from __future__ import annotations

from app.agent.nodes_helpers import trace_step as _trace
from app.agent.persistence import get_or_create_conversation
from app.agent.state import AgentState


def load_conversation_node(state: AgentState) -> AgentState:
    conversation = get_or_create_conversation(state.get("conversation_id"), state.get("user_id", "U1001"))
    return {
        **state,
        "conversation_id": conversation["conversation_id"],
        "current_intent": conversation.get("current_intent"),
        "pending_action": conversation.get("pending_action") or "NONE",
        "slots": conversation.get("slots", {}),
        "history": conversation.get("history", []),
        "conversation_status": conversation.get("status", "ACTIVE"),
        "handoff_status": conversation.get("handoff_status", "NONE"),
        "assigned_agent_id": conversation.get("assigned_agent_id"),
        "route_trace": _trace(state, "load_conversation_node"),
    }


def after_load_decision(state: AgentState) -> str:
    return "human_handoff_node" if state.get("conversation_status") == "HUMAN_HANDLING" else "parse_input_node"

