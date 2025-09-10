from typing import List

def build_rag_prompt(system_prompt: str, context_chunks: List[str], user_query: str) -> str:
    context = "\n\n".join(context_chunks)
    prompt = f"{system_prompt}\n\nContext:\n{context}\n\nUser Query: {user_query}"
    return prompt
