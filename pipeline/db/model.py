from sqlalchemy import Column, Integer, String, Text
from pipeline.db.connection import Base

class ExtractedContent(Base):
    __tablename__ = "extracted_content"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    source_url = Column(String(512), nullable=False)
