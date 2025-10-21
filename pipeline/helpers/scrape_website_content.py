import aiohttp
from bs4 import BeautifulSoup

from pipeline.helpers.headers import HEADERS


async def scrape_website_content(url: str) -> str:
    """Scrape website content asynchronously."""
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url, timeout=15) as response:
                text = await response.text()

        soup = BeautifulSoup(text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "aside"]):
            tag.decompose()

        lines = (line.strip() for line in soup.get_text().splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return "\n".join(chunk for chunk in chunks if chunk)
    except Exception as e:
        return f"Error scraping website: {e}"