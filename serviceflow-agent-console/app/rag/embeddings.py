import hashlib
import math

from app.config import settings
from app.rag.retriever import tokenize


class HashEmbedding:
    """Small deterministic embedding for local demos without external model calls."""

    def __init__(self, dimensions: int | None = None):
        self.dimensions = dimensions or settings.qdrant_vector_size

    def embed(self, text: str) -> list[float]:
        # 哈希 embedding 不是生产语义向量，但足够支撑本地 Qdrant Demo 的可重复检索。
        vector = [0.0] * self.dimensions
        tokens = tokenize(text)
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]
