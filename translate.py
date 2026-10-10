# translate.py
import json
from pathlib import Path

from mappings.mapper import FormatMapper
from encoders.openprinttag_encoder import OpenPrintTagEncoder

def convert_opentag_to_openprinttag(parsed_opentag_payload: dict) -> bytearray:
    """
    Takes parsed OpenTag input dictionary, normalizes it, applies cross-spec
    field mapping, and returns encoded OpenPrintTag CBOR payload bytes.
    """
    mapper = FormatMapper()
    
    # 1. Normalize source inputs to canonical OpenTag human-readable fields
    readable_model = mapper.flatten_opentag_v2(parsed_opentag_payload)

    # 2. Load the OpenTag -> OpenPrintTag mapping rule configuration
    mapping_file = Path("mappings/opentagv2003_to_openprinttagv1.json")
    with open(mapping_file, "r", encoding="utf-8") as f:
        mapping_config = json.load(f)

    # 3. Translate model keys and convert data types
    translated_model, warnings = mapper.translate_with_mapping(readable_model, mapping_config)
    
    if warnings:
        print(f"[Translation Warnings]: {warnings}")

    # 4. Serialize translated dictionary into OpenPrintTag CBOR bytes
    encoder = OpenPrintTagEncoder()
    cbor_payload = encoder.encode_payload(translated_model)

    return cbor_payload


if __name__ == "__main__":
    # Example invocation using your incoming OpenTag data dict
    sample_opentag_input = {
        "Filament Manufacturer": "Prusa",
        "Base Material Name": "PETG",
        "Color 1 Hex": [255, 0, 0, 255],
        "Minimum Print Temperature": 220,
        "Maximum Print Temperature": 250,
        "Minimum Bed Temperature": 70,
        "Maximum Bed Temperature": 90,
        "Density": 1.27,
        "Empty Spool Weight": 200.0
    }

    cbor_output = convert_opentag_to_openprinttag(sample_opentag_input)
    print(f"Generated CBOR payload ({len(cbor_output)} bytes): {cbor_output.hex().upper()}")