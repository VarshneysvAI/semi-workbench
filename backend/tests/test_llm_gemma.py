"""Tests for backend/llm/gemma.py — monkeypatched, no live network."""

from __future__ import annotations

import json

import pytest

from backend.llm import gemma


class _FakeResp:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeModels:
    def __init__(self, payload: str) -> None:
        self.payload = payload

    def generate_content(self, *, model, contents, config=None, **kw):
        return _FakeResp(self.payload)


class _FakeClient:
    def __init__(self, payload: str) -> None:
        self.models = _FakeModels(payload)
        self.last_model = None
        self.last_contents = None

    def Models(self):
        return self.models


@pytest.fixture(autouse=True)
def _configure(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("GOOGLE_GENAI_MODEL", "gemma-4-31b-it-test")
    yield


def _patch_client(monkeypatch, payload: str):
    fake = _FakeClient(payload)
    monkeypatch.setattr(gemma, "_CLIENT_FACTORY",
                       lambda genai_module, *, api_key: fake)
    return fake


def test_extract_field_parses_strict_json(monkeypatch):
    payload = json.dumps({
        "value": "NPT", "unit": "",
        "evidence": "threaded connections NPT", "confidence": 1.0,
    })
    _patch_client(monkeypatch, payload)

    fx = gemma.extract_field("NIBCO", "BV-1001", "thread",
                             "The valve has NPT threaded connections.")
    assert fx.value == "NPT"
    assert fx.confidence == 1.0
    assert fx.extractor == "llm"
    assert "NPT" in fx.evidence_snippet


def test_extract_field_handles_empty_value(monkeypatch):
    payload = json.dumps({"value": "", "unit": "", "evidence": "", "confidence": 0.0})
    _patch_client(monkeypatch, payload)

    fx = gemma.extract_field("NIBCO", "BV-1001", "color",
                             "The valve body is bronze.")
    assert fx.value == ""
    assert fx.confidence == 0.0


def test_extract_field_recovers_from_non_json(monkeypatch):
    _patch_client(monkeypatch, "not json at all")
    fx = gemma.extract_field("NIBCO", "BV-1001", "thread", "anything")
    assert fx.value == ""
    assert fx.confidence == 0.0


def test_classify_json_returns_dict(monkeypatch):
    from google.genai import types
    schema = types.Schema(type="OBJECT", properties={
        "manufacturer_col": types.Schema(type="STRING"),
        "part_number_col": types.Schema(type="STRING"),
    }, required=["manufacturer_col", "part_number_col"])
    _patch_client(monkeypatch, json.dumps({"manufacturer_col": "Brand",
                                            "part_number_col": "MPN"}))
    out = gemma.classify_json("headers here", schema=schema, system="infer")
    assert out["manufacturer_col"] == "Brand"
    assert out["part_number_col"] == "MPN"


def test_not_configured_without_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert gemma.is_configured() is False
    with pytest.raises(gemma.LLMNotConfigured):
        gemma.extract_field("NIBCO", "BV-1001", "thread", "...")
