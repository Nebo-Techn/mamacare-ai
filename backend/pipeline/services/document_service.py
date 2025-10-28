import asyncio
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text
from sqlalchemy.orm import selectinload

from backend.pipeline.db.connection import async_session
from backend.pipeline.db.model import Document, Chunk, Interaction
from backend.pipeline.embeddings.embedder import AsyncEmbedder
from backend.ingest.chunker import chunk_text
import json

class DocumentService:
    """Service for managing documents and chunks in PostgreSQL"""
    
    def __init__(self):
        self.embedder = AsyncEmbedder()
    
    async def create_document(
        self,
        title: str,
        content: str,
        source_url: Optional[str] = None,
        source_type: str = "text",
        file_path: Optional[str] = None,
        language: str = "sw"
    ) -> Document:
        """Create a new document and store it in the database"""
        async with async_session() as session:
            document = Document(
                title=title,
                content=content,
                source_url=source_url,
                source_type=source_type,
                file_path=file_path,
                language=language
            )
            session.add(document)
            await session.commit()
            await session.refresh(document)
            return document
    
    async def chunk_and_embed_document(
        self,
        document_id: uuid.UUID,
        content: str,
        chunk_size: int = 500,
        overlap: int = 100
    ) -> List[Chunk]:
        """Chunk document content and create embeddings"""
        # Chunk the content
        chunks_text = chunk_text(content, chunk_size, overlap)
        
        # Create embeddings for all chunks
        embeddings = await self.embedder.embed_texts(chunks_text)
        
        async with async_session() as session:
            chunks = []
            for i, (chunk_content, embedding) in enumerate(zip(chunks_text, embeddings)):
                chunk = Chunk(
                    document_id=document_id,
                    content=chunk_content,
                    chunk_index=i,
                    token_count=len(chunk_content.split()),
                    embedding=embedding,
                    chunk_metadata=json.dumps({"chunk_size": len(chunk_content), "overlap": overlap})
                )
                session.add(chunk)
                chunks.append(chunk)
            
            await session.commit()
            return chunks
    
    async def get_document_by_id(self, document_id: uuid.UUID) -> Optional[Document]:
        """Retrieve a document by ID with its chunks"""
        async with async_session() as session:
            result = await session.execute(
                select(Document)
                .options(selectinload(Document.chunks))
                .where(Document.id == document_id)
            )
            return result.scalar_one_or_none()
    
    async def get_all_documents(self, limit: int = 100, offset: int = 0) -> List[Document]:
        """Get all documents with pagination"""
        async with async_session() as session:
            result = await session.execute(
                select(Document)
                .limit(limit)
                .offset(offset)
                .order_by(Document.created_at.desc())
            )
            return result.scalars().all()
    
    async def search_similar_chunks(
        self,
        query_embedding: List[float],
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks using vector similarity"""
        async with async_session() as session:
            try:
                # Try pgvector similarity search first
                query = text("""
                    SELECT c.id, c.content, c.chunk_index, c.chunk_metadata,
                        d.title, d.source_url, d.source_type,
                        1 - (c.embedding <=> :embedding) as similarity
                    FROM chunks c
                    JOIN documents d ON c.document_id = d.id
                    WHERE 1 - (c.embedding <=> :embedding) > :threshold
                    ORDER BY c.embedding <=> :embedding
                    LIMIT :limit
                    """)

                result = await session.execute(
                        query,
                        {"embedding": query_embedding, "threshold": similarity_threshold, "limit": limit}
                    )

                
                chunks = []
                for row in result:
                    chunks.append({
                        "id": row.id,
                        "content": row.content,
                        "chunk_index": row.chunk_index,
                        "metadata": json.loads(row.chunk_metadata) if row.chunk_metadata else {},
                        "document_title": row.title,
                        "source_url": row.source_url,
                        "source_type": row.source_type,
                        "similarity": row.similarity
                    })
                
                return chunks
                
            except Exception as e:
                # Fallback to cosine similarity using numpy
                logger.warning(f"pgvector search failed, using fallback: {e}")
                return await self._fallback_similarity_search(query_embedding, limit, similarity_threshold)
    
    async def _fallback_similarity_search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Fallback similarity search using numpy cosine similarity"""
        import numpy as np
        
        async with async_session() as session:
            # Get all chunks with embeddings
            result = await session.execute("""
                SELECT c.id, c.content, c.chunk_index, c.chunk_metadata, c.embedding,
                       d.title, d.source_url, d.source_type
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
                WHERE c.embedding IS NOT NULL
            """)
            
            chunks_with_similarity = []
            query_embedding_np = np.array(query_embedding)
            
            for row in result:
                if row.embedding:
                    chunk_embedding = np.array(row.embedding)
                    # Calculate cosine similarity
                    similarity = np.dot(query_embedding_np, chunk_embedding) / (
                        np.linalg.norm(query_embedding_np) * np.linalg.norm(chunk_embedding)
                    )
                    
                    if similarity > similarity_threshold:
                        chunks_with_similarity.append({
                            "id": row.id,
                            "content": row.content,
                            "chunk_index": row.chunk_index,
                            "metadata": json.loads(row.chunk_metadata) if row.chunk_metadata else {},
                            "document_title": row.title,
                            "source_url": row.source_url,
                            "source_type": row.source_type,
                            "similarity": float(similarity)
                        })
            
            # Sort by similarity and return top results
            chunks_with_similarity.sort(key=lambda x: x["similarity"], reverse=True)
            return chunks_with_similarity[:limit]
    
    async def delete_document(self, document_id: uuid.UUID) -> bool:
        """Delete a document and all its chunks"""
        async with async_session() as session:
            result = await session.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()
            
            if document:
                await session.delete(document)
                await session.commit()
                return True
            return False
    
    async def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about documents and chunks"""
        async with async_session() as session:
            # Count documents
            doc_count_result = await session.execute(text("SELECT COUNT(*) FROM documents"))
            # before: chunk_count_result = await session.execute("SELECT COUNT(*) FROM chunks")
            chunk_count_result = await session.execute(text("SELECT COUNT(*) FROM chunks"))
            # before: interaction_count_result = await session.execute("SELECT COUNT(*) FROM interactions")
            interaction_count_result = await session.execute(text("SELECT COUNT(*) FROM interactions"))
            
            return {
                "total_documents": doc_count_result.scalar(),
                "total_chunks": chunk_count_result.scalar(),
                "total_interactions": interaction_count_result.scalar()
            }
