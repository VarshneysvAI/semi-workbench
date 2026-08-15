import logging
from typing import Dict, Any

from backend.contracts import AssembleInput, AssembleOutput, DeliveryRow, AgentError

logger = logging.getLogger(__name__)

def generate_descriptions(sku: str, attrs: Dict[str, str]) -> tuple[str, str, str, str, str]:
    """Generates the 5 required descriptions from the canonical attributes."""
    manufacturer = attrs.get('manufacturer', attrs.get('manufacturer_name', 'Unknown'))
    title = f"{manufacturer} {sku}"
    
    # Try to find a primary product kind (e.g. from 'product_type' or 'category')
    product_kind = attrs.get('product_type', attrs.get('category', ''))
    if product_kind:
        title += f" {product_kind}"
        
    invoice = title[:40].upper()
    mobile = title[:80].title()
    short = f"Part {sku} - " + ", ".join(f"{k}: {v}" for k, v in attrs.items() if v)[:400]
    long_desc = short
    
    return invoice, mobile, title, short, long_desc

def run_assembly(input_data: AssembleInput) -> AssembleOutput:
    """Phase 6: Assembles canonical attributes into the 252-column Delivery Row."""
    try:
        attrs = {attr.canonical_key: attr.canonical_value for attr in input_data.canonical_attributes}
        uoms = {attr.canonical_key: attr.canonical_unit for attr in input_data.canonical_attributes}
        
        invoice, mobile, title, short, long_desc = generate_descriptions(input_data.sku, attrs)
        
        row = DeliveryRow(
            sku=input_data.sku,
            mfg_part_num=input_data.sku,
            part_desc=short,
            dept="Industrial",
            class_="Hardware",
            fine="General",
            classpath="Industrial > Hardware > General",
            manufacturer_name=attrs.get("manufacturer", "Unknown"),
            brand_name=attrs.get("brand", "Unknown"),
            invoice_desc=invoice,
            mobile_desc=mobile,
            product_title=title,
            short_desc=short,
            long_desc=long_desc,
            attr_labels={k: k.replace("_", " ").title() for k in attrs},
            attr_values=attrs,
            attr_uoms=uoms,
        )
        
        return AssembleOutput(status="ok", data=row)
    except Exception as e:
        logger.error("Assembly failed: %s", str(e))
        return AssembleOutput(status="error", error=AgentError(code="ASSEMBLY_FAILED", message=str(e)))
