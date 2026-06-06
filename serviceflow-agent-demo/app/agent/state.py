from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    user_message: str
    user_id: str
    intent: str
    confidence: float
    reason: str
    extracted_slots: dict[str, Any]
    route_trace: list[str]
    tool_calls: list[dict[str, Any]]
    retrieved_docs: list[dict[str, Any]]
    final_answer: str
    need_human: bool
    ticket_id: str | None
    order_info: dict[str, Any] | None
    return_result: dict[str, Any] | None
