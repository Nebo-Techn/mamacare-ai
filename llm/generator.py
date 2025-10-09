import aiohttp
import asyncio
from typing import Dict, Any, Optional
import os
from peft import PeftModel
import torch
import os
from pathlib import Path

from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline as hf_pipeline

try:
    from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
except Exception:
    HuggingFacePipeline = None

LOCAL_MODEL_DIR = r"C:\Users\User\Documents\mamacare_project\Afyamama_AI\LORA_MATERNAL_MODEL\models--NeboTech--maternal-chatbot-swaLlama"


class Generator:
    """
    Unified generator that wraps a local Hugging Face model via transformers pipeline.
    - Detects nested snapshot folders (snapshots/<hash>) under provided local_model_path.
    - Loads full model or loads base + applies PEFT/LoRA adapter if adapter-only.
    - Provides async `generate` which runs the sync pipeline in an executor and returns generated text.
    """

    def __init__(self, local_model_path: Optional[str] = None, hf_token: Optional[str] = None, device="cuda"):
        self.local_model_path = local_model_path
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        self._pipeline = None
        self.device = device
        self.llm = None
        # Try to initialize but never crash the app if models are unavailable
        try:
            if self.local_model_path:
                self._init_local_model()
        except Exception as e:
            print(f"[Generator] Skipping local model init: {e}")
            self._pipeline = None
            self.llm = None

    def _find_model_dir(self, base: Path) -> Path:
        for root, dirs, files in os.walk(base):
            files_set = set(files)
            if any(n in files_set for n in ("tokenizer.json", "tokenizer_config.json", "adapter_config.json", "adapter_model.safetensors", "pytorch_model.bin", "pytorch_model.safetensors", "config.json")):
                return Path(root)
        raise FileNotFoundError(f"No model snapshot directory found under {base}")

    def _init_local_model(self):
        device = 0 if torch.cuda.is_available() else -1

        model_path = Path(self.local_model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"local_model_path not found: {model_path}")

        model_dir = self._find_model_dir(model_path)
        hf_token = self.hf_token

        has_full = any(model_dir.joinpath(n).exists() for n in ("pytorch_model.bin", "pytorch_model.safetensors"))
        has_adapter = any(model_dir.joinpath(n).exists() for n in ("adapter_model.bin", "adapter_model.safetensors", "adapter_config.json"))

        if has_adapter and not has_full:
            # LoRA adapter detected
            base_local = os.getenv("BASE_MODEL_LOCAL", "").strip()
            base_hf = os.getenv("BASE_MODEL_HF", "").strip()  # e.g. "meta-llama/Llama-2-7b-chat-hf"

            if base_local and Path(base_local).exists():
                print(f"Loading base model from local: {base_local}")
                tokenizer = AutoTokenizer.from_pretrained(base_local, token=hf_token)
                base = AutoModelForCausalLM.from_pretrained(base_local, token=hf_token, device_map="auto")
            elif base_hf:
                print(f"Loading base model from HF: {base_hf}")
                tokenizer = AutoTokenizer.from_pretrained(base_hf, token=hf_token)
                base = AutoModelForCausalLM.from_pretrained(base_hf, token=hf_token, device_map="auto")
            else:
                raise RuntimeError(
                    "LoRA adapter detected but no base model configured. "
                    "Provide BASE_MODEL_LOCAL or BASE_MODEL_HF environment variable."
                )

            # Merge base + adapter
            print(f"Applying adapter from {model_dir}")
            model = PeftModel.from_pretrained(base, model_dir, token=hf_token, device_map="auto")

        else:
            # Full model
            tokenizer = AutoTokenizer.from_pretrained(model_dir, use_auth_token=hf_token)
            model = AutoModelForCausalLM.from_pretrained(model_dir, use_auth_token=hf_token, device_map="auto")

        self._pipeline = hf_pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            device=device,
            return_full_text=True
        )

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
