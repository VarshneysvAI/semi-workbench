"""Precedent flywheel — signature embeddings + cosine retrieval (threshold 0.85).

Pure-Python character 4-gram cosine (deterministic, zero deps) by default;
when ``sentence-transformers`` is installed and ``LEDGER_EMBED=bge-m3`` is
set, BAAI/bge-m3 embeddings replace it. The downstream contract is the same,
so swapping later is invisible to the audit.
"""

from __future__ import annotations

import os
from math import sqrt

THRESHOLD = 0.85


def canonical_signature(value_a: str, value_b: str) -> str:
    """Order-insensitive conflict signature — 'NPT vs BSPT' == 'BSPT vs NPT'.

    A conflict is the same conflict regardless of which rival came first, so
    the ledger shares one signature across manufacturers (the flywheel hit).
    """
    first, second = sorted([value_a.strip(), value_b.strip()])
    return f"{first} vs {second}"


def _char_ngrams(text: str, n: int = 4) -> dict[str, int]:
    text = text.strip().lower()
    if len(text) < n:
        text = text + " " * (n - len(text))
    counts: dict[str, int] = {}
    for i in range(len(text) - n + 1):
        gram = text[i:i + n]
        counts[gram] = counts.get(gram, 0) + 1
    return counts


def embed(text: str) -> object:
    if os.environ.get("LEDGER_EMBED", "").strip().lower() == "bge-m3":
        try:
            from sentence_transformers import SentenceTransformer
            return SentenceTransformer("BAAI/bge-m3").encode([text])[0]
        except Exception:
            pass
    return _char_ngrams(text)


def cosine(a: object, b: object) -> float:
    if hasattr(a, "shape") and hasattr(b, "shape"):
        import numpy as np
        av, bv = np.asarray(a, dtype="float64"), np.asarray(b, dtype="float64")
        return float(np.dot(av, bv) / (np.linalg.norm(av) * np.linalg.norm(bv) or 1.0))
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
    na = sqrt(sum(v * v for v in a.values())) or 1.0
    nb = sqrt(sum(v * v for v in b.values())) or 1.0
    return dot / (na * nb)


def find_precedents(
    signatures: list[str],
    query: str,
    threshold: float = THRESHOLD,
) -> list[tuple[str, float]]:
    """Rows in ``signatures`` that match ``query`` (exact or cosine >= threshold)."""
    query_embed = embed(query)
    hits: list[tuple[str, float]] = []
    for other in signatures:
        if other == query:
            hits.append((other, 1.0))
            continue
        score = cosine(query_embed, embed(other))
        if score >= threshold:
            hits.append((other, round(score, 4)))
    return hits