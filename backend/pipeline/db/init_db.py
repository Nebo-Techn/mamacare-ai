import asyncio
import asyncpg
from backend.pipeline.db.connection import engine, Base, DATABASE_URL
from backend.pipeline.db.model import Document, Chunk, Interaction, ExtractedContent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_pgvector_extension():
    """Create pgvector extension if it doesn't exist"""
    try:
        # Parse the connection string to get individual components
        conn_str = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        
        conn = await asyncpg.connect(conn_str)
        
        # First, try to install the extension
        try:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            logger.info("pgvector extension created/verified")
        except Exception as ext_error:
            logger.warning(f"pgvector extension not available: {ext_error}")
            logger.info("Continuing without pgvector - using standard PostgreSQL")
            # We'll use a fallback approach for vector operations
        
        await conn.close()
    except Exception as e:
        logger.error(f"Failed to create pgvector extension: {e}")
        logger.info("Continuing without pgvector - using standard PostgreSQL")

async def init_db():
    """Initialize database with all tables and extensions"""
    try:
        # Create pgvector extension first
        await create_pgvector_extension()
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created successfully")
        
        # Create vector indexes for better performance
        await create_vector_indexes()
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

async def create_vector_indexes():
    """Create optimized indexes for vector similarity search"""
    try:
        conn_str = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(conn_str)
        
        # Create IVFFlat index for faster similarity search
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_embedding_ivfflat 
            ON chunks USING ivfflat (embedding vector_cosine_ops) 
            WITH (lists = 100);
        """)
        
        # Create HNSW index for even better performance (if supported)
        try:
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw 
                ON chunks USING hnsw (embedding vector_cosine_ops) 
                WITH (m = 16, ef_construction = 64);
            """)
            logger.info("HNSW index created for optimal performance")
        except Exception:
            logger.info("HNSW index not supported, using IVFFlat")
        
        # Create other useful indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_source_type ON documents(source_type);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_interactions_created_at ON interactions(created_at);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);")
        
        await conn.close()
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")
        raise

async def reset_db():
    """Reset database (drop all tables and recreate)"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        await init_db()
        logger.info("Database reset successfully")
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        raise

async def check_db_health():
    """Check database health and connection"""
    try:
        conn_str = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(conn_str)
        
        # Check if pgvector extension exists
        result = await conn.fetchval("SELECT 1 FROM pg_extension WHERE extname = 'vector';")
        if not result:
            logger.warning("pgvector extension not found")
        else:
            logger.info("pgvector extension is active")
        
        # Check table existence
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name IN ('documents', 'chunks', 'interactions')
        """)
        
        expected_tables = {'documents', 'chunks', 'interactions'}
        existing_tables = {row['table_name'] for row in tables}
        
        if expected_tables.issubset(existing_tables):
            logger.info("All required tables exist")
        else:
            missing = expected_tables - existing_tables
            logger.warning(f"Missing tables: {missing}")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "init":
            asyncio.run(init_db())
        elif command == "reset":
            asyncio.run(reset_db())
        elif command == "health":
            asyncio.run(check_db_health())
        else:
            print("Usage: python init_db.py [init|reset|health]")
    else:
        asyncio.run(init_db())