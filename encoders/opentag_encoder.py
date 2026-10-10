# encoders/opentag_encoder.py
from typing import Dict, Any

class OpenTagEncoder:
    """Encodes high-level dictionary models into raw OpenTag binary payloads with proper inverse scaling."""

    def encode_payload(self, scaled_model: Dict[str, Any], spec_fields: list) -> bytes:
        max_len = 0
        for f in spec_fields:
            off = self._get_offset(f)
            length = f.get("length", 1)
            if off + length > max_len:
                max_len = off + length

        payload = bytearray(max_len)

        for field in spec_fields:
            fname = field.get("name")
            fid = field.get("id")

            ftype = field.get("type", "utf8")
            length = field.get("length", 1)
            offset = self._get_offset(field)

            val = None
            for key in (fname, fid):
                if key and key in scaled_model and scaled_model[key] is not None:
                    val = scaled_model[key]
                    break

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

        if ftype in ("int", "int_scale", "int_version"):
            scaling = float(field.get("scaling", field.get("scale", 1.0)))
            signed = field.get("signed", False)
            bit_size = length * 8

            try:
                float_val = float(val) if val is not None else 0.0
            except (ValueError, TypeError):
                float_val = 0.0

            if ftype == "int_version":
                int_val = int(round(float_val * 1000.0)) if float_val < 100.0 else int(round(float_val))
            elif scaling != 1.0 and scaling != 0.0:
                int_val = int(round(float_val / scaling))
            else:
                int_val = int(round(float_val))

            if signed:
                min_val = -(1 << (bit_size - 1))
                max_val = (1 << (bit_size - 1)) - 1
            else:
                min_val = 0
                max_val = (1 << bit_size) - 1

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
            if hasattr(val, "red") and hasattr(val, "green") and hasattr(val, "blue"):
                alpha = val.alpha() if hasattr(val, "alpha") else 255
                rgba_vals = [val.red(), val.green(), val.blue(), alpha]
            elif isinstance(val, (list, tuple)) and len(val) >= 3:
                try:
                    if len(val) == 3:
                        rgba_vals = [int(val[0]), int(val[1]), int(val[2]), 255]
                    else:
                        rgba_vals = [max(0, min(255, int(v))) for v in val[:4]]
                except (ValueError, TypeError):
                    pass
            elif isinstance(val, int):
                rgba_vals = [
                    (val >> 24) & 0xFF,
                    (val >> 16) & 0xFF,
                    (val >> 8) & 0xFF,
                    val & 0xFF
                ]
            elif isinstance(val, str) and val.strip():
                clean_str = val.strip()
                if clean_str.startswith("rgba(") or clean_str.startswith("rgb("):
                    try:
                        nums = [float(x.strip()) for x in clean_str.split("(")[1].split(")")[0].split(",")]
                        if len(nums) >= 3:
                            alpha = int(nums[3] * 255) if len(nums) == 4 and nums[3] <= 1.0 else (int(nums[3]) if len(nums) == 4 else 255)
                            rgba_vals = [int(nums[0]), int(nums[1]), int(nums[2]), alpha]
                    except Exception:
                        pass
                elif "," in clean_str:
                    try:
                        stripped = clean_str.strip("[]() ")
                        nums = [float(x.strip()) for x in stripped.split(",")]
                        if len(nums) >= 3:
                            alpha = int(nums[3]) if len(nums) >= 4 else 255
                            rgba_vals = [int(nums[0]), int(nums[1]), int(nums[2]), alpha]
                    except Exception:
                        pass
                else:
                    clean_hex = clean_str.lstrip("#")
                    if len(clean_hex) == 6:
                        clean_hex += "FF"
                    if len(clean_hex) == 8:
                        try:
                            iv = int(clean_hex, 16)
                            rgba_vals = [
                                (iv >> 24) & 0xFF,
                                (iv >> 16) & 0xFF,
                                (iv >> 8) & 0xFF,
                                iv & 0xFF
                            ]
                        except ValueError:
                            pass
            
            rgba_bytes = bytes([max(0, min(255, int(v))) for v in rgba_vals])
            if length < 4:
                buf.extend(rgba_bytes[:length])
            else:
                buf.extend(rgba_bytes.ljust(length, b"\x00"))

        elif ftype == "date":
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