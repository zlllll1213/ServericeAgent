from app.tools.customer_tools import create_return_request, create_ticket, get_order_status, get_refund_status


def test_order_tool_success_and_not_found(client):
    ok = get_order_status("10001")
    missing = get_order_status("99999")

    assert ok["success"] is True
    assert ok["data"]["order_id"] == "10001"
    assert ok["error"] is None
    assert missing == {"success": False, "order_id": "99999", "data": None, "error": "订单不存在"}


def test_return_tool_success_expired_and_missing_order(client):
    created = create_return_request("10001", "买错了")
    expired = create_return_request("10003", "买错了")
    missing = create_return_request("99999", "买错了")

    assert created["success"] is True
    assert created["data"]["return_id"].startswith("R")
    assert expired["success"] is False
    assert "不符合" in expired["error"]
    assert missing["success"] is False


def test_ticket_and_refund_status_tools_return_standard_shape(client):
    created = create_return_request("10001", "买错了")
    refund = get_refund_status(created["return_id"])
    missing_refund = get_refund_status("R00000000")
    ticket = create_ticket("U1001", "HUMAN_TRANSFER", "用户要求人工客服", [])

    assert refund["success"] is True
    assert refund["data"]["return_id"] == created["return_id"]
    assert missing_refund["success"] is False
    assert ticket["success"] is True
    assert ticket["data"]["ticket_id"].startswith("T")
