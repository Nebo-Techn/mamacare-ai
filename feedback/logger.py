import aiofiles
import json
import asyncio
from feedback.schema import FeedbackSchema
from typing import List

RESULT_FILE = "feedback/result.json"

async def log_feedback(feedback: FeedbackSchema):
    async with aiofiles.open(RESULT_FILE, mode="a") as f:
        await f.write(json.dumps(feedback.dict()) + "\n")

async def log_multiple_feedbacks(feedbacks: List[FeedbackSchema]):
    async with aiofiles.open(RESULT_FILE, mode="a") as f:
        for fb in feedbacks:
            await f.write(json.dumps(fb.dict()) + "\n")
