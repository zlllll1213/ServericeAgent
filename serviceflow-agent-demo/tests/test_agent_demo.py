from fastapi.testclient import TestClient

from app.seed import seed_database
from main import app


client = TestClient(app)


def setup_function():
    seed_database(reset=True)


def post_chat(message: str, conversation_id: str | None = None):
    response = client.post(
        "/api/chat",
        json={"message": message, "user_id": "U1001", "conversation_id": conversation_id},
    )
    assert response.status_code == 200
    return response.json()


def test_order_query_returns_sqlite_order_and_trace():
    data = post_chat("帮我查一下订单 10001 到哪里了")

    assert data["intent"] == "ORDER_QUERY"
    assert "order_query_node" in data["route_trace"]
    assert data["order_info"]["order_id"] == "10001"
    assert "已签收" in data["answer"]
    assert data["tool_calls"][0]["name"] == "get_order_status"
    assert data["conversation_id"].startswith("C")
    assert data["evaluation_result"]["answer_relevance"] > 0
    assert "route_debug" in data


def test_multiturn_return_request_creates_return_only_after_confirmation():
    first = post_chat("我要退货")
    conversation_id = first["conversation_id"]

    assert first["intent"] == "RETURN_REQUEST"
    assert first["slots"]["order_id"] is None
    assert first["missing_slots"] == ["order_id"]
    assert first["awaiting_user_input"] is True
    assert first["pending_action"] in {None, "NONE"}
    assert not any(call["name"] == "create_return_request" for call in first["tool_calls"])

    second = post_chat("10001", conversation_id=conversation_id)
    assert second["conversation_id"] == conversation_id
    assert second["slots"]["order_id"] == "10001"
    assert second["missing_slots"] == ["return_reason"]
    assert "退货原因" in second["answer"]

    third = post_chat("买错了", conversation_id=conversation_id)
    assert third["conversation_id"] == conversation_id
    assert third["slots"]["return_reason"] == "买错了"
    assert third["pending_action"] == "CREATE_RETURN_REQUEST"
    assert third["awaiting_user_input"] is True
    assert "确认创建退货申请" in third["answer"]
    assert any(call["name"] == "get_order_status" for call in third["tool_calls"])
    assert not any(call["name"] == "create_return_request" for call in third["tool_calls"])

    final = post_chat("确认", conversation_id=conversation_id)
    assert final["conversation_id"] == conversation_id
    assert final["pending_action"] in {None, "NONE"}
    assert final["return_result"]["success"] is True
    assert final["return_result"]["return_id"].startswith("R")
    assert any(call["name"] == "create_return_request" for call in final["tool_calls"])
    assert "confirm_node" in final["route_trace"]
    assert "tool_execute_node" in final["route_trace"]


def test_cancel_return_request_does_not_create_return_record():
    prepared = post_chat("我要退货，订单号 10001，原因是买错了")
    conversation_id = prepared["conversation_id"]
    assert prepared["pending_action"] == "CREATE_RETURN_REQUEST"
    assert not any(call["name"] == "create_return_request" for call in prepared["tool_calls"])

    cancelled = post_chat("取消", conversation_id=conversation_id)
    assert cancelled["conversation_id"] == conversation_id
    assert cancelled["pending_action"] in {None, "NONE"}
    assert "取消" in cancelled["answer"]
    assert not any(call["name"] == "create_return_request" for call in cancelled["tool_calls"])

    returns = client.get("/api/returns").json()
    assert returns == []


def test_return_request_rejects_expired_order_before_confirmation():
    data = post_chat("我要退货，订单号 10003，原因是买错了")

    assert data["intent"] == "RETURN_REQUEST"
    assert data["return_result"]["success"] is False
    assert data["pending_action"] in {None, "NONE"}
    assert "超过" in data["answer"]


def test_tech_policy_and_product_questions_retrieve_expected_kbs():
    tech = post_chat("路由器怎么连接 WiFi")
    policy = post_chat("7 天无理由退货规则是什么")
    product = post_chat("SmartRouter X1 支持 macOS 吗")

    assert tech["intent"] == "TECH_SUPPORT"
    assert tech["retrieved_docs"][0]["knowledge_base"] == "tech"
    assert "source_file" in tech["retrieved_docs"][0]
    assert "score" in tech["retrieved_docs"][0]
    assert tech["citations"][0]["source_file"] == "smart_router_wifi.md"
    assert "WiFi" in tech["answer"]

    assert policy["intent"] == "POLICY_QA"
    assert policy["retrieved_docs"][0]["knowledge_base"] == "policy"
    assert policy["retrieved_docs"][0]["category"] in {"return_policy", "warranty_policy"}
    assert policy["citations"][0]["source_file"] == "return_policy.md"
    assert "7" in policy["answer"]

    assert product["intent"] == "PRODUCT_QA"
    assert product["retrieved_docs"][0]["knowledge_base"] == "product"
    assert product["retrieved_docs"][0]["product_name"] == "SmartRouter X1"
    assert "macOS" in product["answer"]


def test_complaint_creates_human_ticket():
    data = post_chat("我要投诉，转人工客服")

    assert data["intent"] in {"COMPLAINT", "HUMAN_TRANSFER"}
    assert data["need_human"] is True
    assert data["ticket_id"].startswith("T")
    assert "human_ticket_node" in data["route_trace"]
    assert data["tool_calls"][0]["output"]["priority"] == "HIGH"
    assert data["tool_calls"][0]["output"]["summary"]


def test_unknown_intent_asks_for_clarification():
    data = post_chat("今天有什么推荐")

    assert data["intent"] == "UNKNOWN"
    assert "clarify_node" in data["route_trace"]
    assert "补充" in data["answer"]


def test_retrieval_filters_are_derived_from_intent_and_product_name():
    from app.rag.service import metadata_filter_for_intent

    product_filter = metadata_filter_for_intent("PRODUCT_QA", "SmartRouter X1 支持 macOS 吗")
    tech_filter = metadata_filter_for_intent("TECH_SUPPORT", "路由器怎么连接 WiFi")

    assert product_filter["knowledge_base"] == "product"
    assert product_filter["product_name"] == "SmartRouter X1"
    assert tech_filter["knowledge_base"] == "tech"


def test_qdrant_fallback_keeps_demo_working_without_qdrant(monkeypatch):
    from app.rag import service

    class BrokenQdrantRetriever:
        def retrieve(self, *args, **kwargs):
            raise service.RetrieverUnavailable("qdrant offline")

    monkeypatch.setattr(service, "QdrantRetriever", lambda: BrokenQdrantRetriever())

    docs = service.retrieve_documents("7 天无理由退货规则是什么", intent="POLICY_QA", top_k=1)

    assert docs
    assert docs[0]["knowledge_base"] == "policy"
    assert docs[0]["retriever"] == "simple_fallback"


def test_conversation_logs_include_trace_tools_and_evaluation():
    first = post_chat("我要退货")
    conversation_id = first["conversation_id"]
    post_chat("10001", conversation_id=conversation_id)
    post_chat("买错了", conversation_id=conversation_id)

    conversation = client.get(f"/api/conversations/{conversation_id}")
    assert conversation.status_code == 200
    assert conversation.json()["slots"]["order_id"] == "10001"

    logs = client.get(f"/api/conversations/{conversation_id}/logs")
    assert logs.status_code == 200
    body = logs.json()
    assert len(body) == 3
    assert body[-1]["route_trace"]
    assert "tool_calls" in body[-1]
    assert body[-1]["evaluation_result"]["need_human_review"] is False

    reset = client.post(f"/api/conversations/{conversation_id}/reset")
    assert reset.status_code == 200
    assert reset.json()["status"] == "RESET"
