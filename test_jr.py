import json_repair as jr
import json
raw = '''{
  "manufacturer_name": "Electrolux Major Appliances, N.A.",
  "brand_name": "Frigidaire",
  "product_name": "24\\" Stainless Steel Tub Built-In Dishwasher with CleanBoost™",
  "taxonomy": {
    "dept}}'''
repaired_str = jr.repair_json(raw)
res = json.loads(repaired_str)
print("Keys:", res.keys())
print("manufacturer_name in res:", "manufacturer_name" in res)
