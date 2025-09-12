from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import os
from ingest.pdf_loader import extract_text_from_pdf
from ingest.url_loader import fetch_url_text
from ingest.chunker import chunk_text
from embeddings.embedder import AsyncEmbedder
from vectorstore.faiss_store import AsyncFaissStore
from query.retriever import AsyncRetriever
from llm.prompter import build_rag_prompt
from llm.generator import AsyncLLMGenerator
from typing import List

app = FastAPI()

# In-memory store for demo
CHUNKS: List[str] = []
METADATA: List[dict] = []
EMBEDDER = AsyncEmbedder()
FAISS_STORE = None
RETRIEVER = None
LLM = AsyncLLMGenerator(ollama_url="http://localhost:11434", model="phi")

class AskRequest(BaseModel):
    query: str

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    # Save uploaded file
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    # Extract text
    text = await extract_text_from_pdf(file_path)
    os.remove(file_path)
    # Chunk text
    chunks = await chunk_text(text)
    global CHUNKS, METADATA, FAISS_STORE, RETRIEVER
    CHUNKS.extend(chunks)
    # Metadata: store chunk text and source
    METADATA.extend([{"chunk": c, "source": file.filename} for c in chunks])
    # Embed chunks
    embeddings = await EMBEDDER.embed_texts(chunks)
    # Init FAISS if first upload
    if FAISS_STORE is None:
        FAISS_STORE = AsyncFaissStore(dim=len(embeddings[0]))
    await FAISS_STORE.add_embeddings(embeddings)
    RETRIEVER = AsyncRetriever(EMBEDDER, FAISS_STORE, METADATA)
    return JSONResponse({"status": f"PDF '{file.filename}' uploaded and processed"})

@app.post("/upload_url")
async def upload_url(url: str = Form(...)):
    # Fetch and clean text
    text = await fetch_url_text(url)
    # Chunk text
    chunks = await chunk_text(text)
    global CHUNKS, METADATA, FAISS_STORE, RETRIEVER
    CHUNKS.extend(chunks)
    METADATA.extend([{"chunk": c, "source": url} for c in chunks])
    # Embed chunks
    embeddings = await EMBEDDER.embed_texts(chunks)
    if FAISS_STORE is None:
        FAISS_STORE = AsyncFaissStore(dim=len(embeddings[0]))
    await FAISS_STORE.add_embeddings(embeddings)
    RETRIEVER = AsyncRetriever(EMBEDDER, FAISS_STORE, METADATA)
    return JSONResponse({"status": f"URL '{url}' uploaded and processed"})

@app.post("/ask")
async def ask_question(request: AskRequest):
    global RETRIEVER, CHUNKS, METADATA, LLM
    if RETRIEVER is None:
        return JSONResponse({"answer": "No documents ingested yet.", "sources": []})
    # Retrieve relevant chunks
    results = await RETRIEVER.search(request.query, k=5)
    context_chunks = [r["chunk"] for r in results]
    sources = [r["source"] for r in results]
    # Build prompt
    system_prompt = "You are a helpful maternal health assistant."
    prompt = build_rag_prompt(system_prompt, context_chunks, request.query)
    # Generate answer
    answer = await LLM.generate(prompt)
    return JSONResponse({"answer": answer, "sources": context_chunks, "source_names": sources})

# To run: uvicorn backend.main:app --reload
