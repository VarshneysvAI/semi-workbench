"""SEMI LLM client — Google AI Studio native SDK (genai).

Channel: ``google.genai`` (Gemini / Gemma) with structured ``response_schema``
JSON output. Reads ``GOOGLE_API_KEY`` + ``GOOGLE_GENAI_MODEL`` from env. No
hardcoded secrets; raises ``LLMNotConfigured`` when unconfigured so callers
fall back to deterministic regex (never silently fake).

Verified live: gemma-4-31b-it on the user's AI Studio key (strict-JSON
single-field extraction ~3s); gemini-2.5-flash as a faster secondary.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class LLMNotConfigured(RuntimeError):
    """Raised when GOOGLE_API_KEY is absent — callers must fall back."""


@dataclass(slots=True)
class FieldExtraction:
    value: str
    unit: str = ""
    evidence_snippet: str = ""
    confidence: float = 0.0
    extractor: str = "llm"


_DEFAULT_MODEL = "gemma-4-31b-it"

_FIELD_SCHEMA = None
_CLASSIFY_SCHEMA_CACHE: dict[str, object] = {}


def _client() -> object:
    key = os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise LLMNotConfigured("GOOGLE_API_KEY not set")
    try:
        from google import genai
    except ImportError as exc:
        raise LLMNotConfigured("google-genai not installed") from exc
    return _CLIENT_FACTORY(genai, api_key=key)


def _CLIENT_FACTORY(genai_module, *, api_key):
    return genai_module.Client(api_key=api_key)


def model_name() -> str:
    return os.environ.get("GOOGLE_GENAI_MODEL") or _DEFAULT_MODEL


def is_configured() -> bool:
    return bool(os.environ.get("GOOGLE_API_KEY"))


def _field_schema():
    global _FIELD_SCHEMA
    if _FIELD_SCHEMA is None:
        from google.genai import types
        _FIELD_SCHEMA = types.Schema(
            type="OBJECT",
            properties={
                "value": types.Schema(type="STRING"),
                "unit": types.Schema(type="STRING"),
                "evidence": types.Schema(type="STRING"),
                "confidence": types.Schema(type="NUMBER"),
            },
            required=["value", "confidence"],
        )
    return _FIELD_SCHEMA


SYSTEM_EXTRACT = (
    "You extract ONE product attribute value from evidence. "
    "If the attribute is NOT explicitly stated, set value='' and confidence=0. "
    "Never infer or use outside knowledge. "
    "evidence must be a verbatim 1-line quote from the input."
)


def extract_field(
    manufacturer: str,
    sku: str,
    attribute: str,
    context: str,
) -> FieldExtraction:
    """Strict-JSON single-field extraction; deterministic at temperature 0."""
    cli = _client()
    evidence = (
        f"Manufacturer: {manufacturer}\nSKU: {sku}\nAttribute: {attribute}\n"
        f"Evidence:\n{context}\n\nExtract the value of '{attribute}'."
    )
    from google.genai import types
    cfg = types.GenerateContentConfig(
        temperature=0.0,
        max_output_tokens=256,
        response_mime_type="application/json",
        response_schema=_field_schema(),
        system_instruction=SYSTEM_EXTRACT,
    )
    resp = cli.models.generate_content(model=model_name(), contents=evidence, config=cfg)
    raw = resp.text or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("gemma returned non-JSON: %r", raw[:200])
        return FieldExtraction(value="", confidence=0.0)
    return FieldExtraction(
        value=str(data.get("value", "") or "").strip(),
        unit=str(data.get("unit", "") or "").strip(),
        evidence_snippet=str(data.get("evidence", "") or "").strip(),
        confidence=float(data.get("confidence", 0.0) or 0.0),
    )


def classify_json(prompt: str, schema, *, system: str = "", temperature: float = 0.0) -> dict:
    """Generic structured call — used by schema inference + audit."""
    cli = _client()
    from google.genai import types
    cfg = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=2048,
        response_mime_type="application/json",
        response_schema=schema,
        system_instruction=system or None,
    )
    resp = cli.models.generate_content(model=model_name(), contents=prompt, config=cfg)
    raw = resp.text or "{}"
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("classify_json non-JSON: %r", raw[:200])
        return {}
