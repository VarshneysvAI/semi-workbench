import os
import time
import requests
from backend.providers.base_provider import BaseProvider, ProviderResult
from backend.pipeline.rate_limiter import nim_limiter
from backend.pipeline.logger_setup import logger
from openai import OpenAI

class NIMProvider(BaseProvider):
    name = "nim"
    
    def extract(self, system_prompt: str, user_prompt: str) -> ProviderResult:
        api_key = os.getenv("LLM_API_KEY_NIM") or os.getenv("NIM_API_KEY")
        base_url = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
        model = os.getenv("LLM_MODEL_NIM", "nvidia/nemotron-3.5-lightning")
        timeout = int(os.getenv("NIM_TIMEOUT", "90"))

        if not api_key:
            return ProviderResult("", self.name, 0.0, "NIM_API_KEY not set")
            
        system_prompt += "\n\nCRITICAL INSTRUCTION: DO NOT OUTPUT ANY THINKING, REASONING, OR EXPLANATION. YOU MUST START YOUR RESPONSE IMMEDIATELY WITH THE RAW JSON OBJECT."
        
        nim_limiter.wait_if_needed()
        start = time.time()
        try:
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
              stream=False,
              extra_body={"chat_template_kwargs":{"enable_thinking":False}}
            )
            
            content = completion.choices[0].message.content
            return ProviderResult(content, self.name, time.time() - start)
        except Exception as e:
            err_str = str(e)
            if "403" in err_str or "Authorization failed" in err_str or "Forbidden" in err_str:
                # Try Nemotron 3.5 Lightning via OpenRouter
                or_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEYS", "").split(",")[0]
                if or_key:
                    try:
                        or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=or_key, timeout=timeout)
                        resp = or_client.chat.completions.create(
                            model="nvidia/nemotron-3.5-lightning:free",
                            messages=[
                                {"role":"system","content":system_prompt},
                                {"role":"user","content":user_prompt}
                            ],
                            max_tokens=4096
                        )
                        return ProviderResult(resp.choices[0].message.content, self.name, time.time() - start)
                    except Exception as or_err:
                        err_str = f"{err_str} | OpenRouter Nemotron fallback error: {or_err}"
            return ProviderResult("", self.name, time.time() - start, err_str)


