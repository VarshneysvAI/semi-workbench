def map_to_delivery(row: dict, audited: dict, UNILOG_HEADER: list) -> dict:
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
        
    attrs = audited.get("attributes", [])
    for idx, attr in enumerate(attrs[:50]):
        if isinstance(attr, dict) and attr.get("confidence", 1.0) >= 0.60:
            out[f"ATTRIBUTE_LABEL {idx+1}"] = attr.get("label", "")
            out[f"ATTRIBUTE_VALUE {idx+1}"] = attr.get("value", "")
            out[f"ATTRIBUTE_UOM {idx+1}"] = attr.get("uom", "")
            
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
    out["Country Of Origin"] = audited.get("country_of_origin", "")
    out["Discontinued"] = audited.get("discontinued", "")

    urls = audited.get("source_urls", {})
    out["MFR URL"] = urls.get("mfr_url", "")
    ref_list = urls.get("ref_urls", [])
    for idx, ref in enumerate(ref_list[:5]):
        out[f"Ref URL {idx+1}"] = ref
    
    return out

