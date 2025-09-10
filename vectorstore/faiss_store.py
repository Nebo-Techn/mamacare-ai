import faiss
import numpy as np
import asyncio
from typing import List, Optional

class AsyncFaissStore:
    def __init__(self, dim: int, index_path: Optional[str] = None):
        self.index = faiss.IndexFlatL2(dim)
        self.index_path = index_path
        if index_path:
            try:
                self.index = faiss.read_index(index_path)
            except Exception:
                pass

    async def add_embeddings(self, embeddings: List[List[float]]):
        arr = np.array(embeddings).astype('float32')
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.index.add, arr)

    async def search(self, query_embedding: List[float], k: int = 5):
        arr = np.array([query_embedding]).astype('float32')
        loop = asyncio.get_event_loop()
        D, I = await loop.run_in_executor(None, self.index.search, arr, k)
        return D[0], I[0]

    async def save(self, path: Optional[str] = None):
        save_path = path or self.index_path
        if save_path:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, faiss.write_index, self.index, save_path)

    async def load(self, path: Optional[str] = None):
        load_path = path or self.index_path
        if load_path:
            loop = asyncio.get_event_loop()
            self.index = await loop.run_in_executor(None, faiss.read_index, load_path)
