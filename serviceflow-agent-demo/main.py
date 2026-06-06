from pathlib import Path

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.agent.persistence import get_conversation, list_conversation_logs, reset_conversation
from app.agent.graph import run_agent
from app.database import Base, SessionLocal, engine
from app.models import Order, ReturnRequest, Ticket
from app.schemas import ChatLogResponse, ChatRequest, ChatResponse, ConversationResponse, OrderResponse, ReturnResponse, TicketResponse

ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "app" / "web"

# Demo 启动时确保 SQLite 表存在，seed 脚本负责写入演示数据。
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ServiceFlow Agent Demo")
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # 所有客服问题统一进入 LangGraph，便于前端展示完整路由轨迹。
    return run_agent(user_message=request.message, user_id=request.user_id, conversation_id=request.conversation_id)


@app.get("/api/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation_state(conversation_id: str):
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return conversation


@app.get("/api/conversations/{conversation_id}/logs", response_model=list[ChatLogResponse])
def get_conversation_logs(conversation_id: str):
    return list_conversation_logs(conversation_id)


@app.post("/api/conversations/{conversation_id}/reset", response_model=ConversationResponse)
def reset_conversation_state(conversation_id: str):
    conversation = reset_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return conversation


@app.get("/api/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str):
    with SessionLocal() as db:
        # 这个接口用于演示业务数据库直查，不经过 Agent 工作流。
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
