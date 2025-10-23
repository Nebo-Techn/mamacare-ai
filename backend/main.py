from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os
import logging
from typing import List, Optional, Dict, Any
import uuid
from backend.pipeline.services.rag_service import RAGService
from backend.pipeline.services.document_service import DocumentService
from backend.pipeline.extraction.content_ingestion import ContentIngestionService
from backend.pipeline.db.init_db import init_db, check_db_health
from backend.pipeline.db.connection import get_db
from backend.pipeline.db.model import Document, Chunk, Interaction
from backend.ingest.pdf_loader import extract_text_from_pdf
from backend.ingest.url_loader import fetch_url_text
from backend.ingest.chunker import chunk_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Afyamama AI RAG API",
    description="Enhanced RAG system for maternal health in Swahili using PostgreSQL",
    version="2.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_service: Optional[RAGService] = None
document_service: Optional[DocumentService] = None
ingestion_service: Optional[ContentIngestionService] = None

HF_TOKEN = os.environ.get("HF_TOKEN", None)
LOCAL_MODEL_DIR = os.path.join(os.getcwd(), "lora_maternal_model")

class AskRequest(BaseModel):
    query: str
    k: Optional[int] = 10
    similarity_threshold: Optional[float] = 0.7
    include_sources: Optional[bool] = True

class UrlsRequest(BaseModel):
    urls: List[str]
    titles: Optional[List[str]] = None

class FeedbackRequest(BaseModel):
    interaction_id: str
    feedback: Optional[str] = None
    rating: Optional[int] = None

class DocumentUploadResponse(BaseModel):
    document_id: str
    title: str
    chunks_created: int
    status: str

class SystemStatsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    total_interactions: int
    average_rating: float
    total_feedback: int
    top_sources: List[Dict[str, Any]]

# Import startup actions lazily so startup errors are clearer
try:
    from backend.pipeline.db.init_db import init_db, check_db_health  # noqa: E402
except Exception:
    init_db = None
    check_db_health = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global rag_service, document_service, ingestion_service
    
    try:
        logger.info("🚀 Starting Afyamama AI RAG API")
        
        if init_db:
            try:
                # Initialize database
                await init_db()
                
                # Check database health
                db_healthy = await check_db_health() if check_db_health else True
                if not db_healthy:
                    logger.warning("Database health check failed on startup")
            except Exception as e:
                logger.exception("Database init failed: %s", e)
        
        # Initialize services
        document_service = DocumentService()
        ingestion_service = ContentIngestionService()
        
        # Initialize RAG service using existing LLM infrastructure
        model_id = os.environ.get("HF_MODEL_ID", "microsoft/DialoGPT-medium")
        hf_token = os.environ.get("HF_TOKEN")
        device = os.environ.get("HF_DEVICE", "auto")
        
        rag_service = RAGService(
            model_id=model_id,
            hf_token=hf_token,
            device=device
        )
        
        logger.info(f"Initialized RAG service with model: {model_id}")
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db_healthy = await check_db_health()
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "database": "connected" if db_healthy else "disconnected",
            "services": {
                "rag_service": rag_service is not None,
                "document_service": document_service is not None,
                "ingestion_service": ingestion_service is not None
            }
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats():
    """Get comprehensive system statistics"""
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        stats = await rag_service.get_system_stats()
        return SystemStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask_question(body: AskRequest):
    """Ask a question using the RAG system"""
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        result = await rag_service.process_query(
            query=body.query,
            k=body.k,
            similarity_threshold=body.similarity_threshold,
            include_sources=body.include_sources
        )
        
        return JSONResponse({
            "answer": result["answer"],
            "sources": result["sources"],
            "retrieval_score": result["retrieval_score"],
            "chunks_used": result["chunks_used"],
            "interaction_id": result["interaction_id"]
        })
        
    except Exception as e:
        logger.error(f"Failed to process query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def submit_feedback(body: FeedbackRequest):
    """Submit feedback for an interaction"""
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        success = await rag_service.add_feedback(
            interaction_id=body.interaction_id,
            feedback=body.feedback,
            rating=body.rating
        )
        
        if success:
            return {"status": "success", "message": "Feedback submitted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Interaction not found")
            
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/interactions")
async def get_interaction_history(limit: int = 50, offset: int = 0):
    """Get interaction history"""
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        interactions = await rag_service.get_interaction_history(limit=limit, offset=offset)
        return {"interactions": interactions}
    except Exception as e:
        logger.error(f"Failed to get interactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Document ingestion endpoints
@app.post("/upload_pdf", response_model=DocumentUploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process a PDF file"""
    if not ingestion_service:
        raise HTTPException(status_code=503, detail="Ingestion service not initialized")
    
    try:
        # Save uploaded file temporarily
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Extract text from PDF
        text = await extract_text_from_pdf(temp_path)
        
        # Clean up temp file
        os.remove(temp_path)
        
        if not text or len(text.strip()) < 100:
            raise HTTPException(status_code=400, detail="Insufficient content extracted from PDF")
        
        # Create document in database
        document = await document_service.create_document(
            title=file.filename,
            content=text,
            source_type="pdf",
            file_path=file.filename,
            language="sw"
        )
        
        # Chunk and embed
        chunks = await document_service.chunk_and_embed_document(
            document_id=document.id,
            content=text
        )
        
        return DocumentUploadResponse(
            document_id=str(document.id),
            title=document.title,
            chunks_created=len(chunks),
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Failed to process PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_url", response_model=DocumentUploadResponse)
async def upload_url(url: str = Form(...), title: Optional[str] = Form(None)):
    """Upload and process a URL"""
    if not ingestion_service:
        raise HTTPException(status_code=503, detail="Ingestion service not initialized")
    
    try:
        result = await ingestion_service.ingest_url(url, title)
        
        if result["status"] == "success":
            return DocumentUploadResponse(
                document_id=result["document_id"],
                title=result["title"],
                chunks_created=result["chunks_created"],
                status="success"
            )
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to ingest URL"))
            
    except Exception as e:
        logger.error(f"Failed to process URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_urls")
async def upload_urls(body: UrlsRequest):
    """Upload and process multiple URLs"""
    if not ingestion_service:
        raise HTTPException(status_code=503, detail="Ingestion service not initialized")
    
    try:
        results = await ingestion_service.batch_ingest_urls(body.urls, body.titles)
        
        successful = [r for r in results if r["status"] == "success"]
        failed = [r for r in results if r["status"] == "failed"]
        
        return {
            "total_processed": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Failed to process URLs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_youtube")
async def upload_youtube(url: str = Form(...), title: Optional[str] = Form(None)):
    """Upload and process a YouTube video"""
    if not ingestion_service:
        raise HTTPException(status_code=503, detail="Ingestion service not initialized")
    
    try:
        result = await ingestion_service.ingest_youtube_video(url, title)
        
        if result["status"] == "success":
            return DocumentUploadResponse(
                document_id=result["document_id"],
                title=result["title"],
                chunks_created=result["chunks_created"],
                status="success"
            )
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to ingest YouTube video"))
            
    except Exception as e:
        logger.error(f"Failed to process YouTube video: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_facebook")
async def upload_facebook(url: str = Form(...), title: Optional[str] = Form(None)):
    """Upload and process a Facebook post"""
    if not ingestion_service:
        raise HTTPException(status_code=503, detail="Ingestion service not initialized")
    
    try:
        result = await ingestion_service.ingest_facebook_post(url, title)
        
        if result["status"] == "success":
            return DocumentUploadResponse(
                document_id=result["document_id"],
                title=result["title"],
                chunks_created=result["chunks_created"],
                status="success"
            )
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to ingest Facebook post"))
            
    except Exception as e:
        logger.error(f"Failed to process Facebook post: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Document management endpoints
@app.get("/documents")
async def get_documents(limit: int = 100, offset: int = 0):
    """Get list of documents"""
    if not document_service:
        raise HTTPException(status_code=503, detail="Document service not initialized")
    
    try:
        documents = await document_service.get_all_documents(limit=limit, offset=offset)
        
        return {
            "documents": [
                {
                    "id": str(doc.id),
                    "title": doc.title,
                    "source_url": doc.source_url,
                    "source_type": doc.source_type,
                    "created_at": doc.created_at.isoformat(),
                    "chunk_count": len(doc.chunks) if hasattr(doc, 'chunks') else 0
                }
                for doc in documents
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}")
async def get_document(document_id: str):
    """Get a specific document with its chunks"""
    if not document_service:
        raise HTTPException(status_code=503, detail="Document service not initialized")
    
    try:
        doc_uuid = uuid.UUID(document_id)
        document = await document_service.get_document_by_id(doc_uuid)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "id": str(document.id),
            "title": document.title,
            "content": document.content,
            "source_url": document.source_url,
            "source_type": document.source_type,
            "created_at": document.created_at.isoformat(),
            "chunks": [
                {
                    "id": str(chunk.id),
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "token_count": chunk.token_count,
                    "has_embedding": chunk.embedding is not None
                }
                for chunk in document.chunks
            ]
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and all its chunks"""
    if not document_service:
        raise HTTPException(status_code=503, detail="Document service not initialized")
    
    try:
        doc_uuid = uuid.UUID(document_id)
        success = await document_service.delete_document(doc_uuid)
        
        if success:
            return {"status": "success", "message": "Document deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/{document_id}/reindex")
async def reindex_document(document_id: str):
    """Reindex a document (re-chunk and re-embed)"""
    if not ingestion_service:
        raise HTTPException(status_code=503, detail="Ingestion service not initialized")
    
    try:
        result = await ingestion_service.reindex_document(document_id)
        
        if result["status"] == "success":
            return {
                "status": "success",
                "message": "Document reindexed successfully",
                "chunks_created": result["chunks_created"]
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to reindex document"))
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")
    except Exception as e:
        logger.error(f"Failed to reindex document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Migration endpoints
@app.post("/migrate/existing-data")
async def migrate_existing_data():
    """Migrate existing data to PostgreSQL"""
    try:
        from backend.pipeline.migration.migrate_existing_data import DataMigrationService
        
        migration_service = DataMigrationService()
        results = await migration_service.migrate_existing_chunks()
        
        return {
            "status": "success",
            "message": "Migration completed",
            "results": results
        }
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/migrate/scraped-content")
async def migrate_scraped_content():
    """Migrate scraped content to PostgreSQL"""
    try:
        from backend.pipeline.migration.migrate_existing_data import DataMigrationService
        
        migration_service = DataMigrationService()
        results = await migration_service.migrate_scraped_content()
        
        return {
            "status": "success",
            "message": "Scraped content migration completed",
            "results": results
        }
    except Exception as e:
        logger.error(f"Scraped content migration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Afyamama AI RAG API running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, log_level="info")