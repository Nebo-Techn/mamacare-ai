import aiohttp
import asyncio
from typing import Dict, Any, Optional
import os
import torch

from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline as hf_pipeline

try:
    from langchain import HuggingFacePipeline
except Exception:
    HuggingFacePipeline = None


class Generator:
    """
    Unified generator that wraps a local Hugging Face model via transformers pipeline.
    - Initializes tokenizer/model from a local path (or HF repo) with optional use_auth_token.
    - Provides async `generate` which runs the sync pipeline in an executor and returns generated text.
    """

    def __init__(self, local_model_path: Optional[str] = None, hf_token: Optional[str] = None):
        self.local_model_path = local_model_path
        self.hf_token = hf_token
        self._pipeline = None
        self.llm = None
        if self.local_model_path:
            self._init_local_model()

    def _init_local_model(self):
        device = 0 if torch.cuda.is_available() else -1

        tokenizer = AutoTokenizer.from_pretrained(self.local_model_path, use_auth_token=self.hf_token)
        model = AutoModelForCausalLM.from_pretrained(self.local_model_path, use_auth_token=self.hf_token)

        # create a transformers pipeline (sync)
        self._pipeline = hf_pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            device=device,
            return_full_text=True
        )

        # optional LangChain wrapper (kept for compatibility)
        if HuggingFacePipeline is not None:
            try:
                self.llm = HuggingFacePipeline(pipeline=self._pipeline)
            except Exception:
                self.llm = None

    async def generate(self, prompt: str, max_new_tokens: int = 256, do_sample: bool = False) -> str:
        """
        Async wrapper around the transformers pipeline.
        Returns the generated text with the prompt stripped when present.
        """
        if self._pipeline is None:
            raise RuntimeError("No model initialized. Provide local_model_path when creating Generator.")

        loop = asyncio.get_event_loop()

        def _call_pipeline():
            outputs = self._pipeline(prompt, max_new_tokens=max_new_tokens, do_sample=do_sample)
            return outputs[0].get("generated_text", "")

        generated = await loop.run_in_executor(None, _call_pipeline)

        # strip the prompt from the generated text if included
        if generated.startswith(prompt):
            return generated[len(prompt):].strip()
        return generated.strip()
