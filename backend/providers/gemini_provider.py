import os
import time
from backend.providers.base_provider import BaseProvider, ProviderResult
from backend.pipeline.rate_limiter import gemini_limiter

class GeminiProvider(BaseProvider):
    name = "gemini"
    
    def extract(self, system_prompt: str, user_prompt: str) -> ProviderResult:
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        
        if not api_key:
            return ProviderResult("", self.name, 0.0, "GOOGLE_API_KEY not set")
            
        gemini_limiter.wait_if_needed()
        start = time.time()
        
        models_to_try = [model, "gemini-1.5-flash", "gemini-2.0-flash-lite"]
        for m in models_to_try:
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
                resp = client.models.generate_content(
                    model=m,
                    contents=user_prompt,
                    config=cfg
                )
                if resp and resp.text:
                    return ProviderResult(resp.text, self.name, time.time() - start)
            except Exception as ex:
                err_str = str(ex)
                if ("503" in err_str or "UNAVAILABLE" in err_str or "404" in err_str) and m != models_to_try[-1]:
                    time.sleep(1)
                    continue
                return ProviderResult("", self.name, time.time() - start, err_str)
        return ProviderResult("", self.name, time.time() - start, "All Gemini models failed")



