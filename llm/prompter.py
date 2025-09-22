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
        '''
            Wewe ni msaidizi wa afya ya uzazi kwa akina mama. Jibu swali lifuatalo kwa Kiswahili, ukitumia tu taarifa kutoka kwenye muktadha. 
            Tafadhali orodhesha dalili za mimba changa kwa nukta (•) na taja chanzo cha kila dalili.

            Mfano:
            • Kichefuchefu (Chanzo: https://afyamaridhawa.com)
            • Kutapika (Chanzo: https://afyamaridhawa.com)

            Muktadha:
            Chanzo: https://afyamaridhawa.com
            Jibu: Mama mjamzito anaweza kupata kichefuchefu, uchovu, na maumivu ya kichwa.

            Swali: Je, ni dalili zipi za mimba changa?
            Jibu:

        '''
    )
    context = "\n\n".join([f"Chanzo: {c['source']}\nJibu: {c['text']}" for c in context_chunks])
    prompt = f"{system_prompt}\n\nMuktadha:\n{context}\n\nSwali: {user_query}\nJibu:"
    return prompt
