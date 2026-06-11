from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SerializableMixin:
    def to_dict(self):
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result


class Order(Base, SerializableMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[str] = mapped_column(Text, unique=True, index=True)
    user_id: Mapped[str] = mapped_column(Text, default="U1001")
    product_name: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    paid_amount: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    can_return: Mapped[bool] = mapped_column(Boolean, default=False)
    logistics_info: Mapped[str] = mapped_column(Text)


class ReturnRequest(Base, SerializableMixin):
    __tablename__ = "return_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    return_id: Mapped[str] = mapped_column(Text, unique=True, index=True)
    order_id: Mapped[str] = mapped_column(Text, index=True)
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="CREATED")
    created_at: Mapped[datetime] = mapped_column(DateTime)


class Ticket(Base, SerializableMixin):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_id: Mapped[str] = mapped_column(Text, unique=True, index=True)
    user_id: Mapped[str] = mapped_column(Text, index=True)
    issue_type: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(Text, default="HIGH")
    summary: Mapped[str] = mapped_column(Text)
    chat_history: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="OPEN")
    assigned_agent_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Conversation(Base, SerializableMixin):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[str] = mapped_column(Text, unique=True, index=True)
    user_id: Mapped[str] = mapped_column(Text, index=True)
    current_intent: Mapped[str | None] = mapped_column(Text, nullable=True)
    pending_action: Mapped[str] = mapped_column(Text, default="NONE")
    slots: Mapped[str] = mapped_column(Text, default="{}")
    history: Mapped[str] = mapped_column(Text, default="[]")
    status: Mapped[str] = mapped_column(Text, default="ACTIVE")
    assigned_agent_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    handoff_status: Mapped[str] = mapped_column(Text, default="NONE")
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)


class ChatLog(Base, SerializableMixin):
    __tablename__ = "chat_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[str] = mapped_column(Text, index=True)
    trace_id: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    user_id: Mapped[str] = mapped_column(Text, index=True)
    sender: Mapped[str] = mapped_column(Text, default="agent")
    user_message: Mapped[str] = mapped_column(Text)
    final_answer: Mapped[str] = mapped_column(Text)
    intent: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    route_trace: Mapped[str] = mapped_column(Text, default="[]")
    tool_calls: Mapped[str] = mapped_column(Text, default="[]")
    retrieved_docs: Mapped[str] = mapped_column(Text, default="[]")
    citations: Mapped[str] = mapped_column(Text, default="[]")
    evaluation_result: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime)


class AgentTrace(Base, SerializableMixin):
    __tablename__ = "agent_traces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[str] = mapped_column(Text, default="T1001", index=True)
    conversation_id: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    trace_id: Mapped[str] = mapped_column(Text, index=True)
    node_name: Mapped[str] = mapped_column(Text, index=True)
    input_state: Mapped[str] = mapped_column(Text)
    output_state: Mapped[str] = mapped_column(Text)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class KnowledgeDocument(Base, SerializableMixin):
    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    doc_id: Mapped[str] = mapped_column(Text, unique=True, index=True)
    title: Mapped[str] = mapped_column(Text)
    knowledge_base: Mapped[str] = mapped_column(Text, index=True)
    source_file: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="DRAFT")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_by: Mapped[str] = mapped_column(Text, default="admin")
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)


class AgentFeedback(Base, SerializableMixin):
    __tablename__ = "agent_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[str] = mapped_column(Text, index=True)
    chat_log_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[str] = mapped_column(Text, index=True)
    rating: Mapped[int] = mapped_column(Integer)
    feedback_type: Mapped[str] = mapped_column(Text, index=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class AdminUser(Base, SerializableMixin):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(Text, unique=True, index=True)
    username: Mapped[str] = mapped_column(Text)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime)
