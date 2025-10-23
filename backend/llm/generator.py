import asyncio
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline as hf_pipeline
from typing import Optional
import os

try:
    from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
except Exception:
    HuggingFacePipeline = None


class Generator:
    """
    Unified generator for a Hugging Face Hub model.
    - Loads the model directly from HF Hub.
    - Runs on GPU (CUDA) if available, otherwise CPU.
    - Provides async `generate` for easy integration in RAG or chat APIs.
    """

    def __init__(self,model_id: str,
                 hf_token: Optional[str] = None,
                 device: str = "cuda"):
        """
        Args:
            model_id (str): Hugging Face Hub repo ID, e.g. "mamacare-ai/maternal-swahili-model"
            hf_token (str, optional): Hugging Face access token
            device (str): "cuda" or "cpu"
        """
        self.model_id = model_id
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        self.device = 0 if torch.cuda.is_available() and device == "cuda" else -1
        self._pipeline = None
        self.llm = None

        try:
            self._init_hf_model()
        except Exception as e:
            print(f"[Generator] Failed to initialize model: {e}")
            self._pipeline = None
            self.llm = None

    def _init_hf_model(self):
        print(f"[Generator] Loading model from Hugging Face Hub: {self.model_id}")

        tokenizer = AutoTokenizer.from_pretrained(
            self.model_id,
            token=self.hf_token
        )

        model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                token=self.hf_token,
                device_map=None,  # disables accelerate auto-mapping
            )

        # If the model was loaded with device_map (accelerate), do NOT pass device to the pipeline
        pipeline_kwargs = {
            "model": model,
            "tokenizer": tokenizer,
            "return_full_text": True,
        }
        if getattr(model, "device_map", None) in (None, {}, "auto") or model.device_map is None:
            # safe to pass device index (-1 for cpu)
            pipeline_kwargs["device"] = self.device

        self._pipeline = hf_pipeline("text-generation", **pipeline_kwargs)

        try:
            self.llm = HuggingFacePipeline(pipeline=self._pipeline)
        except Exception:
            self.llm = None

        print("[Generator] Model loaded successfully ✅")

    async def generate(self, prompt: str, max_new_tokens: int = 256, do_sample: bool = False) -> str:
        """
        Async wrapper around the transformers text-generation backend.pipeline.
        """
        if self._pipeline is None:
            raise RuntimeError("No model initialized.")

        loop = asyncio.get_event_loop()

        def _call_pipeline():
            outputs = self._pipeline(prompt, max_new_tokens=max_new_tokens, do_sample=do_sample)
            return outputs[0].get("generated_text", "")

        generated = await loop.run_in_executor(None, _call_pipeline)

        # strip the prompt from the generated text if included
        if generated.startswith(prompt):
            return generated[len(prompt):].strip()
        return generated.strip()
