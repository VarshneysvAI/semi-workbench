"""Cross-source contradiction detection — same attribute, disagreeing sources."""

from __future__ import annotations

from dataclasses import dataclass

MIN_CONFIDENCE = 0.5


@dataclass(slots=True)
class CandidateRow:
    attribute: str
    value: str
    confidence: float
    source_url: str | None
    authority: float
    extractor: str = "llm"


@dataclass(slots=True)
class Contradiction:
    attribute: str
    a: CandidateRow
    b: CandidateRow

    def detail(self) -> str:
        return (f"{self.a.value!r} ({self.a.source_url or 'unknown'}) vs "
                f"{self.b.value!r} ({self.b.source_url or 'unknown'})")


def detect(rows: list[CandidateRow]) -> list[Contradiction]:
    by_attr: dict[str, list[CandidateRow]] = {}
    for row in rows:
        by_attr.setdefault(row.attribute, []).append(row)

    result: list[Contradiction] = []
    for attr, group in by_attr.items():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                if a.value == b.value:
                    continue
                if a.confidence < MIN_CONFIDENCE or b.confidence < MIN_CONFIDENCE:
                    continue
                result.append(Contradiction(attribute=attr, a=a, b=b))
    return result