import sqlite3
import shutil
import os
from pathlib import Path
from datetime import datetime
from backend.pipeline.logger_setup import logger

DB_FILE = Path(os.getenv("HISTORY_DB_PATH", "backend/history.db"))

def get_connection():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE, timeout=20.0)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
    except Exception:
        pass
    conn.row_factory = sqlite3.Row
    return conn


def init_history_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs_history (
                job_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                total_rows INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                needs_review_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'QUEUED',
                output_dir TEXT NOT NULL
            )
        """)
        conn.commit()

def add_history_record(job_id: str, filename: str, total_rows: int, output_dir: str):
    init_history_db()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO runs_history (job_id, filename, timestamp, total_rows, status, output_dir)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (job_id, filename, now_str, total_rows, "RUNNING", output_dir))
        conn.commit()

def update_history_record(job_id: str, status: str, success_count: int = 0, needs_review_count: int = 0, failed_count: int = 0):
    init_history_db()
    with get_connection() as conn:
        conn.execute("""
            UPDATE runs_history 
            SET status = ?, success_count = ?, needs_review_count = ?, failed_count = ?
            WHERE job_id = ?
        """, (status, success_count, needs_review_count, failed_count, job_id))
        conn.commit()

def get_all_history():
    init_history_db()
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM runs_history ORDER BY timestamp DESC").fetchall()
        return [dict(r) for r in rows]

def get_history_record(job_id: str):
    init_history_db()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM runs_history WHERE job_id = ?", (job_id,)).fetchone()
        return dict(row) if row else None

def delete_history_record(job_id: str):
    init_history_db()
    record = get_history_record(job_id)
    if record:
        output_dir = Path(record["output_dir"])
        if output_dir.exists() and output_dir.is_dir():
            try:
                shutil.rmtree(output_dir, ignore_errors=True)
            except Exception as e:
                logger.error(f"Failed to delete directory {output_dir}: {e}")

        
        with get_connection() as conn:
            conn.execute("DELETE FROM runs_history WHERE job_id = ?", (job_id,))
            conn.commit()
        return True
    return False

init_history_db()
