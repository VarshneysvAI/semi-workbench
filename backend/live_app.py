from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import uuid
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv("backend/.env")

app = FastAPI(title="SEMI UniHack Pipeline")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)
DIST_DIR = Path("dashboard/dist")
if (DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

from backend.history_db import (
    add_history_record, update_history_record, get_all_history, 
    get_history_record, delete_history_record
)

@app.get("/")
def serve_root():
    if (DIST_DIR / "index.html").exists():
        return FileResponse(DIST_DIR / "index.html")
    return HTMLResponse("<html><body><h1>SEMI Backend Active</h1><p>Run 'npm run build' in dashboard/ to serve SPA here.</p></body></html>")

@app.post("/api/run")
async def run_pipeline_api(background_tasks: BackgroundTasks, file: UploadFile = File(...), max_rows: int = Form(100)):
    job_id = str(uuid.uuid4())
    job_dir = OUTPUT_DIR / job_id
    job_dir.mkdir(exist_ok=True)
    
    input_path = job_dir / "input.csv"
    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    filename = file.filename or "input.csv"
    add_history_record(job_id=job_id, filename=filename, total_rows=max_rows, output_dir=str(job_dir))
        
    def _background_worker():
        import logging
        
        # Configure file logger for this job to stream to UI
        log_file = job_dir / "pipeline.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger = logging.getLogger("semi_pipeline")
        logger.addHandler(file_handler)
        
        try:
            from backend.pipeline.orchestrator import run_pipeline
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            os.environ["CONCURRENCY"] = os.getenv("CONCURRENCY", "1")
            loop.run_until_complete(run_pipeline(
                input_csv=str(input_path),
                output_dir=str(job_dir),
                max_rows=max_rows,
                dry_run=False,
                use_cache=True
            ))

            
            # Read run summary to update history DB
            summary_path = job_dir / "run_summary.json"
            success_count, needs_review, failed_count = 0, 0, 0
            if summary_path.exists():
                try:
                    summary_data = json.loads(summary_path.read_text(encoding="utf-8"))
                    success_count = summary_data.get("success", 0)
                    needs_review = summary_data.get("needs_review", 0)
                    failed_count = summary_data.get("parse_failed", 0) + summary_data.get("source_not_found", 0)
                except Exception: pass
            
            update_history_record(
                job_id=job_id, status="COMPLETED",
                success_count=success_count,
                needs_review_count=needs_review,
                failed_count=failed_count
            )
        except Exception as e:
            update_history_record(job_id=job_id, status="FAILED")
            logger.error(f"Background worker failed: {e}")
        finally:
            logger.removeHandler(file_handler)
            with open(job_dir / "done.marker", "w") as f:
                f.write("DONE")
                
    background_tasks.add_task(_background_worker)
    
    return {"job_id": job_id, "status": "queued"}

@app.get("/api/stream/{job_id}")
async def stream_logs(job_id: str):
    async def event_generator():
        job_dir = OUTPUT_DIR / job_id
        log_file = job_dir / "pipeline.log"
        events_file = job_dir / "events.jsonl"
        
        last_log_pos = 0
        last_events_pos = 0
        
        while True:
            is_done = (job_dir / "done.marker").exists()
                
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as f:
                    f.seek(last_log_pos)
                    lines = f.readlines()
                    last_log_pos = f.tell()
                for line in lines:
                    yield f"data: {json.dumps({'type': 'log', 'message': line.strip()})}\n\n"
                    
            if events_file.exists():
                with open(events_file, "r", encoding="utf-8") as f:
                    f.seek(last_events_pos)
                    lines = f.readlines()
                    last_events_pos = f.tell()
                for line in lines:
                    if line.strip():
                        yield f"data: {line.strip()}\n\n"
                        
            if is_done:
                yield f"data: {json.dumps({'type': 'complete'})}\n\n"
                break
                            
            await asyncio.sleep(0.5)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

from pydantic import BaseModel

class ResolveRequest(BaseModel):
    job_id: str = None
    sku: str
    attribute: str
    human_resolution: str
    reason_tags: list[str] = []

@app.post("/api/resolve")
def resolve_conflict(req: ResolveRequest):
    if req.job_id:
        job_dir = OUTPUT_DIR / req.job_id
        csv_path = job_dir / "Unihack_Delivery_Format_Output.csv"
        if csv_path.exists():
            import csv
            rows = []
            headers = []
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                for row in reader:
                    if row.get("MANUFACTURER_PART_NUMBER") == req.sku:
                        if req.attribute in row:
                            row[req.attribute] = req.human_resolution
                    rows.append(row)
            
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(rows)
                
    return {"status": "success", "sku": req.sku, "resolution": req.human_resolution}

@app.get("/api/export_unilog")
def export_unilog():
    latest_file = None
    latest_time = 0
    if OUTPUT_DIR.exists():
        for item in OUTPUT_DIR.glob("*/*.csv"):
            if "Delivery" in item.name or "Unihack" in item.name:
                mtime = item.stat().st_mtime
                if mtime > latest_time:
                    latest_time = mtime
                    latest_file = item
    if latest_file and latest_file.exists():
        return FileResponse(path=latest_file, filename="Unihack_Delivery_Format_Output.csv")
    
    # Fallback to generating a sample delivery CSV if no job outputs exist yet
    import csv
    sample_dir = OUTPUT_DIR / "sample"
    sample_dir.mkdir(parents=True, exist_ok=True)
    sample_file = sample_dir / "Unihack_Delivery_Format_Output.csv"
    if not sample_file.exists():
        from backend.pipeline.orchestrator import UNILOG_HEADER
        with open(sample_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=UNILOG_HEADER)
            writer.writeheader()
            writer.writerow({
                "MANUFACTURER_PART_NUMBER": "DCL183",
                "MANUFACTURER_NAME": "Dewalt / B&D",
                "BRAND_NAME": "DEWALT",
                "SHORT_DESC": "Dewalt DCL183 Rechargeable Light",
                "LONG_DESC1": "Compact high-output rechargeable LED light for industrial jobsite application.",
                "ATTRIBUTE_LABEL 1": "Voltage",
                "ATTRIBUTE_VALUE 1": "20V MAX",
                "Product Image": "https://www.dewalt.com/images/dcl183.jpg",
                "MFR URL": "https://www.dewalt.com/products/lighting/dcl183.pdf"
            })
    return FileResponse(path=sample_file, filename="Unihack_Delivery_Format_Output.csv")


@app.get("/api/history")
def list_history():
    return get_all_history()



@app.get("/api/history/{job_id}/download/{filename}")
@app.get("/api/jobs/{job_id}/files/{filename}")
def download_file(job_id: str, filename: str):
    job_dir = OUTPUT_DIR / job_id
    file_path = job_dir / filename
    if file_path.exists():
        return FileResponse(path=file_path, filename=filename)
    return {"error": f"File {filename} not found for job {job_id}"}

@app.delete("/api/history/{job_id}")
def delete_history(job_id: str):
    success = delete_history_record(job_id)
    if success:
        return {"status": "deleted", "job_id": job_id}
    return {"error": "Record not found"}

@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    if full_path.startswith("api"):
        return {"error": "API route not found"}
    target = DIST_DIR / full_path
    if target.exists() and target.is_file():
        return FileResponse(target)
    if (DIST_DIR / "index.html").exists():
        return FileResponse(DIST_DIR / "index.html")
    return {"error": "Page not found"}


