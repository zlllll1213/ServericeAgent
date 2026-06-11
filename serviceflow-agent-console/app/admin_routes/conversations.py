from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query

from app.admin_routes.common import not_found
from app.agent.persistence import chat_log_to_response, conversation_to_response, decode_json, encode_json
from app.database import SessionLocal
from app.models import ChatLog, Conversation
from app.schemas import AssignRequest, HumanReplyRequest, ResolveRequest

router = APIRouter()


@router.get("/admin/conversations")
def list_admin_conversations(
    status: str | None = None,
    handoff_status: str | None = None,
    user_id: str | None = None,
    intent: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    with SessionLocal() as db:
        query = db.query(Conversation)
        if status:
            query = query.filter(Conversation.status == status)
        if handoff_status:
            query = query.filter(Conversation.handoff_status == handoff_status)
        if user_id:
            query = query.filter(Conversation.user_id == user_id)
        if intent:
            query = query.filter(Conversation.current_intent == intent)
        rows = query.order_by(Conversation.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        items = []
        for conversation in rows:
            history = decode_json(conversation.history, [])
            last = history[-1]["content"] if history else ""
            items.append(
                {
                    "conversation_id": conversation.conversation_id,
                    "user_id": conversation.user_id,
                    "current_intent": conversation.current_intent,
                    "status": conversation.status,
                    "handoff_status": conversation.handoff_status,
                    "assigned_agent_id": conversation.assigned_agent_id,
                    "updated_at": conversation.updated_at.isoformat(),
                    "last_message_preview": last[:80],
                }
            )
        return items


@router.get("/admin/conversations/{conversation_id}")
def get_admin_conversation(conversation_id: str):
    with SessionLocal() as db:
        conversation = db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()
        if conversation is None:
            not_found("会话")
        logs = db.query(ChatLog).filter(ChatLog.conversation_id == conversation_id).order_by(ChatLog.id.asc()).all()
        log_items = [chat_log_to_response(log) for log in logs]
        latest = log_items[-1] if log_items else {}
        return {
            **conversation_to_response(conversation),
            "chat_logs": log_items,
            "route_trace": latest.get("route_trace", []),
            "tool_calls": latest.get("tool_calls", []),
            "retrieved_docs": latest.get("retrieved_docs", []),
            "citations": latest.get("citations", []),
            "evaluation_result": latest.get("evaluation_result", {}),
        }


@router.post("/admin/conversations/{conversation_id}/assign")
def assign_conversation(conversation_id: str, request: AssignRequest):
    with SessionLocal() as db:
        conversation = db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()
        if conversation is None:
            not_found("会话")
        conversation.status = "HUMAN_HANDLING"
        conversation.handoff_status = "ASSIGNED"
        conversation.assigned_agent_id = request.agent_id
        conversation.updated_at = datetime.now()
        db.commit()
        db.refresh(conversation)
        return conversation_to_response(conversation)


@router.post("/admin/conversations/{conversation_id}/reply")
def reply_conversation(conversation_id: str, request: HumanReplyRequest):
    with SessionLocal() as db:
        conversation = db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()
        if conversation is None:
            not_found("会话")
        if not conversation.assigned_agent_id:
            conversation.assigned_agent_id = request.agent_id
        conversation.status = "HUMAN_HANDLING"
        conversation.handoff_status = "ASSIGNED"
        conversation.updated_at = datetime.now()
        history = decode_json(conversation.history, [])
        history.append({"role": "assistant", "sender": "human_agent", "agent_id": request.agent_id, "content": request.message})
        conversation.history = encode_json(history[-50:])
        log = ChatLog(
            conversation_id=conversation_id,
            user_id=conversation.user_id,
            sender="human_agent",
            user_message="",
            final_answer=request.message,
            intent=conversation.current_intent or "HUMAN_TRANSFER",
            confidence=1.0,
            route_trace="[]",
            tool_calls="[]",
            retrieved_docs="[]",
            citations="[]",
            evaluation_result="{}",
            created_at=datetime.now(),
        )
        db.add(log)
        db.commit()
        db.refresh(conversation)
        return conversation_to_response(conversation)


@router.post("/admin/conversations/{conversation_id}/resolve")
def resolve_conversation(conversation_id: str, request: ResolveRequest):
    with SessionLocal() as db:
        conversation = db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()
        if conversation is None:
            not_found("会话")
        conversation.status = "CLOSED"
        conversation.handoff_status = "RESOLVED"
        conversation.assigned_agent_id = request.agent_id
        conversation.updated_at = datetime.now()
        history = decode_json(conversation.history, [])
        history.append({"role": "system", "sender": "system", "content": f"会话已关闭：{request.resolution}"})
        conversation.history = encode_json(history[-50:])
        db.commit()
        db.refresh(conversation)
        return conversation_to_response(conversation)

