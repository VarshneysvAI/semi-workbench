BRAND_ALIASES = {
    "dewlt": "DeWalt",
    "milw": "Milwaukee",
    "milwaukee accessory": "Milwaukee",
    "black & decker": "DeWalt",
    "sq": "Speed Queen",
    "ge": "GE Appliances",
    "lg": "LG",
    "kitchen aid": "KitchenAid",
}

def build_queries(row, manufacturer):
    part = row.get("Mfg_Part_Num", "")
    brand = manufacturer or row.get("E1_Brand", "")
    
    # Remove distributor codes and junk
    if "--" in brand: brand = ""
    brand = brand.replace("(APPDE)", "").replace("(4031)", "").replace("(3073)", "").strip()
    
    brand_lower = brand.lower()
    for key, alias in BRAND_ALIASES.items():
        if key in brand_lower:
            brand = alias
            break

    queries = [
        f"{brand} {part} specification".strip(),
        f"{brand} {part} spec sheet pdf".strip(),
        f"{brand} {part}".strip(),
        f"{brand} {part} product page".strip(),
        f"{brand} {part} manual".strip(),
        f"site:{brand.lower().replace(' ', '')}.com {part}".strip(),
        f"{part} datasheet".strip()
    ]
    return [q for q in queries if q]
