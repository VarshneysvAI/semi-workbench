import io
import csv
from backend.sqlite_store import SQLiteStore
from backend.ingest.output_mapper import map_state_graph

# The exact 252 columns required by the Unilog Delivery Format
UNILOG_COLUMNS = [
    "MFR URL", "Ref URL 1", "Ref URL 2", "Ref URL 3", "Ref URL 4", "Ref URL 5", 
    "PART_NUMBER", "Dept", "Class", "Fine", "SKU - MY_PART_NUMBER", "Mfg_Part_Num", 
    "Part_Desc", "E1_Brand", "Unilog_Brand", "DIB_Brand", "Part_Manuf", 
    "MANUFACTURER_NAME", "BRAND_NAME", "TRADE_NAME", "MANUFACTURER_PART_NUMBER", 
    "ALTERNATE_PART_NUMBER", "Classpath", "MOBILE_DESC", "INVOICE_DESC", "SHORT_DESC", 
    "LONG_DESC1", "RETAIL_DESC", "MARKETING_DESCRIPTION", "ITEM_FEATURES_1", 
    "ITEM_FEATURES_2", "ITEM_FEATURES_3", "ITEM_FEATURES_4", "ITEM_FEATURES_5", 
    "ITEM_FEATURES_6", "ITEM_FEATURES_7", "ITEM_FEATURES_8", "ITEM_FEATURES_9", 
    "ITEM_FEATURES_10", "ITEM_FEATURES_11", "ITEM_FEATURES_12", "ITEM_FEATURES_13", 
    "ITEM_FEATURES_14", "ITEM_FEATURES_15", "ITEM_FEATURES_16", "ITEM_FEATURES_17", 
    "ITEM_FEATURES_18", "ITEM_FEATURES_19", "ITEM_FEATURES_20", "With", 
    "Standard/Approvals", "Prop 65", "Application", "Includes", "Product Name"
]
for i in range(1, 51):
    UNILOG_COLUMNS.extend([f"ATTRIBUTE_LABEL {i}", f"ATTRIBUTE_VALUE {i}", f"ATTRIBUTE_UOM {i}"])

UNILOG_COLUMNS.extend([
    "UPC", "EAN", "GTIN", "UNSPSC", "Warranty", "List Price", "Selling Qty", 
    "Selling UOM", "Standard Packaging Information", "LENGTH", "LENGTH_UOM", 
    "HEIGHT", "HEIGHT_UOM", "WIDTH", "WIDTH_UOM", "WEIGHT", "WEIGHT_UOM", 
    "VOLUME", "VOLUME_UOM", "Product Image", "Alternate Image 1", "Alternate Image 2", 
    "Alternate Image 3", "Alternate Image 4", "SDS", "SDS_1", "Warranty Information", 
    "Catalog", "Specification Sheet", "Instruction/Installation Manual", "Service Manual", 
    "Owners/User Manual", "Line Drawing", "MTR", "RoHS", "Full Engineering Drawing", 
    "Energy Star Guide", "Technical Bulletin", "Submittal", "Compatibility Chart", 
    "Size Chart", "Product Label/Insert", "Video Link", "Video Link 1", "Country Of Origin", 
    "Discontinued", "Actual Image (Yes/No)"
])

def generate_unilog_csv(store: SQLiteStore) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=UNILOG_COLUMNS)
    writer.writeheader()

    for graph in store.get_all_graphs().values():
        row = {c: "" for c in UNILOG_COLUMNS}
        
        # 1. Fill original input columns stored as input candidates
        input_cands = [c for c in graph.extracted_candidates if c.extractor == "input"]
        for cand in input_cands:
            if cand.attribute in row:
                row[cand.attribute] = cand.value
        
        # Mapping standard required fields
        if not row.get("Mfg_Part_Num"):
            row["Mfg_Part_Num"] = graph.sku
        if not row.get("Part_Manuf"):
            row["Part_Manuf"] = graph.manufacturer
            
        row["MANUFACTURER_PART_NUMBER"] = row["Mfg_Part_Num"]
        row["MANUFACTURER_NAME"] = row["Part_Manuf"]
        row["PART_NUMBER"] = row["Mfg_Part_Num"]
        
        # 2. Add Source URLs
        urls = [s.source_url for s in graph.sources if s.source_url]
        for i, url in enumerate(urls[:5]):
            row[f"Ref URL {i+1}"] = url

        # 3. Add Extracted Attributes
        # Get deduplicated best attributes
        attributes = map_state_graph(graph, dedupe=True)
        attr_idx = 1
        for attr in attributes:
            name = attr["attribute"]
            val = attr["value"]
            uom = attr["unit"]
            
            # Special mapped columns
            name_lower = name.lower()
            if name_lower == "weight":
                row["WEIGHT"] = val
                row["WEIGHT_UOM"] = uom
            elif name_lower == "length":
                row["LENGTH"] = val
                row["LENGTH_UOM"] = uom
            elif name_lower == "height":
                row["HEIGHT"] = val
                row["HEIGHT_UOM"] = uom
            elif name_lower == "width":
                row["WIDTH"] = val
                row["WIDTH_UOM"] = uom
            elif name_lower == "volume":
                row["VOLUME"] = val
                row["VOLUME_UOM"] = uom
            elif name_lower == "upc":
                row["UPC"] = val
            elif name_lower == "ean":
                row["EAN"] = val
            elif name_lower == "gtin":
                row["GTIN"] = val
            elif name_lower == "unspsc":
                row["UNSPSC"] = val
            elif name_lower == "warranty":
                row["Warranty"] = val
            elif name_lower in ("list_price", "list price"):
                row["List Price"] = val
            else:
                if attr_idx <= 50:
                    row[f"ATTRIBUTE_LABEL {attr_idx}"] = name.upper()
                    row[f"ATTRIBUTE_VALUE {attr_idx}"] = val
                    row[f"ATTRIBUTE_UOM {attr_idx}"] = uom
                    attr_idx += 1
                    
        writer.writerow(row)
        
    return output.getvalue()
