import os
import time
import requests
from backend.providers.base_provider import BaseProvider, ProviderResult
from backend.pipeline.rate_limiter import nim_limiter
from backend.pipeline.logger_setup import logger

class NIMProvider(BaseProvider):
    name = "nim"
    
    def extract(self, system_prompt: str, user_prompt: str) -> ProviderResult:
        api_key = os.getenv("LLM_API_KEY_NIM") or os.getenv("NIM_API_KEY")
        base_url = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
        model = os.getenv("LLM_MODEL_NIM", "google/gemma-4-31b-it")
        timeout = int(os.getenv("NIM_TIMEOUT", "25"))

        
        if not api_key:
            return ProviderResult("", self.name, 0.0, "NIM_API_KEY not set")
            
        nim_limiter.wait_if_needed()
        start = time.time()
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.0,
                "max_tokens": 8192
            }
            resp = requests.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=timeout
            )
            if resp.status_code >= 400:
                logger.warning(f"NIM HTTP {resp.status_code}: {resp.text[:200]}")
                return ProviderResult("", self.name, time.time() - start, f"NIM HTTP {resp.status_code}")
                
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return ProviderResult(content, self.name, time.time() - start)
        except Exception as e:
            return ProviderResult("", self.name, time.time() - start, str(e))


