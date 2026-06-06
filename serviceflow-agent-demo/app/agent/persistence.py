from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.database import SessionLocal
from app.models import ChatLog, Conversation


def generate_conversation_id() -> str:
    return f"C{datetime.now().strftime('%Y%m%d%H%M%S%f')}"


def decode_json(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def encode_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def get_or_create_conversation(conversation_id: str | None, user_id: str) -> dict[str, Any]:
    db = SessionLocal()
    try:
        conversation = None
        if conversation_id:
            conversation = db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()

        if conversation is None:
            now = datetime.now()
            conversation = Conversation(
                conversation_id=conversation_id or generate_conversation_id(),
                user_id=user_id,
                current_intent=None,
                pending_action="NONE",
                slots="{}",
                history="[]",
                status="ACTIVE",
                created_at=now,
                updated_at=now,
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        return conversation_to_response(conversation)
    finally:
        db.close()


def save_conversation_state(state: dict[str, Any]) -> dict[str, Any]:
    db = SessionLocal()
    try:
        conversation = db.query(Conversation).filter(Conversation.conversation_id == state["conversation_id"]).first()
        if conversation is None:
            now = datetime.now()
            conversation = Conversation(
                conversation_id=state["conversation_id"],
                user_id=state.get("user_id", "U1001"),
                created_at=now,
                updated_at=now,
            )
            db.add(conversation)

        history = [*state.get("history", [])]
        history.append({"role": "user", "content": state.get("user_message", "")})
        history.append({"role": "assistant", "content": state.get("final_answer", "")})

        # 会话表保存的是下一轮需要恢复的最小业务状态，不保存大段调试证据。
        conversation.user_id = state.get("user_id", conversation.user_id)
        conversation.current_intent = state.get("current_intent") or state.get("intent")
        conversation.pending_action = state.get("pending_action") or "NONE"
        conversation.slots = encode_json(state.get("slots", {}))
        conversation.history = encode_json(history[-20:])
        conversation.status = "ACTIVE"
        conversation.updated_at = datetime.now()
        db.commit()
        db.refresh(conversation)
        return conversation_to_response(conversation)
    finally:
        db.close()


def write_chat_log(state: dict[str, Any]) -> dict[str, Any]:
    db = SessionLocal()
    try:
        log = ChatLog(
            conversation_id=state["conversation_id"],
            user_id=state.get("user_id", "U1001"),
            user_message=state.get("user_message", ""),
            final_answer=state.get("final_answer", ""),
            intent=state.get("intent", "UNKNOWN"),
            confidence=float(state.get("confidence", 0.0)),
            route_trace=encode_json(state.get("route_trace", [])),
            tool_calls=encode_json(state.get("tool_calls", [])),
            retrieved_docs=encode_json(state.get("retrieved_docs", [])),
            citations=encode_json(state.get("citations", [])),
            evaluation_result=encode_json(state.get("evaluation_result", {})),
            created_at=datetime.now(),
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return chat_log_to_response(log)
    finally:
        db.close()


def get_conversation(conversation_id: str) -> dict[str, Any] | None:
    db = SessionLocal()
    try:
        conversation = db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()
        return conversation_to_response(conversation) if conversation else None
    finally:
        db.close()


def list_conversation_logs(conversation_id: str) -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        logs = db.query(ChatLog).filter(ChatLog.conversation_id == conversation_id).order_by(ChatLog.id.asc()).all()
        return [chat_log_to_response(log) for log in logs]
    finally:
        db.close()


def reset_conversation(conversation_id: str) -> dict[str, Any] | None:
    db = SessionLocal()
    try:
        conversation = db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()
        if conversation is None:
            return None
        conversation.current_intent = None
        conversation.pending_action = "NONE"
        conversation.slots = "{}"
        conversation.history = "[]"
        conversation.status = "RESET"
        conversation.updated_at = datetime.now()
        db.commit()
        db.refresh(conversation)
        return conversation_to_response(conversation)
    finally:
        db.close()


def conversation_to_response(conversation: Conversation) -> dict[str, Any]:
    data = conversation.to_dict()
    data["slots"] = decode_json(conversation.slots, {})
    data["history"] = decode_json(conversation.history, [])
    return data


def chat_log_to_response(log: ChatLog) -> dict[str, Any]:
    data = log.to_dict()
    data["route_trace"] = decode_json(log.route_trace, [])
    data["tool_calls"] = decode_json(log.tool_calls, [])
    data["retrieved_docs"] = decode_json(log.retrieved_docs, [])
    data["citations"] = decode_json(log.citations, [])
    data["evaluation_result"] = decode_json(log.evaluation_result, {})
    return data
