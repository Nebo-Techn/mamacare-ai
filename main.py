import pickle
import json
import numpy as np
import uuid
import asyncio

from embeddings.embedder import AsyncEmbedder
from vectorstore.faiss_store import AsyncFaissStore
from query.retriever import retrieve_relevant_chunks
from llm.prompter import build_rag_prompt, preprocess_chunks
from llm.generator import AsyncLLMGenerator
from feedback.logger import log_feedback


async def main():
    # Load existing chunks
    with open("trimester1_chunks.pkl", "rb") as f:
        existing_chunks = pickle.load(f)

    # Load Q&A pairs from maternal_qa_train.jsonl and convert to chunks
    with open("maternal_qa_train.jsonl", "r", encoding="utf-8") as f:
        qa_chunks = [json.loads(line) for line in f]
    rag_chunks = [
        {
            "text": qa['answer'],
            "source": "maternal_qa_train"
        }
        for qa in qa_chunks
    ]

    # Combine all chunks
    all_chunks = existing_chunks + rag_chunks

    # Step 1: Embed all chunks
    embedder = AsyncEmbedder()
    texts = [chunk["text"] for chunk in all_chunks]
    embeddings = await embedder.embed_texts(texts)
    embeddings = np.array(embeddings)

    # Step 2: Build and save FAISS index
    faiss_store = AsyncFaissStore(dim=embeddings.shape[1])
    await faiss_store.add_embeddings(embeddings, all_chunks)
    await faiss_store.save("faiss_index.bin", "faiss_meta.pkl")

    # Step 3: Query and retrieve relevant chunks
    user_query = input("Andika swali lako kuhusu afya ya uzazi: ")
    results = await retrieve_relevant_chunks(
        user_query,
        "faiss_index.bin",
        "faiss_meta.pkl",
        k=10,
        min_score=None
    )
    retrieved_chunks = preprocess_chunks(results)[:10]

    # After retrieval, prioritize exact match from Q&A
    exact_match = next((chunk for chunk in retrieved_chunks if user_query.lower() in chunk["text"].lower()), None)
    if exact_match:
        retrieved_chunks = [exact_match] + [chunk for chunk in retrieved_chunks if chunk != exact_match]

    # Step 4: Build prompt and generate answer
    prompt = build_rag_prompt(retrieved_chunks, user_query)
    llm_generator = AsyncLLMGenerator(model_path="./LoRA/lora_maternal_model")
    answer = await llm_generator.generate(prompt)
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