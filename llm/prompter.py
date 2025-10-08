from typing import List, Dict
from langchain_core.prompts import PromptTemplate

def preprocess_chunks(context_chunks: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen_texts = set()
    filtered = []
    for chunk in context_chunks:
        text = chunk.get("text", "").strip()
        source = chunk.get("source", "").strip() if chunk.get("source") else "local"
        if not text:
            continue
        if text in seen_texts:
            continue
        seen_texts.add(text)
        if "dalili" in text.lower() or "ishara" in text.lower() or "•" in text or "-" in text:
            filtered.append({"text": text, "source": source})
    return filtered if filtered else [{"text": c.get("text","").strip(), "source": (c.get("source") or "local")} for c in context_chunks if c.get("text","").strip()]

def get_rag_prompt_template() -> PromptTemplate:
    template = (
        "Wewe ni msaidizi wa afya ya uzazi kwa akina mama. Jibu swali lifuatalo kwa Kiswahili, "
        "ukitumia tu taarifa kutoka kwenye muktadha. Jibu kwa ufupi na kwa vitendo.\n\n"
        "Mfano:\n"
        "• Kichefuchefu (Chanzo: https://afyamaridhawa.com)\n"
        "• Kutapika (Chanzo: https://afyamaridhawa.com)\n\n"
        "Muktadha:\n"
        "{context}\n\n"
        "Swali: {query}\n"
        "Jibu:"
    )
    return PromptTemplate(template=template, input_variables=["context", "query"])

def build_rag_prompt(context_chunks: List[Dict[str, str]], user_query: str) -> str:
    """
    Build a prompt using a LangChain PromptTemplate.
    - context_chunks: list of {"text": "...", "source": "..."} where text should be an answer/paragraph.
    - user_query: the user's question (Kiswahili).
    """
    context_chunks = preprocess_chunks(context_chunks)
    # Build context string: each chunk as "Chanzo: {source}\nJibu: {text}"
    context = "\n\n".join([f"Chanzo: {c.get('source','local')}\nJibu: {c.get('text','')}" for c in context_chunks])
    template = get_rag_prompt_template()
    return template.format(context=context, query=user_query)
