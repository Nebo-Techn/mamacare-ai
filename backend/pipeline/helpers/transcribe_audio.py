import asyncio
from pathlib import Path


async def transcribe_audio(file_path: Path, language="sw") -> str:
    """Transcribe audio using Whisper."""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda: model.transcribe(str(file_path), language=language))
    return result.get("text", "")