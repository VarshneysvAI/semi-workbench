import os
import time
import json
import logging
from openai import OpenAI
from backend.pipeline.logger_setup import logger

class GroqProvider:
    name = "groq"
    def __init__(self):
        # We allow multiple API keys to rotate through them if rate limited
        keys_env = os.environ.get("GROQ_API_KEYS", "")
        if keys_env:
            self.api_keys = [k.strip() for k in keys_env.split(",") if k.strip()]
        else:
            single_key = os.environ.get("GROQ_API_KEY")
            self.api_keys = [single_key] if single_key else []
            
        self.current_key_idx = 0

    def get_client(self):
        if not self.api_keys:
            return None
        return OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=self.api_keys[self.current_key_idx],
            timeout=90
        )

    def rotate_key(self):
        if not self.api_keys:
            return
        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
        logger.warning(f"Rotated to Groq API Key #{self.current_key_idx + 1}")

    def extract(self, system_prompt, user_prompt):
        if not self.api_keys:
            logger.error("No Groq API keys available")
            from backend.providers.base_provider import ProviderResult
            return ProviderResult("", self.name, 0.0, "No API key")
            
        attempts = 0
        max_attempts = len(self.api_keys) * 2 # Try each key twice
        
        start = time.time()
        while attempts < max_attempts:
            client = self.get_client()
            if not client:
                from backend.providers.base_provider import ProviderResult
                return ProviderResult("", self.name, 0.0, "No client")
                
            try:
                res = client.chat.completions.create(
                    model=os.getenv("GROQ_MODEL", "qwen/qwen3.6-27b"),
                    messages=[
                        {"role": "system", "content": system_prompt + "\nOUTPUT RAW JSON ONLY."},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=1500
                )
                from backend.providers.base_provider import ProviderResult
                return ProviderResult(res.choices[0].message.content, self.name, time.time() - start)
                
            except Exception as e:
                err_msg = str(e).lower()
                logger.warning(f"Groq API Error on Key #{self.current_key_idx + 1}: {e}")
                
                # Check for rate limit or authentication errors
                if "rate_limit" in err_msg or "429" in err_msg or "401" in err_msg or "authentication" in err_msg:
                    self.rotate_key()
                    time.sleep(2)
                else:
                    time.sleep(5)
            attempts += 1
            
        logger.error("All Groq API keys exhausted or rate limited")
        from backend.providers.base_provider import ProviderResult
        return ProviderResult("", self.name, time.time() - start, "All keys exhausted")
