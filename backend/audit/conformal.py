"""Split-conformal prediction intervals over extraction confidence.

Honest by construction: ``calibrate`` requires >= 30 labelled calibration
rows, otherwise the pipeline reports an uncalibrated band instead of faking a
calibration. When the official ground-truth (or the human-resolution ledger)
provides labels, this becomes a real 95% CI.
"""

from __future__ import annotations

import math

ALPHA = 0.05
UNCALIBRATED_MARGIN = 0.2
MIN_CALIBRATION_ROWS = 30


def calibrate(rows: list[tuple[float, bool]]) -> float | None:
    """Split-CP quantile from (confidence, correct) calibration rows."""
    if len(rows) < MIN_CALIBRATION_ROWS:
        return None
    scores = sorted(1.0 - conf for conf, _ok in rows)
    n = len(scores)
    idx = min(n - 1, math.ceil((n + 1) * (1 - ALPHA)) - 1)
    return scores[idx]


def predict_interval(confidence: float, qhat: float | None) -> tuple[float, float, bool]:
    """95% prediction interval [lo, hi] for a confidence score."""
    if qhat is None:
        lo = max(0.0, confidence - UNCALIBRATED_MARGIN)
        hi = min(1.0, confidence + UNCALIBRATED_MARGIN)
        return lo, hi, False
    lo = max(0.0, confidence - qhat)
    hi = min(1.0, confidence + qhat)
    return lo, hi, True