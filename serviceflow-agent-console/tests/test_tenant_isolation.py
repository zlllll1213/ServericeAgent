import pytest

from app.rag.qdrant_retriever import build_qdrant_filter


def test_qdrant_retrieval_contract_carries_tenant_filter():
    qdrant_filter = build_qdrant_filter({"tenant_id": "T1001", "knowledge_base": "policy"})

    assert {"key": "tenant_id", "match": {"value": "T1001"}} in qdrant_filter["must"]
    assert {"key": "knowledge_base", "match": {"value": "policy"}} in qdrant_filter["must"]


@pytest.mark.skip(reason="当前仓库是单租户 SQLite Demo，完整跨 tenant 订单/会话/工单隔离需在多租户分支验证。")
def test_full_tenant_isolation_matrix():
    pass
