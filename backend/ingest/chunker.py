import tiktoken
import asyncio
from typing import List

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """Split text into token-aware chunks (synchronous)."""
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    chunks: List[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk = enc.decode(tokens[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

async def chunk_texts(texts: List[str], chunk_size: int = 500, overlap: int = 100) -> List[List[str]]:
    """Async wrapper to chunk multiple texts without blocking the event loop."""
    tasks = [asyncio.to_thread(chunk_text, text, chunk_size, overlap) for text in texts]
    return await asyncio.gather(*tasks)
