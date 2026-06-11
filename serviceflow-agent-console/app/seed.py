from datetime import datetime, timedelta
from pathlib import Path
import sys

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import KNOWLEDGE_BASE_DIR, settings
from app.auth import hash_password
from app.database import Base, SessionLocal, engine
from app.migrations import ensure_schema_updates
from app.models import AdminUser, AgentFeedback, AgentTrace, ChatLog, Conversation, KnowledgeDocument, Order, ReturnRequest, Ticket


def seed_database(reset: bool = False) -> None:
    Base.metadata.create_all(bind=engine)
    ensure_schema_updates()
    db = SessionLocal()
    try:
        if reset:
            for doc in db.query(KnowledgeDocument).all():
                if doc.source_file:
                    path = KNOWLEDGE_BASE_DIR.parent / doc.source_file
                    if path.exists():
                        path.unlink()
            db.query(AgentFeedback).delete()
            db.query(AgentTrace).delete()
            db.query(KnowledgeDocument).delete()
            db.query(ChatLog).delete()
            db.query(Conversation).delete()
            db.query(ReturnRequest).delete()
            db.query(Ticket).delete()
            db.query(AdminUser).delete()
            db.query(Order).delete()
            db.commit()

        if db.query(Order).count() > 0:
            seed_admin_users(db)
            # 订单已存在时仍可能需要回填后台用户 password_hash，必须提交 seed_admin_users 的变更。
            db.commit()
            return

        now = datetime.now()
        orders = [
            Order(
                order_id="10001",
                user_id="U1001",
                product_name="SmartRouter X1",
                status="DELIVERED",
                paid_amount=399,
                created_at=now - timedelta(days=5),
                delivered_at=now - timedelta(days=2),
                can_return=True,
                logistics_info="已签收，签收地点：上海市浦东新区",
            ),
            Order(
                order_id="10002",
                user_id="U1001",
                product_name="SmartCamera C2",
                status="SHIPPED",
                paid_amount=299,
                created_at=now - timedelta(days=3),
                delivered_at=None,
                can_return=False,
                logistics_info="已发货，正在运输中",
            ),
            Order(
                order_id="10003",
                user_id="U1001",
                product_name="SmartRouter X1",
                status="DELIVERED",
                paid_amount=399,
                created_at=now - timedelta(days=20),
                delivered_at=now - timedelta(days=15),
                can_return=False,
                logistics_info="已签收，超过 7 天无理由退货期限",
            ),
        ]
        db.add_all(orders)
        seed_admin_users(db)
        db.commit()
    finally:
        db.close()


def seed_admin_users(db) -> None:
    now = datetime.now()
    # seed 脚本只服务本地演示数据；演示密码在运行时加盐生成，避免源码暴露可复用哈希。
    admin_hash = settings.admin_password_hash or hash_password("admin")
    agent_hash = settings.agent_password_hash or hash_password("agent")
    existing = {user.user_id: user for user in db.query(AdminUser).all()}
    users = []
    if "A1001" not in existing:
        users.append(AdminUser(user_id="A1001", username=settings.admin_username, password_hash=admin_hash, role="admin", created_at=now))
    else:
        existing["A1001"].username = settings.admin_username
        existing["A1001"].password_hash = admin_hash or existing["A1001"].password_hash
    if "S1001" not in existing:
        users.append(AdminUser(user_id="S1001", username=settings.agent_username, password_hash=agent_hash, role="agent", created_at=now))
    else:
        existing["S1001"].username = settings.agent_username
        existing["S1001"].password_hash = agent_hash or existing["S1001"].password_hash
    if users:
        db.add_all(users)


if __name__ == "__main__":
    seed_database(reset=True)
    print("Seeded data/serviceflow.db")
