import asyncio
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from pipeline.db.connection import async_session
from pipeline.db.model import Document, Chunk
from pipeline.services.document_service import DocumentService
from pipeline.helpers.scrape_website_content import scrape_website_content
from pipeline.helpers.facebook_scraper import scrape_facebook_content
from pipeline.helpers.get_youtube_transcript import get_youtube_transcript
from pipeline.helpers.transcribe_audio import transcribe_audio_file
from pipeline.helpers.save_content import save_content_to_file
from pipeline.helpers.sanitize_filename import sanitize_filename
from pipeline.helpers.headers import HEADERS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentIngestionService:
    """Enhanced content ingestion service with PostgreSQL storage"""
    
    def __init__(self):
        self.document_service = DocumentService()
        self.scraped_content_dir = Path("scraped_content")
        self.scraped_content_dir.mkdir(exist_ok=True)
    
    async def ingest_url(
        self,
        url: str,
        title: Optional[str] = None,
        source_type: str = "url"
    ) -> Dict[str, Any]:
        """Ingest content from a URL and store in PostgreSQL"""
        try:
            logger.info(f"Ingesting URL: {url}")
            
            # Scrape content from URL
            content = await scrape_website_content(url)
            if not content or len(content.strip()) < 100:
                raise ValueError("Insufficient content extracted from URL")
            
            # Generate title if not provided
            if not title:
                title = self._extract_title_from_content(content, url)
            
            # Create document in database
            document = await self.document_service.create_document(
                title=title,
                content=content,
                source_url=url,
                source_type=source_type,
                language="sw"
            )
            
            # Chunk and embed the document
            chunks = await self.document_service.chunk_and_embed_document(
                document_id=document.id,
                content=content
            )
            
            # Save content to file for backup
            filename = sanitize_filename(title) + ".txt"
            file_path = self.scraped_content_dir / filename
            await save_content_to_file(content, file_path)
            
            logger.info(f"Successfully ingested URL: {title} ({len(chunks)} chunks)")
            
            return {
                "document_id": str(document.id),
                "title": title,
                "chunks_created": len(chunks),
                "file_path": str(file_path),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Failed to ingest URL {url}: {e}")
            return {
                "url": url,
                "error": str(e),
                "status": "failed"
            }
    
    async def ingest_youtube_video(
        self,
        video_url: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Ingest YouTube video transcript and store in PostgreSQL"""
        try:
            logger.info(f"Ingesting YouTube video: {video_url}")
            
            # Get transcript
            transcript = await get_youtube_transcript(video_url)
            if not transcript or len(transcript.strip()) < 100:
                raise ValueError("No transcript available or insufficient content")
            
            # Generate title if not provided
            if not title:
                title = f"YouTube Video - {video_url.split('v=')[-1] if 'v=' in video_url else 'Unknown'}"
            
            # Create document in database
            document = await self.document_service.create_document(
                title=title,
                content=transcript,
                source_url=video_url,
                source_type="youtube",
                language="sw"
            )
            
            # Chunk and embed the document
            chunks = await self.document_service.chunk_and_embed_document(
                document_id=document.id,
                content=transcript
            )
            
            # Save transcript to file
            filename = sanitize_filename(title) + ".txt"
            file_path = self.scraped_content_dir / filename
            await save_content_to_file(transcript, file_path)
            
            logger.info(f"Successfully ingested YouTube video: {title} ({len(chunks)} chunks)")
            
            return {
                "document_id": str(document.id),
                "title": title,
                "chunks_created": len(chunks),
                "file_path": str(file_path),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Failed to ingest YouTube video {video_url}: {e}")
            return {
                "url": video_url,
                "error": str(e),
                "status": "failed"
            }
    
    async def ingest_facebook_post(
        self,
        post_url: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Ingest Facebook post content and store in PostgreSQL"""
        try:
            logger.info(f"Ingesting Facebook post: {post_url}")
            
            # Scrape Facebook content
            content = await scrape_facebook_content(post_url)
            if not content or len(content.strip()) < 50:
                raise ValueError("Insufficient content extracted from Facebook post")
            
            # Generate title if not provided
            if not title:
                title = f"Facebook Post - {post_url.split('/')[-1]}"
            
            # Create document in database
            document = await self.document_service.create_document(
                title=title,
                content=content,
                source_url=post_url,
                source_type="facebook",
                language="sw"
            )
            
            # Chunk and embed the document
            chunks = await self.document_service.chunk_and_embed_document(
                document_id=document.id,
                content=content
            )
            
            # Save content to file
            filename = sanitize_filename(title) + ".txt"
            file_path = self.scraped_content_dir / filename
            await save_content_to_file(content, file_path)
            
            logger.info(f"Successfully ingested Facebook post: {title} ({len(chunks)} chunks)")
            
            return {
                "document_id": str(document.id),
                "title": title,
                "chunks_created": len(chunks),
                "file_path": str(file_path),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Failed to ingest Facebook post {post_url}: {e}")
            return {
                "url": post_url,
                "error": str(e),
                "status": "failed"
            }
    
    async def ingest_audio_file(
        self,
        audio_path: str,
        title: Optional[str] = None,
        source_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Ingest audio file by transcribing and storing in PostgreSQL"""
        try:
            logger.info(f"Ingesting audio file: {audio_path}")
            
            # Transcribe audio
            transcript = await transcribe_audio_file(audio_path)
            if not transcript or len(transcript.strip()) < 100:
                raise ValueError("No transcript generated or insufficient content")
            
            # Generate title if not provided
            if not title:
                title = Path(audio_path).stem
            
            # Create document in database
            document = await self.document_service.create_document(
                title=title,
                content=transcript,
                source_url=source_url,
                source_type="audio",
                file_path=audio_path,
                language="sw"
            )
            
            # Chunk and embed the document
            chunks = await self.document_service.chunk_and_embed_document(
                document_id=document.id,
                content=transcript
            )
            
            # Save transcript to file
            filename = sanitize_filename(title) + ".txt"
            file_path = self.scraped_content_dir / filename
            await save_content_to_file(transcript, file_path)
            
            logger.info(f"Successfully ingested audio file: {title} ({len(chunks)} chunks)")
            
            return {
                "document_id": str(document.id),
                "title": title,
                "chunks_created": len(chunks),
                "file_path": str(file_path),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Failed to ingest audio file {audio_path}: {e}")
            return {
                "file_path": audio_path,
                "error": str(e),
                "status": "failed"
            }
    
    async def ingest_text_file(
        self,
        file_path: str,
        title: Optional[str] = None,
        source_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Ingest text file and store in PostgreSQL"""
        try:
            logger.info(f"Ingesting text file: {file_path}")
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content or len(content.strip()) < 100:
                raise ValueError("File is empty or has insufficient content")
            
            # Generate title if not provided
            if not title:
                title = Path(file_path).stem
            
            # Create document in database
            document = await self.document_service.create_document(
                title=title,
                content=content,
                source_url=source_url,
                source_type="text_file",
                file_path=file_path,
                language="sw"
            )
            
            # Chunk and embed the document
            chunks = await self.document_service.chunk_and_embed_document(
                document_id=document.id,
                content=content
            )
            
            logger.info(f"Successfully ingested text file: {title} ({len(chunks)} chunks)")
            
            return {
                "document_id": str(document.id),
                "title": title,
                "chunks_created": len(chunks),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Failed to ingest text file {file_path}: {e}")
            return {
                "file_path": file_path,
                "error": str(e),
                "status": "failed"
            }
    
    async def batch_ingest_urls(
        self,
        urls: List[str],
        titles: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Batch ingest multiple URLs"""
        results = []
        
        for i, url in enumerate(urls):
            title = titles[i] if titles and i < len(titles) else None
            result = await self.ingest_url(url, title)
            results.append(result)
            
            # Small delay to avoid overwhelming servers
            await asyncio.sleep(1)
        
        return results
    
    async def get_ingestion_stats(self) -> Dict[str, Any]:
        """Get statistics about ingested content"""
        return await self.document_service.get_document_stats()
    
    def _extract_title_from_content(self, content: str, url: str) -> str:
        """Extract a meaningful title from content"""
        # Try to find the first heading or use URL
        lines = content.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if len(line) > 10 and len(line) < 200:
                return line
        
        # Fallback to URL-based title
        if 'youtube.com' in url:
            return f"YouTube Video - {url.split('v=')[-1] if 'v=' in url else 'Unknown'}"
        elif 'facebook.com' in url:
            return f"Facebook Post - {url.split('/')[-1]}"
        else:
            return f"Content from {url.split('/')[2] if len(url.split('/')) > 2 else 'Unknown'}"
    
    async def reindex_document(self, document_id: str) -> Dict[str, Any]:
        """Reindex a document (re-chunk and re-embed)"""
        try:
            doc_uuid = uuid.UUID(document_id)
            document = await self.document_service.get_document_by_id(doc_uuid)
            
            if not document:
                raise ValueError("Document not found")
            
            # Delete existing chunks
            async with async_session() as session:
                from sqlalchemy import delete
                await session.execute(delete(Chunk).where(Chunk.document_id == doc_uuid))
                await session.commit()
            
            # Re-chunk and re-embed
            chunks = await self.document_service.chunk_and_embed_document(
                document_id=doc_uuid,
                content=document.content
            )
            
            logger.info(f"✅ Successfully reindexed document: {document.title} ({len(chunks)} chunks)")
            
            return {
                "document_id": document_id,
                "title": document.title,
                "chunks_created": len(chunks),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to reindex document {document_id}: {e}")
            return {
                "document_id": document_id,
                "error": str(e),
                "status": "failed"
            }

# Usage example
async def main():
    """Example usage of the content ingestion service"""
    service = ContentIngestionService()
    
    # Example URLs to ingest
    urls = [
        "https://afyamaridhawa.com/zijue-dalili-za-mimba-changa-dalili-12-za-awali/",
        "https://www.tfnc.go.tz/tips/lishe-ya-mama-mjamzito"
    ]
    
    # Batch ingest URLs
    results = await service.batch_ingest_urls(urls)
    
    # Print results
    for result in results:
        if result["status"] == "success":
            print(f"{result['title']}: {result['chunks_created']} chunks")
        else:
            print(f"Failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())