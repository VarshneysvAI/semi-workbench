import time
import json
from backend.providers.base_provider import BaseProvider, ProviderResult

MOCK_RESPONSE = {
  "manufacturer_name": "Frigidaire",
  "brand_name": "FRIGIDAIRE®",
  "trade_name": "",
  "product_name": "FRIGIDAIRE® Professional Series PDSH4816AF Dishwasher",
  "taxonomy": {
    "dept": "Appliances",
    "class": "Large Appliances",
    "fine": "Dishwashers",
    "classpath": "Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers"
  },
  "descriptions": {
    "mobile_desc": "Frigidaire Professional Series Dishwasher",
    "invoice_desc": "DISHWASHER LEG 5 SST 120V 15A 50-1/4IN",
    "short_desc": "FRIGIDAIRE® Professional Series PDSH4816AF Dishwasher With CleanBoost™, Leg Mounting, 5-Wash Cycle, Stainless Steel",
    "long_desc": "FRIGIDAIRE® Dishwasher With CleanBoost™, Professional Series, 5 Wash Cycles, 120 V, 15 A, Leg Mounting, Stainless Steel",
    "retail_desc": "Professional Series Dishwasher, Leg Mounting, 5-Wash Cycle, Stainless Steel",
    "marketing_description_verbatim": ""
  },
  "features": ["With CleanBoost™", "5 Wash Cycles", "Leg Mounting", "Stainless Steel"],
  "attributes": [
    {
      "label": "Voltage Rating",
      "value": "120",
      "uom": "V",
      "source_url": "https://mock",
      "evidence": "120 V",
      "confidence": 0.95
    }
  ],
  "with": "With CleanBoost™",
  "standards_approvals": ["ENERGY STAR Certified", "UL Listed"],
  "prop65": "",
  "application": "",
  "includes": "",
  "dimensions": {
    "length": "", "length_uom": "", "height": "", "height_uom": "", "width": "24", "width_uom": "in",
    "weight": "", "weight_uom": "", "volume": "", "volume_uom": ""
  },
  "media": {
    "product_image": "", "alternate_images": [], "spec_sheet": "", "catalog": "",
    "installation_manual": "", "owners_manual": "", "sds": "", "video_link": ""
  },
  "identifiers": {"upc": "", "ean": "", "gtin": "", "unspsc": ""},
  "warranty": "",
  "list_price": "",
  "country_of_origin": "",
  "discontinued": "",
  "actual_image_yes_no": "",
  "source_urls": {"mfr_url": "https://mock", "ref_urls": []}
}

class MockProvider(BaseProvider):
    name = "mock"
    def extract(self, system_prompt: str, user_prompt: str) -> ProviderResult:
        time.sleep(0.5)
        return ProviderResult(json.dumps(MOCK_RESPONSE), self.name, 0.5)
