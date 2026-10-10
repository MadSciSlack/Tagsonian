import json
import struct
from pathlib import Path


class TagEncoder:
    """Encodes Common Data Model values into an NDEF binary payload using a spec.json schema."""

    def __init__(self, schema_path: str | Path):
        self.schema_path = Path(schema_path) if isinstance(schema_path, str) else schema_path
        with open(self.schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)
            
        # Parse fields from core.fields or root fields
        if "core" in self.schema and "fields" in self.schema["core"]:
            self.fields = self.schema["core"]["fields"]
        else:
            self.fields = self.schema.get("fields", [])
            
        self.mime_type = self.schema.get("mime_type", "application/opentag3d")

    def encode_payload(self, data_model: dict) -> bytearray:
        # Calculate max buffer size using hex/int offsets
        max_len = 0
        for f in self.fields:
            raw_off = f.get("start", f.get("offset", 0))
            off = int(raw_off, 16) if isinstance(raw_off, str) else int(raw_off)
            length = f.get("length", 1)
            max_len = max(max_len, off + length)

        payload = bytearray(max_len)

        for field in self.fields:
            fname = field["name"]
            raw_off = field.get("start", field.get("offset", 0))
            off = int(raw_off, 16) if isinstance(raw_off, str) else int(raw_off)
            length = field.get("length", 1)
            ftype = field.get("type", "utf8")

            val = data_model.get(fname, "")
            field_bytes = self._encode_field(val, ftype, length, field)
            payload[off : off + len(field_bytes)] = field_bytes

        return payload

    def wrap_ndef_mime(self, payload: bytearray) -> bytearray:
        mime_bytes = self.mime_type.encode("ascii")
        payload_len = len(payload)
        
        if payload_len <= 255:
            header = 0xD2
            ndef_record = bytearray([header, len(mime_bytes), payload_len]) + mime_bytes + payload
        else:
            header = 0xC2
            ndef_record = bytearray([header, len(mime_bytes)]) + struct.pack(">I", payload_len) + mime_bytes + payload

        tlv_len = len(ndef_record)
        if tlv_len <= 255:
            tlv = bytearray([0x03, tlv_len]) + ndef_record + bytearray([0xFE])
        else:
            tlv = bytearray([0x03, 0xFF, (tlv_len >> 8) & 0xFF, tlv_len & 0xFF]) + ndef_record + bytearray([0xFE])

        return tlv

    def _encode_field(self, val, ftype: str, length: int, field_spec: dict) -> bytearray:
        b = bytearray(length)
        if val is None or val == "":
            return b

        try:
            scale = field_spec.get("scaling", field_spec.get("scale", 1.0))

            if ftype in ("utf8", "ascii"):
                encoded = str(val).encode(ftype, errors="ignore")
                b[: len(encoded)] = encoded[:length]

            elif ftype == "int_version":
                ver_float = float(val)
                ver_int = int(round(ver_float * 1000))
                b = bytearray(ver_int.to_bytes(length, byteorder="big"))

            elif ftype in ("int", "int_scale"):
                num = float(val)
                # If scaling is defined (e.g., 5 for temps or 0.001 for diameter), divide accordingly
                raw_int = int(round(num / scale)) if scale != 0 else int(num)
                b = bytearray(raw_int.to_bytes(length, byteorder="big"))

            elif ftype == "rgba":
                clean_hex = str(val).lstrip("#")
                if len(clean_hex) == 8:
                    b = bytearray(bytes.fromhex(clean_hex))

            elif ftype == "date":
                parts = [int(p) for p in str(val).split("-")]
                if len(parts) == 3:
                    b[0:2] = parts[0].to_bytes(2, "big")
                    b[2] = parts[1]
                    b[3] = parts[2]

            elif ftype == "time":
                clean_time = str(val).replace(" UTC", "")
                parts = [int(p) for p in clean_time.split(":")]
                if len(parts) >= 2:
                    b[0] = parts[0]
                    b[1] = parts[1]
                    b[2] = parts[2] if len(parts) > 2 else 0

        except Exception as e:
            print(f"Warning: Failed to encode field {field_spec.get('name')}: {e}")

        return b