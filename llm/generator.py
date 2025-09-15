import aiohttp
import asyncio
from typing import Dict, Any

class AsyncLLMGenerator:
    def __init__(self, ollama_url: str, model: str):
        self.ollama_url = ollama_url.rstrip("/")
        self.model = model

    async def generate(self, prompt: str, options: Dict[str, Any] = None) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
        }
        if options:
            payload.update(options)
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.ollama_url}/api/generate", json=payload) as response:
                result = await response.json()
                return result.get("response", "")
            
    @staticmethod
    async def generate_answer_ollama(prompt: str, model: str = "gemma:2b"):
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("response", "")

    # Usage example:
    # import asyncio
    # from llm.prompter import build_rag_prompt
    # context_chunks = [...]  # from retriever
    # user_query = "Dalili za mimba changa ni zipi?"
    # prompt = build_rag_prompt(context_chunks, user_query)
    # answer = asyncio.run(generate_answer_ollama(prompt))
    # print(answer)
