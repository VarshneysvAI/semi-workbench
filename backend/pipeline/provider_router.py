import os
import logging
from backend.providers.nim_provider import NIMProvider
from backend.providers.gemini_provider import GeminiProvider
from backend.providers.groq_provider import GroqProvider
from backend.providers.mock_provider import MockProvider
from backend.pipeline.json_repair import repair_json

from backend.pipeline.logger_setup import logger

class ProviderRouter:
    def __init__(self):
        self.primary = os.getenv("PRIMARY_PROVIDER", "nim").lower()
        self.providers = {
            "gemini": GeminiProvider(),
            "groq": GroqProvider(),
            "nim": NIMProvider(),
            "mock": MockProvider()
        }

    def run_extraction(self, system_prompt: str, user_prompt: str, expected_key: str = "manufacturer_name"):
        # 1. Try Primary
        provider_name = os.getenv("PRIMARY_PROVIDER", "nim").lower()
        provider = self.providers.get(provider_name, NIMProvider())
        logger.info(f"Using primary provider: {provider.name}")
        res = provider.extract(system_prompt, user_prompt)
        
        parsed = repair_json(res.raw_text)
        if not res.error and parsed and isinstance(parsed, dict) and expected_key in parsed:
            return res, parsed

        logger.warning(f"{provider.name} failed or returned bad schema. Error: {res.error}. Raw: {res.raw_text[:200] if res.raw_text else 'None'}. Trying Groq provider.")
        
        # Determine fallback providers
        fallbacks = ["groq", "gemini"]
        
        for fallback_name in fallbacks:
            if fallback_name == provider_name:
                continue
            
            provider = self.providers.get(fallback_name)
            if not provider:
                continue
                
            res = provider.extract(system_prompt, user_prompt)
            parsed_fallback = repair_json(res.raw_text)
            if not res.error and parsed_fallback and isinstance(parsed_fallback, dict) and expected_key in parsed_fallback:
                return res, parsed_fallback
                
            logger.warning(f"{provider.name} failed or returned bad schema. Error: {res.error}. Raw: {res.raw_text[:200] if res.raw_text else 'None'}. Trying next provider.")
            
        logger.error(f"All primary & secondary providers failed. Final Error: {res.error}. Raw text: {res.raw_text[:200] if res.raw_text else 'None'}")
        return res, None

provider_router = ProviderRouter()

