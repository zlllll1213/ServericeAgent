from typing import Any

from app.agent.intents import Intent
from app.config import settings
from app.rag.qdrant_retriever import QdrantRetriever, QdrantUnavailable
from app.rag.retriever import SimpleRetriever


RetrieverUnavailable = QdrantUnavailable

INTENT_KB = {
    Intent.TECH_SUPPORT.value: "tech",
    Intent.POLICY_QA.value: "policy",
    Intent.PRODUCT_QA.value: "product",
}


def metadata_filter_for_intent(intent: str, query: str) -> dict[str, Any]:
    # 用意图决定知识库分区，避免技术问题检索到政策或产品资料。
    filters: dict[str, Any] = {"knowledge_base": INTENT_KB.get(intent)}
    product_name = product_name_from_query(query)
    # 对明确产品的问题追加产品过滤，提升 Qdrant 命中的可解释性。
    if product_name and intent in {Intent.PRODUCT_QA.value, Intent.TECH_SUPPORT.value}:
        filters["product_name"] = product_name
    return {key: value for key, value in filters.items() if value}


def product_name_from_query(query: str) -> str | None:
    lowered = query.lower()
    if "smartrouter x1" in lowered or "路由器" in lowered:
        return "SmartRouter X1"
    if "smartcamera c2" in lowered or "摄像头" in lowered:
        return "SmartCamera C2"
    return None


def retrieve_documents(query: str, intent: str, top_k: int = 3) -> list[dict]:
    filters = metadata_filter_for_intent(intent, query)
    knowledge_base = filters.get("knowledge_base", "tech")

    if settings.qdrant_enabled:
        try:
            # Qdrant 是主检索器；失败时不抛给用户，保持 Demo 离线可跑。
            qdrant_docs = QdrantRetriever().retrieve(
                query=query,
                knowledge_base=knowledge_base,
                top_k=top_k,
                metadata_filter=filters,
            )
            if qdrant_docs:
                return qdrant_docs
        except QdrantUnavailable:
            pass

    # Qdrant 可用但尚未索引时会返回空结果，此时继续用本地知识库兜底。
    docs = SimpleRetriever().retrieve(query=query, knowledge_base=knowledge_base, top_k=top_k)
    # 标记 fallback 来源，调试面板能看出当前走的是哪条检索路径。
    return [{**doc, "retriever": "simple_fallback"} for doc in docs]
