from datetime import datetime, timedelta
from pathlib import Path
import sys

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import Base, SessionLocal, engine
from app.models import Order, ReturnRequest, Ticket


def seed_database(reset: bool = False) -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if reset:
            db.query(ReturnRequest).delete()
            db.query(Ticket).delete()
            db.query(Order).delete()
            db.commit()

        if db.query(Order).count() > 0:
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
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database(reset=True)
    print("Seeded data/serviceflow.db")
