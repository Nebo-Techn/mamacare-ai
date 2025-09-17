import asyncio
import pickle
import numpy as np
import uuid

from embeddings.embedder import AsyncEmbedder
from vectorstore.faiss_store import AsyncFaissStore
from query.retriever import retrieve_relevant_chunks
from llm.prompter import build_rag_prompt, preprocess_chunks
from llm.generator import AsyncLLMGenerator
from feedback.logger import log_feedback

async def main():
    # Step 1: Load chunks and embed
    with open("trimester1_chunks.pkl", "rb") as f:
        chunks = pickle.load(f)
    texts = [chunk["text"] for chunk in chunks]
    embedder = AsyncEmbedder()
    embeddings = await embedder.embed_texts(texts)
    embeddings = np.array(embeddings)

    # Step 2: Build and save FAISS index
    faiss_store = AsyncFaissStore(dim=embeddings.shape[1])
    await faiss_store.add_embeddings(embeddings, chunks)
    await faiss_store.save("faiss_index.bin", "faiss_meta.pkl")

    # Step 3: Query and retrieve relevant chunks (improved retrieval)
    user_query = "SABABU 10 ZA MAUMIVU YA KIUNO, NYONGA, CHINI YA KITOVU KWA WANAWAKE."
    results = await retrieve_relevant_chunks(
        user_query,
        "faiss_index.bin",
        "faiss_meta.pkl",
        k=20,  # Increase k for more context
        min_score=None
    )
    # Use only the most relevant chunks mentioning "dalili" or lists
    retrieved_chunks = preprocess_chunks(results)[:10]

    # Step 4: Build prompt and generate answer
    prompt = build_rag_prompt(retrieved_chunks, user_query)
    answer = await AsyncLLMGenerator.generate_answer_ollama(prompt, model="gemma:2b")
    print("User Query:", user_query)
    print("Answer:", answer)

    # Improved source handling
    sources = [chunk.get("source", "") for chunk in retrieved_chunks if chunk.get("source", "")]
    sources = list(dict.fromkeys(sources))  # Deduplicate and preserve order

    print("Sources:")
    for src in sources:
        print("-", src)

    # Step 5: Collect and log feedback
    user_feedback = input("Je, jibu hili limekusaidia? (Andika maoni yako): ")
    interaction_id = str(uuid.uuid4())
    await log_feedback(
        interaction_id=interaction_id,
        query=user_query,
        answer=answer,
        sources=sources,
        feedback=user_feedback
    )

if __name__ == "__main__":
    asyncio.run(main())