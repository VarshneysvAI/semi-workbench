import os
import logging
from backend.providers.nim_provider import NIMProvider
from backend.providers.gemini_provider import GeminiProvider
from backend.providers.groq_provider import GroqProvider
from backend.providers.openrouter_provider import OpenRouterProvider
from backend.providers.mock_provider import MockProvider
from backend.pipeline.json_repair import repair_json

from backend.pipeline.logger_setup import logger

class ProviderRouter:
    def __init__(self):
        self.primary = os.getenv("PRIMARY_PROVIDER", "nim").lower()
        self.providers = {
            "gemini": GeminiProvider(),
            "groq": GroqProvider(),
            "openrouter": OpenRouterProvider(),
            "nim": NIMProvider(),
            "mock": MockProvider()
        }

    def run_extraction(self, system_prompt: str, user_prompt: str, expected_key: str = "manufacturer_name"):
        provider_name = os.getenv("PRIMARY_PROVIDER", "nim").lower()
        provider = self.providers.get(provider_name, NIMProvider())
        
        # Try Primary Provider up to 3 times (1 initial + 2 retries)
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Using primary provider: {provider.name} (Attempt {attempt}/{max_attempts})")
            res = provider.extract(system_prompt, user_prompt)
            parsed = repair_json(res.raw_text)
            
            if not res.error and parsed and isinstance(parsed, dict) and expected_key in parsed:
                return res, parsed
            
            logger.warning(f"{provider.name} attempt {attempt} failed or returned bad schema. Error: {res.error}")
            
            # If authorization failed (403/401), don't waste time on retries
            err_str = str(res.error or "")
            if "403" in err_str or "401" in err_str or "Authorization failed" in err_str or "Forbidden" in err_str:
                logger.warning(f"{provider.name} authorization failed ({res.error}). Skipping retries and trying fallbacks.")
                break

            if attempt < max_attempts:
                import time
                time.sleep(1.5)

        logger.warning(f"{provider.name} failed all {max_attempts} attempts. Trying secondary fallbacks.")
        
        # Fallback providers
        fallbacks = ["groq", "openrouter", "gemini", "mock"]
        
        for fallback_name in fallbacks:
            if fallback_name == provider_name:
                continue
            
            p = self.providers.get(fallback_name)
            if not p:
                continue
                
            res = p.extract(system_prompt, user_prompt)
            parsed_fallback = repair_json(res.raw_text)
            if not res.error and parsed_fallback and isinstance(parsed_fallback, dict) and expected_key in parsed_fallback:
                logger.info(f"Fallback provider {p.name} succeeded")
                return res, parsed_fallback
                
            logger.warning(f"{p.name} failed or returned bad schema. Error: {res.error}")
            
        logger.error("All providers failed. Returning empty schema dict.")
        return res, {expected_key: ""}

provider_router = ProviderRouter()

