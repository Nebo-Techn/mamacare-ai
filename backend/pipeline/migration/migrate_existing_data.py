import asyncio
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any
import logging

from pipeline.db.connection import async_session
from pipeline.db.model import Document, Chunk
from pipeline.services.document_service import DocumentService
from pipeline.embeddings.embedder import AsyncEmbedder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataMigrationService:
    """Service to migrate existing data to PostgreSQL"""
    
    def __init__(self):
        self.document_service = DocumentService()
        self.embedder = AsyncEmbedder()
    
    async def migrate_existing_chunks(
        self,
        chunks_file: str = "trimester1_chunks.pkl",
        qa_file: str = "maternal_qa_train.jsonl"
    ) -> Dict[str, Any]:
        """Migrate existing chunks and Q&A data to PostgreSQL"""
        results = {
            "chunks_migrated": 0,
            "qa_migrated": 0,
            "errors": []
        }
        
        try:
            # Migrate existing chunks
            if Path(chunks_file).exists():
                logger.info(f"Migrating chunks from {chunks_file}")
                chunks_result = await self._migrate_chunks_file(chunks_file)
                results["chunks_migrated"] = chunks_result["migrated"]
                results["errors"].extend(chunks_result["errors"])
            
            # Migrate Q&A data
            if Path(qa_file).exists():
                logger.info(f"Migrating Q&A data from {qa_file}")
                qa_result = await self._migrate_qa_file(qa_file)
                results["qa_migrated"] = qa_result["migrated"]
                results["errors"].extend(qa_result["errors"])
            
            logger.info(f"Migration completed: {results['chunks_migrated']} chunks, {results['qa_migrated']} Q&A pairs")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            results["errors"].append(str(e))
        
        return results
    
    async def _migrate_chunks_file(self, chunks_file: str) -> Dict[str, Any]:
        """Migrate chunks from pickle file"""
        result = {"migrated": 0, "errors": []}
        
        try:
            with open(chunks_file, "rb") as f:
                chunks = pickle.load(f)
            
            logger.info(f"Found {len(chunks)} chunks to migrate")
            
            for i, chunk in enumerate(chunks):
                try:
                    # Create document
                    document = await self.document_service.create_document(
                        title=f"Migrated Chunk {i+1}",
                        content=chunk.get("text", ""),
                        source_url=chunk.get("source", ""),
                        source_type="migrated_chunk",
                        language="sw"
                    )
                    
                    # Create embedding and chunk
                    embedding = await self.embedder.embed_text(chunk.get("text", ""))
                    
                    async with async_session() as session:
                        db_chunk = Chunk(
                            document_id=document.id,
                            content=chunk.get("text", ""),
                            chunk_index=0,
                            token_count=len(chunk.get("text", "").split()),
                            embedding=embedding,
                            chunk_metadata=json.dumps({"migrated_from": chunks_file, "original_source": chunk.get("source", "")})
                        )
                        session.add(db_chunk)
                        await session.commit()
                    
                    result["migrated"] += 1
                    
                    if (i + 1) % 100 == 0:
                        logger.info(f"Migrated {i+1}/{len(chunks)} chunks")
                
                except Exception as e:
                    error_msg = f"Failed to migrate chunk {i}: {e}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
            
        except Exception as e:
            error_msg = f"Failed to load chunks file: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
        
        return result
    
    async def _migrate_qa_file(self, qa_file: str) -> Dict[str, Any]:
        """Migrate Q&A data from JSONL file"""
        result = {"migrated": 0, "errors": []}
        
        try:
            with open(qa_file, "r", encoding="utf-8") as f:
                qa_pairs = [json.loads(line) for line in f]
            
            logger.info(f"Found {len(qa_pairs)} Q&A pairs to migrate")
            
            for i, qa in enumerate(qa_pairs):
                try:
                    # Create document for the answer
                    document = await self.document_service.create_document(
                        title=f"Q&A: {qa.get('question', 'Unknown Question')[:100]}",
                        content=qa.get('answer', ''),
                        source_url="maternal_qa_train",
                        source_type="qa_pair",
                        language="sw"
                    )
                    
                    # Create embedding and chunk
                    embedding = await self.embedder.embed_text(qa.get('answer', ''))
                    
                    async with async_session() as session:
                        db_chunk = Chunk(
                            document_id=document.id,
                            content=qa.get('answer', ''),
                            chunk_index=0,
                            token_count=len(qa.get('answer', '').split()),
                            embedding=embedding,
                            chunk_metadata=json.dumps({
                                "question": qa.get('question', ''),
                                "migrated_from": qa_file,
                                "qa_pair": True
                            })
                        )
                        session.add(db_chunk)
                        await session.commit()
                    
                    result["migrated"] += 1
                    
                    if (i + 1) % 50 == 0:
                        logger.info(f"Migrated {i+1}/{len(qa_pairs)} Q&A pairs")
                
                except Exception as e:
                    error_msg = f"Failed to migrate Q&A pair {i}: {e}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
            
        except Exception as e:
            error_msg = f"Failed to load Q&A file: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
        
        return result
    
    async def migrate_scraped_content(self, content_dir: str = "scraped_content") -> Dict[str, Any]:
        """Migrate existing scraped content files"""
        result = {"migrated": 0, "errors": []}
        
        try:
            content_path = Path(content_dir)
            if not content_path.exists():
                logger.warning(f"Content directory {content_dir} does not exist")
                return result
            
            txt_files = list(content_path.glob("*.txt"))
            logger.info(f"Found {len(txt_files)} text files to migrate")
            
            for file_path in txt_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if len(content.strip()) < 100:
                        logger.warning(f"Skipping {file_path.name}: insufficient content")
                        continue
                    
                    # Create document
                    document = await self.document_service.create_document(
                        title=file_path.stem,
                        content=content,
                        source_url=f"file://{file_path}",
                        source_type="scraped_content",
                        file_path=str(file_path),
                        language="sw"
                    )
                    
                    # Chunk and embed
                    chunks = await self.document_service.chunk_and_embed_document(
                        document_id=document.id,
                        content=content
                    )
                    
                    result["migrated"] += 1
                    logger.info(f"Migrated {file_path.name}: {len(chunks)} chunks")
                
                except Exception as e:
                    error_msg = f"Failed to migrate {file_path.name}: {e}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
            
        except Exception as e:
            error_msg = f"Failed to migrate scraped content: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
        
        return result
    
    async def migrate_facebook_posts(self, posts_dir: str = "facebook_posts") -> Dict[str, Any]:
        """Migrate existing Facebook posts"""
        result = {"migrated": 0, "errors": []}
        
        try:
            posts_path = Path(posts_dir)
            if not posts_path.exists():
                logger.warning(f"Facebook posts directory {posts_dir} does not exist")
                return result
            
            txt_files = list(posts_path.glob("*.txt"))
            logger.info(f"Found {len(txt_files)} Facebook post files to migrate")
            
            for file_path in txt_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if len(content.strip()) < 50:
                        logger.warning(f"Skipping {file_path.name}: insufficient content")
                        continue
                    
                    # Create document
                    document = await self.document_service.create_document(
                        title=f"Facebook Post: {file_path.stem}",
                        content=content,
                        source_url=f"facebook://{file_path.stem}",
                        source_type="facebook",
                        file_path=str(file_path),
                        language="sw"
                    )
                    
                    # Chunk and embed
                    chunks = await self.document_service.chunk_and_embed_document(
                        document_id=document.id,
                        content=content
                    )
                    
                    result["migrated"] += 1
                    logger.info(f"Migrated Facebook post {file_path.name}: {len(chunks)} chunks")
                
                except Exception as e:
                    error_msg = f"Failed to migrate Facebook post {file_path.name}: {e}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
            
        except Exception as e:
            error_msg = f"Failed to migrate Facebook posts: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
        
        return result
    
    async def verify_migration(self) -> Dict[str, Any]:
        """Verify that migration was successful"""
        try:
            stats = await self.document_service.get_document_stats()
            
            # Check for documents with embeddings
            async with async_session() as session:
                from sqlalchemy import text
                result = await session.execute(text("""
                    SELECT 
                        COUNT(DISTINCT d.id) as total_documents,
                        COUNT(c.id) as total_chunks,
                        COUNT(CASE WHEN c.embedding IS NOT NULL THEN 1 END) as chunks_with_embeddings
                    FROM documents d
                    LEFT JOIN chunks c ON d.id = c.document_id
                """))
                
                row = result.fetchone()
                verification = {
                    "total_documents": row.total_documents,
                    "total_chunks": row.total_chunks,
                    "chunks_with_embeddings": row.chunks_with_embeddings,
                    "migration_successful": row.chunks_with_embeddings > 0
                }
            
            logger.info(f"Migration verification: {verification}")
            return verification
            
        except Exception as e:
            logger.error(f"Migration verification failed: {e}")
            return {"migration_successful": False, "error": str(e)}

async def main():
    """Run the complete migration process"""
    migration_service = DataMigrationService()
    
    logger.info("Starting data migration to PostgreSQL")
    
    # Initialize database
    from pipeline.db.init_db import init_db
    await init_db()
    
    # Migrate existing data
    results = await migration_service.migrate_existing_chunks()
    logger.info(f"Chunks migration: {results}")
    
    # Migrate scraped content
    scraped_results = await migration_service.migrate_scraped_content()
    logger.info(f"Scraped content migration: {scraped_results}")
    
    # Migrate Facebook posts
    fb_results = await migration_service.migrate_facebook_posts()
    logger.info(f"Facebook posts migration: {fb_results}")
    
    # Verify migration
    verification = await migration_service.verify_migration()
    logger.info(f"Migration verification: {verification}")
    
    if verification["migration_successful"]:
        logger.info("Migration completed successfully!")
    else:
        logger.error("Migration verification failed")

if __name__ == "__main__":
    asyncio.run(main())
