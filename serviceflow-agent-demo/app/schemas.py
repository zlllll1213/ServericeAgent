from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    user_id: str = "U1001"
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    trace_id: str | None = None
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
    assigned_agent_id: str | None = None
    resolution: str | None = None
    created_at: str
    updated_at: str | None = None


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
    assigned_agent_id: str | None = None
    handoff_status: str = "NONE"
    created_at: str
    updated_at: str


class ChatLogResponse(BaseModel):
    id: int
    conversation_id: str
    trace_id: str | None = None
    user_id: str
    sender: str = "agent"
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


class AssignRequest(BaseModel):
    agent_id: str = Field(min_length=1)


class HumanReplyRequest(BaseModel):
    agent_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


class ResolveRequest(BaseModel):
    agent_id: str = Field(min_length=1)
    resolution: str = Field(min_length=1)


class KnowledgeDocumentCreate(BaseModel):
    title: str = Field(min_length=1)
    knowledge_base: str = Field(pattern="^(tech|policy|product)$")
    content: str = Field(min_length=1)
    created_by: str = "admin"


class KnowledgeDocumentUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    knowledge_base: str | None = Field(default=None, pattern="^(tech|policy|product)$")


class KnowledgeDocumentResponse(BaseModel):
    id: int
    doc_id: str
    title: str
    knowledge_base: str
    source_file: str | None = None
    content: str
    status: str
    version: int
    created_by: str
    created_at: str
    updated_at: str


class FeedbackRequest(BaseModel):
    conversation_id: str
    chat_log_id: int
    user_id: str
    rating: int = Field(ge=1, le=5)
    feedback_type: str = Field(pattern="^(GOOD|WRONG_INTENT|WRONG_TOOL|BAD_ANSWER|MISSING_CITATION|NEED_HUMAN)$")
    comment: str | None = None


class FeedbackResponse(BaseModel):
    id: int
    conversation_id: str
    chat_log_id: int
    user_id: str
    rating: int
    feedback_type: str
    comment: str | None = None
    created_at: str
