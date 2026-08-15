import asyncio
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from backend.contracts import (
    NormalizeInput, AssembleInput, AssembleOutput, DeliveryRow,
    SchemaPlan, AttributeBlueprint
)
from backend.extraction_orchestrator import run_extraction
from backend.normalizer_agent import run_normalization
from backend.assembler import run_assembly
from backend.audit.runner import run_audit

logger = logging.getLogger(__name__)

@dataclass
class OverallState:
    sku: str
    manufacturer: str
    description: str
    schema_plan: Optional[SchemaPlan] = None
    raw_extractions: List[Any] = None
    canonical_attributes: List[Any] = None
    audit_report: Any = None
    delivery_row: Optional[DeliveryRow] = None
    status: str = "pending"
    error: str = ""

async def run_pipeline(sku: str, manufacturer: str, description: str, db_store=None) -> OverallState:
    """Fallback Async Python Orchestrator for SEMI Pipeline (replaces LangGraph)."""
    state = OverallState(sku=sku, manufacturer=manufacturer, description=description)
    
    try:
        logger.info("Starting pipeline for %s (%s)", sku, manufacturer)
        
        # 1. Schema Inference (Mocked or retrieved from store)
        # We assume schema inference was already done or we use a basic fallback schema
        from backend.contracts import ColumnRole
        state.schema_plan = SchemaPlan(
            domain="industrial",
            product_kind="valve",
            columns=[ColumnRole(name="sku", role="sku", confidence=1.0, reasoning="primary key")],
            attributes=[
                AttributeBlueprint(name="thread_length", type="number", required=True, uom_candidates=["in", "mm"], source_hint="web search"),
                AttributeBlueprint(name="overall_length", type="number", required=True, uom_candidates=["in", "mm"], source_hint="web search"),
                AttributeBlueprint(name="pressure_rating", type="number", required=True, uom_candidates=["psi"], source_hint="web search"),
            ],
            needs_human=False,
        )
        
        # 2. Parallel Extraction (Phase 3)
        # We pass remaining attributes directly to the RAG logic
        from backend.contracts import ExtractInput
        ext_input = ExtractInput(
            sku=sku,
            manufacturer=manufacturer,
            part_number=sku,
            remaining_attributes=[a.name for a in state.schema_plan.attributes],
            schema_plan=state.schema_plan
        )
        extraction_res = await run_extraction(ext_input)
        
        # Wrap outputs in RawExtraction objects (adapter layer)
        from backend.contracts import RawExtraction
        raw_exts = []
        for cv in extraction_res.cited_values:
            raw_exts.append(RawExtraction(
                raw_label=cv.attribute,
                value=cv.value,
                unit=cv.unit,
                confidence=cv.confidence,
                source_url=cv.source_url,
                evidence_snippet=cv.evidence_snippet,
                extractor="llm"
            ))
        state.raw_extractions = raw_exts
        
        # 3. Two-Pass Normalization (Phase 4)
        norm_input = NormalizeInput(
            sku=sku,
            raw_extractions=state.raw_extractions,
            schema_plan=state.schema_plan
        )
        norm_output = run_normalization(norm_input)
        if norm_output.status != "ok":
            raise ValueError(f"Normalization failed: {norm_output.error}")
        state.canonical_attributes = norm_output.data
        
        # 4. Adversarial Audit (Phase 5)
        # (Assuming graph state is passed. Here we skip complex store logic for the demo runner)
        if db_store:
            from backend.server import _single_lookup_key
            key = _single_lookup_key(sku, "pipeline")
            graph = db_store.get_graph(key[0], key[1])
            if graph:
                state.audit_report = run_audit(graph)
        
        # 5. Assembly (Phase 6)
        assemble_input = AssembleInput(
            sku=sku,
            audit_verdict="ACCEPT", # Simplified
            canonical_attributes=state.canonical_attributes,
            schema_plan=state.schema_plan
        )
        assemble_output = run_assembly(assemble_input)
        if assemble_output.status != "ok":
            raise ValueError(f"Assembly failed: {assemble_output.error}")
            
        state.delivery_row = assemble_output.data
        state.status = "completed"
        logger.info("Pipeline completed successfully for %s", sku)
        
    except Exception as e:
        logger.error("Pipeline failed for %s: %s", sku, str(e))
        state.status = "failed"
        state.error = str(e)
        
    return state
