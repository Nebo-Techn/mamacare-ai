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
