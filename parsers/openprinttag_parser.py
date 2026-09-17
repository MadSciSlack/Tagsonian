# parsers/openprinttag_parser.py
import cbor2


class OpenPrintTagParser:
    """Parses raw OpenPrintTag binary buffers (NDEF/CBOR) into a normalized dictionary."""

    # CBOR Field Tag Key Map according to the OpenPrintTag Specification
    FIELD_MAP = {
        0: "instance_uuid",
        1: "package_uuid",
        2: "material_uuid",
        3: "brand_uuid",
        4: "gtin",
        8: "material_class",
        9: "material_type",
        10: "material_name",
        11: "material_abbreviation",
        12: "brand_name",
        13: "manufactured_date",
        17: "nominal_netto_full_weight",
        21: "primary_color",
        27: "transmission_distance",
        28: "tags",
        33: "density",
        37: "min_print_temperature",
        38: "max_print_temperature",
        41: "min_bed_temperature",
        42: "max_bed_temperature",
    }

    @classmethod
    def parse_cbor_region(cls, raw_bytes: bytes) -> tuple[dict, dict]:
        """Decodes a CBOR region map into standard fields and raw unknown fields."""
        parsed_fields = {}
        unknown_fields = {}

        if not raw_bytes or raw_bytes == b"\x00" * len(raw_bytes):
            return parsed_fields, unknown_fields

        try:
            # Decode CBOR map (handles both fixed-length and indefinite streams like 0xBF ... 0xFF)
            decoded_map = cbor2.loads(raw_bytes)
            if isinstance(decoded_map, dict):
                for key, value in decoded_map.items():
                    if key in cls.FIELD_MAP:
                        field_name = cls.FIELD_MAP[key]
                        parsed_fields[field_name] = value
                    else:
                        # Store unrecognized key-value pairs as hex strings
                        hex_key = hex(key)[2:] if isinstance(key, int) else str(key)
                        if isinstance(value, bytes):
                            hex_val = value.hex()
                        else:
                            hex_val = str(value)
                        unknown_fields[hex_key] = hex_val
        except Exception as err:
            print(f"[OpenPrintTagParser] CBOR decode error/notice: {err}")

        return parsed_fields, unknown_fields

    @classmethod
    def parse_payload(cls, payload_bytes: bytes) -> dict:
        """Parses the main region payload and builds an engine-ready data model."""
        fields, unknown = cls.parse_cbor_region(payload_bytes)

        # Formats RGBA/Color byte sequences into clean hex strings if required
        if "primary_color" in fields:
            val = fields["primary_color"]
            if isinstance(val, bytes):
                fields["primary_color"] = f"#{val.hex().upper()}"
            elif isinstance(val, list):
                fields["primary_color"] = f"#{''.join(f'{x:02X}' for x in val)}"

        return {
            "protocol": "openprinttag",
            "parsed_fields": fields,
            "unknown_fields": unknown,
        }