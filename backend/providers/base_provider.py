import time
from dataclasses import dataclass
from typing import Optional

@dataclass
class ProviderResult:
    raw_text: str
    provider_name: str
    latency_seconds: float
    error: Optional[str] = None

class BaseProvider:
    name: str = "base"
    
    def extract(self, system_prompt: str, user_prompt: str) -> ProviderResult:
        raise NotImplementedError
