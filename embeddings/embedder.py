from sentence_transformers import SentenceTransformer
import asyncio
from typing import List
import pickle
import numpy as np

class AsyncEmbedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    async def embed_text(self, text: str) -> List[float]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.model.encode, text)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        tasks = [self.embed_text(text) for text in texts]
        return await asyncio.gather(*tasks)

    @staticmethod
    async def embed_and_save_chunks(chunk_file: str, embedding_file: str):
        # Load chunks
        with open(chunk_file, "rb") as f:
            chunks = pickle.load(f)
        texts = [chunk["text"] for chunk in chunks]

        embedder = AsyncEmbedder()
        embeddings = await embedder.embed_texts(texts)
        embeddings = np.array(embeddings)

        # Save embeddings and chunks
        with open(embedding_file, "wb") as f:
            pickle.dump({"embeddings": embeddings, "chunks": chunks}, f)
        print(f"Saved {len(embeddings)} embeddings to {embedding_file}")

    # Usage example:
    # asyncio.run(embed_and_save_chunks("trimester1_chunks.pkl", "trimester1_embeddings.pkl"))
