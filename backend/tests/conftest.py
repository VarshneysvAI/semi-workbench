"""Pytest bootstrap — make the repo root importable as `backend`."""

from __future__ import annotations

import sys
import tempfile
import os
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


@pytest.fixture(autouse=True)
def fresh_store():
    """Create a fresh temp SQLite store for each test."""
    from backend.sqlite_store import SQLiteStore
    import backend.server as server_module
    
    # Create a new temp DB for this test
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    test_store = SQLiteStore(db_path)
    server_module.store = test_store
    yield test_store
    
    # Cleanup: close store and remove files
    try:
        test_store.close()
    except Exception:
        pass
    # Remove DB + WAL + SHM files
    for suffix in ("", "-wal", "-shm"):
        try:
            os.unlink(db_path + suffix)
        except (PermissionError, OSError, FileNotFoundError):
            pass

