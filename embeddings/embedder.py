from sentence_transformers import SentenceTransformer
import asyncio
from typing import List

class AsyncEmbedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    async def embed_text(self, text: str) -> List[float]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.model.encode, text)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        tasks = [self.embed_text(text) for text in texts]
        return await asyncio.gather(*tasks)
