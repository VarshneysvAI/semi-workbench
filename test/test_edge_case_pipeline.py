"""
SEMI — Edge Case Pipeline Test (Backend-Only)

Runs the full 3-pass pipeline on a 5-row edge case dataset and
analyzes the output for field population coverage.

Edge cases covered:
  Row 1: Milwaukee accessory with distributor code (4031) in Part_Manuf
  Row 2: DeWalt product with "&" in manufacturer name  
  Row 3: Unknown manufacturer (dash "-")
  Row 4: Appliance with distributor code (APPDE)
  Row 5: Missing MPN (empty Mfg_Part_Num)
"""
import asyncio
import csv
import json
import sys
import os
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Must load env before importing pipeline modules
from dotenv import load_dotenv
load_dotenv("backend/.env")

from backend.pipeline.orchestrator import run_pipeline
from backend.pipeline.delivery_header import UNILOG_HEADER


INPUT_CSV = str(Path(__file__).parent / "edge_case_input.csv")
OUTPUT_DIR = str(Path(__file__).parent / "edge_case_output")


async def main():
    # Clean previous output
    out_path = Path(OUTPUT_DIR)
    if out_path.exists():
        shutil.rmtree(out_path)
    out_path.mkdir(parents=True, exist_ok=True)
    
    print("="*70)
    print("SEMI Edge Case Pipeline Test — 5 Row Dataset")
    print("="*70)
    print(f"Input:  {INPUT_CSV}")
    print(f"Output: {OUTPUT_DIR}")
    print()
    
    # Run the pipeline
    print("[1/3] Running pipeline...")
    await run_pipeline(
        input_csv=INPUT_CSV,
        output_dir=OUTPUT_DIR,
        max_rows=5,
        dry_run=False,
        use_cache=False  # Force fresh extraction for testing
    )
    
    # Analyze output CSV
    print("\n[2/3] Analyzing output...")
    delivery_csv = out_path / "Unihack_Delivery_Format_Output.csv"
    if not delivery_csv.exists():
        print("FAIL: Delivery CSV not generated!")
        return
    
    with open(delivery_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        output_headers = reader.fieldnames
        rows = list(reader)
    
    # Header checks
    print(f"\n{'='*70}")
    print("HEADER ANALYSIS")
    print(f"{'='*70}")
    print(f"  Output columns: {len(output_headers)}")
    print(f"  Expected min:   {len(UNILOG_HEADER)} (252)")
    
    # Check all standard headers preserved
    missing_headers = [h for h in UNILOG_HEADER if h not in output_headers]
    if missing_headers:
        print(f"  FAIL: Missing standard headers: {missing_headers[:10]}...")
    else:
        print(f"  PASS: All 252 standard headers present")
    
    # Row-by-row analysis
    print(f"\n{'='*70}")
    print("ROW-BY-ROW FIELD POPULATION ANALYSIS")
    print(f"{'='*70}")
    
    # Critical fields that MUST be populated for every row
    critical_fields = [
        "MANUFACTURER_PART_NUMBER", "Mfg_Part_Num", "PART_NUMBER", "SKU - MY_PART_NUMBER",
        "SHORT_DESC", "LONG_DESC1", "INVOICE_DESC", "MOBILE_DESC",
        "Product Name", "RETAIL_DESC",
    ]
    
    # Important fields (should be populated if web extraction succeeded)
    important_fields = [
        "MANUFACTURER_NAME", "BRAND_NAME", "MFR URL",
        "Dept", "Class", "Classpath",
        "ATTRIBUTE_LABEL 1", "ATTRIBUTE_VALUE 1",
    ]
    
    for i, row in enumerate(rows):
        mpn = row.get("Mfg_Part_Num", "MISSING")
        total = len(output_headers)
        non_empty = sum(1 for k in output_headers if row.get(k, "").strip())
        pct = round(non_empty / total * 100, 1)
        
        print(f"\n  --- Row {i+1}: MPN={mpn} ---")
        print(f"  Non-empty fields: {non_empty}/{total} ({pct}%)")
        
        # Check critical fields
        critical_ok = 0
        critical_missing = []
        for field in critical_fields:
            if row.get(field, "").strip():
                critical_ok += 1
            else:
                critical_missing.append(field)
        
        if critical_missing:
            print(f"  Critical MISSING: {', '.join(critical_missing)}")
        else:
            print(f"  Critical fields: ALL {critical_ok}/{len(critical_fields)} populated [OK]")
        
        # Check important fields
        important_ok = 0
        important_missing = []
        for field in important_fields:
            if row.get(field, "").strip():
                important_ok += 1
            else:
                important_missing.append(field)
        
        if important_missing:
            print(f"  Important MISSING: {', '.join(important_missing)}")
        else:
            print(f"  Important fields: ALL {important_ok}/{len(important_fields)} populated [OK]")
        
        # Show key values
        print(f"  MANUFACTURER_NAME: '{row.get('MANUFACTURER_NAME', '')[:50]}'")
        print(f"  BRAND_NAME: '{row.get('BRAND_NAME', '')[:50]}'")
        print(f"  INVOICE_DESC: '{row.get('INVOICE_DESC', '')[:50]}'")
        print(f"  MOBILE_DESC: '{row.get('MOBILE_DESC', '')[:60]}'")
        print(f"  SHORT_DESC: '{row.get('SHORT_DESC', '')[:60]}'")
        print(f"  ATTR_LABEL 1: '{row.get('ATTRIBUTE_LABEL 1', '')}'")
        print(f"  ATTR_VALUE 1: '{row.get('ATTRIBUTE_VALUE 1', '')}'")
        print(f"  ATTR_UOM 1: '{row.get('ATTRIBUTE_UOM 1', '')}'")
        print(f"  MFR URL: '{row.get('MFR URL', '')[:60]}'")
        print(f"  Product Image: '{row.get('Product Image', '')[:60]}'")
    
    # Status report analysis
    print(f"\n{'='*70}")
    print("STATUS REPORT")
    print(f"{'='*70}")
    
    status_csv = out_path / "status_report.csv"
    if status_csv.exists():
        with open(status_csv, "r", encoding="utf-8") as f:
            statuses = list(csv.DictReader(f))
        
        for s in statuses:
            print(f"  Row {s['row_index']}: {s['Mfg_Part_Num'] or 'MISSING'} -> {s['status']} (provider: {s['provider_used']}, search: {s['search_provider']})")
    
    # Run summary
    summary_path = out_path / "run_summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        print(f"\n  Total: {summary['total_rows']}")
        print(f"  Success: {summary.get('success', 0)}")
        print(f"  Needs Review: {summary.get('needs_review', 0)}")
        print(f"  Parse Failed: {summary.get('parse_failed', 0)}")
        print(f"  Source Not Found: {summary.get('source_not_found', 0)}")
        print(f"  Missing MPN: {summary.get('missing_part_number', 0)}")
        print(f"  Cached: {summary.get('cached', 0)}")
        print(f"  Duration: {summary.get('duration_seconds', 0)}s")
    
    print(f"\n{'='*70}")
    print("EDGE CASE PIPELINE TEST COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())
