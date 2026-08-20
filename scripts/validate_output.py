import os
import csv
import argparse
from pathlib import Path

def validate(output_dir):
    p = Path(output_dir)
    print(f"Validating output in {output_dir}...")
    
    delivery_csv = p / "Unihack_Delivery_Format_Output.csv"
    if not delivery_csv.exists():
        print("FAIL: Delivery CSV missing.")
        return False
        
    with open(delivery_csv, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        if len(header) != 252:
            print(f"FAIL: Header length is {len(header)}, expected 252.")
            return False
            
    print("PASS: Delivery CSV exists and has 252 columns.")
    
    if not (p / "status_report.csv").exists():
        print("FAIL: status_report.csv missing.")
        return False
        
    print("PASS: Status report exists.")
    print("ALL TESTS PASSED!")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    validate(args.output)
