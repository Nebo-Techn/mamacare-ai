from pipeline.extraction.content_ingestion import TEXT_DIR
from pipeline.helpers import sanitize_filename


async def save_content(name: str, content: str, source_url: str):
    """Save content to file and DB."""
    filename = TEXT_DIR / f"{sanitize_filename(name)}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    # Save to SQLite DB asynchronously
    await save_extracted_data("extracted", {"name": name, "content": content, "source_url": source_url})
    print(f"Saved content: {filename}")