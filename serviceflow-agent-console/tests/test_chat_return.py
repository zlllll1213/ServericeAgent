def test_return_request_multiturn_confirm_flow(chat, client):
    first = chat("我要退货")
    second = chat("10001", conversation_id=first["conversation_id"])
    third = chat("买错了", conversation_id=first["conversation_id"])
    final = chat("确认", conversation_id=first["conversation_id"])

    assert second["conversation_id"] == first["conversation_id"]
    assert third["slots"]["return_reason"] == "买错了"
    assert third["pending_action"] == "CREATE_RETURN_REQUEST"
    assert not any(call["name"] == "create_return_request" for call in third["tool_calls"])
    assert final["return_result"]["success"] is True
    assert any(call["name"] == "create_return_request" for call in final["tool_calls"])
    assert client.get("/api/returns").json()[0]["order_id"] == "10001"


def test_return_request_cancel_flow_does_not_create_record(chat, client):
    prepared = chat("我要退货，订单号 10001，原因是买错了")
    cancelled = chat("取消", conversation_id=prepared["conversation_id"])

    assert cancelled["pending_action"] in {None, "NONE"}
    assert "取消" in cancelled["answer"]
    assert client.get("/api/returns").json() == []
