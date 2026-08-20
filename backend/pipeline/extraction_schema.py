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
