from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import os
from typing import List, Optional
from ingest.pdf_loader import extract_text_from_pdf
from ingest.url_loader import fetch_url_text
from ingest.chunker import chunk_text
from llm.generator import Generator

# LangChain imports
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain.docstore.document import Document
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter

app = FastAPI()

# Runtime state
EMBEDDINGS = None  # HuggingFaceEmbeddings
VECTORSTORE: Optional[FAISS] = None
RETRIEVER = None
QA_CHAIN: Optional[RetrievalQA] = None

HF_TOKEN = os.environ.get("HF_TOKEN", None)
LOCAL_MODEL_DIR = os.path.join(os.getcwd(), "lora_maternal_model")

RAG = Generator(local_model_path=LOCAL_MODEL_DIR if os.path.isdir(LOCAL_MODEL_DIR) else None, hf_token=HF_TOKEN)

# Storage paths
FAISS_DIR = os.path.join(os.getcwd(), "faiss_store")
FAISS_INDEX_PATH = os.path.join(FAISS_DIR, "index")

@app.on_event("startup")
def startup():
    global EMBEDDINGS, VECTORSTORE, RETRIEVER, QA_CHAIN
    os.makedirs(FAISS_DIR, exist_ok=True)
    EMBEDDINGS = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", model_kwargs={"device": "cpu"})
    # Try loading an existing index
    try:
        if os.path.exists(FAISS_DIR):
            VECTORSTORE = FAISS.load_local(FAISS_DIR, EMBEDDINGS, allow_dangerous_deserialization=True)
    except Exception:
        VECTORSTORE = None
    if VECTORSTORE is not None:
        RETRIEVER = VECTORSTORE.as_retriever(search_kwargs={"k": 6})
    if RAG.llm is not None and RETRIEVER is not None:
        QA_CHAIN = RetrievalQA.from_chain_type(
            llm=RAG.llm,
            retriever=RETRIEVER,
            return_source_documents=True,
            chain_type="stuff"
        )

class AskRequest(BaseModel):
    query: str

class UrlsRequest(BaseModel):
    urls: List[str]

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Index a single PDF file."""
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    text = await extract_text_from_pdf(file_path)
    os.remove(file_path)
    return await _index_texts([text], sources=[file.filename])

@app.post("/upload_pdfs")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    """Index multiple PDF files."""
    texts: List[str] = []
    sources: List[str] = []
    for file in files:
        file_path = f"temp_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())
        text = await extract_text_from_pdf(file_path)
        os.remove(file_path)
        texts.append(text)
        sources.append(file.filename)
    return await _index_texts(texts, sources=sources)

@app.post("/upload_url")
async def upload_url(url: str = Form(...)):
    text = await fetch_url_text(url)
    return await _index_texts([text], sources=[url])

@app.post("/upload_urls")
async def upload_urls(body: UrlsRequest):
    texts: List[str] = []
    sources: List[str] = []
    for url in body.urls:
        text = await fetch_url_text(url)
        texts.append(text)
        sources.append(url)
    return await _index_texts(texts, sources=sources)

async def _index_texts(texts: List[str], sources: List[str]):
    """Chunk, embed, and index texts into FAISS; update retriever and QA chain."""
    global VECTORSTORE, RETRIEVER, QA_CHAIN
    # Prefer our custom tiktoken chunker if present; fallback to a reasonable splitter
    docs: List[Document] = []
    for text, source in zip(texts, sources):
        try:
            chunks = await chunk_text(text)
        except Exception:
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
            chunks = splitter.split_text(text)
        docs.extend([Document(page_content=c, metadata={"source": source}) for c in chunks])

    if VECTORSTORE is None:
        VECTORSTORE = FAISS.from_documents(docs, EMBEDDINGS)
    else:
        VECTORSTORE.add_documents(docs)

    # Persist to disk
    VECTORSTORE.save_local(FAISS_DIR)

    # Update retriever and chain
    RETRIEVER = VECTORSTORE.as_retriever(search_kwargs={"k": 6})
    if RAG.llm is not None:
        QA_CHAIN = RetrievalQA.from_chain_type(
            llm=RAG.llm,
            retriever=RETRIEVER,
            return_source_documents=True,
            chain_type="stuff"
        )
    return JSONResponse({"status": f"Indexed {len(docs)} chunks from {len(texts)} document(s)"})

@app.post("/ask")
async def ask_question(body: AskRequest):
    if QA_CHAIN is None:
        return JSONResponse({"answer": "Index or model not initialized.", "sources": []})
    # Run chain synchronously (RetrievalQA is sync); execute in thread to avoid blocking event loop
    loop = asyncio.get_event_loop()
    def _invoke():
        return QA_CHAIN({"query": body.query})
    result = await loop.run_in_executor(None, _invoke)
    answer = result.get("result", "")
    src_docs = result.get("source_documents", []) or []
    sources = []
    for d in src_docs:
        meta = d.metadata or {}
        sources.append(meta.get("source", ""))
    return JSONResponse({"answer": answer, "sources": sources})

# To run: uvicorn backend.main:app --reload
