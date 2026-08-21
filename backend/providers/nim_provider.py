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
        model = os.getenv("LLM_MODEL_NIM", "nvidia/nemotron-3.5-lightning-30b-a3b")
        timeout = int(os.getenv("NIM_TIMEOUT", "90"))

        
        if not api_key:
            return ProviderResult("", self.name, 0.0, "NIM_API_KEY not set")
            
        nim_limiter.wait_if_needed()
        start = time.time()
        try:
            from openai import OpenAI
            client = OpenAI(
              base_url = base_url,
              api_key = api_key,
              timeout=timeout
            )
            
            completion = client.chat.completions.create(
              model=model,
              messages=[
                  {"role":"system","content":system_prompt},
                  {"role":"user","content":user_prompt}
              ],
              temperature=0.0,
              max_tokens=8192,
              extra_body={"chat_template_kwargs":{"enable_thinking":True},"reasoning_budget":8192},
              stream=False
            )
            
            message = completion.choices[0].message
            reasoning = getattr(message, "reasoning_content", None) or getattr(message, "reasoning", None)
            if reasoning:
                logger.info(f"NIM Reasoning (deepseek): {reasoning[:200]}...")
                
            content = message.content
            return ProviderResult(content, self.name, time.time() - start)
        except Exception as e:
            return ProviderResult("", self.name, time.time() - start, str(e))


