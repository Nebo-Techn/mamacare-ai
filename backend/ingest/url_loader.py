import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List

async def fetch_url_text(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            # Remove scripts/styles
            for tag in soup(["script", "style"]):
                tag.decompose()
            text = soup.get_text(separator=" ", strip=True)
            return text

async def fetch_texts_from_urls(urls: List[str]) -> List[str]:
    tasks = [fetch_url_text(url) for url in urls]
    return await asyncio.gather(*tasks)
