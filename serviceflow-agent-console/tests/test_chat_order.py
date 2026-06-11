def test_order_query_calls_order_tool_without_rag(chat):
    data = chat("帮我查一下订单 10001 到哪里了")

    assert data["intent"] == "ORDER_QUERY"
    assert "order_query_node" in data["route_trace"]
    assert data["tool_calls"][0]["name"] == "get_order_status"
    assert data["tool_calls"][0]["output"]["success"] is True
    assert "已签收" in data["answer"]
    assert data["retrieved_docs"] == []
    assert data["ticket_id"] is None
