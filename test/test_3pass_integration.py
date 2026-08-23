"""
SEMI — Integration Test for 3-Pass Architecture

Tests the complete pipeline with a 3-row sample to verify:
  1. All 252 headers present in output CSV
  2. No header mutation / corruption
  3. Synthesis engine fills mandatory fields
  4. 3-pass extraction produces valid merged JSON
  5. Output file is well-formed CSV
"""
import asyncio
import csv
import sys
import os
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.pipeline.delivery_header import UNILOG_HEADER
from backend.pipeline.spec_filter import filter_spec_lines, extract_product_header
from backend.pipeline.synthesis_engine import synthesize_delivery_row, normalize_uom, split_value_uom
from backend.pipeline.delivery_mapper import map_to_delivery, merge_pass_results, merge_sources


def test_unilog_header_integrity():
    """Verify the 252-column header is intact."""
    print(f"  Header column count: {len(UNILOG_HEADER)}")
    
    # Check critical columns exist
    critical = [
        "MANUFACTURER_PART_NUMBER", "MANUFACTURER_NAME", "BRAND_NAME",
        "SHORT_DESC", "LONG_DESC1", "INVOICE_DESC", "MOBILE_DESC",
        "ATTRIBUTE_LABEL 1", "ATTRIBUTE_VALUE 1", "ATTRIBUTE_UOM 1",
        "ATTRIBUTE_LABEL 50", "ATTRIBUTE_VALUE 50", "ATTRIBUTE_UOM 50",
        "Product Image", "MFR URL", "UPC", "UNSPSC",
        "LENGTH", "LENGTH_UOM", "WEIGHT", "WEIGHT_UOM",
        "Country Of Origin", "Warranty", "Actual Image (Yes/No)"
    ]
    missing = [c for c in critical if c not in UNILOG_HEADER]
    if missing:
        print(f"  FAIL: Missing critical columns: {missing}")
        return False
    
    print("  PASS: All critical columns present")
    return True


def test_spec_filter():
    """Test the spec line filter with sample product page text."""
    sample_text = """
    DeWalt DCL183 18V XR LED Flashlight
    
    The DeWalt DCL183 provides bright LED illumination for jobsite work.
    
    Navigation Menu | About | Contact | Careers | Login
    
    Specifications:
    Voltage: 18V / 20V MAX
    Lumens: 500 lm
    Battery: Lithium Ion
    Weight: 0.68 kg
    Length: 182 mm
    Runtime: Up to 10 hours
    LED Type: High-efficiency
    
    Reviews and ratings...
    Copyright 2025 DeWalt Industrial Tool Co.
    """
    
    filtered = filter_spec_lines(sample_text, max_chars=2000)
    header = extract_product_header(sample_text, max_chars=1000)
    
    # Verify spec lines are kept
    assert "Voltage" in filtered or "18V" in filtered, "Spec filter should preserve voltage"
    assert "500" in filtered or "Lumens" in filtered, "Spec filter should preserve lumens"
    
    # Verify header extraction works
    assert "DeWalt" in header, "Header should contain product name"
    
    print(f"  Spec filter: {len(sample_text)} -> {len(filtered)} chars")
    print(f"  Header extract: {len(header)} chars")
    print("  PASS: Spec filter working correctly")
    return True


def test_uom_normalization():
    """Test UOM normalization."""
    cases = [
        ("volts", "V"), ("inches", "IN"), ("lbs", "LB"),
        ("kg", "KG"), ("mm", "MM"), ("watts", "W"),
        ("psi", "PSI"), ("fahrenheit", "°F"),
    ]
    for raw, expected in cases:
        result = normalize_uom(raw)
        assert result == expected, f"normalize_uom('{raw}') = '{result}', expected '{expected}'"
    
    print("  PASS: UOM normalization correct")
    return True


def test_value_uom_splitting():
    """Test combined value+unit splitting."""
    cases = [
        ("120V", "120", "V"),
        ("2.5 lbs", "2.5", "LB"),
        ("18", "18", ""),
        ("500 mm", "500", "MM"),
    ]
    for raw, exp_val, exp_uom in cases:
        val, uom = split_value_uom(raw)
        assert val == exp_val, f"split_value_uom('{raw}') value = '{val}', expected '{exp_val}'"
        assert uom == exp_uom, f"split_value_uom('{raw}') uom = '{uom}', expected '{exp_uom}'"
    
    print("  PASS: Value/UOM splitting correct")
    return True


def test_merge_pass_results():
    """Test merging 3 NIM pass results."""
    pass1 = {
        "manufacturer_name": "DeWalt",
        "brand_name": "DEWALT",
        "taxonomy": {"dept": "Power Tools", "class": "Lighting", "fine": "Flashlights"},
        "descriptions": {"short_desc": "18V XR LED Torch", "long_desc": "Professional LED flashlight"},
        "features": ["500 lumens", "IP54 rated"],
    }
    pass2 = {
        "attributes": [
            {"label": "Voltage", "value": "18", "uom": "V"},
            {"label": "Lumens", "value": "500", "uom": "lm"},
            {"label": "Weight", "value": "0.68", "uom": "kg"},
        ]
    }
    pass3 = {
        "identifiers": {"upc": "885911123456", "unspsc": "39111610"},
        "dimensions": {"length": "182", "length_uom": "mm", "weight": "0.68", "weight_uom": "kg"},
        "media": {"product_image": "https://dewalt.com/dcl183.jpg"},
        "warranty": "3 Years",
    }
    
    merged = merge_pass_results(pass1, pass2, pass3)
    
    assert merged["manufacturer_name"] == "DeWalt"
    assert len(merged["attributes"]) == 3
    assert merged["identifiers"]["upc"] == "885911123456"
    assert merged["warranty"] == "3 Years"
    
    print("  PASS: 3-pass merge correct")
    return True


def test_merge_sources():
    """Test dual-source merging."""
    src_a = {
        "manufacturer_name": "DeWalt",
        "brand_name": "DEWALT",
        "descriptions": {"short_desc": "18V LED Torch"},
        "attributes": [{"label": "Voltage", "value": "18", "uom": "V"}],
        "identifiers": {"upc": "", "unspsc": ""},
    }
    src_b = {
        "manufacturer_name": "",
        "brand_name": "DEWALT",
        "descriptions": {"short_desc": ""},
        "attributes": [{"label": "Weight", "value": "1.5", "uom": "LB"}],
        "identifiers": {"upc": "885911123456", "unspsc": "39111610"},
    }
    
    merged = merge_sources(src_a, src_b)
    
    assert merged["manufacturer_name"] == "DeWalt", "Source A manufacturer should win"
    assert merged["identifiers"]["upc"] == "885911123456", "Source B UPC should fill gap"
    assert len(merged["attributes"]) == 2, "Attributes should be merged and deduped"
    
    print("  PASS: Dual-source merge correct")
    return True


def test_synthesis_engine():
    """Test deterministic synthesis fills mandatory fields."""
    input_row = {"Mfg_Part_Num": "DCL183", "Part_Desc": "18V XR LED Torch", "Part_Manuf": "DeWalt"}
    delivery_row = {k: "" for k in UNILOG_HEADER}
    delivery_row["Mfg_Part_Num"] = "DCL183"
    delivery_row["Part_Manuf"] = "DeWalt"
    delivery_row["MANUFACTURER_NAME"] = "DeWalt"
    delivery_row["BRAND_NAME"] = "DEWALT"
    delivery_row["SHORT_DESC"] = "DeWalt 18V XR LED Torch"
    delivery_row["Product Image"] = "https://dewalt.com/dcl183.jpg"
    
    result = synthesize_delivery_row(delivery_row, {}, input_row)
    
    # Check mandatory fields are now populated
    assert result["INVOICE_DESC"], "INVOICE_DESC should be synthesized"
    assert result["MOBILE_DESC"], "MOBILE_DESC should be synthesized"
    assert len(result["INVOICE_DESC"]) <= 40, "INVOICE_DESC must be <= 40 chars"
    assert result["INVOICE_DESC"] == result["INVOICE_DESC"].upper(), "INVOICE_DESC must be uppercase"
    assert result["Actual Image (Yes/No)"] == "Yes", "Should detect product image"
    assert result["MANUFACTURER_PART_NUMBER"] == "DCL183", "MPN should be set"
    
    print(f"  INVOICE_DESC: '{result['INVOICE_DESC']}'")
    print(f"  MOBILE_DESC: '{result['MOBILE_DESC']}'")
    print(f"  Actual Image: '{result['Actual Image (Yes/No)']}'")
    print("  PASS: Synthesis engine fills mandatory fields")
    return True


def test_delivery_mapper():
    """Test full delivery mapping with sample extraction data."""
    input_row = {"Mfg_Part_Num": "DCL183", "Part_Desc": "18V Torch", "Part_Manuf": "DeWalt", "E1_Brand": "DEWLT", "Unilog_Brand": "DEWALT", "DIB_Brand": "DEWALT"}
    
    extracted = {
        "manufacturer_name": "DeWalt",
        "brand_name": "DEWALT",
        "product_name": "18V XR LED Flashlight",
        "taxonomy": {"dept": "Power Tools", "class": "Lighting", "fine": "Flashlights", "classpath": "Power Tools > Lighting > Flashlights"},
        "descriptions": {"short_desc": "18V XR LED Torch", "long_desc": "Professional 500-lumen LED flashlight for industrial use.", "invoice_desc": "DEWALT DCL183 LED TORCH", "mobile_desc": ""},
        "features": ["500 lumens", "IP54 rated", "Lightweight"],
        "attributes": [
            {"label": "Voltage", "value": "18", "uom": "V"},
            {"label": "Lumens", "value": "500", "uom": "lm"},
            {"label": "Battery Type", "value": "Lithium Ion", "uom": ""},
        ],
        "identifiers": {"upc": "885911123456"},
        "dimensions": {"weight": "0.68", "weight_uom": "kg", "length": "182", "length_uom": "mm"},
        "media": {"product_image": "https://dewalt.com/dcl183.jpg"},
        "warranty": "3 Years",
        "source_urls": {"mfr_url": "https://dewalt.com/dcl183", "ref_urls": ["https://grainger.com/dcl183"]},
    }
    
    delivery = map_to_delivery(input_row, extracted, UNILOG_HEADER)
    delivery = synthesize_delivery_row(delivery, extracted, input_row)
    
    # Verify key fields
    assert delivery["MANUFACTURER_NAME"] == "DeWalt"
    assert delivery["BRAND_NAME"] == "DEWALT"
    assert delivery["ATTRIBUTE_LABEL 1"] == "Voltage"
    assert delivery["ATTRIBUTE_VALUE 1"] == "18"
    assert delivery["ATTRIBUTE_UOM 1"] == "V"
    assert delivery["ATTRIBUTE_LABEL 2"] == "Lumens"
    assert delivery["Product Image"] == "https://dewalt.com/dcl183.jpg"
    assert delivery["Actual Image (Yes/No)"] == "Yes"
    assert delivery["UPC"] == "885911123456"
    assert delivery["WEIGHT"] == "0.68"
    assert delivery["WEIGHT_UOM"] == "KG"
    assert delivery["MOBILE_DESC"], "MOBILE_DESC should be synthesized"
    assert delivery["ITEM_FEATURES_1"] == "500 lumens"
    
    # Count non-empty fields
    non_empty = sum(1 for v in delivery.values() if v and str(v).strip())
    print(f"  Non-empty fields: {non_empty} / {len(UNILOG_HEADER)}")
    print("  PASS: Delivery mapper produces correct 252-column row")
    return True


def test_output_csv_headers():
    """Test that writing to CSV preserves all 252 headers."""
    import tempfile
    
    test_dir = Path(tempfile.mkdtemp())
    csv_path = test_dir / "test_output.csv"
    
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=UNILOG_HEADER)
        writer.writeheader()
        
        # Write a sample row
        row = {k: "" for k in UNILOG_HEADER}
        row["MANUFACTURER_PART_NUMBER"] = "TEST123"
        row["MANUFACTURER_NAME"] = "TestMfr"
        writer.writerow(row)
    
    # Read back and verify
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        written_header = next(reader)
    
    assert len(written_header) == len(UNILOG_HEADER), f"Header length mismatch: {len(written_header)} vs {len(UNILOG_HEADER)}"
    assert written_header == UNILOG_HEADER, "Written headers don't match UNILOG_HEADER"
    
    print(f"  Written CSV has {len(written_header)} columns")
    print("  PASS: CSV header integrity preserved")
    
    # Cleanup
    csv_path.unlink()
    test_dir.rmdir()
    return True


if __name__ == "__main__":
    print("\n" + "="*60)
    print("SEMI 3-Pass Architecture — Integration Tests")
    print("="*60)
    
    tests = [
        ("Header Integrity", test_unilog_header_integrity),
        ("Spec Filter", test_spec_filter),
        ("UOM Normalization", test_uom_normalization),
        ("Value/UOM Splitting", test_value_uom_splitting),
        ("3-Pass Merge", test_merge_pass_results),
        ("Dual-Source Merge", test_merge_sources),
        ("Synthesis Engine", test_synthesis_engine),
        ("Delivery Mapper", test_delivery_mapper),
        ("Output CSV Headers", test_output_csv_headers),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        print(f"\n[TEST] {name}")
        try:
            if test_fn():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  FAIL: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print(f"{'='*60}\n")
    
    sys.exit(0 if failed == 0 else 1)
