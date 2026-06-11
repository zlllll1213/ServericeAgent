from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    trace_id: str
    tenant_id: str
    conversation_id: str | None
    user_message: str
    user_id: str
    current_intent: str | None
    conversation_status: str
    handoff_status: str
    assigned_agent_id: str | None
    pending_action: str
    slots: dict[str, Any]
    missing_slots: list[str]
    history: list[dict[str, Any]]
    awaiting_user_input: bool
    confirm_decision: str | None
    intent: str
    confidence: float
    reason: str
    extracted_slots: dict[str, Any]
    route_trace: list[str]
    route_debug: dict[str, Any]
    tool_calls: list[dict[str, Any]]
    retrieved_docs: list[dict[str, Any]]
    citations: list[dict[str, Any]]
    evaluation_result: dict[str, Any]
    final_answer: str
    sender: str
    need_human: bool
    ticket_id: str | None
    order_info: dict[str, Any] | None
    return_result: dict[str, Any] | None
