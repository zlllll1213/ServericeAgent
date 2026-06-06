from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.agent.graph import run_agent
from app.database import Base, SessionLocal, engine
from app.models import Order, ReturnRequest, Ticket
from app.schemas import ChatRequest, ChatResponse, OrderResponse, ReturnResponse, TicketResponse

ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "app" / "web"

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ServiceFlow Agent Demo")
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    return run_agent(user_message=request.message, user_id=request.user_id)


@app.get("/api/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str):
    with SessionLocal() as db:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if order is None:
            return {"error": "订单不存在", "order_id": order_id}
        return order.to_dict()


@app.get("/api/tickets", response_model=list[TicketResponse])
def list_tickets():
    with SessionLocal() as db:
        tickets = db.query(Ticket).order_by(Ticket.id.desc()).all()
        return [ticket.to_dict() for ticket in tickets]


@app.get("/api/returns", response_model=list[ReturnResponse])
def list_returns():
    with SessionLocal() as db:
        returns = db.query(ReturnRequest).order_by(ReturnRequest.id.desc()).all()
        return [item.to_dict() for item in returns]
