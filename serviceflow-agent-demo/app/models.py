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
    created_at: Mapped[datetime] = mapped_column(DateTime)


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
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)


class ChatLog(Base, SerializableMixin):
    __tablename__ = "chat_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[str] = mapped_column(Text, index=True)
    user_id: Mapped[str] = mapped_column(Text, index=True)
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
