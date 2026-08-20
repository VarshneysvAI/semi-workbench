import json
from pathlib import Path
from backend.config import CACHE_FILE

def is_valid_cache_entry(entry):
    if not entry:
        return False
    if not entry.get("delivery_row"):
        return False
    # Check if any enrichment field is non-empty
    enriched_fields = [
        "MANUFACTURER_NAME", "BRAND_NAME", "SHORT_DESC", "LONG_DESC1"
    ]
    for field in enriched_fields:
        if entry["delivery_row"].get(field):
            return True
    return False

class Cache:
    def __init__(self):
        self.file = CACHE_FILE
        self.data = {}
        if self.file.exists():
            try:
                self.data = json.loads(self.file.read_text())
            except: pass

    def get(self, key):
        entry = self.data.get(key)
        if entry and not is_valid_cache_entry(entry):
            del self.data[key]
            return None
        return entry
        
    def set(self, key, val):
        self.data[key] = val
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text(json.dumps(self.data))

global_cache = Cache()
