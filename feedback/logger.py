import aiofiles
import json
from typing import List

from feedback.schema import FeedbackSchema

RESULT_FILE = "feedback/result.json"

async def log_feedback(interaction_id: str, query: str, answer: str, sources: list, feedback: str, file_path: str = RESULT_FILE):
    entry = {
        "interaction_id": interaction_id,
        "query": query,
        "answer": answer,
        "sources": sources,
        "feedback": feedback
    }
    async with aiofiles.open(file_path, "a", encoding="utf-8") as f:
        await f.write(json.dumps(entry, ensure_ascii=False) + "\n")

async def log_multiple_feedbacks(feedbacks: List[FeedbackSchema]):
    async with aiofiles.open(RESULT_FILE, mode="a") as f:
        for fb in feedbacks:
            await f.write(json.dumps(fb.dict()) + "\n")
