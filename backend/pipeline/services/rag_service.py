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
import logging
import traceback
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGService:
    """Enhanced RAG service using PostgreSQL for storage and retrieval"""
    
    def __init__(
        self, 
        endpoint_url: str,
    ):
        self.document_service = DocumentService()
        self.embedder = AsyncEmbedder()
        
        # Use existing LLM generator
        self.llm_generator = Generator(
            endpoint_url=endpoint_url
        )
    
    async def process_query(self,query: str,k: int = 10,similarity_threshold: float = 0.7,include_sources: bool = True) -> Dict[str, Any]:
        """Process a user query and return an answer with sources"""
        try:
            logger.info(f"Received query: {query}")

            # Step 1: Embed the query
            query_embedding = await self.embedder.embed_text(query)
            # logger.info(f"Query embedding generated: {len(query_embedding)} dimensions")

            # Step 2: Retrieve similar chunks
            similar_chunks = await self.document_service.search_similar_chunks(
                query_embedding=query_embedding,
                limit=k,
                similarity_threshold=similarity_threshold
            )
            # logger.info(f"Found {len(similar_chunks)} similar chunks")

            if not similar_chunks:
                logger.warning("No similar chunks found for query")
                return {
                    "answer": "Samahani, sijapata taarifa za kutosha kujibu swali lako. Tafadhali jaribu swali lingine.",
                    "sources": [],
                    "retrieval_score": 0.0,
                    "chunks_used": 0
                }

            # Step 3: Convert chunks
            context_chunks = []
            for chunk in similar_chunks:
                context_chunks.append({
                    "text": chunk.get("content"),
                    "source": chunk.get("source_url") or "local"
                })
            # logger.info(f"Prepared {len(context_chunks)} context chunks")

            # Step 4: Preprocess and build prompt
            processed_chunks = preprocess_chunks(context_chunks)
            prompt = build_rag_prompt(processed_chunks, query)
            # logger.info(f"Prompt built successfully (length: {len(prompt)} chars)")

            # Step 5: Generate answer
            answer = await self.llm_generator.generate(prompt)
            # logger.info("Answer generated successfully")

            # Step 6: Collect sources
            sources = []
            if include_sources:
                sources = [
                    {
                        "title": chunk.get("document_title"),
                        "url": chunk.get("source_url"),
                        "type": chunk.get("source_type"),
                        "similarity": chunk.get("similarity"),
                    }
                    for chunk in similar_chunks[:5]
                ]
                # logger.info(f"Collected {len(sources)} sources")

            # Step 7: Log interaction
            interaction_id = await self._log_interaction(
                query=query,
                answer=answer,
                chunks_used=similar_chunks,
                retrieval_score=similar_chunks[0].get("similarity", 0.0),
            )
            # logger.info(f"Interaction logged with ID: {interaction_id}")

            return {
                "answer": answer,
                "sources": sources,
                "retrieval_score": similar_chunks[0].get("similarity", 0.0),
                "chunks_used": len(similar_chunks),
                "interaction_id": str(interaction_id),
            }

        except Exception as e:
            # logger.error(f"Error during process_query: {e}")
            # logger.error(traceback.format_exc())
            raise

    
    
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
                SELECT source_type,title,COUNT(*) as cnt FROM documents
                GROUP BY source_type,title ORDER BY cnt DESC LIMIT 10
            """))
            top_sources = [
                {
                    "title": row.title,
                    "type": row.source_type,
                    "usage_count": row.cnt
                }
                for row in sources_result.fetchall()
            ]
        
        return {
            **doc_stats,
            "average_rating": float(feedback_stats.avg_rating) if feedback_stats.avg_rating else 0.0,
            "total_feedback": feedback_stats.total_feedback or 0,
            "top_sources": top_sources
        }
