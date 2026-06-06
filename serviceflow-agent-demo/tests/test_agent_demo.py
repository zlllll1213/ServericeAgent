from fastapi.testclient import TestClient

from app.seed import seed_database
from main import app


client = TestClient(app)


def setup_function():
    seed_database(reset=True)


def post_chat(message: str):
    response = client.post("/api/chat", json={"message": message, "user_id": "U1001"})
    assert response.status_code == 200
    return response.json()


def test_order_query_returns_sqlite_order_and_trace():
    data = post_chat("帮我查一下订单 10001 到哪里了")

    assert data["intent"] == "ORDER_QUERY"
    assert "order_query_node" in data["route_trace"]
    assert data["order_info"]["order_id"] == "10001"
    assert "已签收" in data["answer"]
    assert data["tool_calls"][0]["name"] == "get_order_status"


def test_return_request_creates_return_for_eligible_order():
    data = post_chat("我要退货，订单号 10001")

    assert data["intent"] == "RETURN_REQUEST"
    assert "return_request_node" in data["route_trace"]
    assert data["return_result"]["success"] is True
    assert data["return_result"]["return_id"].startswith("R")
    assert any(call["name"] == "create_return_request" for call in data["tool_calls"])


def test_return_request_rejects_expired_order():
    data = post_chat("我要退货，订单号 10003")

    assert data["intent"] == "RETURN_REQUEST"
    assert data["return_result"]["success"] is False
    assert "超过" in data["answer"]


def test_tech_policy_and_product_questions_retrieve_expected_kbs():
    tech = post_chat("路由器怎么连接 WiFi")
    policy = post_chat("7 天无理由退货规则是什么")
    product = post_chat("SmartRouter X1 支持 macOS 吗")

    assert tech["intent"] == "TECH_SUPPORT"
    assert tech["retrieved_docs"][0]["knowledge_base"] == "tech"
    assert "WiFi" in tech["answer"]

    assert policy["intent"] == "POLICY_QA"
    assert policy["retrieved_docs"][0]["knowledge_base"] == "policy"
    assert "7" in policy["answer"]

    assert product["intent"] == "PRODUCT_QA"
    assert product["retrieved_docs"][0]["knowledge_base"] == "product"
    assert "macOS" in product["answer"]


def test_complaint_creates_human_ticket():
    data = post_chat("我要投诉，转人工客服")

    assert data["intent"] in {"COMPLAINT", "HUMAN_TRANSFER"}
    assert data["need_human"] is True
    assert data["ticket_id"].startswith("T")
    assert "human_ticket_node" in data["route_trace"]


def test_unknown_intent_asks_for_clarification():
    data = post_chat("今天有什么推荐")

    assert data["intent"] == "UNKNOWN"
    assert "clarify_node" in data["route_trace"]
    assert "补充" in data["answer"]
