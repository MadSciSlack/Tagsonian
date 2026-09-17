# encoders/opentag_encoder.py
from typing import Dict, Any

class OpenTagEncoder:
    def encode_payload(self, model: Dict[str, Any], spec_fields: list) -> bytes:
        # 1. Determine exact total byte allocation based on max field offset + length
        max_len = 0
        for f in spec_fields:
            off = self._get_offset(f)
            length = f.get("length", 1)
            if off + length > max_len:
                max_len = off + length

        payload = bytearray(max_len)

        # 2. Pack each field directly into its explicit start offset
        for field in spec_fields:
            fname = field.get("name")
            ftype = field.get("type", "utf8")
            length = field.get("length", 1)
            offset = self._get_offset(field)
            val = model.get(fname, None)

            packed = self._pack_field(ftype, length, val, field)
            payload[offset : offset + len(packed)] = packed

        return bytes(payload)

    def _get_offset(self, field: Dict[str, Any]) -> int:
        raw_off = field.get("start", field.get("offset", 0))
        if isinstance(raw_off, str):
            return int(raw_off, 16) if raw_off.startswith("0x") else int(raw_off)
        return int(raw_off)

    def _pack_field(self, ftype: str, length: int, val: Any, field: Dict[str, Any]) -> bytes:
        buf = bytearray()
        fname = field.get("name", "unknown")

        if ftype in ("int", "int_scale", "int_version"):
            # The schema defines 'scaling' directly (e.g., 5, 0.001, 0.01, 0.1)
            scaling = float(field.get("scaling", field.get("scale", 1.0)))
            signed = field.get("signed", False)
            bit_size = length * 8

            if signed:
                min_val = -(1 << (bit_size - 1))
                max_val = (1 << (bit_size - 1)) - 1
            else:
                min_val = 0
                max_val = (1 << bit_size) - 1

            try:
                if val is None or val == "":
                    int_val = 0
                else:
                    # Raw Byte Value = Engineering Value / Scaling
                    int_val = int(round(float(val) / scaling))
            except (ValueError, TypeError):
                int_val = 0

            clamped_val = max(min_val, min(int_val, max_val))
            buf.extend(clamped_val.to_bytes(length, byteorder="big", signed=signed))

        elif ftype in ("utf8", "ascii"):
            clean_str = str(val).replace("\x00", "") if val is not None else ""
            str_bytes = clean_str.encode(ftype, errors="ignore")
            if len(str_bytes) > length:
                buf.extend(str_bytes[:length])
            else:
                buf.extend(str_bytes.ljust(length, b"\x00"))

        elif ftype == "rgba":
            rgba_vals = [0, 0, 0, 0]
            if isinstance(val, list) and len(val) >= 4:
                rgba_vals = [int(v) for v in val[:4]]
            elif isinstance(val, str) and "," in val:
                parts = [p.strip() for p in val.split(",")]
                rgba_vals = [int(p) for p in parts[:4]] if len(parts) >= 4 else rgba_vals
            buf.extend(bytes(rgba_vals[:length]))

        elif ftype == "date":
            # YYYY-MM-DD -> 2 bytes Year, 1 byte Month, 1 byte Day
            try:
                if isinstance(val, (list, tuple)) and len(val) >= 3:
                    y, m, d = int(val[0]), int(val[1]), int(val[2])
                else:
                    parts = [int(x) for x in str(val).split("-")]
                    y, m, d = parts[0], parts[1], parts[2]
                buf.extend(y.to_bytes(2, byteorder="big"))
                buf.append(m)
                buf.append(d)
            except Exception:
                buf.extend(b"\x00" * length)

        elif ftype == "time":
            # HH:MM:SS -> 1 byte Hr, 1 byte Min, 1 byte Sec
            try:
                if isinstance(val, (list, tuple)) and len(val) >= 3:
                    h, m, s = int(val[0]), int(val[1]), int(val[2])
                else:
                    parts = [int(x) for x in str(val).split(":")]
                    h, m, s = parts[0], parts[1], parts[2]
                buf.append(h)
                buf.append(m)
                buf.append(s)
            except Exception:
                buf.extend(b"\x00" * length)

        else:
            if isinstance(val, (bytes, bytearray)):
                buf.extend(val[:length].ljust(length, b"\x00"))
            else:
                buf.extend(b"\x00" * length)

        return bytes(buf)