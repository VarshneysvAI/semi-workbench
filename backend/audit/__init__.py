"""Audit engine — the core differentiator (Day 6/7).

Deterministic, math-based checks over extracted candidates: physics/constraint
rules, cross-source contradiction, weighted consensus, refusal gate and
split-conformal prediction intervals. No second-LLM guess, no invented values:
thin evidence produces REFUSE, not a guess.
"""

from .runner import AuditReport, run_audit, authority_of_source  # noqa: F401

__all__ = ["AuditReport", "run_audit", "authority_of_source"]