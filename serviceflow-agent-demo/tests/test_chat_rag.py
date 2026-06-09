def test_rag_questions_route_to_expected_knowledge_base(chat):
    cases = [
        ("路由器无法连接 WiFi 怎么办？", "TECH_SUPPORT", "tech"),
        ("7 天无理由退货规则是什么？", "POLICY_QA", "policy"),
        ("SmartRouter X1 支持 macOS 吗？", "PRODUCT_QA", "product"),
    ]

    for message, intent, knowledge_base in cases:
        data = chat(message)
        assert data["intent"] == intent
        assert "rag_node" in data["route_trace"]
        assert data["retrieved_docs"]
        assert data["retrieved_docs"][0]["knowledge_base"] == knowledge_base
        assert data["citations"]
        assert "根据我的猜测" not in data["answer"]
