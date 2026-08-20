import os
import time
from backend.providers.base_provider import BaseProvider, ProviderResult
from backend.pipeline.rate_limiter import gemini_limiter

class GeminiProvider(BaseProvider):
    name = "gemini"
    
    def extract(self, system_prompt: str, user_prompt: str) -> ProviderResult:
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        if not api_key:
            return ProviderResult("", self.name, 0.0, "GOOGLE_API_KEY not set")
            
        gemini_limiter.wait_if_needed()
        start = time.time()
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=api_key)
            cfg = types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=8192,
                system_instruction=system_prompt,
                response_mime_type="application/json"
            )
            attempts = 2
            for attempt in range(attempts):
                try:
                    resp = client.models.generate_content(
                        model=model,
                        contents=user_prompt,
                        config=cfg
                    )
                    return ProviderResult(resp.text or "", self.name, time.time() - start)
                except Exception as ex:
                    if ("503" in str(ex) or "UNAVAILABLE" in str(ex)) and attempt < attempts - 1:
                        time.sleep(2)
                        continue
                    return ProviderResult("", self.name, time.time() - start, str(ex))
            return ProviderResult("", self.name, time.time() - start, "Max retries exceeded")
        except Exception as e:
            return ProviderResult("", self.name, time.time() - start, str(e))



