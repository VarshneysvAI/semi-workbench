"""
SEMI — Delivery Mapper (Updated for 3-Pass Architecture)

Maps extracted JSON from NIM micro-prompts into the 252-column
Unilog Delivery Format. Handles:
  - Merging 3 separate pass results into a unified row
  - Flattening spec arrays into ATTRIBUTE_LABEL/VALUE/UOM 1..50 slots
  - Multi-source data merging (Source A + Source B)
"""
from backend.pipeline.logger_setup import logger


def merge_pass_results(pass1: dict, pass2: dict, pass3: dict) -> dict:
    """
    Merge the 3 NIM micro-pass results into a single unified dict
    matching the legacy extraction schema format.
    
    Pass 1: identity, taxonomy, descriptions, features
    Pass 2: attributes array
    Pass 3: identifiers, dimensions, media, compliance
    """
    merged = {}
    
    # From Pass 1
    if pass1:
        merged["manufacturer_name"] = pass1.get("manufacturer_name", "")
        merged["brand_name"] = pass1.get("brand_name", "")
        merged["trade_name"] = pass1.get("trade_name", "")
        merged["product_name"] = pass1.get("product_name", "")
        merged["taxonomy"] = pass1.get("taxonomy", {})
        merged["descriptions"] = pass1.get("descriptions", {})
        merged["features"] = pass1.get("features", [])
        merged["with"] = pass1.get("with", "")
        merged["standards_approvals"] = pass1.get("standards_approvals", [])
        merged["prop65"] = pass1.get("prop65", "")
        merged["application"] = pass1.get("application", "")
        merged["includes"] = pass1.get("includes", "")
    
    # From Pass 2
    if pass2:
        merged["attributes"] = pass2.get("attributes", [])
    elif "attributes" not in merged:
        merged["attributes"] = []
    
    # From Pass 3
    if pass3:
        merged["identifiers"] = pass3.get("identifiers", {})
        merged["dimensions"] = pass3.get("dimensions", {})
        merged["media"] = pass3.get("media", {})
        merged["warranty"] = pass3.get("warranty", "")
        merged["list_price"] = pass3.get("list_price", "")
        merged["country_of_origin"] = pass3.get("country_of_origin", "")
        merged["discontinued"] = pass3.get("discontinued", "")
        merged["selling_qty"] = pass3.get("selling_qty", "")
        merged["selling_uom"] = pass3.get("selling_uom", "")
        merged["std_packaging"] = pass3.get("std_packaging", "")
        merged["source_urls"] = pass3.get("source_urls", {})
    
    return merged


def merge_sources(src_a: dict, src_b: dict) -> dict:
    """
    Merge two extraction results (Source A = manufacturer, Source B = distributor).
    Source A values take priority. Source B fills in blanks.
    """
    if not src_a:
        return src_b or {}
    if not src_b:
        return src_a
    
    merged = dict(src_a)
    
    for key, val in src_b.items():
        if key not in merged or not merged[key]:
            merged[key] = val
        elif isinstance(merged[key], dict) and isinstance(val, dict):
            for k2, v2 in val.items():
                if not merged[key].get(k2):
                    merged[key][k2] = v2
        elif isinstance(merged[key], list) and isinstance(val, list):
            if not merged[key] and val:
                merged[key] = val
    
    # Special handling: merge attributes arrays (deduplicate by label)
    attrs_a = src_a.get("attributes", [])
    attrs_b = src_b.get("attributes", [])
    if attrs_b:
        existing_labels = {a.get("label", "").lower() for a in attrs_a if isinstance(a, dict)}
        for attr in attrs_b:
            if isinstance(attr, dict):
                label = attr.get("label", "").lower()
                if label and label not in existing_labels:
                    attrs_a.append(attr)
                    existing_labels.add(label)
        merged["attributes"] = attrs_a
    
    return merged


def map_to_delivery(row: dict, audited: dict, UNILOG_HEADER: list) -> dict:
    """
    Map extracted JSON into the 252-column delivery format.
    Handles both legacy single-pass and new 3-pass merged dicts.
    """
    out = {k: "" for k in UNILOG_HEADER}
    out.update(row)
    mfg_pn = row.get("Mfg_Part_Num") or row.get("mpn") or ""
    out["Mfg_Part_Num"] = mfg_pn
    out["Part_Desc"] = row.get("Part_Desc") or row.get("description") or ""
    out["E1_Brand"] = row.get("E1_Brand", "")
    out["Unilog_Brand"] = row.get("Unilog_Brand", "")
    out["DIB_Brand"] = row.get("DIB_Brand", "")
    out["Part_Manuf"] = row.get("Part_Manuf") or row.get("manufacturer") or ""
    out["MANUFACTURER_PART_NUMBER"] = mfg_pn
    out["PART_NUMBER"] = mfg_pn
    out["SKU - MY_PART_NUMBER"] = mfg_pn
    
    if not audited: return out
    
    out["MANUFACTURER_NAME"] = audited.get("manufacturer_name", "")
    out["BRAND_NAME"] = audited.get("brand_name", "")
    out["TRADE_NAME"] = audited.get("trade_name", "")
    out["Product Name"] = audited.get("product_name", "")
    
    tax = audited.get("taxonomy", {})
    out["Dept"] = tax.get("dept", "")
    out["Class"] = tax.get("class", "")
    out["Fine"] = tax.get("fine", "")
    out["Classpath"] = tax.get("classpath", "")
    
    desc = audited.get("descriptions", {})
    out["MOBILE_DESC"] = desc.get("mobile_desc", "")
    out["INVOICE_DESC"] = desc.get("invoice_desc", "")
    out["SHORT_DESC"] = desc.get("short_desc", "")
    out["LONG_DESC1"] = desc.get("long_desc", "")
    out["RETAIL_DESC"] = desc.get("retail_desc", "")
    out["MARKETING_DESCRIPTION"] = desc.get("marketing_description_verbatim", "")
    
    features = audited.get("features", [])
    for idx, feat in enumerate(features[:20]):
        out[f"ITEM_FEATURES_{idx+1}"] = str(feat)
        
    # ── Flatten attributes array into ATTRIBUTE_LABEL/VALUE/UOM 1..50 ──
    attrs = audited.get("attributes", [])
    attr_idx = 0
    for attr in attrs:
        if attr_idx >= 50:
            break
        if isinstance(attr, dict):
            label = attr.get("label", "")
            value = attr.get("value", "")
            if not label and not value:
                continue
            # Only include attributes with reasonable confidence
            confidence = attr.get("confidence", 1.0)
            if isinstance(confidence, (int, float)) and confidence < 0.30:
                continue
            
            attr_idx += 1
            out[f"ATTRIBUTE_LABEL {attr_idx}"] = label
            out[f"ATTRIBUTE_VALUE {attr_idx}"] = str(value)
            out[f"ATTRIBUTE_UOM {attr_idx}"] = attr.get("uom", "")
            
    dim = audited.get("dimensions", {})
    for k in ["length", "height", "width", "weight", "volume"]:
        out[k.upper()] = dim.get(k, "")
        out[f"{k.upper()}_UOM"] = dim.get(f"{k}_uom", "")
        
    med = audited.get("media", {})
    out["Product Image"] = med.get("product_image", "")
    out["Specification Sheet"] = med.get("spec_sheet", "")
    out["Catalog"] = med.get("catalog", "")
    out["Instruction/Installation Manual"] = med.get("installation_manual", "")
    out["Owners/User Manual"] = med.get("owners_manual", "")
    out["SDS"] = med.get("sds", "")
    out["Video Link"] = med.get("video_link", "")
    out["Actual Image (Yes/No)"] = "Yes" if out["Product Image"] else ""

    # Alternate images
    alt_images = med.get("alternate_images", [])
    for idx, img_url in enumerate(alt_images[:4]):
        out[f"Alternate Image {idx+1}"] = img_url

    out["With"] = audited.get("with", "")
    std = audited.get("standards_approvals", [])
    out["Standard/Approvals"] = ", ".join(std) if isinstance(std, list) else str(std or "")
    out["Prop 65"] = audited.get("prop65", "")
    out["Application"] = audited.get("application", "")
    out["Includes"] = audited.get("includes", "")

    idents = audited.get("identifiers", {})
    out["UPC"] = idents.get("upc", "")
    out["EAN"] = idents.get("ean", "")
    out["GTIN"] = idents.get("gtin", "")
    out["UNSPSC"] = idents.get("unspsc", "")

    out["Warranty"] = audited.get("warranty", "")
    out["List Price"] = audited.get("list_price", "")
    out["Selling Qty"] = audited.get("selling_qty", "")
    out["Selling UOM"] = audited.get("selling_uom", "")
    out["Standard Packaging Information"] = audited.get("std_packaging", "")
    out["Country Of Origin"] = audited.get("country_of_origin", "")
    out["Discontinued"] = audited.get("discontinued", "")

    urls = audited.get("source_urls", {})
    out["MFR URL"] = urls.get("mfr_url", "")
    ref_list = urls.get("ref_urls", [])
    for idx, ref in enumerate(ref_list[:5]):
        out[f"Ref URL {idx+1}"] = ref
    
    return out
