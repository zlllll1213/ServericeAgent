from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from app.admin_routes.common import not_found, ticket_response
from app.database import SessionLocal
from app.models import Ticket
from app.schemas import AssignRequest, ResolveRequest

router = APIRouter()


@router.get("/admin/tickets")
def list_admin_tickets(status: str | None = None, priority: str | None = None, assigned_agent_id: str | None = None):
    with SessionLocal() as db:
        query = db.query(Ticket)
        if status:
            query = query.filter(Ticket.status == status)
        if priority:
            query = query.filter(Ticket.priority == priority)
        if assigned_agent_id:
            query = query.filter(Ticket.assigned_agent_id == assigned_agent_id)
        return [ticket_response(ticket) for ticket in query.order_by(Ticket.id.desc()).all()]


@router.get("/admin/tickets/{ticket_id}")
def get_admin_ticket(ticket_id: str):
    with SessionLocal() as db:
        ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        if ticket is None:
            not_found("工单")
        return ticket_response(ticket)


@router.post("/admin/tickets/{ticket_id}/assign")
def assign_ticket(ticket_id: str, request: AssignRequest):
    with SessionLocal() as db:
        ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        if ticket is None:
            not_found("工单")
        ticket.status = "ASSIGNED"
        ticket.assigned_agent_id = request.agent_id
        ticket.updated_at = datetime.now()
        db.commit()
        db.refresh(ticket)
        return ticket_response(ticket)


@router.post("/admin/tickets/{ticket_id}/resolve")
def resolve_ticket(ticket_id: str, request: ResolveRequest):
    with SessionLocal() as db:
        ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        if ticket is None:
            not_found("工单")
        ticket.status = "RESOLVED"
        ticket.assigned_agent_id = request.agent_id
        ticket.resolution = request.resolution
        ticket.updated_at = datetime.now()
        db.commit()
        db.refresh(ticket)
        return ticket_response(ticket)


@router.post("/admin/tickets/{ticket_id}/close")
def close_ticket(ticket_id: str):
    with SessionLocal() as db:
        ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        if ticket is None:
            not_found("工单")
        ticket.status = "CLOSED"
        ticket.updated_at = datetime.now()
        db.commit()
        db.refresh(ticket)
        return ticket_response(ticket)
