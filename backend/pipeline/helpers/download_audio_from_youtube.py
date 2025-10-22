import asyncio
from pathlib import Path
from pipeline.extraction.content_ingestion import AUDIO_DIR
from pipeline.helpers import sanitize_filename


async def download_audio_from_youtube(url: str, name: str) -> Path:
    """Download YouTube audio to mp3."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    filepath = AUDIO_DIR / f"{sanitize_filename(name)}.mp3"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(filepath),
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'quiet': True,
    }

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: YoutubeDL(ydl_opts).download([url]))
    return filepath