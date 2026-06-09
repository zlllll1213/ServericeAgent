from app.rag.qdrant_retriever import build_qdrant_filter
from app.rag.retriever import SimpleRetriever
from app.rag.service import metadata_filter_for_intent


def test_simple_retriever_loads_local_knowledge_base(client):
    docs = SimpleRetriever().retrieve("SmartRouter X1 支持 macOS 吗", "product", top_k=3)

    assert docs
    assert docs[0]["source_file"]
    assert "chunk_id" in docs[0]
    assert docs == sorted(docs, key=lambda item: item["score"], reverse=True)


def test_simple_retriever_empty_query_returns_no_results(client):
    docs = SimpleRetriever().retrieve("zzzxxyyqq", "unknown", top_k=3)

    assert docs == []


def test_qdrant_filters_include_tenant_and_knowledge_base():
    filters = metadata_filter_for_intent("PRODUCT_QA", "SmartRouter X1 支持 macOS 吗")
    qdrant_filter = build_qdrant_filter({**filters, "tenant_id": "T1001"})

    keys = {item["key"] for item in qdrant_filter["must"]}
    assert {"knowledge_base", "product_name", "tenant_id"} <= keys
