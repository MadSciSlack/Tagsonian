{
  "mapping_id": "opentag_v2_to_openprinttag_v1",
  "source_schema": "opentag_v2_003",
  "target_schema": "openprinttag_v1",
  "field_rules": [
    {
      "source_field": "Filament Manufacturer",
      "target_field": "brand_name",
      "data_type": "string",
      "default_fallback": "Generic"
    },
    {
      "source_field": "Base Material Name",
      "target_field": "material_name",
      "data_type": "string",
      "default_fallback": "PLA"
    },
    {
      "source_field": "Color 1 Hex",
      "target_field": "primary_color",
      "data_type": "color",
      "source_spec": { "format": "rgba_bytes" },
      "target_spec": { "format": "hex_string", "prefix": "#" },
      "default_fallback": "#FFAABBFF"
    },
    {
      "source_field": "Target Print Temperature",
      "target_field": "target_print_temperature",
      "data_type": "int",
      "default_fallback": 210
    },
    {
      "source_field": "Minimum Print Temperature",
      "target_field": "min_print_temperature",
      "data_type": "int",
      "default_fallback": 190
    },
    {
      "source_field": "Maximum Print Temperature",
      "target_field": "max_print_temperature",
      "data_type": "int",
      "default_fallback": 230
    },
    {
      "source_field": "Target Bed Temperature",
      "target_field": "target_bed_temperature",
      "data_type": "int",
      "default_fallback": 60
    },
    {
      "source_field": "Minimum Bed Temperature",
      "target_field": "min_bed_temperature",
      "data_type": "int",
      "default_fallback": 50
    },
    {
      "source_field": "Maximum Bed Temperature",
      "target_field": "max_bed_temperature",
      "data_type": "int",
      "default_fallback": 70
    },
    {
      "source_field": "Density",
      "target_field": "density",
      "data_type": "float",
      "default_fallback": 1.24
    },
    {
      "source_field": "Empty Spool Weight",
      "target_field": "empty_container_weight",
      "data_type": "float",
      "default_fallback": 200.0
    }
  ]
}