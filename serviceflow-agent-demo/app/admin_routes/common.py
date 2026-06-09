from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.config import KNOWLEDGE_BASE_DIR
from app.models import AgentTrace, KnowledgeDocument, Ticket
from app.rag.qdrant_retriever import QdrantUnavailable, index_knowledge_base

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "reports"


def not_found(name: str):
    raise HTTPException(status_code=404, detail=f"{name} 不存在")


def ticket_response(ticket: Ticket) -> dict[str, Any]:
    data = ticket.to_dict()
    data["chat_history"] = ticket.chat_history
    return data


def doc_id_from_title(title: str) -> str:
    mapped = {
        "延保服务政策": "extended_warranty_policy",
        "SmartRouter X1 WiFi 连接指南": "smart_router_x1_wifi_guide",
    }
    if title in mapped:
        return mapped[title]
    safe = "".join(ch.lower() if ch.isalnum() else "_" for ch in title.strip())
    safe = "_".join(part for part in safe.split("_") if part)
    return safe[:48] or f"doc_{datetime.now().strftime('%Y%m%d%H%M%S')}"


def write_knowledge_file(doc: KnowledgeDocument) -> Path:
    base_dir = KNOWLEDGE_BASE_DIR / doc.knowledge_base
    base_dir.mkdir(parents=True, exist_ok=True)
    path = base_dir / f"{doc.doc_id}.md"
    # 发布时写入 Markdown，SimpleRetriever 下一次实例化即可检索到新文档。
    path.write_text(f"# {doc.title}\n\n{doc.content}\n", encoding="utf-8")
    return path


def reindex_best_effort() -> int:
    try:
        return index_knowledge_base(reset=True)
    except (QdrantUnavailable, Exception):
        return 0


def request_latencies(traces: list[AgentTrace]) -> list[float]:
    grouped: dict[str, float] = defaultdict(float)
    for trace in traces:
        grouped[trace.trace_id] += float(trace.latency_ms or 0)
    return list(grouped.values())


def percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round((len(ordered) - 1) * ratio)))
    return round(ordered[index], 3)


def avg_node_latency(traces: list[AgentTrace], node_name: str) -> float:
    values = [float(trace.latency_ms or 0) for trace in traces if trace.node_name == node_name]
    return round(sum(values) / len(values), 3) if values else 0.0

