import asyncio
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from backend.pipeline.db.connection import async_session
from backend.pipeline.db.model import Interaction
from backend.pipeline.services.document_service import DocumentService
from backend.pipeline.embeddings.embedder import AsyncEmbedder
from backend.llm.generator import Generator
from backend.llm.prompter import build_rag_prompt, preprocess_chunks
from sqlalchemy import select
import json

class RAGService:
    """Enhanced RAG service using PostgreSQL for storage and retrieval"""
    
    def __init__(
        self, 
        model_id: str = "microsoft/DialoGPT-medium",
        hf_token: Optional[str] = None,
        device: str = "auto"
    ):
        self.document_service = DocumentService()
        self.embedder = AsyncEmbedder()
        
        # Use existing LLM generator
        self.llm_generator = Generator(
            model_id=model_id,
            hf_token=hf_token,
            device=device
        )
    
    async def process_query(
        self,
        query: str,
        k: int = 10,
        similarity_threshold: float = 0.7,
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """Process a user query and return an answer with sources"""
        
        # Step 1: Embed the query
        query_embedding = await self.embedder.embed_text(query)
        
        # Step 2: Retrieve similar chunks
        similar_chunks = await self.document_service.search_similar_chunks(
            query_embedding=query_embedding,
            limit=k,
            similarity_threshold=similarity_threshold
        )
        
        if not similar_chunks:
            return {
                "answer": "Samahani, sijapata taarifa za kutosha kujibu swali lako. Tafadhali jaribu swali lingine.",
                "sources": [],
                "retrieval_score": 0.0,
                "chunks_used": 0
            }
        
        # Step 3: Convert chunks to format expected by existing prompter
        context_chunks = []
        for chunk in similar_chunks:
            context_chunks.append({
                "text": chunk["content"],
                "source": chunk["source_url"] or "local"
            })
        
        # Step 4: Preprocess chunks using existing function
        processed_chunks = preprocess_chunks(context_chunks)
        
        # Step 5: Build prompt using existing function
        prompt = build_rag_prompt(processed_chunks, query)
        
        # Step 6: Generate answer using existing generator
        answer = await self.llm_generator.generate(prompt)
        
        # Step 7: Extract sources
        sources = []
        if include_sources:
            sources = [
                {
                    "title": chunk["document_title"],
                    "url": chunk["source_url"],
                    "type": chunk["source_type"],
                    "similarity": chunk["similarity"]
                }
                for chunk in similar_chunks[:5]  # Top 5 sources
            ]
            # Remove duplicates while preserving order
            seen = set()
            unique_sources = []
            for source in sources:
                key = (source["title"], source["url"])
                if key not in seen:
                    seen.add(key)
                    unique_sources.append(source)
            sources = unique_sources
        
        # Step 8: Log the interaction
        interaction_id = await self._log_interaction(
            query=query,
            answer=answer,
            chunks_used=similar_chunks,
            retrieval_score=similar_chunks[0]["similarity"] if similar_chunks else 0.0
        )
        
        return {
            "answer": answer,
            "sources": sources,
            "retrieval_score": similar_chunks[0]["similarity"] if similar_chunks else 0.0,
            "chunks_used": len(similar_chunks),
            "interaction_id": str(interaction_id)
        }
    
    
    async def _log_interaction(
        self,
        query: str,
        answer: str,
        chunks_used: List[Dict[str, Any]],
        retrieval_score: float
    ) -> uuid.UUID:
        """Log the interaction to the database"""
        async with async_session() as session:
            interaction = Interaction(
                query=query,
                answer=answer,
                retrieval_score=retrieval_score,
                document_id=chunks_used[0]["document_id"] if chunks_used else None,
                chunk_id=chunks_used[0]["id"] if chunks_used else None
            )
            session.add(interaction)
            await session.commit()
            await session.refresh(interaction)
            return interaction.id
    
    async def add_feedback(
        self,
        interaction_id: str,
        feedback: str,
        rating: Optional[int] = None
    ) -> bool:
        """Add user feedback to an interaction"""
        try:
            interaction_uuid = uuid.UUID(interaction_id)
            async with async_session() as session:
                result = await session.execute(
                    select(Interaction).where(Interaction.id == interaction_uuid)
                )
                interaction = result.scalar_one_or_none()
                
                if interaction:
                    interaction.user_feedback = feedback
                    if rating is not None:
                        interaction.feedback_rating = rating
                    await session.commit()
                    return True
                return False
        except ValueError:
            return False
    
    async def get_interaction_history(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get interaction history with pagination"""
        async with async_session() as session:
            result = await session.execute(
                select(Interaction)
                .order_by(Interaction.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            interactions = result.scalars().all()
            
            return [
                {
                    "id": str(interaction.id),
                    "query": interaction.query,
                    "answer": interaction.answer,
                    "retrieval_score": interaction.retrieval_score,
                    "user_feedback": interaction.user_feedback,
                    "feedback_rating": interaction.feedback_rating,
                    "created_at": interaction.created_at.isoformat()
                }
                for interaction in interactions
            ]
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        doc_stats = await self.document_service.get_document_stats()
        
        async with async_session() as session:
            # Get feedback statistics
            feedback_result = await session.execute(text(
                "SELECT AVG(feedback_rating) as avg_rating, COUNT(*) as total_feedback "
                "FROM interactions WHERE feedback_rating IS NOT NULL"
            ))
            feedback_stats = feedback_result.fetchone()
            
            # Get top sources
            sources_result = await session.execute(text("""
                SELECT source, COUNT(*) as cnt FROM documents
                GROUP BY source ORDER BY cnt DESC LIMIT 10
            """))
            top_sources = [
                {
                    "title": row.title,
                    "type": row.source_type,
                    "usage_count": row.usage_count
                }
                for row in sources_result.fetchall()
            ]
        
        return {
            **doc_stats,
            "average_rating": float(feedback_stats.avg_rating) if feedback_stats.avg_rating else 0.0,
            "total_feedback": feedback_stats.total_feedback or 0,
            "top_sources": top_sources
        }
