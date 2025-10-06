from typing import List, Optional
import asyncio
import pickle
import numpy as np

from langchain.embeddings import HuggingFaceEmbeddings

class AsyncEmbedder:
    """
    Async wrapper around LangChain's HuggingFaceEmbeddings.

    Usage:
        embedder = AsyncEmbedder(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        embeddings = await embedder.embed_texts(["text1", "text2"])
    """
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", device: str = "cpu"):
        # device can be "cpu" or "cuda"
        self.model_name = model_name
        self.device = device
        self._embedder = HuggingFaceEmbeddings(model_name=self.model_name, model_kwargs={"device": self.device})

    async def embed_text(self, text: str) -> List[float]:
        loop = asyncio.get_event_loop()
        # call embed_documents with single-item list in executor
        vecs = await loop.run_in_executor(None, self._embedder.embed_documents, [text])
        return vecs[0]

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._embedder.embed_documents, texts)

    @staticmethod
    async def embed_and_save_chunks(chunk_file: str, embedding_file: str, model_name: Optional[str] = None, device: str = "cpu"):
        """
        Load chunks (pickle list of dicts with 'text'), embed using LangChain HuggingFaceEmbeddings
        and save {"embeddings": np.array, "chunks": chunks} to embedding_file (pickle).
        """
        # Load chunks
        with open(chunk_file, "rb") as f:
            chunks = pickle.load(f)
        texts = [chunk["text"] for chunk in chunks]

        embedder = AsyncEmbedder(model_name=model_name or "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", device=device)
        embeddings = await embedder.embed_texts(texts)
        embeddings = np.array(embeddings)

        # Save embeddings and chunks
        with open(embedding_file, "wb") as f:
            pickle.dump({"embeddings": embeddings, "chunks": chunks}, f)
        print(f"Saved {len(embeddings)} embeddings to {embedding_file}")

    # Usage example:
    # asyncio.run(embed_and_save_chunks("trimester1_chunks.pkl", "trimester1_embeddings.pkl"))
