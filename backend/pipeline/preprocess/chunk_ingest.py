import os
import asyncio
from pathlib import Path
import textwrap
from typing import List

from langchain.vectorstores import PGVector
from langchain.schema import Document

from pipeline.embeddings.embedder import AsyncEmbedder

# Load Postgres connection from Docker environment variables
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "mamacare")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

CONN_STRING = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Directories
SCRAPED_DIR = Path("/app/data/scraped_content")
FACEBOOK_DIR = Path("/app/data/facebook_posts")

# Chunk size
CHUNK_SIZE = 500
MIN_CHUNK_LENGTH = 100

async def load_chunks_from_dir(directory: Path, source_mapping: dict = None) -> List[dict]:
    """Load text files and split into chunks"""
    chunks = []
    for file in directory.glob("*.txt"):
        source = source_mapping.get(file.stem, file.stem) if source_mapping else file.stem
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()

        for chunk_text in textwrap.wrap(text, width=CHUNK_SIZE):
            if len(chunk_text.strip()) > MIN_CHUNK_LENGTH:
                chunks.append({"text": chunk_text.strip(), "source": source})
    return chunks

async def main():
    # Load all chunks
    web_chunks = await load_chunks_from_dir(SCRAPED_DIR)
    fb_chunks = await load_chunks_from_dir(FACEBOOK_DIR)
    all_chunks = web_chunks + fb_chunks
    print(f"Total chunks: {len(all_chunks)}")

    if not all_chunks:
        print("No chunks found. Exiting.")
        return

    # Embed chunks
    embedder = AsyncEmbedder()
    texts = [chunk["text"] for chunk in all_chunks]
    embeddings = await embedder.embed_texts(texts)

    # Convert to LangChain Documents
    documents = [Document(page_content=chunk["text"], metadata={"source": chunk["source"]}) for chunk in all_chunks]

    # Store in PGVector
    vectorstore = PGVector.from_documents(
        documents,
        embedding=embedder._embedder,  # LangChain embedding object
        collection_name="mamacare_chunks",
        connection_string=CONN_STRING
    )
    print(f"Stored {len(documents)} chunks into PGVector collection 'mamacare_chunks'.")

if __name__ == "__main__":
    asyncio.run(main())
