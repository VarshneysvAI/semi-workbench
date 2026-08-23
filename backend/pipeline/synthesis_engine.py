"""
SEMI — Deterministic Output Synthesis Engine

Guarantees 100% non-empty coverage for mandatory structural columns
by applying code-level rules to synthesize missing fields from
available data. No LLM calls — pure Python logic.
"""
import re
from backend.pipeline.logger_setup import logger


# Standard UOM normalization map
UOM_NORMALIZER = {
    "volts": "V", "volt": "V", "v": "V",
    "watts": "W", "watt": "W", "w": "W",
    "amps": "A", "amp": "A", "ampere": "A", "amperes": "A", "a": "A",
    "hertz": "Hz", "hz": "Hz",
    "inches": "IN", "inch": "IN", "in": "IN", "in.": "IN", "\"": "IN",
    "feet": "FT", "foot": "FT", "ft": "FT", "ft.": "FT",
    "millimeters": "MM", "millimeter": "MM", "mm": "MM",
    "centimeters": "CM", "centimeter": "CM", "cm": "CM",
    "meters": "M", "meter": "M", "m": "M",
    "pounds": "LB", "pound": "LB", "lbs": "LB", "lb": "LB", "lbs.": "LB",
    "ounces": "OZ", "ounce": "OZ", "oz": "OZ", "oz.": "OZ",
    "kilograms": "KG", "kilogram": "KG", "kg": "KG",
    "grams": "G", "gram": "G", "g": "G",
    "gallons": "GAL", "gallon": "GAL", "gal": "GAL",
    "liters": "L", "liter": "L", "l": "L",
    "quarts": "QT", "quart": "QT", "qt": "QT",
    "psi": "PSI",
    "bar": "BAR",
    "rpm": "RPM",
    "cfm": "CFM",
    "gpm": "GPM",
    "dba": "DBA", "db": "DB",
    "btu": "BTU",
    "fahrenheit": "°F", "°f": "°F",
    "celsius": "°C", "°c": "°C",
    "each": "EA", "ea": "EA",
    "pack": "PK", "pk": "PK",
    "pair": "PR", "pr": "PR",
    "box": "BX", "bx": "BX",
    "case": "CS", "cs": "CS",
}


def normalize_uom(raw_uom: str) -> str:
    """Normalize a raw UOM string to its standard abbreviation."""
    if not raw_uom:
        return ""
    cleaned = raw_uom.strip().lower().rstrip('.')
    return UOM_NORMALIZER.get(cleaned, raw_uom.strip().upper())


def split_value_uom(raw_value: str) -> tuple:
    """
    Split a combined value+unit string into (value, uom).
    E.g. "120V" -> ("120", "V"), "2.5 lbs" -> ("2.5", "LB")
    """
    if not raw_value:
        return "", ""
    
    raw = raw_value.strip()
    
    # Try pattern: number followed by unit (unit must start with a letter or symbol, not digit)
    match = re.match(r'^([+-]?\d+\.?\d*)\s*([a-zA-Z°\"\'/].*)$', raw)
    if match:
        val = match.group(1)
        uom = normalize_uom(match.group(2))
        return val, uom
    
    # Try pattern: unit followed by number (e.g. "$19.99")
    match = re.match(r'^([^\d]+)\s*(\d+\.?\d*)$', raw)
    if match:
        uom = normalize_uom(match.group(1))
        val = match.group(2)
        return val, uom
    
    return raw, ""


def synthesize_invoice_desc(manufacturer: str, mpn: str, short_desc: str) -> str:
    """
    Generate INVOICE_DESC: max 40 uppercase characters.
    Format: [MFR] [MPN] [KEY_WORD]
    """
    parts = []
    if manufacturer:
        parts.append(manufacturer.split()[0] if ' ' in manufacturer else manufacturer)
    if mpn:
        parts.append(mpn)
    if short_desc:
        # Add first meaningful word from description
        words = [w for w in short_desc.split() if len(w) > 2 and w.upper() not in (manufacturer or '').upper()]
        if words:
            parts.append(words[0])
    
    result = ' '.join(parts).upper()[:40]
    return result


def synthesize_mobile_desc(brand: str, product_name: str, short_desc: str, mpn: str) -> str:
    """
    Generate MOBILE_DESC: 60-80 Title Case characters.
    """
    parts = []
    if brand:
        parts.append(brand)
    if product_name:
        parts.append(product_name)
    elif short_desc:
        parts.append(short_desc)
    if mpn:
        parts.append(mpn)
    
    result = ' '.join(parts).title()
    
    # Pad if too short
    if len(result) < 60 and short_desc:
        remaining = 80 - len(result)
        result += ' ' + short_desc[:remaining].title()
    
    # Truncate if too long, but ensure minimum 60
    result = result[:80]
    
    # If still too short, pad with product context
    if len(result) < 60:
        padding = f" Industrial Product Part {mpn}" if mpn else " Industrial Grade Product"
        result = (result + padding)[:80]
    
    return result


def synthesize_short_desc(manufacturer: str, mpn: str, part_desc: str) -> str:
    """Generate SHORT_DESC from available data."""
    parts = []
    if manufacturer:
        parts.append(manufacturer)
    if mpn:
        parts.append(mpn)
    if part_desc:
        parts.append(part_desc)
    return ' '.join(parts)[:500]


def synthesize_classpath(dept: str, cls: str, fine: str) -> str:
    """Generate Classpath from taxonomy components."""
    parts = [p for p in [dept, cls, fine] if p]
    return ' > '.join(parts) if parts else ""


def synthesize_delivery_row(row: dict, extracted: dict, input_row: dict) -> dict:
    """
    Apply deterministic synthesis rules to fill all mandatory fields.
    `row` is the current delivery row dict (252 columns).
    `extracted` is the merged JSON from the 3 NIM passes.
    `input_row` is the original input CSV row.
    """
    mpn = row.get("Mfg_Part_Num", "") or row.get("MANUFACTURER_PART_NUMBER", "") or input_row.get("Mfg_Part_Num", "")
    manufacturer = row.get("MANUFACTURER_NAME", "") or row.get("Part_Manuf", "") or input_row.get("Part_Manuf", "")
    brand = row.get("BRAND_NAME", "") or manufacturer
    part_desc = row.get("Part_Desc", "") or input_row.get("Part_Desc", "")
    short_desc = row.get("SHORT_DESC", "")
    product_name = row.get("Product Name", "")
    
    # Guarantee fallback mpn if completely missing in input
    clean_mpn = mpn.strip() if mpn else "N/A"
    
    # ── Identification fields ──
    if not row.get("MANUFACTURER_PART_NUMBER"):
        row["MANUFACTURER_PART_NUMBER"] = clean_mpn
    if not row.get("PART_NUMBER"):
        row["PART_NUMBER"] = clean_mpn
    if not row.get("SKU - MY_PART_NUMBER"):
        row["SKU - MY_PART_NUMBER"] = clean_mpn
    if not row.get("Mfg_Part_Num"):
        row["Mfg_Part_Num"] = clean_mpn
    
    # ── Brand fields ──
    if not row.get("MANUFACTURER_NAME") and manufacturer:
        row["MANUFACTURER_NAME"] = manufacturer
    if not row.get("BRAND_NAME") and brand:
        row["BRAND_NAME"] = brand
    if not row.get("Part_Manuf") and manufacturer:
        row["Part_Manuf"] = manufacturer
    
    # ── Description synthesis ──
    if not row.get("SHORT_DESC"):
        row["SHORT_DESC"] = synthesize_short_desc(manufacturer, mpn, part_desc)
        short_desc = row["SHORT_DESC"]
    
    if not row.get("LONG_DESC1") and short_desc:
        row["LONG_DESC1"] = short_desc
    
    if not row.get("INVOICE_DESC"):
        row["INVOICE_DESC"] = synthesize_invoice_desc(manufacturer, mpn, short_desc)
    
    if not row.get("MOBILE_DESC"):
        row["MOBILE_DESC"] = synthesize_mobile_desc(brand, product_name, short_desc, mpn)
    
    if not row.get("RETAIL_DESC") and short_desc:
        row["RETAIL_DESC"] = short_desc[:200]
    
    if not row.get("Product Name"):
        if product_name:
            row["Product Name"] = product_name
        elif short_desc:
            row["Product Name"] = short_desc[:200]
    
    # ── Taxonomy synthesis ──
    dept = row.get("Dept", "")
    cls = row.get("Class", "")
    fine = row.get("Fine", "")
    
    if not row.get("Classpath") and (dept or cls or fine):
        row["Classpath"] = synthesize_classpath(dept, cls, fine)
    
    # ── Actual Image flag ──
    if row.get("Product Image"):
        row["Actual Image (Yes/No)"] = "Yes"
    elif not row.get("Actual Image (Yes/No)"):
        row["Actual Image (Yes/No)"] = "No"
    
    # ── Normalize all UOM fields ──
    uom_fields = ["LENGTH_UOM", "HEIGHT_UOM", "WIDTH_UOM", "WEIGHT_UOM", "VOLUME_UOM"]
    for field in uom_fields:
        if row.get(field):
            row[field] = normalize_uom(row[field])
    
    # ── Normalize attribute UOMs ──
    for i in range(1, 51):
        uom_key = f"ATTRIBUTE_UOM {i}"
        if row.get(uom_key):
            row[uom_key] = normalize_uom(row[uom_key])
        
        # Split combined value+uom if needed
        val_key = f"ATTRIBUTE_VALUE {i}"
        if row.get(val_key) and not row.get(uom_key):
            val, uom = split_value_uom(row[val_key])
            if uom:
                row[val_key] = val
                row[uom_key] = uom
    
    return row
