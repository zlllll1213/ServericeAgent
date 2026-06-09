def test_agent_trace_records_each_node_for_chat(chat, client, admin_headers):
    data = chat("我要退货，订单号 10001，原因是买错了")

    traces = client.get(f"/api/admin/traces?trace_id={data['trace_id']}", headers=admin_headers)
    assert traces.status_code == 200
    nodes = {item["node_name"] for item in traces.json()}
    assert {"load_conversation_node", "parse_input_node", "slot_filling_node"} <= nodes

    chain = client.get(f"/api/admin/traces/{data['trace_id']}", headers=admin_headers).json()
    assert chain["nodes"][0]["input_state"]
    assert "password" not in str(chain["nodes"][0]["input_state"]).lower()
