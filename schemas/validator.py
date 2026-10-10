# schemas/validator.py
import json
from typing import Dict, Any, List, Tuple

class SchemaValidationError(Exception):
    """Custom exception raised when schema validation rules fail."""
    def __init__(self, message: str, errors: List[str] = None):
        super().__init__(message)
        self.errors = errors or [message]


class SchemaValidator:
    """Validates raw JSON text and domain boundaries for Tagsonian schema definitions."""

    INT_TYPE_BIT_BOUNDS = {
        "uint8": (0, 255, 8),
        "int8": (-128, 127, 8),
        "uint16": (0, 65535, 16),
        "int16": (-32768, 32767, 16),
        "uint24": (0, 16777215, 24),
        "int24": (-8388608, 8388607, 24),
        "uint32": (0, 4294967295, 32),
        "int32": (-2147483648, 2147483647, 32),
    }

    @classmethod
    def validate_raw_schema_text(cls, raw_text: str) -> Tuple[bool, dict, List[str]]:
        """Stage 1 & 2 Combined Validation:
        1. Checks JSON syntax.
        2. Validates field data types, lengths, and scaling sanity.
        
        Returns: (is_valid, parsed_json_dict, list_of_error_messages)
        """
        errors = []

        # --- Stage 1: JSON Syntax Validation ---
        try:
            schema_data = json.loads(raw_text)
        except json.JSONDecodeError as e:
            syntax_err = f"Syntax Error (Line {e.lineno}, Col {e.colno}): {e.msg}"
            return False, {}, [syntax_err]

        if not isinstance(schema_data, dict):
            return False, {}, ["Root JSON must be an object/dictionary."]

        # --- Stage 2: Schema Domain & Structural Validation ---
        fields = schema_data.get("fields") or schema_data.get("core", {}).get("fields", [])
        if not isinstance(fields, list):
            errors.append("Schema error: 'fields' must be a list.")
            return False, schema_data, errors

        seen_ids = set()
        for idx, field in enumerate(fields):
            if not isinstance(field, dict):
                errors.append(f"Field index [{idx}]: Must be an object.")
                continue

            field_id = field.get("id") or field.get("name")
            if not field_id:
                errors.append(f"Field index [{idx}]: Missing required 'id' or 'name'.")
                continue

            if field_id in seen_ids:
                errors.append(f"Field '{field_id}': Duplicate field identifier found.")
            seen_ids.add(field_id)

            # Check 1: Length appropriateness to Data Type
            cls._validate_field_length_and_type(field, errors)

            # Check 2: Value & Scaling Sanity
            cls._validate_scaling_and_bounds(field, errors)

        return len(errors) == 0, schema_data, errors

    @classmethod
    def _validate_field_length_and_type(cls, field: dict, errors: List[str]):
        field_id = field.get("id") or field.get("name", "Unknown")
        ftype = str(field.get("type", "")).lower()
        
        # Support alternative length keys used across OpenTag and OpenPrintTag schemas
        length_bytes = (
            field.get("length") 
            or field.get("byte_length") 
            or field.get("max_bytes")
            or field.get("max_length")
        )
        length_bits = field.get("bit_length")

        # Fixed integer type validations
        if ftype in cls.INT_TYPE_BIT_BOUNDS:
            expected_bits = cls.INT_TYPE_BIT_BOUNDS[ftype][2]
            if length_bits is not None and length_bits != expected_bits:
                errors.append(
                    f"Field '{field_id}': Type '{ftype}' requires bit_length={expected_bits}, "
                    f"but got {length_bits}."
                )
            if length_bytes is not None and length_bytes != (expected_bits // 8):
                errors.append(
                    f"Field '{field_id}': Type '{ftype}' requires length={expected_bits // 8} bytes, "
                    f"but got {length_bytes}."
                )

        # String / UTF-8 / Hex Color validations
        elif ftype in ("utf8", "string", "ascii", "color_hex"):
            # If a default value is provided and is empty string, or max_bytes is defined, allow it
            if length_bytes is None:
                # If it's a color_hex or similar with a format specifier instead of max_bytes, it's valid
                if ftype == "color_hex" and field.get("format"):
                    return
                errors.append(f"Field '{field_id}': String/text type '{ftype}' must declare a positive integer 'length' or 'max_bytes'.")
            elif not isinstance(length_bytes, int) or length_bytes <= 0:
                errors.append(f"Field '{field_id}': String type '{ftype}' length/max_bytes must be a positive integer.")

        # RGBA Color Validation (Requires 4 bytes or 32 bits)
        elif ftype == "rgba":
            if length_bytes is not None and length_bytes != 4:
                errors.append(f"Field '{field_id}': RGBA color fields must be exactly 4 bytes in length.")

    @classmethod
    def _validate_scaling_and_bounds(cls, field: dict, errors: List[str]):
        field_id = field.get("id") or field.get("name", "Unknown")
        ftype = str(field.get("type", "")).lower()
        scale = field.get("scale") or field.get("scaling")
        min_val = field.get("min") or field.get("min_val")
        max_val = field.get("max") or field.get("max_val")

        # 1. Scale Validation
        if scale is not None:
            if not isinstance(scale, (int, float)):
                errors.append(f"Field '{field_id}': 'scale' factor must be a number, got {type(scale).__name__}.")
            elif scale <= 0:
                errors.append(f"Field '{field_id}': 'scale' factor must be greater than 0.")
            elif scale > 1000 or scale < 0.00001:
                errors.append(
                    f"Field '{field_id}': Unreasonable scaling factor ({scale}). "
                    f"Expected values between 0.0001 and 1000.0."
                )

        # 2. Min / Max Sanity
        if min_val is not None and max_val is not None:
            if min_val > max_val:
                errors.append(f"Field '{field_id}': 'min' value ({min_val}) cannot be greater than 'max' value ({max_val}).")

        # 3. Check min/max bounds against binary container type limits
        if ftype in cls.INT_TYPE_BIT_BOUNDS:
            raw_min, raw_max, _ = cls.INT_TYPE_BIT_BOUNDS[ftype]
            scale_factor = scale if isinstance(scale, (int, float)) and scale > 0 else 1.0

            if max_val is not None:
                stored_max = max_val / scale_factor
                if stored_max > raw_max:
                    errors.append(
                        f"Field '{field_id}': Max value {max_val} (scaled raw value {stored_max:.1f}) "
                        f"exceeds maximum capacity ({raw_max}) of integer type '{ftype}'."
                    )

            if min_val is not None:
                stored_min = min_val / scale_factor
                if stored_min < raw_min:
                    errors.append(
                        f"Field '{field_id}': Min value {min_val} (scaled raw value {stored_min:.1f}) "
                        f"exceeds minimum capacity ({raw_min}) of integer type '{ftype}'."
                    )