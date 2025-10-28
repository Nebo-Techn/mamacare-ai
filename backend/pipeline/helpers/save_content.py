from pathlib import Path
from backend.pipeline.db.connection import async_session
from backend.pipeline.db.model import ExtractedContent
from backend.pipeline.helpers import sanitize_filename
from backend.pipeline.contants.contants import TEXT_DIR




async def save_content(name: str, content: str, source_url: str):
    """Save extracted content to file and Postgres DB."""
    # Save to local text file
    filename = TEXT_DIR / f"{sanitize_filename(name)}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    # Save to Postgres
    async with async_session() as session:
        new_entry = ExtractedContent(
            name=name,
            content=content,
            source_url=source_url
        )
        session.add(new_entry)
        await session.commit()

    print(f"Saved content: {filename} and record in Postgres.")
