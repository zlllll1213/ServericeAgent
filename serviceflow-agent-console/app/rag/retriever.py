import math
import re
from collections import Counter
from typing import Protocol

from app.rag.loader import KnowledgeDocument, load_documents


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+|[\u4e00-\u9fff]")


def tokenize(text: str) -> list[str]:
    normalized = text.lower()
    tokens = TOKEN_PATTERN.findall(normalized)
    words = ["wifi" if token in {"wi", "fi"} else token for token in tokens]
    return [token for token in words if token.strip()]


class Retriever(Protocol):
    def retrieve(self, query: str, knowledge_base: str, top_k: int = 3) -> list[dict]:
        ...


class SimpleRetriever:
    def __init__(self, documents: list[KnowledgeDocument] | None = None):
        self.documents = documents if documents is not None else load_documents()
        self.doc_tokens = [Counter(tokenize(doc.content + " " + doc.title)) for doc in self.documents]
        self.idf = self._build_idf()

    def _build_idf(self) -> dict[str, float]:
        doc_count = max(len(self.doc_tokens), 1)
        all_terms = set().union(*(tokens.keys() for tokens in self.doc_tokens)) if self.doc_tokens else set()
        return {
            term: math.log((1 + doc_count) / (1 + sum(1 for tokens in self.doc_tokens if term in tokens))) + 1
            for term in all_terms
        }

    def retrieve(self, query: str, knowledge_base: str, top_k: int = 3) -> list[dict]:
        query_tokens = Counter(tokenize(query))
        scored: list[tuple[float, KnowledgeDocument]] = []

        for doc, tokens in zip(self.documents, self.doc_tokens):
            if doc.knowledge_base != knowledge_base:
                continue
            score = 0.0
            for term, count in query_tokens.items():
                score += count * tokens.get(term, 0) * self.idf.get(term, 1.0)
            for phrase in [query.lower(), "wifi", "macos", "7 天", "无理由"]:
                if phrase and phrase in doc.content.lower():
                    score += 2.5
            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "knowledge_base": doc.knowledge_base,
                "source": doc.source_file,
                "source_file": doc.source_file,
                "chunk_id": f"{doc.category}_001",
                "title": doc.title,
                "score": round(score, 3),
                "product_name": doc.product_name,
                "category": doc.category,
                "snippet": self._snippet(doc.content),
                "retriever": "simple",
            }
            for score, doc in scored[:top_k]
        ]

    @staticmethod
    def _snippet(content: str, limit: int = 260) -> str:
        compact = " ".join(line.strip() for line in content.splitlines() if line.strip())
        return compact[:limit] + ("..." if len(compact) > limit else "")


class VectorRetriever:
    """Future adapter for Qdrant, pgvector, or another vector database."""

    def retrieve(self, query: str, knowledge_base: str, top_k: int = 3) -> list[dict]:
        raise NotImplementedError("VectorRetriever is reserved for a later integration.")
