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
import time
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
_ALL_FIELDS_SCHEMA = None
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


def _all_fields_schema():
    global _ALL_FIELDS_SCHEMA
    if _ALL_FIELDS_SCHEMA is None:
        from google.genai import types
        _ALL_FIELDS_SCHEMA = types.Schema(
            type="ARRAY",
            items=types.Schema(
                type="OBJECT",
                properties={
                    "attribute": types.Schema(type="STRING"),
                    "value": types.Schema(type="STRING"),
                    "unit": types.Schema(type="STRING"),
                    "evidence": types.Schema(type="STRING"),
                    "confidence": types.Schema(type="NUMBER"),
                },
                required=["attribute", "value", "confidence"]
            )
        )
    return _ALL_FIELDS_SCHEMA


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
        temperature=float(os.environ.get("LLM_TEMPERATURE", "0.0")),
        max_output_tokens=256,
        response_mime_type="application/json",
        response_schema=_field_schema(),
        system_instruction=SYSTEM_EXTRACT,
    )
    
    # Rate limit throttling to avoid 429 Free Tier limits
    delay = float(os.environ.get("LLM_DELAY_SECONDS", "4.2"))
    if delay > 0:
        time.sleep(delay)
        
    resp = cli.models.generate_content(model=model_name(), contents=evidence, config=cfg)
    raw = (resp.text or "{}").strip()
    if raw.startswith("```json"):
        raw = raw[7:].strip()
    if raw.startswith("```"):
        raw = raw[3:].strip()
    if raw.endswith("```"):
        raw = raw[:-3].strip()
    
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


SYSTEM_EXTRACT_ALL = (
    "You extract ALL available technical specifications, dimensions, features, materials, and certifications from the evidence. "
    "Return a JSON array of objects, where each object represents a single extracted attribute. "
    "Do NOT extract information already provided. Extract as many distinct attributes as you can find. "
    "Never infer or use outside knowledge. 'evidence' must be a verbatim 1-line quote from the input."
)

@dataclass(slots=True)
class NamedFieldExtraction:
    attribute: str
    value: str
    unit: str = ""
    evidence_snippet: str = ""
    confidence: float = 0.0
    extractor: str = "llm"

def extract_all_fields(
    manufacturer: str,
    sku: str,
    context: str,
    known_attributes: dict = None,
) -> list[NamedFieldExtraction]:
    """Strict-JSON bulk field extraction; returns all found technical attributes."""
    cli = _client()
    
    known_str = ""
    if known_attributes:
        known_str = "\nAlready Known Attributes (DO NOT extract these):\n" + "\n".join(
            f"- {k}: {v}" for k, v in known_attributes.items() if v and str(v).strip()
        )
        
    evidence = (
        f"Manufacturer: {manufacturer}\nSKU: {sku}\n{known_str}\n"
        f"Evidence:\n{context}\n\nExtract ALL technical attributes and features."
    )
    from google.genai import types
    cfg = types.GenerateContentConfig(
        temperature=float(os.environ.get("LLM_TEMPERATURE", "0.0")),
        max_output_tokens=4096,
        response_mime_type="application/json",
        response_schema=_all_fields_schema(),
        system_instruction=SYSTEM_EXTRACT_ALL,
    )
    
    # Rate limit throttling to avoid 429 Free Tier limits
    delay = float(os.environ.get("LLM_DELAY_SECONDS", "4.2"))
    if delay > 0:
        time.sleep(delay)
        
    resp = cli.models.generate_content(model=model_name(), contents=evidence, config=cfg)
    raw = (resp.text or "[]").strip()
    if raw.startswith("```json"): raw = raw[7:].strip()
    if raw.startswith("```"): raw = raw[3:].strip()
    if raw.endswith("```"): raw = raw[:-3].strip()
    
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("gemma extract_all returned non-JSON: %r", raw[:200])
        return []
        
    if not isinstance(data, list):
        data = [data] if isinstance(data, dict) else []
        
    results = []
    for item in data:
        if not isinstance(item, dict): continue
        attr = str(item.get("attribute", "") or "").strip()
        val = str(item.get("value", "") or "").strip()
        if not attr or not val: continue
        results.append(NamedFieldExtraction(
            attribute=attr,
            value=val,
            unit=str(item.get("unit", "") or "").strip(),
            evidence_snippet=str(item.get("evidence", "") or "").strip(),
            confidence=float(item.get("confidence", 0.0) or 0.0),
        ))
    return results


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
