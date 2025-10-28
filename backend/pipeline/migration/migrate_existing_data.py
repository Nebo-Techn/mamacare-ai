import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import pickle
import json
import logging
import uuid

from backend.pipeline.db.connection import async_session
from backend.pipeline.db.model import Document, Chunk
from backend.pipeline.services.document_service import DocumentService
from backend.pipeline.embeddings.embedder import AsyncEmbedder
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _embedding_to_pgvector_literal(emb: List[float]) -> str:
    """Convert embedding list to pgvector literal string: '[0.1,0.2,...]'"""
    return "[" + ",".join(str(float(x)) for x in emb) + "]"

class DataMigrationService:
    """Service to migrate existing data to PostgreSQL"""

    def __init__(self):
        self.embedder = AsyncEmbedder()
        self.document_service = DocumentService()

    async def migrate_existing_chunks(
        self,
        chunks_file: str = "trimester1_chunks.pkl",
        qa_file: str = "maternal_qa_train.jsonl"
    ) -> Dict[str, Any]:
        results = {"chunks_migrated": 0, "qa_migrated": 0, "errors": []}

        # detect embedder output dimension (best-effort)
        embedding_dim: Optional[int] = None
        try:
            sample = await self.embedder.embed_text("test")
            if sample:
                embedding_dim = len(sample)
            logger.info("Detected embedder output dimension: %s", embedding_dim)
        except Exception as e:
            logger.warning("Could not detect embedder dimension automatically: %s", e)
            embedding_dim = None

        # Migrate chunks if file exists
        chunks_path = Path(chunks_file)
        if chunks_path.exists():
            try:
                cr = await self._migrate_chunks_file(chunks_file, embedding_dim)
                results["chunks_migrated"] = cr.get("migrated", 0)
                results["errors"].extend(cr.get("errors", []))
            except Exception as e:
                logger.error("Chunks migration failed: %s", e)
                results["errors"].append(str(e))
        else:
            logger.info("Chunks file not found: %s", chunks_file)

        # Q&A migration placeholder (kept minimal)
        qa_path = Path(qa_file)
        if qa_path.exists():
            try:
                qr = await self._migrate_qa_file(qa_file, embedding_dim)
                results["qa_migrated"] = qr.get("migrated", 0)
                results["errors"].extend(qr.get("errors", []))
            except Exception as e:
                logger.error("QA migration failed: %s", e)
                results["errors"].append(str(e))
        else:
            logger.info("QA file not found: %s", qa_file)

        logger.info("Migration completed: %s chunks, %s Q&A pairs", results["chunks_migrated"], results["qa_migrated"])
        return results

    async def _migrate_chunks_file(self, chunks_file: str, embedding_dim: Optional[int]) -> Dict[str, Any]:
        """Load chunks from a pickle file and insert into DB with safe handling of embeddings."""
        result = {"migrated": 0, "errors": []}

        # load chunks: expected to be iterable of dict-like items
        with open(chunks_file, "rb") as f:
            try:
                chunks_data = pickle.load(f)
            except Exception as e:
                logger.error("Failed to load chunks pickle: %s", e)
                return {"migrated": 0, "errors": [str(e)]}

        # normalize to list
        if not isinstance(chunks_data, (list, tuple)):
            chunks_list = list(chunks_data)
        else:
            chunks_list = chunks_data

        insert_sql = text("""
            INSERT INTO chunks (id, document_id, content, chunk_index, token_count, embedding, chunk_metadata)
            VALUES (:id, :document_id, :content, :chunk_index, :token_count, :embedding::vector, :chunk_metadata)
            RETURNING id
        """)

        async with async_session() as session:
            for raw in chunks_list:
                try:
                    # raw can be dict-like; build a safe chunk dict
                    chunk = dict(raw) if not isinstance(raw, dict) else raw.copy()
                    # ensure ids exist
                    chunk_id = chunk.get("id") or uuid.uuid4()
                    document_id = chunk.get("document_id") or uuid.uuid4()
                    content = chunk.get("content", "")[:100000]  # cap to avoid overly long inserts
                    chunk_index = int(chunk.get("chunk_index", 0))
                    token_count = int(chunk.get("token_count", 0))
                    emb = chunk.get("embedding", None)
                    metadata = chunk.get("chunk_metadata") or {}

                    # ensure metadata is JSON-serializable dict
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except Exception:
                            metadata = {"raw": metadata}

                    # Decide how to store embedding
                    emb_param = None
                    if emb is None:
                        emb_param = None
                    elif isinstance(emb, (list, tuple)):
                        if embedding_dim is None or len(emb) == embedding_dim:
                            emb_param = _embedding_to_pgvector_literal(emb)
                        else:
                            # dimension mismatch -> store raw embedding in metadata and keep embedding NULL
                            metadata["embedding_raw"] = emb
                            emb_param = None
                            logger.warning(
                                "Embedding dim mismatch for chunk %s: %s (expected %s). Storing in metadata.",
                                chunk_id, len(emb), embedding_dim
                            )
                    else:
                        # unknown type: try to coerce to list
                        try:
                            emb_list = list(emb)
                            if embedding_dim is None or len(emb_list) == embedding_dim:
                                emb_param = _embedding_to_pgvector_literal(emb_list)
                            else:
                                metadata["embedding_raw"] = emb_list
                                emb_param = None
                        except Exception:
                            metadata["embedding_raw"] = str(emb)
                            emb_param = None

                    params = {
                        "id": str(chunk_id),
                        "document_id": str(document_id),
                        "content": content,
                        "chunk_index": chunk_index,
                        "token_count": token_count,
                        "embedding": emb_param,
                        "chunk_metadata": json.dumps(metadata),
                    }

                    await session.execute(insert_sql, params)
                    result["migrated"] += 1

                except Exception as e:
                    logger.error("Failed to insert chunk %s: %s", raw.get("id", "<unknown>"), e)
                    result["errors"].append({"chunk_id": raw.get("id", None), "error": str(e)})
            await session.commit()

        return result

    async def _migrate_qa_file(self, qa_file: str, embedding_dim: Optional[int]) -> Dict[str, Any]:
        """Minimal QA migration: keep entries, attach embeddings similarly to chunks."""
        # For now, return empty result — implement as needed for your QA format
        return {"migrated": 0, "errors": []}

    async def migrate_scraped_content(self, content_dir: str = "scraped_content") -> Dict[str, Any]:
        return {"migrated": 0, "errors": []}

    async def migrate_facebook_posts(self, posts_dir: str = "facebook_posts") -> Dict[str, Any]:
        return {"migrated": 0, "errors": []}

    async def verify_migration(self) -> Dict[str, Any]:
        # simple verification hook; expand as needed
        return {"verified": True}

async def main():
    """Run the complete migration process"""
    migration_service = DataMigrationService()

    logger.info("Starting data migration to PostgreSQL")

    # Initialize database
    from backend.pipeline.db.init_db import init_db
    await init_db()

    # Run migration
    res = await migration_service.migrate_existing_chunks()
    logger.info("Migration result: %s", res)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
