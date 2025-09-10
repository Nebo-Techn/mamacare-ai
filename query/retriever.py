from embeddings.embedder import AsyncEmbedder
from vectorstore.faiss_store import AsyncFaissStore
import asyncio
from typing import List, Dict, Any

class AsyncRetriever:
    def __init__(self, embedder: AsyncEmbedder, faiss_store: AsyncFaissStore, metadata: List[Dict[str, Any]]):
        self.embedder = embedder
        self.faiss_store = faiss_store
        self.metadata = metadata  # List of metadata dicts, one per chunk

    async def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        query_embedding = await self.embedder.embed_text(query)
        distances, indices = await self.faiss_store.search(query_embedding, k)
        results = []
        for i, idx in enumerate(indices):
            if idx < len(self.metadata):
                result = self.metadata[idx].copy()
                result["score"] = float(distances[i])
                results.append(result)
        return results
