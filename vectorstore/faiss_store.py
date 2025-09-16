import faiss
import pickle
import numpy as np
import asyncio
from typing import List, Optional

class AsyncFaissStore:
    def __init__(self, dim: int, index_path: Optional[str] = None):
        self.index = faiss.IndexFlatL2(dim)
        self.index_path = index_path
        self.chunks = []
        if index_path:
            try:
                self.index = faiss.read_index(index_path)
                with open(index_path.replace('.bin', '_meta.pkl'), "rb") as f:
                    self.chunks = pickle.load(f)
            except Exception:
                pass

    async def add_embeddings(self, embeddings: np.ndarray, chunks: list):
        arr = embeddings.astype('float32')
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.index.add, arr)
        self.chunks.extend(chunks)

    async def search(self, query_embedding: List[float], k: int = 5):
        arr = np.array([query_embedding]).astype('float32')
        loop = asyncio.get_event_loop()
        D, I = await loop.run_in_executor(None, self.index.search, arr, k)
        return D[0], I[0]

    async def save(self, index_path: str, meta_path: str):
        faiss.write_index(self.index, index_path)
        with open(meta_path, "wb") as f:
            pickle.dump(self.chunks, f)
        print(f"Saved FAISS index to {index_path} and metadata to {meta_path}")

    async def load(self, index_path: str, meta_path: str):
        self.index = faiss.read_index(index_path)
        with open(meta_path, "rb") as f:
            self.chunks = pickle.load(f)
