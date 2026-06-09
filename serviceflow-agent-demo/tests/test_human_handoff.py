def test_handoff_assign_reply_then_user_sees_human_message(chat, client, admin_headers):
    created = chat("我要投诉，找人工客服")
    conversation_id = created["conversation_id"]

    assert created["ticket_id"].startswith("T")
    detail = client.get(f"/api/admin/conversations/{conversation_id}", headers=admin_headers).json()
    assert detail["status"] == "WAITING_HUMAN"
    assert detail["handoff_status"] == "REQUESTED"

    assigned = client.post(
        f"/api/admin/conversations/{conversation_id}/assign",
        json={"agent_id": "S1001"},
        headers=admin_headers,
    )
    assert assigned.json()["status"] == "HUMAN_HANDLING"

    blocked = chat("有人在吗", conversation_id=conversation_id)
    assert blocked["route_trace"] == [
        "load_conversation_node",
        "human_handoff_node",
        "final_response_node",
        "evaluation_node",
        "save_conversation_node",
    ]
    assert blocked["evaluation_result"]["need_human_review"] is True
    assert blocked["answer"] == "人工客服正在处理中，请等待客服回复。"

    replied = client.post(
        f"/api/admin/conversations/{conversation_id}/reply",
        json={"agent_id": "S1001", "message": "您好，我是人工客服，请问您遇到了什么问题？"},
        headers=admin_headers,
    )
    assert replied.status_code == 200
    assert replied.json()["history"][-1]["sender"] == "human_agent"
