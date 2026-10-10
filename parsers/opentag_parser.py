# parsers/opentag_parser.py
import json
import struct
from pathlib import Path
from parsers.openprinttag_parser import OpenPrintTagParser

# Fallback schema aligned with opentag_v2_003.json SSOT specification
OPENTAG_V2_SCHEMA = [
    {"name": "Tag Version", "id": "tag_version", "start": "0x00", "length": 2, "type": "int", "scaling": 0.001},
    {"name": "Base Material Name", "id": "material", "start": "0x02", "length": 5, "type": "utf8"},
    {"name": "Material Modifiers", "id": "material_mod", "start": "0x07", "length": 5, "type": "utf8"},
    {"name": "Filament Manufacturer", "id": "manufacturer", "start": "0x0C", "length": 16, "type": "utf8"},
    {"name": "Color Name", "id": "color_name", "start": "0x1C", "length": 32, "type": "utf8"},
    {"name": "Color 1 Hex", "id": "color_1", "start": "0x3C", "length": 4, "type": "rgba"},
    {"name": "Color 2 Hex", "id": "color_2", "start": "0x40", "length": 4, "type": "rgba"},
    {"name": "Color 3 Hex", "id": "color_3", "start": "0x44", "length": 4, "type": "rgba"},
    {"name": "Color 4 Hex", "id": "color_4", "start": "0x48", "length": 4, "type": "rgba"},
    {"name": "Serial Number / Batch ID", "id": "serial", "start": "0x4C", "length": 32, "type": "utf8"},
    {"name": "SKU", "id": "sku", "start": "0x6C", "length": 16, "type": "utf8"},
    {"name": "Barcode", "id": "barcode", "start": "0x7C", "length": 6, "type": "int"},
    {"name": "Manufacture Date", "id": "mfg_date", "start": "0x84", "length": 4, "type": "date"},
    {"name": "Manufacture Time", "id": "mfg_time", "start": "0x88", "length": 3, "type": "time"},
    {"name": "Filament Diameter", "id": "diameter", "start": "0x8C", "length": 2, "type": "int", "scaling": 0.001},
    {"name": "Measured Tolerance", "id": "tolerance", "start": "0x8E", "length": 1, "type": "int", "scaling": 0.01},
    {"name": "Minimum Nozzle Diameter", "id": "nozzle_diameter", "start": "0x8F", "length": 1, "type": "int", "scaling": 0.1},
    {"name": "Target Print Temperature", "id": "print_temp", "start": "0x90", "length": 1, "type": "int", "scaling": 5},
    {"name": "Minimum Print Temperature", "id": "min_print_temp", "start": "0x91", "length": 1, "type": "int", "scaling": 5},
    {"name": "Maximum Print Temperature", "id": "max_print_temp", "start": "0x92", "length": 1, "type": "int", "scaling": 5},
    {"name": "Target Chamber Temperature", "id": "chamber_temp", "start": "0x93", "length": 1, "type": "int", "scaling": 5},
    {"name": "Target Bed Temperature", "id": "bed_temp", "start": "0x94", "length": 1, "type": "int", "scaling": 5},
    {"name": "Minimum Bed Temperature", "id": "min_bed_temp", "start": "0x95", "length": 1, "type": "int", "scaling": 5},
    {"name": "Maximum Bed Temperature", "id": "max_bed_temp", "start": "0x96", "length": 1, "type": "int", "scaling": 5},
    {"name": "Target Volumetric Speed", "id": "target_vso", "start": "0x97", "length": 1, "type": "int"},
    {"name": "Minimum Volumetric Speed", "id": "min_vso", "start": "0x98", "length": 1, "type": "int"},
    {"name": "Maximum Volumetric Speed", "id": "max_vso", "start": "0x99", "length": 1, "type": "int"},
    {"name": "Maximum Dry Temperature", "id": "max_dry_temp", "start": "0x9A", "length": 1, "type": "int", "scaling": 5},
    {"name": "Dry Time", "id": "dry_time", "start": "0x9B", "length": 1, "type": "int"},
    {"name": "Density", "id": "density", "start": "0x9C", "length": 2, "type": "int", "scaling": 0.001},
    {"name": "Target Weight", "id": "weight", "start": "0x9E", "length": 2, "type": "int"},
    {"name": "Empty Spool Weight", "id": "empty_spool_weight", "start": "0xA0", "length": 2, "type": "int"},
    {"name": "Measured Filament Length", "id": "measured_length", "start": "0xA2", "length": 2, "type": "int"},
    {"name": "Measured Filament Weight", "id": "measured_weight", "start": "0xA4", "length": 2, "type": "int"},
    {"name": "Spool Core Diameter", "id": "spool_core_diameter", "start": "0xA6", "length": 1, "type": "int"},
    {"name": "Transmission Distance (TD)", "id": "td", "start": "0xA7", "length": 1, "type": "int", "scaling": 0.1},
    {"name": "MFI Temp", "id": "mfi_temp", "start": "0xA8", "length": 1, "type": "int", "scaling": 5},
    {"name": "MFI Load", "id": "mfi_load", "start": "0xA9", "length": 1, "type": "int", "scaling": 0.01},
    {"name": "MFI Value", "id": "mfi_value", "start": "0xAA", "length": 1, "type": "int"},
    {"name": "Online Data URL", "id": "data_url", "start": "0xB8", "length": 32, "type": "ascii"}
]


class OpenTagBinaryDecoder:
    """Low-level binary decoder: Extracts NDEF payloads and unpacks bytes into fields."""

    @staticmethod
    def extract_ndef_payload(raw_memory: bytearray) -> tuple[str | None, bytearray | None]:
        mem = raw_memory[16:] if len(raw_memory) >= 16 else raw_memory
        idx = 0
        while idx < len(mem):
            tlv_type = mem[idx]
            if tlv_type == 0x00:
                idx += 1
                continue
            if tlv_type == 0xFE:
                break
            if tlv_type == 0x03:
                length = mem[idx + 1]
                offset = 2
                if length == 0xFF:
                    length = (mem[idx + 2] << 8) | mem[idx + 3]
                    offset = 4
                
                ndef_record = mem[idx + offset : idx + offset + length]
                return OpenTagBinaryDecoder._parse_ndef_record(ndef_record)
            
            length = mem[idx + 1]
            idx += 2 + length
            
        return None, None

    @staticmethod
    def _parse_ndef_record(record: bytearray) -> tuple[str | None, bytearray | None]:
        if not record:
            return None, None
        header = record[0]
        type_len = record[1]
        is_sr = bool(header & 0x10)
        payload_len = record[2] if is_sr else struct.unpack(">I", record[2:6])[0]
        
        header_bytes = 3 if is_sr else 6
        mime_type = record[header_bytes : header_bytes + type_len].decode("ascii", errors="ignore")
        payload = record[header_bytes + type_len : header_bytes + type_len + payload_len]
        
        return mime_type, payload

    @classmethod
    def parse_payload(cls, payload: bytearray, schema: list[dict | str], mime_type: str | None = None) -> dict:
        if mime_type and "openprinttag" in mime_type.lower():
            opt_model = OpenPrintTagParser.parse_payload(bytes(payload))
            return opt_model.get("parsed_fields", {})

        parsed_data = {}
        running_offset = 0

        for field in schema:
            if not isinstance(field, dict):
                continue

            field_name = field.get("name")
            if not field_name:
                continue

            if "start" in field or "offset" in field:
                raw_off = field.get("start", field.get("offset", 0))
                off = int(raw_off, 16) if isinstance(raw_off, str) else int(raw_off)
            else:
                off = running_offset

            length = field.get("length", 1)
            f_type = field.get("type", "utf8")
            scaling = float(field.get("scaling", field.get("scale", 1.0)))
            signed = field.get("signed", False)

            running_offset = off + length

            if off + length > len(payload):
                continue

            raw_bytes = payload[off : off + length]

            if f_type in ("utf8", "ascii"):
                value = raw_bytes.decode(f_type, errors="ignore").rstrip("\x00").strip()

            elif f_type == "int_version":
                raw_int = int.from_bytes(raw_bytes, byteorder="big", signed=False)
                value = round(raw_int / 1000.0, 3)

            elif f_type in ("int", "int_scale"):
                raw_int = int.from_bytes(raw_bytes, byteorder="big", signed=signed)
                if scaling != 1.0 and scaling != 0:
                    val_calc = round(float(raw_int) * scaling, 4)
                    value = int(val_calc) if val_calc.is_integer() else val_calc
                else:
                    value = raw_int

            elif f_type == "rgba":
                value = [int(b) for b in raw_bytes[:4]]

            elif f_type == "date":
                year = int.from_bytes(raw_bytes[0:2], byteorder="big", signed=False)
                value = f"{year:04d}-{raw_bytes[2]:02d}-{raw_bytes[3]:02d}"

            elif f_type == "time":
                value = f"{raw_bytes[0]:02d}:{raw_bytes[1]:02d}:{raw_bytes[2]:02d}"

            else:
                value = raw_bytes.hex()

            parsed_data[field_name] = value

        return parsed_data


class OpenTagParser:
    def __init__(self, schema_input="schemas/opentag_v2_003.json"):
        self.spec_data = {}

        if isinstance(schema_input, (str, Path)):
            schema_path = Path(schema_input)
            if schema_path.exists():
                with open(schema_path, "r", encoding="utf-8") as f:
                    self.spec_data = json.load(f)
        elif isinstance(schema_input, dict):
            self.spec_data = schema_input

        if "core" in self.spec_data and "fields" in self.spec_data["core"]:
            raw_fields = self.spec_data["core"]["fields"]
        else:
            raw_fields = self.spec_data.get("fields", [])

        self.fields = self._normalize_fields(raw_fields)

        if not self.fields:
            self.fields = self._normalize_fields(OPENTAG_V2_SCHEMA)

        self._field_map = {}
        for f in self.fields:
            if isinstance(f, dict):
                if "name" in f:
                    self._field_map[f["name"]] = f
                if "id" in f:
                    self._field_map[f["id"]] = f
            elif isinstance(f, str):
                self._field_map[f] = {"name": f, "type": "utf8"}

    def _normalize_fields(self, raw_fields: list | dict) -> list[dict]:
        """Flattens list or region-dict schemas into a list of field dictionaries."""
        flat_fields = []

        if isinstance(raw_fields, list):
            for item in raw_fields:
                if isinstance(item, dict):
                    flat_fields.append(item)
                elif isinstance(item, str):
                    flat_fields.append({"name": item, "type": "utf8"})

        elif isinstance(raw_fields, dict):
            for region_name, field_list in raw_fields.items():
                if isinstance(field_list, list):
                    for item in field_list:
                        if isinstance(item, dict):
                            field_copy = dict(item)
                            field_copy["region"] = region_name
                            flat_fields.append(field_copy)
                        elif isinstance(item, str):
                            flat_fields.append(
                                {"name": item, "type": "utf8", "region": region_name}
                            )

        return flat_fields

    def get_field(self, field_name: str) -> dict | None:
        """Retrieves a field specification dictionary from the loaded schema by field name or ID."""
        return self._field_map.get(field_name)

    def extract_ndef_payload(self, raw_memory: bytearray) -> tuple[str | None, bytearray | None]:
        return OpenTagBinaryDecoder.extract_ndef_payload(raw_memory)

    def parse(self, payload: bytearray, mime_type: str | None = None) -> dict:
        return OpenTagBinaryDecoder.parse_payload(payload, self.fields, mime_type)

    def wrap_ndef_mime(self, raw_payload: bytearray, mime_type: str = "application/opentag3d") -> bytearray:
        mime_bytes = mime_type.encode("ascii")
        type_len = len(mime_bytes)
        payload_len = len(raw_payload)

        header = 0xD2
        record = bytearray([header, type_len, payload_len]) + mime_bytes + raw_payload

        record_len = len(record)
        if record_len < 0xFF:
            tlv = bytearray([0x03, record_len]) + record
        else:
            tlv = bytearray([0x03, 0xFF, (record_len >> 8) & 0xFF, record_len & 0xFF]) + record

        tlv.append(0xFE)
        return tlv