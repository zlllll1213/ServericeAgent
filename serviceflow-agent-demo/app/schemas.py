from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    user_id: str = "U1001"
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    intent: str
    confidence: float
    reason: str | None = None
    slots: dict[str, Any] = Field(default_factory=dict)
    missing_slots: list[str] = Field(default_factory=list)
    pending_action: str | None = None
    awaiting_user_input: bool = False
    extracted_slots: dict[str, Any] = Field(default_factory=dict)
    route_trace: list[str] = Field(default_factory=list)
    route_debug: dict[str, Any] = Field(default_factory=dict)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    retrieved_docs: list[dict[str, Any]] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    evaluation_result: dict[str, Any] = Field(default_factory=dict)
    need_human: bool = False
    ticket_id: str | None = None
    order_info: dict[str, Any] | None = None
    return_result: dict[str, Any] | None = None


class OrderResponse(BaseModel):
    id: int | None = None
    order_id: str
    user_id: str | None = None
    product_name: str | None = None
    status: str | None = None
    paid_amount: float | None = None
    created_at: str | None = None
    delivered_at: str | None = None
    can_return: bool | None = None
    logistics_info: str | None = None
    error: str | None = None


class TicketResponse(BaseModel):
    id: int
    ticket_id: str
    user_id: str
    issue_type: str
    priority: str
    summary: str
    chat_history: str
    status: str
    created_at: str


class ReturnResponse(BaseModel):
    id: int
    return_id: str
    order_id: str
    reason: str
    status: str
    created_at: str


class ConversationResponse(BaseModel):
    conversation_id: str
    user_id: str
    current_intent: str | None = None
    pending_action: str = "NONE"
    slots: dict[str, Any] = Field(default_factory=dict)
    history: list[dict[str, Any]] = Field(default_factory=list)
    status: str
    created_at: str
    updated_at: str


class ChatLogResponse(BaseModel):
    id: int
    conversation_id: str
    user_id: str
    user_message: str
    final_answer: str
    intent: str
    confidence: float
    route_trace: list[str] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    retrieved_docs: list[dict[str, Any]] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    evaluation_result: dict[str, Any] = Field(default_factory=dict)
    created_at: str
