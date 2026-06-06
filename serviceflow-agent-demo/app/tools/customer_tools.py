from datetime import datetime
import json

from app.database import SessionLocal
from app.models import Order, ReturnRequest, Ticket


def _timestamp_id(prefix: str) -> str:
    return f"{prefix}{datetime.now().strftime('%Y%m%d%H%M%S%f')}"


def get_order_status(order_id: str) -> dict:
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if order is None:
            return {"success": False, "error": "订单不存在", "order_id": order_id}
        data = order.to_dict()
        data["success"] = True
        return data
    finally:
        db.close()


def create_return_request(order_id: str, reason: str) -> dict:
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if order is None:
            return {"success": False, "error": "订单不存在", "order_id": order_id}
        if not order.can_return:
            return {
                "success": False,
                "error": f"订单 {order_id} 当前不符合无理由退货条件：{order.logistics_info}",
                "order_id": order_id,
            }

        existing = db.query(ReturnRequest).filter(ReturnRequest.order_id == order_id).first()
        if existing:
            return {"success": True, "return_id": existing.return_id, "status": existing.status, "order_id": order_id}

        return_request = ReturnRequest(
            return_id=_timestamp_id("R"),
            order_id=order_id,
            reason=reason,
            status="CREATED",
            created_at=datetime.now(),
        )
        db.add(return_request)
        db.commit()
        return {"success": True, "return_id": return_request.return_id, "status": return_request.status, "order_id": order_id}
    finally:
        db.close()


def get_refund_status(return_id: str) -> dict:
    db = SessionLocal()
    try:
        item = db.query(ReturnRequest).filter(ReturnRequest.return_id == return_id).first()
        if item is None:
            return {"success": False, "error": "退货申请不存在", "return_id": return_id}
        data = item.to_dict()
        data["success"] = True
        return data
    finally:
        db.close()


def create_ticket(user_id: str, issue_type: str, summary: str, chat_history: list) -> dict:
    db = SessionLocal()
    try:
        ticket = Ticket(
            ticket_id=_timestamp_id("T"),
            user_id=user_id,
            issue_type=issue_type,
            priority="HIGH" if issue_type in {"COMPLAINT", "HUMAN_TRANSFER"} else "MEDIUM",
            summary=summary,
            chat_history=json.dumps(chat_history, ensure_ascii=False),
            status="OPEN",
            created_at=datetime.now(),
        )
        db.add(ticket)
        db.commit()
        return {"success": True, "ticket_id": ticket.ticket_id, "status": ticket.status, "priority": ticket.priority}
    finally:
        db.close()
