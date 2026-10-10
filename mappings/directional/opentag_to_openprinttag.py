# mappings/directional/opentag_to_openprinttag.py
from typing import Dict, Any, Tuple, List
from mappings.base import BaseMapper


class OpenTagToOpenPrintTagMapper(BaseMapper):
    """Directional mapper from OpenTag V2 to OpenPrintTag V1."""

    @property
    def source_schema_id(self) -> str:
        return "opentag_v2_003"

    @property
    def target_schema_id(self) -> str:
        return "openprinttag_v1"

    def translate(self, source_data: dict, **kwargs) -> Tuple[dict, List[str]]:
        translated = {}
        warnings = []

        if isinstance(source_data, dict) and "parsed_fields" in source_data:
            fields = source_data["parsed_fields"]
        elif isinstance(source_data, dict) and "core" in source_data:
            fields = source_data["core"]
        else:
            fields = source_data if isinstance(source_data, dict) else {}

        def get_val(keys, default):
            for k in keys:
                if k in fields and fields[k] is not None and fields[k] != "":
                    return fields[k]
            return default

        def get_int(keys, default):
            val = get_val(keys, default)
            try:
                return int(float(val))
            except (ValueError, TypeError):
                return default

        def get_float(keys, default):
            val = get_val(keys, default)
            try:
                return float(val)
            except (ValueError, TypeError):
                return default

        # Target metadata
        translated["schema_id"] = "openprinttag_v1"
        translated["protocol"] = "openprinttag"
        translated["version"] = "1.0"

        # Field mapping
        translated["brand_name"] = str(get_val(["Filament Manufacturer", "manufacturer", "brand"], "Generic"))
        translated["material_name"] = str(get_val(["Base Material Name", "material", "material_name"], "PLA"))
        translated["material_abbreviation"] = str(get_val(["Material Modifiers", "material_mod", "material_abbreviation"], "PLA"))
        translated["material_class"] = str(get_val(["material_class"], "filament"))
        translated["material_type"] = str(get_val(["material_type"], "PLA"))

        # Color mapping (RGBA list or Hex -> Hex string)
        color_raw = get_val(["Color 1 Hex", "color_1", "primary_color"], [255, 170, 187, 255])
        if isinstance(color_raw, list) and len(color_raw) >= 3:
            r, g, b = color_raw[0], color_raw[1], color_raw[2]
            a = color_raw[3] if len(color_raw) >= 4 else 255
            translated["primary_color"] = f"#{r:02X}{g:02X}{b:02X}{a:02X}"
        elif isinstance(color_raw, str):
            translated["primary_color"] = color_raw if color_raw.startswith("#") else f"#{color_raw}"
        else:
            translated["primary_color"] = "#FFAABBFF"

        # Temperatures
        translated["min_print_temperature"] = get_int(["Minimum Print Temperature", "min_print_temp"], 190)
        translated["max_print_temperature"] = get_int(["Maximum Print Temperature", "max_print_temp"], 230)
        translated["preheat_temperature"] = get_int(["Target Print Temperature", "print_temp", "preheat_temperature"], 170)
        translated["min_bed_temperature"] = get_int(["Minimum Bed Temperature", "min_bed_temp"], 50)
        translated["max_bed_temperature"] = get_int(["Maximum Bed Temperature", "max_bed_temp"], 70)
        translated["min_chamber_temperature"] = get_int(["min_chamber_temperature"], 0)
        translated["max_chamber_temperature"] = get_int(["max_chamber_temperature"], 0)
        translated["drying_temperature"] = get_int(["drying_temperature"], 55)
        translated["drying_time"] = get_int(["drying_time"], 6)

        # Filament diameter
        dia = get_val(["Filament Diameter", "diameter", "filament_diameter_v2"], 1.75)
        try:
            dia_f = float(dia)
            if dia_f < 10.0:
                translated["filament_diameter_v2"] = int(dia_f * 1000)
            else:
                translated["filament_diameter_v2"] = int(dia_f)
        except (ValueError, TypeError):
            translated["filament_diameter_v2"] = 1750

        # Density, weights, and UUIDs
        translated["density"] = get_float(["Density", "density"], 1.24)
        translated["nominal_netto_full_weight"] = get_float(["Target Weight", "weight", "nominal_netto_full_weight"], 1000.0)
        translated["actual_netto_full_weight"] = get_float(["actual_netto_full_weight"], 1000.0)
        translated["empty_container_weight"] = get_float(["Empty Spool Weight", "empty_spool_weight", "empty_container_weight"], 200.0)

        translated["instance_uuid"] = str(get_val(["Serial Number / Batch ID", "serial", "instance_uuid"], ""))
        translated["material_uuid"] = str(get_val(["material_uuid"], ""))
        translated["gtin"] = str(get_val(["gtin"], ""))

        return translated, warnings