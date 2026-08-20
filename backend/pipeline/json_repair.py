import json
import re
from backend.pipeline.logger_setup import logger

def repair_json(raw_text: str) -> dict | None:
    if not raw_text or not isinstance(raw_text, str) or not raw_text.strip():
        return None
        
    raw = raw_text.strip()
    if raw.startswith("```json"): raw = raw[7:].strip()
    elif raw.startswith("```"): raw = raw[3:].strip()
    if raw.endswith("```"): raw = raw[:-3].strip()
    
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        raw = raw[start:end+1]
    elif start != -1:
        # Truncated JSON
        raw = raw[start:]
        open_braces = raw.count("{") - raw.count("}")
        open_brackets = raw.count("[") - raw.count("]")
        raw += "]" * max(0, open_brackets)
        raw += "}" * max(0, open_braces)
        
    # Attempt 1: Standard load
    try:
        res = json.loads(raw)
        logger.info("JSON_REPAIRED")
        return res
    except Exception:
        pass

    # Attempt 2: Strip trailing commas before closing braces/brackets
    cleaned = re.sub(r',\s*([}\]])', r'\1', raw)
    try:
        res = json.loads(cleaned)
        logger.info("JSON_REPAIRED (trailing commas fixed)")
        return res
    except Exception:
        pass

    # Attempt 3: Try third-party json_repair library if installed
    try:
        import json_repair as jr
        repaired_str = jr.repair_json(raw)
        if isinstance(repaired_str, str):
            res = json.loads(repaired_str)
            if isinstance(res, dict) and res:
                logger.info("JSON_REPAIRED (via json_repair lib)")
                return res
    except ImportError:
        pass
    except Exception:
        pass


    logger.error("JSON Parse failed completely")
    return None


