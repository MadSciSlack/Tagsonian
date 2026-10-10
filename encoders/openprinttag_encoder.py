# encoders/openprinttag_encoder.py
import cbor2
from encoders.base import BaseEncoder


class OpenPrintTagEncoder(BaseEncoder):
    """Encodes standard model dictionaries into OpenPrintTag-compliant CBOR payloads."""

    # Reverse mapping matching OpenPrintTag CBOR field IDs
    REVERSE_FIELD_MAP = {
        "instance_uuid": 0,
        "package_uuid": 1,
        "material_uuid": 2,
        "brand_uuid": 3,
        "gtin": 4,
        "material_class": 8,
        "material_type": 9,
        "material_name": 10,
        "material_abbreviation": 11,
        "brand_name": 12,
        "manufactured_date": 13,
        "nominal_netto_full_weight": 17,
        "primary_color": 21,
        "transmission_distance": 27,
        "tags": 28,
        "density": 33,
        "min_print_temperature": 37,
        "max_print_temperature": 38,
        "min_bed_temperature": 41,
        "max_bed_temperature": 42,
    }

    def __init__(self, schema_input=None):
        pass

    def encode_payload(self, model: dict) -> bytearray:
        """Packs model fields into an OpenPrintTag CBOR byte array."""
        cbor_dict = {}

        for field_name, value in model.items():
            if field_name in self.REVERSE_FIELD_MAP:
                tag_id = self.REVERSE_FIELD_MAP[field_name]

                # Convert Hex color string back to raw bytes for OpenPrintTag primary_color
                if field_name == "primary_color" and isinstance(value, str):
                    clean_hex = value.lstrip("#")
                    try:
                        cbor_dict[tag_id] = bytes.fromhex(clean_hex)
                    except ValueError:
                        cbor_dict[tag_id] = b"\xff\xaa\xbb\xff"
                else:
                    cbor_dict[tag_id] = value

        return bytearray(cbor2.dumps(cbor_dict))