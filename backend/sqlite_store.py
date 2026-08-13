"""SQLite persistence for the SEMI store — survives restarts.

Replaces the in-memory Store with a SQLite-backed store that keeps:
- StateGraphs (per SKU)
- Conflicts
- Ledger rows
- WebSocket connections (in-memory only, recreated on restart)
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from backend.schemas.state_graph import (
    Conflict, ConflictSide, ExtractedCandidate, LedgerRow, Source, StateGraph
)

logger = logging.getLogger("semi.sqlite_store")

# Database schema
SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS state_graphs (
    manufacturer TEXT NOT NULL,
    sku TEXT NOT NULL,
    graph_json TEXT NOT NULL,
    updated_at INTEGER NOT NULL,
    PRIMARY KEY (manufacturer, sku)
);

CREATE TABLE IF NOT EXISTS conflicts (
    manufacturer TEXT NOT NULL,
    sku TEXT NOT NULL,
    attribute TEXT NOT NULL,
    status TEXT NOT NULL,
    a_value TEXT NOT NULL,
    a_source_path TEXT NOT NULL,
    a_source_url TEXT,
    a_authority REAL NOT NULL,
    b_value TEXT NOT NULL,
    b_source_path TEXT NOT NULL,
    b_source_url TEXT,
    b_authority REAL NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    PRIMARY KEY (manufacturer, sku)
);

CREATE TABLE IF NOT EXISTS ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL,
    manufacturer TEXT NOT NULL,
    signature TEXT NOT NULL,
    resolution TEXT NOT NULL,
    note TEXT NOT NULL,
    source_url TEXT,
    changed_outcome INTEGER NOT NULL,
    at INTEGER NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ledger_signature ON ledger(signature);
CREATE INDEX IF NOT EXISTS idx_ledger_sku ON ledger(manufacturer, sku);
CREATE INDEX IF NOT EXISTS idx_ledger_at ON ledger(at);

CREATE TABLE IF NOT EXISTS enrichments (
    manufacturer TEXT NOT NULL,
    sku TEXT NOT NULL,
    delivery_json TEXT NOT NULL,
    quality_json TEXT,
    enriched_at INTEGER NOT NULL,
    PRIMARY KEY (manufacturer, sku)
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS schema_plans (
    plan_id TEXT PRIMARY KEY,
    domain TEXT NOT NULL,
    product_kind TEXT NOT NULL,
    plan_json TEXT NOT NULL,
    confidence REAL NOT NULL,
    needs_human INTEGER NOT NULL DEFAULT 0,
    source_file TEXT NOT NULL DEFAULT '',
    discovered_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS attribute_knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT NOT NULL,
    product_kind TEXT NOT NULL,
    attribute TEXT NOT NULL,
    value TEXT NOT NULL,
    uom TEXT NOT NULL DEFAULT '',
    source_url TEXT NOT NULL DEFAULT '',
    evidence_snippet TEXT NOT NULL DEFAULT '',
    confidence REAL NOT NULL DEFAULT 0.0,
    sku TEXT NOT NULL DEFAULT '',
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ak_domain_attr ON attribute_knowledge(domain, attribute);
CREATE INDEX IF NOT EXISTS idx_ak_sku ON attribute_knowledge(sku);

CREATE TABLE IF NOT EXISTS review_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id TEXT NOT NULL,
    sku TEXT NOT NULL,
    domain TEXT NOT NULL,
    attribute TEXT NOT NULL,
    value TEXT NOT NULL,
    uom TEXT NOT NULL DEFAULT '',
    source_url TEXT NOT NULL DEFAULT '',
    evidence_snippet TEXT NOT NULL DEFAULT '',
    confidence REAL NOT NULL DEFAULT 0.0,
    reason TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',  -- pending | approved | rejected | corrected
    corrected_value TEXT NOT NULL DEFAULT '',
    reviewed_at INTEGER
);
CREATE INDEX IF NOT EXISTS idx_rq_status ON review_queue(status);
CREATE INDEX IF NOT EXISTS idx_rq_sku ON review_queue(sku);
"""


class SQLiteStore:
    """Thread-safe SQLite-backed store compatible with the in-memory Store API."""

    def __init__(self, db_path: str = "semi.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._conn: sqlite3.Connection | None = None
        self._init_db()
        # WebSocket connections are still in-memory (recreated on restart)
        self.sockets: set[Any] = set()

    def _init_db(self):
        """Initialize database schema."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.executescript(SCHEMA_SQL)
            conn.commit()
            conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        """Get a thread-local connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self) -> None:
        """Close the persistent connection (call for clean teardown)."""
        with self._lock:
            if self._conn is not None:
                try:
                    self._conn.close()
                except Exception:
                    pass
                self._conn = None

    @staticmethod
    def key(manufacturer: str, sku: str) -> tuple[str, str]:
        return manufacturer.strip().lower(), sku.strip().lower()

    # ---- StateGraph operations ----
    def get_graph(self, manufacturer: str, sku: str) -> StateGraph | None:
        key = self.key(manufacturer, sku)
        with self._lock:
            conn = self._get_conn()
            row = conn.execute(
                "SELECT graph_json FROM state_graphs WHERE manufacturer=? AND sku=?",
                (key[0], key[1])
            ).fetchone()
        if row:
            return StateGraph.model_validate_json(row["graph_json"])
        return None

    def set_graph(self, graph: StateGraph) -> None:
        key = self.key(graph.manufacturer, graph.sku)
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                """INSERT OR REPLACE INTO state_graphs (manufacturer, sku, graph_json, updated_at)
                   VALUES (?, ?, ?, ?)""",
                (key[0], key[1], graph.model_dump_json(), int(time.time()))
            )
            conn.commit()

    def get_all_graphs(self) -> dict[tuple[str, str], StateGraph]:
        with self._lock:
            conn = self._get_conn()
            rows = conn.execute(
                "SELECT manufacturer, sku, graph_json FROM state_graphs"
            ).fetchall()
        return {
            (r["manufacturer"], r["sku"]): StateGraph.model_validate_json(r["graph_json"])
            for r in rows
        }

    # ---- Conflict operations ----
    def get_conflict(self, manufacturer: str, sku: str) -> Conflict | None:
        key = self.key(manufacturer, sku)
        with self._lock:
            conn = self._get_conn()
            row = conn.execute(
                """SELECT * FROM conflicts WHERE manufacturer=? AND sku=?""",
                (key[0], key[1])
            ).fetchone()
        if row:
            return Conflict(
                sku=row["sku"],
                manufacturer=row["manufacturer"],
                attribute=row["attribute"],
                status=row["status"],
                a=ConflictSide(
                    value=row["a_value"],
                    source_path=row["a_source_path"],
                    source_url=row["a_source_url"],
                    authority=row["a_authority"]
                ),
                b=ConflictSide(
                    value=row["b_value"],
                    source_path=row["b_source_path"],
                    source_url=row["b_source_url"],
                    authority=row["b_authority"]
                ),
            )
        return None

    def set_conflict(self, conflict: Conflict) -> None:
        key = self.key(conflict.manufacturer, conflict.sku)
        with self._lock:
            conn = self._get_conn()
            now = int(time.time())
            conn.execute(
                """INSERT OR REPLACE INTO conflicts
                   (manufacturer, sku, attribute, status,
                    a_value, a_source_path, a_source_url, a_authority,
                    b_value, b_source_path, b_source_url, b_authority,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                           COALESCE((SELECT created_at FROM conflicts WHERE manufacturer=? AND sku=?), ?),
                           ?)""",
                (key[0], key[1], conflict.attribute, conflict.status,
                 conflict.a.value, conflict.a.source_path, conflict.a.source_url, conflict.a.authority,
                 conflict.b.value, conflict.b.source_path, conflict.b.source_url, conflict.b.authority,
                 key[0], key[1], now, now)
            )
            conn.commit()

    def get_all_conflicts(self) -> dict[tuple[str, str], Conflict]:
        with self._lock:
            conn = self._get_conn()
            rows = conn.execute("SELECT * FROM conflicts").fetchall()
        result = {}
        for row in rows:
            key = (row["manufacturer"], row["sku"])
            result[key] = Conflict(
                sku=row["sku"],
                manufacturer=row["manufacturer"],
                attribute=row["attribute"],
                status=row["status"],
                a=ConflictSide(
                    value=row["a_value"],
                    source_path=row["a_source_path"],
                    source_url=row["a_source_url"],
                    authority=row["a_authority"]
                ),
                b=ConflictSide(
                    value=row["b_value"],
                    source_path=row["b_source_path"],
                    source_url=row["b_source_url"],
                    authority=row["b_authority"]
                ),
            )
        return result

    # ---- Ledger operations ----
    def append_ledger(self, row: LedgerRow) -> None:
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                """INSERT INTO ledger (sku, manufacturer, signature, resolution, note, source_url, changed_outcome, at, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (row.sku, row.manufacturer, row.signature, row.resolution,
                 row.note, row.source_url, int(row.changed_outcome), row.at, int(time.time()))
            )
            conn.commit()

    def get_ledger(self) -> list[LedgerRow]:
        with self._lock:
            conn = self._get_conn()
            rows = conn.execute(
                "SELECT sku, manufacturer, signature, resolution, note, source_url, changed_outcome, at FROM ledger ORDER BY at"
            ).fetchall()
        return [
            LedgerRow(
                sku=r["sku"],
                manufacturer=r["manufacturer"],
                signature=r["signature"],
                resolution=r["resolution"],
                note=r["note"],
                source_url=r["source_url"],
                changed_outcome=bool(r["changed_outcome"]),
                at=r["at"],
            )
            for r in rows
        ]

    def get_ledger_by_signature(self, signature: str) -> list[LedgerRow]:
        with self._lock:
            conn = self._get_conn()
            rows = conn.execute(
                "SELECT sku, manufacturer, signature, resolution, note, source_url, changed_outcome, at FROM ledger WHERE signature=? ORDER BY at",
                (signature,)
            ).fetchall()
        return [
            LedgerRow(
                sku=r["sku"],
                manufacturer=r["manufacturer"],
                signature=r["signature"],
                resolution=r["resolution"],
                note=r["note"],
                source_url=r["source_url"],
                changed_outcome=bool(r["changed_outcome"]),
                at=r["at"],
            )
            for r in rows
        ]

    # ---- Enrichment caching ----
    def save_enrichment(self, manufacturer: str, sku: str, delivery: dict, quality: dict | None) -> None:
        key = self.key(manufacturer, sku)
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                """INSERT OR REPLACE INTO enrichments (manufacturer, sku, delivery_json, quality_json, enriched_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (key[0], key[1], json.dumps(delivery), json.dumps(quality) if quality else None, int(time.time()))
            )
            conn.commit()

    def get_enrichment(self, manufacturer: str, sku: str) -> tuple[dict, dict | None] | None:
        key = self.key(manufacturer, sku)
        with self._lock:
            conn = self._get_conn()
            row = conn.execute(
                "SELECT delivery_json, quality_json FROM enrichments WHERE manufacturer=? AND sku=?",
                (key[0], key[1])
            ).fetchone()
        if row:
            return json.loads(row["delivery_json"]), json.loads(row["quality_json"]) if row["quality_json"] else None
        return None

    # ---- Event log (for debugging/replay) ----
    def log_event(self, event_type: str, payload: dict) -> None:
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                "INSERT INTO events (event_type, payload_json, created_at) VALUES (?, ?, ?)",
                (event_type, json.dumps(payload), int(time.time()))
            )
            conn.commit()

    # ---- Stats ----
    def get_stats(self) -> dict:
        with self._lock:
            conn = self._get_conn()
            graphs = conn.execute("SELECT COUNT(*) as c FROM state_graphs").fetchone()["c"]
            conflicts = conn.execute("SELECT COUNT(*) as c FROM conflicts").fetchone()["c"]
            ledger = conn.execute("SELECT COUNT(*) as c FROM ledger").fetchone()["c"]
            enrichments = conn.execute("SELECT COUNT(*) as c FROM enrichments").fetchone()["c"]
        return {
            "graphs": graphs,
            "conflicts": conflicts,
            "ledger_rows": ledger,
            "enrichments": enrichments,
        }


# ---- Global store instance (can be swapped for in-memory Store) ----
_store_instance: SQLiteStore | None = None


# ---- Schema plan + knowledge base + review queue helpers -------------------

def save_schema_plan(store: "SQLiteStore", plan) -> None:
    """Persist a SchemaPlan (backend.schema.plan.SchemaPlan)."""
    d = plan.to_dict()
    with store._lock:
        conn = store._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO schema_plans
               (plan_id, domain, product_kind, plan_json, confidence,
                needs_human, source_file, discovered_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (plan.plan_id, plan.domain, plan.product_kind, plan.to_json(),
             plan.confidence, int(plan.needs_human), plan.source_file,
             int(plan.discovered_at)),
        )
        conn.commit()


def get_schema_plan(store: "SQLiteStore", plan_id: str):
    """Load a SchemaPlan by id, or None."""
    from backend.schema.plan import SchemaPlan
    with store._lock:
        conn = store._get_conn()
        row = conn.execute(
            "SELECT plan_json FROM schema_plans WHERE plan_id=?",
            (plan_id,),
        ).fetchone()
    if row:
        return SchemaPlan.from_dict(__import__("json").loads(row["plan_json"]),
                                    plan_id=plan_id)
    return None


def save_attribute_knowledge(
    store: "SQLiteStore", *,
    domain: str, product_kind: str, attribute: str, value: str,
    uom: str = "", source_url: str = "", evidence_snippet: str = "",
    confidence: float = 0.0, sku: str = "",
) -> None:
    """Persist a cited attribute value into the knowledge base."""
    with store._lock:
        conn = store._get_conn()
        conn.execute(
            """INSERT INTO attribute_knowledge
               (domain, product_kind, attribute, value, uom, source_url,
                evidence_snippet, confidence, sku, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (domain, product_kind, attribute, value, uom, source_url,
             evidence_snippet, confidence, sku, int(time.time())),
        )
        conn.commit()


def query_knowledge(
    store: "SQLiteStore", *,
    domain: str = "", attribute: str = "",
    limit: int = 50,
) -> list[dict]:
    """Best-known cited values for (domain, attribute) — reuse for future runs."""
    with store._lock:
        conn = store._get_conn()
        sql = ("SELECT domain, product_kind, attribute, value, uom, source_url, "
               "evidence_snippet, confidence, sku FROM attribute_knowledge")
        where = []
        params: list = []
        if domain:
            where.append("domain=?")
            params.append(domain)
        if attribute:
            where.append("attribute=?")
            params.append(attribute)
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY confidence DESC, id DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def enqueue_review(
    store: "SQLiteStore", *,
    plan_id: str, sku: str, domain: str, attribute: str, value: str,
    uom: str = "", source_url: str = "", evidence_snippet: str = "",
    confidence: float = 0.0, reason: str = "",
) -> int:
    """Route a low-confidence value to the human review queue."""
    with store._lock:
        conn = store._get_conn()
        cur = conn.execute(
            """INSERT INTO review_queue
               (plan_id, sku, domain, attribute, value, uom, source_url,
                evidence_snippet, confidence, reason, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')""",
            (plan_id, sku, domain, attribute, value, uom, source_url,
             evidence_snippet, confidence, reason),
        )
        conn.commit()
        return int(cur.lastrowid)


def pending_reviews(store: "SQLiteStore", limit: int = 200) -> list[dict]:
    with store._lock:
        conn = store._get_conn()
        rows = conn.execute(
            """SELECT * FROM review_queue
               WHERE status='pending' ORDER BY id LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def resolve_review(
    store: "SQLiteStore", review_id: int, *,
    status: str, corrected_value: str = "",
) -> None:
    """Human decision on a queued value: approved | rejected | corrected."""
    assert status in ("approved", "rejected", "corrected")
    with store._lock:
        conn = store._get_conn()
        conn.execute(
            """UPDATE review_queue
               SET status=?, corrected_value=?, reviewed_at=?
               WHERE id=?""",
            (status, corrected_value, int(time.time()), review_id),
        )
        conn.commit()


def get_store() -> SQLiteStore:
    """Get or create the global SQLite store."""
    global _store_instance
    if _store_instance is None:
        _store_instance = SQLiteStore()
    return _store_instance


def init_store(db_path: str = "semi.db") -> SQLiteStore:
    """Initialize the global store with a specific path."""
    global _store_instance
    _store_instance = SQLiteStore(db_path)
    return _store_instance


# ---- Test ----
if __name__ == "__main__":
    import tempfile
    import os

    # Test with temp database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        store = SQLiteStore(db_path)

        # Test StateGraph
        graph = StateGraph(
            sku="TEST-001",
            manufacturer="NIBCO",
            sources=[],
            extracted_candidates=[],
        )
        store.set_graph(graph)
        retrieved = store.get_graph("NIBCO", "TEST-001")
        assert retrieved is not None
        assert retrieved.sku == "TEST-001"
        assert retrieved.manufacturer == "NIBCO"
        print("✓ StateGraph CRUD works")

        # Test Conflict
        conflict = Conflict(
            sku="TEST-001",
            manufacturer="NIBCO",
            attribute="thread_standard",
            status="open",
            a={"value": "NPT", "source_url": "https://a.com", "authority": 1.0},
            b={"value": "BSPT", "source_url": "https://b.com", "authority": 0.8},
        )
        store.set_conflict(conflict)
        retrieved = store.get_conflict("NIBCO", "TEST-001")
        assert retrieved is not None
        assert retrieved.a.value == "NPT"
        print("✓ Conflict CRUD works")

        # Test Ledger
        from backend.schemas.state_graph import LedgerRow
        ledger_row = LedgerRow(
            sku="TEST-001",
            manufacturer="NIBCO",
            signature="BSPT vs NPT",
            resolution="NPT",
            note="spec_sheet_authority",
            source_url="https://a.com",
            changed_outcome=False,
            at=int(time.time()),
        )
        store.append_ledger(ledger_row)
        ledger = store.get_ledger()
        assert len(ledger) == 1
        assert ledger[0].resolution == "NPT"
        print("✓ Ledger append works")

        # Test enrichment caching
        store.save_enrichment("NIBCO", "TEST-001", {"sku": "TEST-001", "test": "data"}, {"confidence": 0.9})
        delivery, quality = store.get_enrichment("NIBCO", "TEST-001")
        assert delivery["sku"] == "TEST-001"
        assert quality["confidence"] == 0.9
        print("✓ Enrichment caching works")

        # Test stats
        stats = store.get_stats()
        print(f"Stats: {stats}")

        print("\n✓ All SQLite store tests passed!")
    finally:
        os.unlink(db_path)