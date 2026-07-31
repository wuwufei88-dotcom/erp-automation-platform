from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, host: str, port: int, collection: str) -> None:
        self.host = host
        self.port = port
        self.collection = collection

    async def insert(self, vectors: list[dict]) -> list[str]:
        logger.info("Inserting %d vectors into %s", len(vectors), self.collection)
        return [f"vec-{i}" for i in range(len(vectors))]

    async def search(self, query_vector: list[float], top_k: int = 10, filter_expr: Optional[str] = None) -> list[dict]:
        logger.info("Searching %s (top_k=%d, filter=%s)", self.collection, top_k, filter_expr)
        return []

    async def delete_by_project(self, project_id: str) -> int:
        logger.info("Deleting vectors for project %s", project_id)
        return 0


class Embedder:
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 1536 for _ in texts]


class Retriever:
    def __init__(self, store: VectorStore, embedder: Embedder) -> None:
        self.store = store
        self.embedder = embedder

    async def semantic_search(self, query: str, project_id: Optional[str] = None, top_k: int = 5) -> list[dict]:
        vectors = await self.embedder.embed([query])
        filter_expr = f'project_id == "{project_id}"' if project_id else None
        return await self.store.search(vectors[0], top_k=top_k, filter_expr=filter_expr)
