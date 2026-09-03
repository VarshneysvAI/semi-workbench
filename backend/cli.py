import argparse
import asyncio
from dotenv import load_dotenv
load_dotenv("backend/.env")
from backend.pipeline.orchestrator import run_pipeline

def main():
    parser = argparse.ArgumentParser(description="SEMI Pipeline CLI")
    parser.add_argument("--input", required=True, help="Input CSV or Excel (.xlsx/.xls) path")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--max-rows", type=int, default=200)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--sync", action="store_true")
    args = parser.parse_args()

    asyncio.run(run_pipeline(
        input_csv=args.input,
        output_dir=args.output,
        max_rows=args.max_rows,
        dry_run=args.dry_run,
        use_cache=not args.no_cache
    ))

if __name__ == "__main__":
    main()
