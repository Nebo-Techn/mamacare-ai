from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pipeline.db.connection import Base
import uuid
from sqlalchemy.types import UserDefinedType

class Vector(UserDefinedType):
    def __init__(self, dimensions):
        self.dimensions = dimensions

    def get_col_spec(self, **kw):
        return f"vector({self.dimensions})"

    def bind_processor(self, dialect):
        def process(value):
            return value
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            return value
        return process

class Document(Base):
    """Stores original documents and their metadata"""
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    source_url = Column(String(1000))
    source_type = Column(String(50), nullable=False)  # 'pdf', 'url', 'facebook', 'youtube'
    file_path = Column(String(500))  # For local files
    language = Column(String(10), default='sw')  # Language code
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    interactions = relationship("Interaction", back_populates="document")

class Chunk(Base):
    """Stores text chunks with embeddings"""
    __tablename__ = "chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Order within document
    token_count = Column(Integer)
    embedding = Column(Vector(768))  # Use your actual embedding dimension
    chunk_metadata = Column(Text)  # JSON metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    interactions = relationship("Interaction", back_populates="chunk")
    
    # Index for vector similarity search
    __table_args__ = (
        Index('idx_chunk_embedding', 'embedding', postgresql_using='ivfflat'),
    )

class Interaction(Base):
    """Stores user queries and system responses"""
    __tablename__ = "interactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    query = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("chunks.id"))
    retrieval_score = Column(Float)  # Similarity score
    user_feedback = Column(Text)  # User feedback on answer quality
    feedback_rating = Column(Integer)  # 1-5 rating
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="interactions")
    chunk = relationship("Chunk", back_populates="interactions")

class ExtractedContent(Base):
    """Legacy table for backward compatibility"""
    __tablename__ = "extracted_content"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    source_url = Column(String(512), nullable=False)
