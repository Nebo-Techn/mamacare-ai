from typing import List, Dict

def build_rag_prompt(context_chunks: List[Dict[str, str]], user_query: str) -> str:
    system_prompt = (
        "You are a helpful maternal health assistant for mothers. "
        "Answer questions with accurate, supportive, and practical advice based on trusted sources."
    )
    context = "\n\n".join([f"Source: {c['source']}\nText: {c['text']}" for c in context_chunks])
    prompt = f"{system_prompt}\n\nContext:\n{context}\n\nQuestion: {user_query}\nAnswer:"
    return prompt
