"""SEMI LLM client — NVIDIA NIM (OpenAI-compatible) as secondary channel.

Channel B: NVIDIA NIM serves Gemma 4-31B-IT via OpenAI-compatible API.
Used as a fallback when Google AI Studio hits rate limits, or as a parallel
extraction channel for dual-source verification.

Reads ``LLM_API_KEY_NIM`` + ``LLM_MODEL_NIM`` + ``LLM_BASE_URL_NIM`` from env.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass

from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger(__name__)


class NvidiaNotConfigured(RuntimeError):
    """Raised when LLM_API_KEY_NIM is absent."""


@dataclass(slots=True)
class NvidiaFieldExtraction:
    attribute: str
    value: str
    unit: str = ""
    evidence_snippet: str = ""
    confidence: float = 0.0
    extractor: str = "nvidia_nim"


_DEFAULT_NIM_MODEL = "google/gemma-4-31b-it"
_DEFAULT_NIM_BASE = "https://integrate.api.nvidia.com/v1"


def is_configured() -> bool:
    return bool(os.environ.get("LLM_API_KEY_NIM"))


def model_name() -> str:
    return os.environ.get("LLM_MODEL_NIM") or _DEFAULT_NIM_MODEL


def _base_url() -> str:
    return os.environ.get("LLM_BASE_URL_NIM") or _DEFAULT_NIM_BASE


SYSTEM_EXTRACT_ALL = (
    "You extract ALL available technical specifications, dimensions, features, "
    "materials, and certifications from the evidence. "
    "Return a JSON array of objects. Each object: "
    '{"attribute": "...", "value": "...", "unit": "...", "evidence": "...", "confidence": 0.0-1.0}. '
    "Do NOT extract information already provided. Extract as many distinct attributes as you can find. "
    "Never infer or use outside knowledge. 'evidence' must be a verbatim 1-line quote from the input."
)


def extract_all_fields(
    manufacturer: str,
    sku: str,
    context: str,
    known_attributes: dict | None = None,
) -> list[NvidiaFieldExtraction]:
    """Bulk extraction via NVIDIA NIM OpenAI-compatible endpoint."""
    import httpx

    key = os.environ.get("LLM_API_KEY_NIM")
    if not key:
        raise NvidiaNotConfigured("LLM_API_KEY_NIM not set")

    known_str = ""
    if known_attributes:
        known_str = "\nAlready Known Attributes (DO NOT extract these):\n" + "\n".join(
            f"- {k}: {v}" for k, v in known_attributes.items() if v and str(v).strip()
        )

    user_content = (
        f"Manufacturer: {manufacturer}\nSKU: {sku}\n{known_str}\n"
        f"Evidence:\n{context}\n\nExtract ALL technical attributes and features."
    )

    body = {
        "model": model_name(),
        "messages": [
            {"role": "system", "content": SYSTEM_EXTRACT_ALL},
            {"role": "user", "content": user_content},
        ],
        "temperature": float(os.environ.get("LLM_TEMPERATURE", "0.0")),
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
    }

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    # Rate limit throttle
    delay = float(os.environ.get("LLM_DELAY_SECONDS_NIM", "1.0"))
    if delay > 0:
        time.sleep(delay)

    try:
        with httpx.Client(timeout=60.0) as cli:
            r = cli.post(f"{_base_url()}/chat/completions", json=body, headers=headers)

        if r.status_code >= 400:
            logger.warning("NVIDIA NIM %s: %s", r.status_code, r.text[:200])
            return []

        resp_data = r.json()
        raw = resp_data.get("choices", [{}])[0].get("message", {}).get("content", "[]")
    except Exception as exc:
        logger.warning("NVIDIA NIM request failed: %s", exc)
        return []

    # Parse response
    raw = raw.strip()
    if raw.startswith("```json"):
        raw = raw[7:].strip()
    if raw.startswith("```"):
        raw = raw[3:].strip()
    if raw.endswith("```"):
        raw = raw[:-3].strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("NVIDIA NIM non-JSON: %r", raw[:200])
        return []

    # Handle both array and {attributes: [...]} shapes
    if isinstance(data, dict):
        data = data.get("attributes") or data.get("results") or data.get("data") or [data]
    if not isinstance(data, list):
        data = []

    results = []
    for item in data:
        if not isinstance(item, dict):
            continue
        attr = str(item.get("attribute", "") or "").strip()
        val = str(item.get("value", "") or "").strip()
        if not attr or not val:
            continue
        results.append(NvidiaFieldExtraction(
            attribute=attr,
            value=val,
            unit=str(item.get("unit", "") or "").strip(),
            evidence_snippet=str(item.get("evidence", "") or "").strip(),
            confidence=float(item.get("confidence", 0.0) or 0.0),
        ))
    return results
