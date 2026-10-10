"""
OpenPrintTag V1 Python Helper
Loads openprinttag_v1.json and provides utility accessors.
"""

import json
import os
from typing import Any, Dict, List

# Path to the actual JSON file
JSON_PATH = os.path.join(os.path.dirname(__file__), "openprinttag_v1.json")


def load_schema() -> Dict[str, Any]:
    """Loads and returns the raw schema dictionary from openprinttag_v1.json."""
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


OPENPRINTTAG_V1_SCHEMA = load_schema()


def get_flat_fields() -> List[Dict[str, Any]]:
    """Returns a flat list of field definitions for pipeline mapping."""
    flat = []
    fields = OPENPRINTTAG_V1_SCHEMA.get("fields", {})

    if isinstance(fields, list):
        return fields

    for region, region_fields in fields.items():
        for field in region_fields:
            field_copy = dict(field)
            field_copy["region"] = region
            flat.append(field_copy)
    return flat


def get_flat_field_map() -> Dict[str, Dict[str, Any]]:
    """Returns a dictionary keyed by field name for fast lookup."""
    return {field["name"]: field for field in get_flat_fields()}