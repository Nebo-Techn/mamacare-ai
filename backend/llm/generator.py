<<<<<<< HEAD
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
            use_auth_token=self.hf_token
        )

        model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
            use_auth_token=self.hf_token
        )

        self._pipeline = hf_pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            device=self.device,
            return_full_text=True
        )

        try:
            self.llm = HuggingFacePipeline(pipeline=self._pipeline)
        except Exception:
            self.llm = None

        print("[Generator] Model loaded successfully ✅")

    async def generate(self, prompt: str, max_new_tokens: int = 256, do_sample: bool = False) -> str:
        """
        Async wrapper around the transformers text-generation pipeline.
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
=======
import httpx
import json
from typing import Dict, Any

class Generator:
    """
    Generator class optimized for calling a remote vLLM endpoint.
    This eliminates local GPU loading and relies solely on HTTP communication.
    """

    def __init__(self, endpoint_url: str):
        """
        Args:
            endpoint_url (str): The full URL of the vLLM completion endpoint.
                                e.g., "http://your-vllm-ip:8000/generate"
        """
        self.endpoint_url = endpoint_url
        print(f"[Generator] Initialized with endpoint: {self.endpoint_url}")

    async def generate(self, prompt: str, max_new_tokens: int = 256, temperature: float = 0.1) -> str:
        """
        Sends the RAG prompt to the vLLM endpoint asynchronously.
        """
        
        # vLLM API request payload structure
        payload = {
            "prompt": prompt,
            "max_tokens": max_new_tokens,
            "temperature": temperature,
            # Add other vLLM parameters like 'top_p', 'stop_token_ids', etc.
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Use POST request to send the prompt
                response = await client.post(
                    self.endpoint_url,
                    json=payload
                )
                response.raise_for_status() # Raise exception for bad status codes (4xx or 5xx)

                # Assuming vLLM standard output format:
                # {"text": [generated_text_1, generated_text_2, ...]}
                data = response.json()
                
                # Extract the generated text (it's often a list of results)
                generated_text = data.get("text", [""])[0]
                
                # The vLLM response often includes the prompt; we need to strip it.
                if generated_text.startswith(prompt):
                    return generated_text[len(prompt):].strip()
                
                return generated_text.strip()
            
            except httpx.HTTPStatusError as e:
                print(f"[VLLMGenerator] HTTP Error: {e.response.status_code} - {e.response.text}")
                raise RuntimeError(f"vLLM API failed: {e}")
            except Exception as e:
                print(f"[VLLMGenerator] An error occurred: {e}")
                raise RuntimeError(f"Generation failed: {e}")
>>>>>>> 8ab8df8a869bd09a5e750e2819ef3c0136c906f3
