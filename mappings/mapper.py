# mappings/mapper.py
from typing import Dict, Any, List, Tuple

class FormatMapper:
    """
    Translates incoming raw or intermediate data models into the target 
    OpenTag3D schema, applying unit scaling and logging out-of-bound warnings.
    """

    def __init__(self):
        # Explicit mapping rules for incoming fields to OpenTag3D target fields
        self.field_aliases = {
            # OpenPrintTag / Generic aliases -> OpenTag3D field names
            "temp_nozzle": "nozzle_temp_min",
            "nozzle_temperature": "nozzle_temp_min",
            "min_nozzle_temp": "nozzle_temp_min",
            "max_nozzle_temp": "nozzle_temp_max",
            "bed_temperature": "bed_temp_min",
            "min_bed_temp": "bed_temp_min",
            "max_bed_temp": "bed_temp_max",
            "filament_diameter": "diameter",
            "spool_weight": "net_weight",
            "filament_weight": "net_weight",
            "vendor_name": "brand",
            "manufacturer": "brand",
            "material_name": "material",
        }

    def translate(self, source_model: Dict[str, Any], target_schema_fields: List[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], List[str]]:
        translated = {}
        warnings = []

        # Build alias lookup map
        for src_key, raw_val in source_model.items():
            if raw_val is None or raw_val == "":
                continue

            target_key = self.field_aliases.get(src_key.lower(), src_key)
            translated[target_key] = raw_val

        # If schema field definitions are passed, validate bounds & explicit scales
        if target_schema_fields:
            for field in target_schema_fields:
                fname = field.get("name")
                ftype = field.get("type", "utf8")
                length = field.get("length", 1)
                scale = field.get("scale", 1)
                signed = field.get("signed", False)

                if fname not in translated or translated[fname] == "":
                    continue

                val = translated[fname]

                # Validate numeric types
                if ftype in ("int", "int_scale"):
                    try:
                        numeric_val = float(val)
                        scaled_val = int(round(numeric_val * scale))

                        # Determine bit boundaries for target field
                        bit_size = length * 8
                        if signed:
                            min_bound = -(1 << (bit_size - 1))
                            max_bound = (1 << (bit_size - 1)) - 1
                        else:
                            min_bound = 0
                            max_bound = (1 << bit_size) - 1

                        # Check if mapped value fits into the target datatype
                        if scaled_val < min_bound or scaled_val > max_bound:
                            warnings.append(
                                f"Field '{fname}' value ({val}) scaled to {scaled_val} "
                                f"exceeds target field size ({length} bytes, range: {min_bound}..{max_bound})."
                            )

                    except (ValueError, TypeError):
                        warnings.append(f"Field '{fname}' contains non-numeric value '{val}' for target type '{ftype}'.")

        return translated, warnings