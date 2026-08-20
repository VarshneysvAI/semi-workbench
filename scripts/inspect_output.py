import csv
import sys
from pathlib import Path

# Ensure UTF-8 stdout printing
sys.stdout.reconfigure(encoding='utf-8')

csv_path = Path("test_run_live/Unihack_Delivery_Format_Output.csv")
if not csv_path.exists():
    print("CSV file not found")
    exit(1)

with open(csv_path, "r", encoding="utf-8") as f:
    reader = list(csv.reader(f))
    header = reader[0]
    rows = reader[1:]

for idx, row in enumerate(rows):
    non_empty = {header[i]: row[i] for i in range(len(header)) if row[i].strip()}
    part_num = non_empty.get("Mfg_Part_Num") or non_empty.get("PART_NUMBER") or f"Row {idx}"
    brand = non_empty.get("BRAND_NAME") or non_empty.get("MANUFACTURER_NAME") or "Unknown"
    print(f"\n==================================================")
    print(f"ROW {idx}: {brand} - {part_num} ({len(non_empty)} non-empty fields)")
    print(f"==================================================")
    for k, v in non_empty.items():
        print(f"  {k}: {v}")
