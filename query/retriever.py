import pickle
import numpy as np
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

async def retrieve_relevant_chunks(query: str, index_path: str, meta_path: str, k: int = 5, min_score: float = None):
    # Load FAISS index and metadata
    with open(meta_path, "rb") as f:
        chunks = pickle.load(f)
    embedder = AsyncEmbedder()
    query_embedding = await embedder.embed_text(query)
    store = AsyncFaissStore(dim=len(query_embedding))
    await store.load(index_path, meta_path)
    D, I = await store.search(query_embedding, k)
    results = []
    for idx, score in zip(I, D):
        chunk = store.chunks[idx]
        # Lower score means more relevant (L2 distance)
        if min_score is not None and score > min_score:
            continue
        results.append({
            "score": float(score),
            "text": chunk["text"],
            "source": chunk.get("source", "")
        })
    # Sort by score (ascending: most relevant first)
    results.sort(key=lambda x: x["score"])
    return results

# Usage example:
# results = asyncio.run(retrieve_relevant_chunks(
#     "Dalili za mimba changa ni zipi?",
#     "faiss_index.bin",
#     "faiss_meta.pkl",
#     k=10,  # Increase k for more context
#     min_score=0.0  # Optionally filter by score
# ))
# print(results)
