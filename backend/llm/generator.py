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
                response.raise_for_status()
                
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

