import aiohttp
import asyncio
from typing import Dict, Any
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class AsyncLLMGenerator:
    def __init__(self, model_path: str = "./lora_maternal_model"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(model_path)

    async def generate(self, prompt: str, max_new_tokens: int = 256) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,      # ensure clean stop
                do_sample=False,                                # optional: add sampling for more natural answers
                top_p=0.9,                                     # nucleus sampling 
                temperature=1.0                                # control creativity vs determinism
            )
        decoded = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Remove the prompt from the output, keep only the answer

        if prompt in decoded:
            answer = decoded.split(prompt, 1)[-1].strip()

        else:
            answer = decoded.strip()

        if "Mwisho wa jibu" in answer:
            answer = answer.split("Mwisho wa jibu")[0].strip()

        import re
        answer = re.sub(r'\s+', ' ', answer).strip()

        return answer

    async def generate_legacy(self, prompt: str, options: Dict[str, Any] = None) -> str:
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
