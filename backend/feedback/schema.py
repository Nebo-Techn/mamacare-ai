from pydantic import BaseModel
from typing import List, Optional

class FeedbackSchema(BaseModel):
    interaction_id: str
    query: str
    answer: str
    sources: List[str]
    feedback: Optional[str]
