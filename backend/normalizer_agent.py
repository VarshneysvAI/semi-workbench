import logging
from typing import Dict, List

from backend.contracts import (
    NormalizeInput, NormalizeOutput, CanonicalAttribute, RawExtraction, SchemaPlan, AgentError
)
from backend.llm.gemma import classify_json, is_configured as gemma_configured

logger = logging.getLogger(__name__)

# Deterministic calculator for unit conversions to prevent LLM hallucinations.
# Used on the backend/CLI to quickly resolve mathematical conversions.
CONVERSIONS = {
    ("in", "mm"): 25.4,
    ("mm", "in"): 1 / 25.4,
    ("lb", "kg"): 0.453592,
    ("kg", "lb"): 1 / 0.453592,
    ("f", "c"): lambda f: (f - 32) * 5/9,
    ("c", "f"): lambda c: (c * 9/5) + 32,
    ("cm", "in"): 1 / 2.54,
    ("in", "cm"): 2.54,
    ("v", "mv"): 1000.0,
    ("mv", "v"): 1 / 1000.0,
}

def deterministic_convert_unit(value_str: str, from_unit: str, to_unit: str) -> str:
    """Calculates unit conversion deterministically rather than relying on LLM math."""
    from_u = (from_unit or "").strip().lower()
    to_u = (to_unit or "").strip().lower()
    if not from_u or not to_u or from_u == to_u:
        return value_str
        
    try:
        val = float(value_str)
    except ValueError:
        return value_str  # Not a pure number, fallback to raw string
        
    pair = (from_u, to_u)
    if pair in CONVERSIONS:
        conv = CONVERSIONS[pair]
        if callable(conv):
            new_val = conv(val)
        else:
            new_val = val * conv
            
        # Clean formatting (max 2 decimals, strip trailing zeros)
        if new_val.is_integer():
            return str(int(new_val))
        return f"{new_val:.2f}".rstrip("0").rstrip(".")
        
    logger.warning("No deterministic calculator conversion found for %s -> %s", from_u, to_u)
    return value_str


def get_precedence(ext: RawExtraction) -> int:
    """
    Ranks the authority of the extraction source.
    1. Manufacturer spec sheet PDF (1.0)
    2. Manufacturer HTML product page (0.9)
    3. Manual PDF (0.7)
    4. Distributor (0.5)
    5. Third-party video transcript (0.3)
    """
    kind = ext.extractor
    url = ext.source_url.lower()
    
    if kind == "pdf_reader_mcp":
        if "manual" in url or "guide" in url or "install" in url:
            return 3
        return 1
    elif kind in ("crawl4ai", "firecrawl_scrape", "httpx"):
        return 2
    elif kind == "youtube_transcript":
        return 5
    return 4


def map_labels_to_keys(extractions: List[RawExtraction], schema: SchemaPlan) -> Dict[str, str]:
    """Pass A: Context-aware LLM mapping. 
    Passes BOTH the label and the evidence snippet so the LLM can distinguish 
    ambiguous terms (e.g. 'length' of a screw vs 'length' of its thread)."""
    if not extractions:
        return {}
        
    target_keys = [attr.name for attr in schema.attributes]
    
    # If LLM not configured, use identity mapping (raw_label → raw_label if it matches)
    if not gemma_configured():
        logger.info("LLM not configured — using identity label mapping")
        return {ext.raw_label: ext.raw_label for ext in extractions if ext.raw_label in target_keys}
    
    try:
        from google.genai import types
    except ImportError:
        logger.warning("google-genai not installed — using identity label mapping")
        return {ext.raw_label: ext.raw_label for ext in extractions if ext.raw_label in target_keys}
    
    mapping_schema = types.Schema(
        type="OBJECT",
        properties={
            "mappings": types.Schema(
                type="OBJECT",
                description="Mapping of raw_label to canonical_key. canonical_key MUST be one of the target_keys. Values must be strings."
            )
        }
    )
    
    system_prompt = (
        f"You are an expert industrial data normalizer.\n"
        f"Map each of the following raw labels to the most appropriate canonical key based on its context/evidence.\n"
        f"Available canonical keys: {', '.join(target_keys)}\n"
        f"Pay close attention to the evidence to disambiguate (e.g. overall length vs thread length).\n"
        f"If a raw label doesn't match any canonical key perfectly, map it to 'unknown'.\n"
        f"Return a JSON object with a 'mappings' dictionary where keys are the exact 'raw_label's provided."
    )
    
    # Deduplicate extractions by raw_label to save tokens, but keep the snippet for context
    unique_exts = {ext.raw_label: ext.evidence_snippet for ext in extractions}
    
    prompt = "Raw labels and their context to map:\n"
    for label, snippet in unique_exts.items():
        prompt += f"- Label: '{label}' | Context: '{snippet}'\n"
    
    # Temperature 0.0 for deterministic classification
    result = classify_json(prompt, mapping_schema, system=system_prompt, temperature=0.0)
    mappings = result.get("mappings", {})
    
    clean_mappings = {}
    for raw, canonical in mappings.items():
        if canonical in target_keys:
            clean_mappings[raw] = canonical
            
    return clean_mappings


def run_normalization(input_data: NormalizeInput) -> NormalizeOutput:
    """Executes Phase 4: Two-Pass Normalization."""
    try:
        # Pass A — Label -> Canonical Key (Context-Aware)
        label_map = map_labels_to_keys(input_data.raw_extractions, input_data.schema_plan)
        
        # Group extractions by their canonical key
        grouped: Dict[str, List[RawExtraction]] = {}
        for ext in input_data.raw_extractions:
            canonical = label_map.get(ext.raw_label)
            if canonical:
                grouped.setdefault(canonical, []).append(ext)
            elif ext.raw_label in [a.name for a in input_data.schema_plan.attributes]:
                # It might already be a canonical key (e.g. from our deterministic RAG)
                grouped.setdefault(ext.raw_label, []).append(ext)
                
        # Pass B — Unit -> Canonical Unit + Conflict Resolution
        canonical_attributes = []
        for canonical_key, exts in grouped.items():
            # 1. Sort by precedence (lower number = higher authority)
            exts.sort(key=get_precedence)
            
            # 2. Winner is the highest authority extraction
            winner = exts[0]
            
            # 3. Determine canonical storage unit from schema blueprint
            canonical_unit = winner.unit or ""
            target_attr = next((a for a in input_data.schema_plan.attributes if a.name == canonical_key), None)
            
            if target_attr and target_attr.uom_candidates and len(target_attr.uom_candidates) > 0:
                canonical_unit = target_attr.uom_candidates[0]
            
            # 4. Deterministic Unit Calculator Conversion
            canonical_value = deterministic_convert_unit(winner.value, winner.unit, canonical_unit)
            
            canonical_attributes.append(CanonicalAttribute(
                canonical_key=canonical_key,
                canonical_value=canonical_value,
                canonical_unit=canonical_unit,
                confidence=winner.confidence,
                source_url=winner.source_url,
                precedence_rank=get_precedence(winner),
                raw_variants=exts
            ))
            
        return NormalizeOutput(status="ok", data=canonical_attributes)
    except Exception as e:
        logger.error("Normalization failed: %s", str(e))
        return NormalizeOutput(
            status="error", 
            error=AgentError(code="NORMALIZATION_FAILED", message=str(e))
        )
