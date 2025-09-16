from typing import List, Dict

def preprocess_chunks(context_chunks: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen_texts = set()
    filtered = []
    for chunk in context_chunks:
        text = chunk.get("text", "").strip()
        source = chunk.get("source", "").strip()
        if not text or not source:
            continue
        if text in seen_texts:
            continue
        seen_texts.add(text)
        # Prioritize chunks mentioning "dalili" or containing bullet points
        if "dalili" in text.lower() or "ishara" in text.lower() or "•" in text or "-" in text:
            filtered.append({"text": text, "source": source})
    # If none found, fallback to all chunks
    return filtered if filtered else context_chunks

def build_rag_prompt(context_chunks: List[Dict[str, str]], user_query: str) -> str:
    # Post-process chunks before building prompt
    context_chunks = preprocess_chunks(context_chunks)
    system_prompt = (
        "Wewe ni msaidizi wa afya ya uzazi kwa akina mama. "
        "Jibu swali lifuatalo kwa Kiswahili, ukitumia tu taarifa kutoka kwenye muktadha. "
        "Tafadhali orodhesha dalili za mimba changa kwa kutumia alama za nukta (•) na taja chanzo cha kila dalili."
    )
    context = "\n\n".join([f"Chanzo: {c['source']}\nMaandishi: {c['text']}" for c in context_chunks])
    prompt = (
        f"{system_prompt}\n\nMuktadha:\n{context}\n\n"
        f"Swali: {user_query}\n"
        "Jibu kwa kutumia taarifa kutoka kwenye muktadha pekee, na orodhesha dalili kwa nukta na chanzo."
        "\nJibu:"
    )
    return prompt
