import json
import asyncio
from backend.pipeline.provider_router import provider_router
from backend.pipeline.logger_setup import logger

BRAND_ALIASES = {
    "dewlt": "DeWalt",
    "milw": "Milwaukee",
    "milwaukee accessory": "Milwaukee",
    "black & decker": "DeWalt",
    "sq": "Speed Queen",
    "ge": "GE Appliances",
    "lg": "LG",
    "kitchen aid": "KitchenAid",
}

async def build_queries(row, manufacturer):
    part = row.get("Mfg_Part_Num", "")
    brand = manufacturer or row.get("E1_Brand", "")
    desc = row.get("Part_Desc", "")
    
    # Remove distributor codes and junk
    if "--" in brand: brand = ""
    brand = brand.replace("(APPDE)", "").replace("(4031)", "").replace("(3073)", "").strip()
    
    brand_lower = brand.lower()
    for key, alias in BRAND_ALIASES.items():
        if key in brand_lower:
            brand = alias
            break

    # Construct the LLM Request
    system_prompt = "You are an expert industrial search engineer. Given a product's raw catalog data, generate a single, highly optimized Google search query that will reliably return the official manufacturer's technical specification page or product manual. DO NOT OUTPUT ANY THINKING OR REASONING. ONLY OUTPUT A RAW JSON OBJECT with a single key 'query' containing the exact search string."
    user_prompt = f"Product Data: Brand: {brand} | Part Number: {part} | Description: {desc}"
    
    queries = []
    try:
        res, parsed_json = await asyncio.to_thread(provider_router.run_extraction, system_prompt, user_prompt)
        if parsed_json and "query" in parsed_json:
            smart_query = parsed_json["query"]
            logger.info(f"LLM_SEARCH_QUERY_GENERATED: {smart_query}")
            queries.append(smart_query)
    except Exception as e:
        logger.warning(f"Failed to generate LLM search query: {e}")

    # Fallbacks
    queries.extend([
        f"{brand} {part} technical specifications".strip(),
        f"site:{brand.lower().replace(' ', '')}.com {part}".strip(),
        f"{brand} {part} product page".strip(),
        f"{part} datasheet".strip()
    ])
    
    return [q for q in queries if q]
