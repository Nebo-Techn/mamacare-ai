from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import os
from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from ingest.pdf_loader import extract_text_from_pdf
from ingest.url_loader import fetch_url_text
from ingest.chunker import chunk_text
from embeddings.embedder import AsyncEmbedder
from vectorstore.faiss_store import AsyncFaissStore
from query.retriever import AsyncRetriever
from llm.prompter import build_rag_prompt
from llm.generator import Generator
from typing import List

app = FastAPI()

CHUNKS: List[str] = []
METADATA: List[dict] = []
EMBEDDER = AsyncEmbedder()
FAISS_STORE = None
RETRIEVER = None

HF_TOKEN = os.environ.get("HF_TOKEN", None)
LOCAL_MODEL_DIR = os.path.join(os.getcwd(), "lora_maternal_model")

RAG = Generator(local_model_path=LOCAL_MODEL_DIR if os.path.isdir(LOCAL_MODEL_DIR) else None, hf_token=HF_TOKEN)

@app.on_event("startup")
def load_index_if_exists():
    idx_path = os.path.join(os.getcwd(), "faiss_local", "index")
    if os.path.exists(os.path.dirname(idx_path)):
        try:
            if hasattr(RAG, "load_index"):
                RAG.load_index(idx_path)
        except Exception:
            pass

class AskRequest(BaseModel):
    query: str

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    text = await extract_text_from_pdf(file_path)
    os.remove(file_path)
    chunks = await chunk_text(text)
    global CHUNKS, METADATA, FAISS_STORE, RETRIEVER
    CHUNKS.extend(chunks)
    METADATA.extend([{"chunk": c, "source": file.filename} for c in chunks])
    embeddings = await EMBEDDER.embed_texts(chunks)
    if FAISS_STORE is None:
        FAISS_STORE = AsyncFaissStore(dim=len(embeddings[0]))
    await FAISS_STORE.add_embeddings(embeddings)
    RETRIEVER = AsyncRetriever(EMBEDDER, FAISS_STORE, METADATA)
    return JSONResponse({"status": f"PDF '{file.filename}' uploaded and processed"})

@app.post("/upload_url")
async def upload_url(url: str = Form(...)):
    text = await fetch_url_text(url)
    chunks = await chunk_text(text)
    global CHUNKS, METADATA, FAISS_STORE, RETRIEVER
    CHUNKS.extend(chunks)
    METADATA.extend([{"chunk": c, "source": url} for c in chunks])
    embeddings = await EMBEDDER.embed_texts(chunks)
    if FAISS_STORE is None:
        FAISS_STORE = AsyncFaissStore(dim=len(embeddings[0]))
    await FAISS_STORE.add_embeddings(embeddings)
    RETRIEVER = AsyncRetriever(EMBEDDER, FAISS_STORE, METADATA)
    return JSONResponse({"status": f"URL '{url}' uploaded and processed"})

@app.post("/ask")
async def ask_question(query: str = Form(...)):
    res = RAG.query(query, k=6, use_graph=True)
    return JSONResponse({"answer": res["answer"] or "No generated answer", "sources": res["sources"]})

# To run: uvicorn backend.main:app --reload

#Read token: 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

