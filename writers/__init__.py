# writers/__init__.py
from typing import Dict, Any
from writers.base import BaseWriter
from writers.opentag_writer import OpenTagWriter
from writers.openprinttag_writer import OpenPrintTagWriter

WRITER_REGISTRY = {
    "opentag_v2": OpenTagWriter,
    "openprinttag_v1": OpenPrintTagWriter,
}

def get_writer_for_schema(schema_identifier: str, schema_def: Dict[str, Any]) -> BaseWriter:
    """
    Factory method to instantiate and return the matching BaseWriter subclass for a given schema.
    """
    # Normalize identifier lookup key
    key = schema_identifier.lower().replace(".", "_")
    
    for reg_key, writer_cls in WRITER_REGISTRY.items():
        if reg_key in key:
            return writer_cls(schema_def)
            
    # Default fallback to OpenTagWriter if no explicit key match
    return OpenTagWriter(schema_def)