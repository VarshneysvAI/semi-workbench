"""
SEMI — Edge Case Test Report Generator
Reads the edge_case_output CSV and prints a clean summary table.
"""
import csv
import json
from pathlib import Path

OUTPUT_DIR = Path("test/edge_case_output")
DELIVERY_CSV = OUTPUT_DIR / "Unihack_Delivery_Format_Output.csv"
STATUS_CSV = OUTPUT_DIR / "status_report.csv"

def main():
    if not DELIVERY_CSV.exists():
        print("Output CSV not found!")
        return

    with open(DELIVERY_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        rows = list(reader)

    print("=" * 80)
    print("SEMI WORKBENCH — EDGE CASE PIPELINE TEST RESULTS")
    print("=" * 80)
    print(f"Total Header Columns: {len(headers)} (Target: 252)")
    print(f"Total Test Rows Processed: {len(rows)}\n")

    # Column coverage per row
    print("-" * 80)
    print(f"{'Row':<5} | {'MPN':<15} | {'MFR Name':<20} | {'Non-Empty Cols':<15} | {'Coverage %':<10}")
    print("-" * 80)

    mandatory_cols = [
        "MANUFACTURER_PART_NUMBER", "Mfg_Part_Num", "PART_NUMBER", "SKU - MY_PART_NUMBER",
        "SHORT_DESC", "LONG_DESC1", "INVOICE_DESC", "MOBILE_DESC",
        "Product Name", "RETAIL_DESC", "Actual Image (Yes/No)"
    ]

    all_mandatory_pass = True

    for i, r in enumerate(rows):
        mpn = r.get("Mfg_Part_Num") or r.get("MANUFACTURER_PART_NUMBER") or "(None)"
        mfr = r.get("MANUFACTURER_NAME") or r.get("Part_Manuf") or "(None)"
        non_empty = sum(1 for k in headers if r.get(k, "").strip())
        pct = round(non_empty / len(headers) * 100, 1)

        print(f"{i+1:<5} | {mpn[:15]:<15} | {mfr[:20]:<20} | {non_empty:<15} | {pct}%")

        # Mandatory check
        for mc in mandatory_cols:
            if not r.get(mc, "").strip():
                all_mandatory_pass = False
                print(f"      [WARNING] Mandatory field '{mc}' is empty in Row {i+1}!")

    print("-" * 80)
    print(f"100% Mandatory Field Population: {'PASSED [OK]' if all_mandatory_pass else 'FAILED'}")
    print("=" * 80)

if __name__ == "__main__":
    main()
