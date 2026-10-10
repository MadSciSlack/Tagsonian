# mappings/directional/openprinttag_to_opentag.py
from typing import Dict, Any, Tuple, List
from mappings.base import BaseMapper


class OpenPrintTagToOpenTagMapper(BaseMapper):
    """Directional mapper from OpenPrintTag V1 to OpenTag V2."""

    @property
    def source_schema_id(self) -> str:
        return "openprinttag_v1"

    @property
    def target_schema_id(self) -> str:
        return "opentag_v2_003"

    def translate(self, source_data: dict, target_schema_fields: list = None, **kwargs) -> Tuple[dict, List[str]]:
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

        translated = {}

        # Target metadata
        translated["schema_id"] = "opentag_v2_003"
        translated["protocol"] = "opentag"
        translated["tag_version"] = 2.0
        translated["Tag Version"] = 2.0

        # Diameter
        dia = get_val(["filament_diameter_v2", "filament_diameter", "Filament Diameter"], 1.75)
        try:
            dia_f = float(dia)
            if dia_f > 10.0:
                dia_f = dia_f / 1000.0
            translated["diameter"] = dia_f
            translated["Filament Diameter"] = dia_f
        except (ValueError, TypeError):
            translated["diameter"] = 1.75
            translated["Filament Diameter"] = 1.75

        # Density & Transmission Distance
        density_v = float(get_val(["density", "Density"], 1.24))
        translated["density"] = density_v
        translated["Density"] = density_v

        td_v = float(get_val(["transmission_distance", "Transmission Distance (TD)"], 0.0))
        translated["td"] = td_v
        translated["Transmission Distance (TD)"] = td_v

        # Temperatures
        print_t = int(get_val(["preheat_temperature", "target_print_temperature", "Target Print Temperature"], 210))
        translated["print_temp"] = print_t
        translated["Target Print Temperature"] = print_t

        min_print_t = int(get_val(["min_print_temperature", "Minimum Print Temperature"], 190))
        translated["min_print_temp"] = min_print_t
        translated["Minimum Print Temperature"] = min_print_t

        max_print_t = int(get_val(["max_print_temperature", "Maximum Print Temperature"], 230))
        translated["max_print_temp"] = max_print_t
        translated["Maximum Print Temperature"] = max_print_t

        avg_bed = (int(get_val(["min_bed_temperature"], 50)) + int(get_val(["max_bed_temperature"], 70))) // 2
        bed_t = int(get_val(["target_bed_temperature", "Target Bed Temperature"], avg_bed))
        translated["bed_temp"] = bed_t
        translated["Target Bed Temperature"] = bed_t

        min_bed_t = int(get_val(["min_bed_temperature", "Minimum Bed Temperature"], 50))
        translated["min_bed_temp"] = min_bed_t
        translated["Minimum Bed Temperature"] = min_bed_t

        max_bed_t = int(get_val(["max_bed_temperature", "Maximum Bed Temperature"], 70))
        translated["max_bed_temp"] = max_bed_t
        translated["Maximum Bed Temperature"] = max_bed_t

        nozzle_v = float(get_val(["minimum_nozzle_diameter", "Minimum Nozzle Diameter", "nozzle_diameter"], 0.4))
        translated["nozzle_diameter"] = nozzle_v
        translated["Minimum Nozzle Diameter"] = nozzle_v

        # Strings & Identifiers
        mfr = str(get_val(["brand_name", "Filament Manufacturer", "manufacturer"], "Generic"))
        translated["manufacturer"] = mfr
        translated["Filament Manufacturer"] = mfr

        mat = str(get_val(["material_name", "Base Material Name", "material"], "PLA"))
        translated["material"] = mat
        translated["Base Material Name"] = mat

        mod = str(get_val(["material_abbreviation", "Material Modifiers", "material_mod"], ""))
        translated["material_mod"] = mod
        translated["Material Modifiers"] = mod

        serial_v = str(get_val(["instance_uuid", "serial_number", "Serial Number / Batch ID"], ""))
        translated["serial"] = serial_v
        translated["Serial Number / Batch ID"] = serial_v

        # Color
        color_raw = get_val(["primary_color", "Color 1 Hex", "color_1"], "#FFAABBFF")
        if isinstance(color_raw, str):
            cleaned = color_raw.lstrip("#").strip()
            if len(cleaned) == 6:
                cleaned += "FF"
            try:
                rgba = [int(cleaned[i:i+2], 16) for i in (0, 2, 4, 6)]
            except ValueError:
                rgba = [255, 170, 187, 255]
        elif isinstance(color_raw, list):
            rgba = color_raw
        else:
            rgba = [255, 170, 187, 255]

        translated["color_1"] = rgba
        translated["Color 1 Hex"] = rgba
        translated["color_2"] = [0, 0, 0, 0]
        translated["color_3"] = [0, 0, 0, 0]
        translated["color_4"] = [0, 0, 0, 0]

        # Weights
        empty_w = float(get_val(["empty_container_weight", "Empty Spool Weight", "empty_spool_weight"], 200.0))
        translated["empty_spool_weight"] = empty_w
        translated["Empty Spool Weight"] = empty_w

        target_w = float(get_val(["nominal_netto_full_weight", "actual_netto_full_weight", "Target Weight", "weight"], 1000.0))
        translated["weight"] = target_w
        translated["Target Weight"] = target_w

        return translated, warnings