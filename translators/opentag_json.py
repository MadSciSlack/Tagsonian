from translators.base import BaseImporter


class OpenTagJSONImporter(BaseImporter):
    """Handles standard OpenTag key-value dictionaries and list-of-objects schemas."""

    def can_handle(self, data: dict | list) -> bool:
        # Fallback importer for structured JSON dicts or arrays
        return isinstance(data, (dict, list))

    def parse(self, data: dict | list, schema_fields: list[dict]) -> dict:
        data_map = {}

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    key = item.get("name") or item.get("field") or item.get("key")
                    val = item.get("value") if "value" in item else item.get("val", "")
                    if key:
                        data_map[key] = val
        elif isinstance(data, dict):
            unwrapped = data.get("data", data.get("fields", data))
            if isinstance(unwrapped, list):
                for item in unwrapped:
                    if isinstance(item, dict):
                        key = item.get("name") or item.get("field") or item.get("key")
                        val = item.get("value") if "value" in item else item.get("val", "")
                        if key:
                            data_map[key] = val
            elif isinstance(unwrapped, dict):
                data_map = unwrapped

        # Map against schema and coerce primitive types
        imported_model = {}
        for field in schema_fields:
            fname = field["name"]
            val = data_map.get(fname, "")

            if val == "":
                imported_model[fname] = ""
                continue

            ftype = field.get("type", "utf8")

            if ftype in ("int", "int_scale") and not isinstance(val, (int, float)):
                try:
                    val = float(val) if "." in str(val) else int(val)
                except ValueError:
                    val = 0
            elif ftype == "rgba" and isinstance(val, str):
                clean = val.lstrip("#")
                if len(clean) == 8:
                    val = [int(clean[i : i + 2], 16) for i in (0, 2, 4, 6)]

            imported_model[fname] = val

        return imported_model