"""
SEMI — 3-Pass Micro-Prompt Extraction Schema

Decomposes the 252-column extraction into 3 focused NIM micro-prompts:
  Pass 1: Core Identity & Descriptions (~8 keys, ~300ms)
  Pass 2: Technical Specifications Array (flat array, ~400ms)
  Pass 3: Identifiers, Dimensions, Media & Compliance (~10 keys, ~300ms)

This prevents NIM from being overloaded with a single massive schema,
guaranteeing valid JSON output and staying within 40 RPM limits.
"""


# ─────────────────────────────────────────────────────────────────────
# PASS 1: Core Identity, Taxonomy & Descriptions
# ─────────────────────────────────────────────────────────────────────

def build_identity_system_prompt() -> str:
    return """You are a product data extraction engine for industrial catalogs.
Return ONLY valid JSON. No markdown, no explanation, no thinking.
If a value is not found in the source text, use empty string "".
Do not guess or hallucinate values.
Extract manufacturer and brand names exactly as they appear in the source.
Descriptions must be based on real product information from the source text."""


def build_identity_user_prompt(row: dict, manufacturer: str, source_url: str, source_text: str) -> str:
    return f"""Input row:
Mfg_Part_Num: {row.get('Mfg_Part_Num', '') or row.get('mpn', '')}
Part_Desc: {row.get('Part_Desc', '') or row.get('description', '')}
Inferred manufacturer: {manufacturer}
Source URL: {source_url}

Source text (excerpt):
{source_text[:3000]}

Extract ONLY these fields as a JSON object:
{{
  "manufacturer_name": "",
  "brand_name": "",
  "trade_name": "",
  "product_name": "",
  "taxonomy": {{"dept": "", "class": "", "fine": "", "classpath": ""}},
  "descriptions": {{
    "mobile_desc": "",
    "invoice_desc": "",
    "short_desc": "",
    "long_desc": "",
    "retail_desc": "",
    "marketing_description_verbatim": ""
  }},
  "features": [],
  "with": "",
  "standards_approvals": [],
  "prop65": "",
  "application": "",
  "includes": ""
}}"""


# ─────────────────────────────────────────────────────────────────────
# PASS 2: Technical Specifications as a Flat Array
# ─────────────────────────────────────────────────────────────────────

def build_specs_system_prompt() -> str:
    return """You are a technical specification extraction engine.
Return ONLY valid JSON. No markdown, no explanation, no thinking.
Extract ALL technical specifications from the source text as a flat array.
Separate numeric values from their units of measurement.
Example: voltage "120V" becomes label:"Voltage", value:"120", uom:"V".
Do not skip any specification found in the source text.
If a spec has no unit, use empty string for uom."""


def build_specs_user_prompt(row: dict, manufacturer: str, source_text: str) -> str:
    return f"""Product: {manufacturer} {row.get('Mfg_Part_Num', '') or row.get('mpn', '')}
Description: {row.get('Part_Desc', '') or row.get('description', '')}

Source text (specifications section):
{source_text[:4000]}

Extract ALL technical specifications as a JSON object with a single key "attributes":
{{
  "attributes": [
    {{"label": "Voltage", "value": "120", "uom": "V"}},
    {{"label": "Weight", "value": "2.5", "uom": "LB"}},
    {{"label": "Material", "value": "Stainless Steel", "uom": ""}}
  ]
}}"""


# ─────────────────────────────────────────────────────────────────────
# PASS 3: Identifiers, Dimensions, Media & Compliance
# ─────────────────────────────────────────────────────────────────────

def build_compliance_system_prompt() -> str:
    return """You are an industrial product data extraction engine.
Return ONLY valid JSON. No markdown, no explanation, no thinking.
Extract product identifiers, physical dimensions, media URLs, and compliance data.
Separate numeric dimension values from their units.
If a value is not found, use empty string ""."""


def build_compliance_user_prompt(row: dict, manufacturer: str, source_url: str, source_text: str) -> str:
    return f"""Product: {manufacturer} {row.get('Mfg_Part_Num', '') or row.get('mpn', '')}
Source URL: {source_url}

Source text:
{source_text[:3000]}

Extract these fields as a JSON object:
{{
  "identifiers": {{"upc": "", "ean": "", "gtin": "", "unspsc": ""}},
  "dimensions": {{
    "length": "", "length_uom": "",
    "height": "", "height_uom": "",
    "width": "", "width_uom": "",
    "weight": "", "weight_uom": "",
    "volume": "", "volume_uom": ""
  }},
  "media": {{
    "product_image": "",
    "alternate_images": [],
    "spec_sheet": "",
    "catalog": "",
    "installation_manual": "",
    "owners_manual": "",
    "sds": "",
    "video_link": ""
  }},
  "warranty": "",
  "list_price": "",
  "country_of_origin": "",
  "discontinued": "",
  "selling_qty": "",
  "selling_uom": "",
  "std_packaging": "",
  "source_urls": {{"mfr_url": "{source_url}", "ref_urls": []}}
}}"""


# ─────────────────────────────────────────────────────────────────────
# BACKWARD COMPAT: Legacy single-prompt (kept for fallback/testing)
# ─────────────────────────────────────────────────────────────────────

def build_system_prompt() -> str:
    return """You are Unilog product data extraction engine.
Return ONLY valid JSON.
Do not return markdown.
Do not return explanations.
Do not guess.
If a value is not found, use empty string or empty array.
Use only the provided source text.
Separate numeric value and UOM where possible.
Marketing description must be copied verbatim from manufacturer source if present.
"""

def build_user_prompt(row, manufacturer, source, source_text) -> str:
    return f"""Input row:
Mfg_Part_Num: {row.get('Mfg_Part_Num')}
Part_Desc: {row.get('Part_Desc')}
Inferred manufacturer: {manufacturer}
Selected source URL: {source.url}
Source text: {source_text}

Extract data matching this JSON format exactly:
{{
  "manufacturer_name": "", "brand_name": "", "product_name": "",
  "taxonomy": {{"dept": "", "class": "", "fine": "", "classpath": ""}},
  "descriptions": {{"mobile_desc": "", "invoice_desc": "", "short_desc": "", "long_desc": "", "retail_desc": "", "marketing_description_verbatim": ""}},
  "features": [],
  "attributes": [{{"label": "", "value": "", "uom": "", "source_url": "", "evidence": "", "confidence": 0.0}}],
  "with": "", "standards_approvals": [], "prop65": "", "application": "", "includes": "",
  "dimensions": {{"length": "", "length_uom": "", "height": "", "height_uom": "", "width": "", "width_uom": "", "weight": "", "weight_uom": "", "volume": "", "volume_uom": ""}},
  "media": {{"product_image": "", "alternate_images": [], "spec_sheet": "", "catalog": "", "installation_manual": "", "owners_manual": "", "sds": "", "video_link": ""}},
  "identifiers": {{"upc": "", "ean": "", "gtin": "", "unspsc": ""}},
  "warranty": "", "list_price": "", "country_of_origin": "", "discontinued": "", "actual_image_yes_no": "",
  "source_urls": {{"mfr_url": "", "ref_urls": []}}
}}
"""
