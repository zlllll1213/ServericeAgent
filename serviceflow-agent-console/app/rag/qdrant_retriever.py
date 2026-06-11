from __future__ import annotations

import uuid
from dataclasses import asdict
from time import sleep
from typing import Any
from urllib.parse import quote

import httpx

from app.config import settings
from app.rag.embeddings import HashEmbedding
from app.rag.loader import KnowledgeDocument, load_documents


class QdrantUnavailable(RuntimeError):
    pass


class QdrantRestClient:
    """Qdrant REST 客户端，使用 httpx 复用连接并统一超时错误。"""

    def __init__(self, url: str | None = None, api_key: str | None = None, timeout: float | None = None, client: httpx.Client | None = None):
        self.url = (url or settings.qdrant_url).rstrip("/")
        self.api_key = api_key or settings.qdrant_api_key
        self.timeout = timeout if timeout is not None else settings.qdrant_timeout_seconds
        # Qdrant 是本地/显式配置的内部服务，禁用环境代理可避免系统代理变量污染离线演示和测试。
        self.client = client or httpx.Client(timeout=self.timeout, trust_env=False)

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["api-key"] = self.api_key
        try:
            response = self.client.request(method, f"{self.url}{path}", json=body, headers=headers)
            if response.status_code == 404:
                return {"status": "not_found"}
            response.raise_for_status()
            return response.json() if response.content else {}
        except httpx.HTTPStatusError as exc:
            raise QdrantUnavailable(f"Qdrant HTTP {exc.response.status_code}: {exc.response.text}") from exc
        except httpx.HTTPError as exc:
            raise QdrantUnavailable(str(exc)) from exc


class QdrantRetriever:
    def __init__(self, client: QdrantRestClient | None = None, embedder: HashEmbedding | None = None):
        self.client = client or QdrantRestClient()
        self.embedder = embedder or HashEmbedding()
        self.collection_name = settings.qdrant_collection

    def retrieve(
        self,
        query: str,
        knowledge_base: str,
        top_k: int = 3,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict]:
        # Qdrant payload filter 保证检索只在对应知识库和产品范围内发生。
        query_filter = build_qdrant_filter({**(metadata_filter or {}), "knowledge_base": knowledge_base})
        body = {
            "query": self.embedder.embed(query),
            "filter": query_filter,
            "limit": top_k,
            "with_payload": True,
        }
        result = self.client.request("POST", f"/collections/{quote(self.collection_name)}/points/query", body)
        points = result.get("result", {}).get("points", result.get("result", []))
        docs = []
        for point in points:
            payload = point.get("payload") or {}
            # 返回结构与 SimpleRetriever 保持一致，前端和回答生成无需关心来源。
            docs.append(
                {
                    "knowledge_base": payload.get("knowledge_base"),
                    "source": payload.get("source_file"),
                    "source_file": payload.get("source_file"),
                    "chunk_id": f"{payload.get('category', 'doc')}_{int(payload.get('chunk_index', 0)) + 1:03d}",
                    "title": payload.get("title"),
                    "score": round(float(point.get("score", 0)), 4),
                    "product_name": payload.get("product_name", "通用"),
                    "category": payload.get("category", "general"),
                    "snippet": payload.get("chunk_text", ""),
                    "retriever": "qdrant",
                }
            )
        return docs


def build_qdrant_filter(metadata_filter: dict[str, Any]) -> dict[str, Any]:
    # REST API 的 filter DSL：must 内每个条件都是 payload 字段精确匹配。
    conditions = []
    for key, value in metadata_filter.items():
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            conditions.append({"key": key, "match": {"any": list(value)}})
        else:
            conditions.append({"key": key, "match": {"value": value}})
    return {"must": conditions}


def collection_exists(client: QdrantRestClient, collection_name: str) -> bool:
    response = client.request("GET", f"/collections/{quote(collection_name)}")
    return response.get("status") != "not_found"


def ensure_collection(client: QdrantRestClient | None = None) -> QdrantRestClient:
    qdrant = client or QdrantRestClient()
    if not collection_exists(qdrant, settings.qdrant_collection):
        qdrant.request(
            "PUT",
            f"/collections/{quote(settings.qdrant_collection)}",
            {"vectors": {"size": settings.qdrant_vector_size, "distance": "Cosine"}},
        )
    return qdrant


def document_payload(doc: KnowledgeDocument, chunk_text: str, chunk_index: int) -> dict[str, Any]:
    # payload 既保留文档级 metadata，也保留 chunk 信息用于调试和溯源。
    payload = asdict(doc)
    payload.update(
        {
            "source": doc.source_file,
            "chunk_text": chunk_text,
            "chunk_index": chunk_index,
        }
    )
    return payload


def chunk_document(content: str, max_chars: int = 700) -> list[str]:
    # 第一版按段落合并切块，保持 chunk 可读；后续可替换为 token-aware splitter。
    paragraphs = [paragraph.strip() for paragraph in content.split("\n\n") if paragraph.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        next_value = f"{current}\n\n{paragraph}".strip()
        if current and len(next_value) > max_chars:
            chunks.append(current)
            current = paragraph
        else:
            current = next_value
    if current:
        chunks.append(current)
    return chunks


def index_knowledge_base(reset: bool = False) -> int:
    client = QdrantRestClient()
    wait_for_qdrant(client)
    if reset and collection_exists(client, settings.qdrant_collection):
        client.request("DELETE", f"/collections/{quote(settings.qdrant_collection)}")
    ensure_collection(client)

    embedder = HashEmbedding()
    points = []
    for doc in load_documents():
        for chunk_index, chunk_text in enumerate(chunk_document(doc.content)):
            # 使用稳定 UUID，重复索引同一文件不会生成重复点。
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc.source_file}:{chunk_index}"))
            points.append(
                {
                    "id": point_id,
                    "vector": embedder.embed(f"{doc.title}\n{chunk_text}"),
                    "payload": document_payload(doc, chunk_text, chunk_index),
                }
            )

    if points:
        client.request("PUT", f"/collections/{quote(settings.qdrant_collection)}/points?wait=true", {"points": points})
    return len(points)


def wait_for_qdrant(client: QdrantRestClient, attempts: int = 8, delay_seconds: float = 0.5) -> None:
    # Docker 刚启动时 REST 端口可能已开放但服务未完全就绪，索引前短暂重试。
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            client.request("GET", "/collections")
            return
        except Exception as exc:
            last_error = exc
            sleep(delay_seconds)
    raise QdrantUnavailable(f"Qdrant is not ready: {last_error}")


if __name__ == "__main__":
    count = index_knowledge_base(reset=True)
    print(f"Indexed {count} knowledge chunks into Qdrant collection '{settings.qdrant_collection}'")
