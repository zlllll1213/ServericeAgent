import pytest


client = None
post_chat = None
_admin_headers = None


@pytest.fixture(autouse=True)
def bind_shared_test_helpers(client, admin_headers, chat):
    globals()["client"] = client
    globals()["post_chat"] = chat
    globals()["_admin_headers"] = admin_headers


def admin_get(path: str):
    return client.get(path, headers=_admin_headers)


def admin_post(path: str, payload: dict | None = None):
    return client.post(path, json=payload or {}, headers=_admin_headers)


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


def test_human_handoff_assign_reply_and_resolve_flow():
    data = post_chat("我要找人工客服")
    conversation_id = data["conversation_id"]

    assert data["need_human"] is True
    assert data["ticket_id"].startswith("T")

    conversation = admin_get(f"/api/admin/conversations/{conversation_id}").json()
    assert conversation["status"] == "WAITING_HUMAN"
    assert conversation["handoff_status"] == "REQUESTED"

    assign = admin_post(f"/api/admin/conversations/{conversation_id}/assign", {"agent_id": "S1001"})
    assert assign.status_code == 200
    assert assign.json()["status"] == "HUMAN_HANDLING"
    assert assign.json()["assigned_agent_id"] == "S1001"

    blocked = post_chat("人工客服在吗", conversation_id=conversation_id)
    assert blocked["answer"] == "人工客服正在处理中，请等待客服回复。"
    assert blocked["route_trace"] == [
        "load_conversation_node",
        "human_handoff_node",
        "final_response_node",
        "evaluation_node",
        "save_conversation_node",
    ]
    assert blocked["evaluation_result"]["need_human_review"] is True

    reply = admin_post(
        f"/api/admin/conversations/{conversation_id}/reply",
        {"agent_id": "S1001", "message": "您好，我是人工客服，请问您遇到了什么问题？"},
    )
    assert reply.status_code == 200
    assert reply.json()["history"][-1]["sender"] == "human_agent"

    resolved = admin_post(
        f"/api/admin/conversations/{conversation_id}/resolve",
        {"agent_id": "S1001", "resolution": "已为用户解释退货政策。"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "CLOSED"
    assert resolved.json()["handoff_status"] == "RESOLVED"


def test_admin_ticket_assignment_and_resolution_flow():
    data = post_chat("我要投诉，找人工客服")
    ticket_id = data["ticket_id"]

    tickets = admin_get("/api/admin/tickets").json()
    assert any(ticket["ticket_id"] == ticket_id for ticket in tickets)

    assigned = admin_post(f"/api/admin/tickets/{ticket_id}/assign", {"agent_id": "S1001"})
    assert assigned.status_code == 200
    assert assigned.json()["status"] == "ASSIGNED"
    assert assigned.json()["assigned_agent_id"] == "S1001"

    resolved = admin_post(
        f"/api/admin/tickets/{ticket_id}/resolve",
        {"agent_id": "S1001", "resolution": "已联系用户并解决问题。"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "RESOLVED"
    assert resolved.json()["resolution"] == "已联系用户并解决问题。"

    closed = admin_post(f"/api/admin/tickets/{ticket_id}/close")
    assert closed.status_code == 200
    assert closed.json()["status"] == "CLOSED"


def test_knowledge_document_publish_is_retrievable_and_cited():
    created = client.post(
        "/api/admin/knowledge-documents",
        json={
            "title": "延保服务政策",
            "knowledge_base": "policy",
            "content": "SmartRouter X1 支持购买 1 年延保服务，延保期内非人为损坏可免费维修。",
        },
        headers=_admin_headers,
    )
    assert created.status_code == 200
    doc_id = created.json()["doc_id"]
    assert created.json()["status"] == "DRAFT"

    published = admin_post(f"/api/admin/knowledge-documents/{doc_id}/publish")
    assert published.status_code == 200
    assert published.json()["status"] == "PUBLISHED"

    answer = post_chat("SmartRouter X1 有延保服务吗？")
    assert answer["intent"] in {"POLICY_QA", "PRODUCT_QA"}
    assert any(citation["source_file"] == f"{doc_id}.md" for citation in answer["citations"])
    assert "延保" in answer["answer"]


def test_feedback_and_evaluation_summary_update():
    data = post_chat("7 天无理由退货规则是什么")
    logs = client.get(f"/api/conversations/{data['conversation_id']}/logs").json()
    chat_log_id = logs[-1]["id"]

    feedback = client.post(
        "/api/feedback",
        json={
            "conversation_id": data["conversation_id"],
            "chat_log_id": chat_log_id,
            "user_id": "U1001",
            "rating": 2,
            "feedback_type": "WRONG_INTENT",
            "comment": "用户问的是售后政策，但系统路由到了产品咨询。",
        },
    )
    assert feedback.status_code == 200
    assert feedback.json()["feedback_type"] == "WRONG_INTENT"

    feedback_list = admin_get("/api/admin/feedback").json()
    assert feedback_list[0]["feedback_type"] == "WRONG_INTENT"

    summary = admin_get("/api/admin/evaluation-summary").json()
    assert summary["total_chats"] >= 1
    assert summary["negative_feedback_count"] == 1
    assert summary["top_error_types"][0]["type"] == "WRONG_INTENT"


def test_auth_health_trace_and_metrics_smoke():
    login = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    bad_login = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert bad_login.status_code == 401

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["role"] == "admin"

    unauthorized = client.get("/api/admin/conversations")
    assert unauthorized.status_code == 401

    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    data = post_chat("我要退货，订单号 10001，原因是买错了")
    traces = admin_get(f"/api/admin/traces?trace_id={data['trace_id']}").json()
    assert {trace["node_name"] for trace in traces} >= {"load_conversation_node", "slot_filling_node"}

    chain = admin_get(f"/api/admin/traces/{data['trace_id']}").json()
    assert chain["trace_id"] == data["trace_id"]
    assert chain["nodes"][0]["input_state"]

    metrics = admin_get("/api/admin/metrics/overview").json()
    assert metrics["total_chats_today"] >= 1
    assert "intent_distribution" in metrics
    assert "tool_success_rate" in metrics
