import asyncio
from typing import Dict
from pipeline.extraction.helpers import get_youtube_transcript, save_content, scrape_website_content


async def process_link(name: str, url: str):
    """Process a single link (website or YouTube)."""
    print(f"Processing: {name} ({url})")
    if "youtube.com" in url or "youtu.be" in url:
        content = await get_youtube_transcript(url, name)
    else:
        content = await scrape_website_content(url)

    await save_content(name, content, url)


async def process_links(links: Dict[str, str]):
    """Process multiple links concurrently."""
    tasks = [process_link(name, url) for name, url in links.items() if url]
    await asyncio.gather(*tasks)