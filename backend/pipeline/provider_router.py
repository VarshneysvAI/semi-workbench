import os
import logging
from backend.providers.nim_provider import NIMProvider
from backend.providers.gemini_provider import GeminiProvider
from backend.providers.mock_provider import MockProvider
from backend.pipeline.json_repair import repair_json

logger = logging.getLogger(__name__)

class ProviderRouter:
    def __init__(self):
        self.primary = os.getenv("PRIMARY_PROVIDER", "gemini").lower()
        self.providers = {
            "gemini": GeminiProvider(),
            "nim": NIMProvider(),
            "mock": MockProvider()
        }

    def run_extraction(self, system_prompt: str, user_prompt: str):
        # 1. Try Primary
        provider_name = os.getenv("PRIMARY_PROVIDER", "gemini").lower()
        provider = self.providers.get(provider_name, GeminiProvider())
        logger.info(f"Using primary provider: {provider.name}")
        res = provider.extract(system_prompt, user_prompt)
        
        parsed = repair_json(res.raw_text)
        if not res.error and parsed and isinstance(parsed, dict) and "manufacturer_name" in parsed:
            return res, parsed

        logger.warning(f"{provider.name} failed or returned bad schema. Error: {res.error}. Raw: {res.raw_text[:200]}. Trying fallback provider.")
        
        # Determine fallback provider
        fallback_name = "nim" if provider.name == "gemini" else "gemini"
        provider = self.providers.get(fallback_name, GeminiProvider())
        res = provider.extract(system_prompt, user_prompt)
        
        parsed_fallback = repair_json(res.raw_text)
        if not res.error and parsed_fallback and isinstance(parsed_fallback, dict) and "manufacturer_name" in parsed_fallback:
            return res, parsed_fallback
            
        logger.error(f"All primary & secondary providers failed. Error: {res.error}. Raw text: {res.raw_text[:200]}")
        return res, None

provider_router = ProviderRouter()

