import os
import asyncio
import aiohttp
import time
from pathlib import Path
from typing import List, Dict
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from yt_dlp import YoutubeDL
import whisper


from pipeline.extraction.helpers.process_link import process_links

# Initialize Whisper model (small/medium/large)
model = whisper.load_model("small")

# Folders
AUDIO_DIR = Path("audio")
TEXT_DIR = Path("scraped_content")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
TEXT_DIR.mkdir(parents=True, exist_ok=True)

# User-Agent for web scraping
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}


if __name__ == "__main__":
    # Admin can dynamically load links from JSON or database
    import json

    LINKS_FILE = "links.json"  # e.g., editable via admin UI
    if Path(LINKS_FILE).exists():
        with open(LINKS_FILE, "r", encoding="utf-8") as f:
            links = json.load(f)
    else:
        links = {}  # fallback empty dict

    asyncio.run(process_links(links))