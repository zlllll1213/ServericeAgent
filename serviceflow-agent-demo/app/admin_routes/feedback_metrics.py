from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Query
from sqlalchemy import func

from app.admin_routes.common import avg_node_latency, percentile, request_latencies
from app.agent.persistence import chat_log_to_response, decode_json
from app.database import SessionLocal
from app.models import AgentFeedback, AgentTrace, ChatLog, Conversation
from app.schemas import FeedbackRequest

router = APIRouter()


@router.post("/feedback")
def create_feedback(request: FeedbackRequest):
    with SessionLocal() as db:
        feedback = AgentFeedback(
            conversation_id=request.conversation_id,
            chat_log_id=request.chat_log_id,
            user_id=request.user_id,
            rating=request.rating,
            feedback_type=request.feedback_type,
            comment=request.comment,
            created_at=datetime.now(),
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback.to_dict()


@router.get("/admin/feedback")
def list_feedback():
    with SessionLocal() as db:
        rows = db.query(AgentFeedback).order_by(AgentFeedback.id.desc()).all()
        return [row.to_dict() for row in rows]


@router.get("/admin/evaluation-summary")
def evaluation_summary(days: int = Query(default=7, ge=1, le=90)):
    with SessionLocal() as db:
        since = datetime.now() - timedelta(days=days)
        logs = db.query(ChatLog.evaluation_result).filter(ChatLog.created_at >= since).all()
        total = db.query(func.count(ChatLog.id)).filter(ChatLog.created_at >= since).scalar() or 0

        def avg(key: str) -> float:
            values = []
            for log in logs:
                result = decode_json(log.evaluation_result, {})
                if key in result:
                    values.append(float(result[key]))
            return round(sum(values) / len(values), 3) if values else 0.0

        human_transfers = db.query(func.count(Conversation.id)).filter(Conversation.handoff_status != "NONE", Conversation.updated_at >= since).scalar() or 0
        negative_filter = (AgentFeedback.rating <= 2) | (AgentFeedback.feedback_type != "GOOD")
        negative_count = db.query(func.count(AgentFeedback.id)).filter(AgentFeedback.created_at >= since, negative_filter).scalar() or 0
        top_rows = (
            db.query(AgentFeedback.feedback_type, func.count(AgentFeedback.id))
            .filter(AgentFeedback.created_at >= since, negative_filter)
            .group_by(AgentFeedback.feedback_type)
            .order_by(func.count(AgentFeedback.id).desc())
            .limit(5)
            .all()
        )
        top = [{"type": row[0], "count": row[1]} for row in top_rows]
        return {
            "total_chats": total,
            "avg_intent_correctness": avg("intent_correctness"),
            "avg_answer_relevance": avg("answer_relevance"),
            "avg_tool_call_correctness": avg("tool_call_correctness"),
            "human_transfer_rate": round(human_transfers / total, 3) if total else 0.0,
            "negative_feedback_count": negative_count,
            "top_error_types": top,
            "window_days": days,
        }


@router.get("/admin/chat-logs")
def list_admin_chat_logs(limit: int = Query(default=50, ge=1, le=200)):
    with SessionLocal() as db:
        logs = db.query(ChatLog).order_by(ChatLog.id.desc()).limit(limit).all()
        return [chat_log_to_response(log) for log in logs]


@router.get("/admin/metrics/overview")
def metrics_overview(days: int = Query(default=7, ge=1, le=90)):
    with SessionLocal() as db:
        today_start = datetime.combine(datetime.now().date(), datetime.min.time())
        since = datetime.now() - timedelta(days=days)
        total_chats_today = db.query(func.count(ChatLog.id)).filter(ChatLog.created_at >= today_start).scalar() or 0
        traces = db.query(AgentTrace).filter(AgentTrace.created_at >= since).all()
        logs_for_tools = db.query(ChatLog.intent, ChatLog.tool_calls).filter(ChatLog.created_at >= since).all()
        trace_latencies = request_latencies(traces)
        p95 = percentile(trace_latencies, 0.95)
        tool_calls = [call for log in logs_for_tools for call in decode_json(log.tool_calls, [])]
        tool_success = [bool((call.get("output") or {}).get("success", True)) for call in tool_calls]
        errors = [trace for trace in traces if not trace.success]
        intent_rows = (
            db.query(ChatLog.intent, func.count(ChatLog.id))
            .filter(ChatLog.created_at >= since)
            .group_by(ChatLog.intent)
            .all()
        )
        conversation_count = db.query(func.count(Conversation.id)).filter(Conversation.updated_at >= since).scalar() or 0
        human_transfers = (
            db.query(func.count(Conversation.id))
            .filter(Conversation.updated_at >= since, Conversation.handoff_status != "NONE")
            .scalar()
            or 0
        )
        feedback_count = db.query(func.count(AgentFeedback.id)).filter(AgentFeedback.created_at >= since).scalar() or 0
        negative_feedback_count = (
            db.query(func.count(AgentFeedback.id))
            .filter(AgentFeedback.created_at >= since, (AgentFeedback.rating <= 2) | (AgentFeedback.feedback_type != "GOOD"))
            .scalar()
            or 0
        )

        return {
            "total_chats_today": total_chats_today,
            "avg_latency_ms": round(sum(trace_latencies) / len(trace_latencies), 3) if trace_latencies else 0,
            "p95_latency_ms": p95,
            "intent_distribution": {row[0]: row[1] for row in intent_rows},
            "tool_call_count": len(tool_calls),
            "tool_success_rate": round(sum(tool_success) / len(tool_success), 3) if tool_success else 1.0,
            "rag_avg_latency_ms": avg_node_latency(traces, "rag_node"),
            "human_transfer_rate": round(human_transfers / conversation_count, 3) if conversation_count else 0,
            "negative_feedback_rate": round(negative_feedback_count / feedback_count, 3) if feedback_count else 0,
            "error_rate": round(len(errors) / len(traces), 3) if traces else 0,
            "window_days": days,
        }


@router.get("/admin/metrics/daily")
def metrics_daily():
    with SessionLocal() as db:
        start = datetime.now().date() - timedelta(days=6)
        since = datetime.combine(start, datetime.min.time())
        buckets = {start + timedelta(days=i): {"date": (start + timedelta(days=i)).isoformat(), "chats": 0, "errors": 0} for i in range(7)}
        log_rows = db.query(func.date(ChatLog.created_at), func.count(ChatLog.id)).filter(ChatLog.created_at >= since).group_by(func.date(ChatLog.created_at)).all()
        for day_value, count in log_rows:
            day = datetime.fromisoformat(str(day_value)).date()
            if day in buckets:
                buckets[day]["chats"] = count
        error_rows = (
            db.query(func.date(AgentTrace.created_at), func.count(AgentTrace.id))
            .filter(AgentTrace.created_at >= since, AgentTrace.success == False)  # noqa: E712
            .group_by(func.date(AgentTrace.created_at))
            .all()
        )
        for day_value, count in error_rows:
            day = datetime.fromisoformat(str(day_value)).date()
            if day in buckets:
                buckets[day]["errors"] = count
        return list(buckets.values())

