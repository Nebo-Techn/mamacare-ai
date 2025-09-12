import aiosqlite
import asyncio

DB_PATH = "pipeline/extraction/extracted_data.db"

async def save_extracted_data(table: str, data: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        values = tuple(data.values())
        await db.execute(f"CREATE TABLE IF NOT EXISTS {table} ({columns})")
        await db.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values)
        await db.commit()

# Example usage:
# await save_extracted_data("maternal_health", {"field1": "value1", "field2": "value2"})
