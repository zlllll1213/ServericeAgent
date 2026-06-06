from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    user_id: str = "U1001"


class ChatResponse(BaseModel):
    answer: str
    intent: str
    confidence: float
    reason: str | None = None
    extracted_slots: dict[str, Any] = Field(default_factory=dict)
    route_trace: list[str] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    retrieved_docs: list[dict[str, Any]] = Field(default_factory=list)
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
