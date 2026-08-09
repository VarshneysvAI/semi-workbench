"""Tests for backend/schema_inference/infer.py — monkeypatched, no live LLM."""

from __future__ import annotations

import pandas as pd
import pytest

from backend.llm import gemma
from backend.schema_inference import infer as infer_mod
from backend.schema_inference.infer import InferredSchema, infer_from_workbook, is_meaningful


@pytest.fixture(autouse=True)
def _llm_configured(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")


def _write_workbook(path, columns, row):
    df = pd.DataFrame([row], columns=columns)
    df.to_excel(path, index=False)


def test_infer_maps_columns(monkeypatch, tmp_path):
    p = tmp_path / "in.xlsx"
    _write_workbook(p, ["Brand", "MPN", "Pressure", "Unit", "SpecURL"],
                    ["NIBCO", "BV-1001", "150", "psi", "https://x"])

    def fake_classify_json(prompt, schema, *, system="", temperature=0.0):
        return {
            "manufacturer_col": "Brand",
            "part_number_col": "MPN",
            "attribute_cols": ["Pressure"],
            "unit_col": "Unit",
            "source_url_col": "SpecURL",
            "confidence": 0.9,
            "notes": "ok",
        }
    monkeypatch.setattr(gemma, "classify_json", fake_classify_json)

    schema = infer_from_workbook(p)
    assert schema.used_llm is True
    assert schema.manufacturer_col == "Brand"
    assert schema.part_number_col == "MPN"
    assert schema.attribute_cols == ["Pressure"]
    assert schema.unit_col == "Unit"
    assert schema.source_url_col == "SpecURL"
    assert schema.confidence == pytest.approx(0.9)
    assert is_meaningful(schema) is True


def test_infer_drops_unknown_columns(monkeypatch, tmp_path):
    p = tmp_path / "in.xlsx"
    _write_workbook(p, ["Brand", "MPN"], ["NIBCO", "BV-1001"])

    def fake_classify_json(prompt, schema, *, system="", temperature=0.0):
        return {"manufacturer_col": "Brand",
                "part_number_col": "DoesNotExist",
                "attribute_cols": ["AlsoMissing", "MPN"],
                "confidence": 0.4}
    monkeypatch.setattr(gemma, "classify_json", fake_classify_json)

    schema = infer_from_workbook(p)
    assert schema.manufacturer_col == "Brand"
    assert schema.part_number_col is None
    assert schema.attribute_cols == ["MPN"]
    assert is_meaningful(schema) is False


def test_infer_without_llm_returns_not_meaningful(monkeypatch, tmp_path):
    p = tmp_path / "in.xlsx"
    _write_workbook(p, ["Brand", "MPN"], ["NIBCO", "BV-1001"])
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    schema = infer_from_workbook(p)
    assert schema.used_llm is False
    assert is_meaningful(schema) is False
