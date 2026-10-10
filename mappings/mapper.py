# mappings/mapper.py
import logging
from typing import Dict, Any, List, Tuple

from mappings.directional.opentag_to_openprinttag import OpenTagToOpenPrintTagMapper
from mappings.directional.openprinttag_to_opentag import OpenPrintTagToOpenTagMapper
from writers import get_writer_for_schema, BaseWriter

logger = logging.getLogger(__name__)


def debug_mapping_coverage(source_data: dict, mapping_config: dict) -> str:
    """Evaluates mapping rules against raw source data and returns a detailed,
    structured plain-text report tracking matched rules, fallback triggers,
    unmapped source fields, and translation coverage percentages.
    """
    lines = []
    lines.append("=" * 78)
    lines.append(f" MAPPING DIAGNOSTIC REPORT: {mapping_config.get('mapping_id', 'Unknown ID')}")
    lines.append(f" Source Schema : {mapping_config.get('source_schema', 'N/A')}")
    lines.append(f" Target Schema : {mapping_config.get('target_schema', 'N/A')}")
    lines.append("=" * 78)

    if isinstance(source_data, dict) and "parsed_fields" in source_data:
        source_fields = source_data["parsed_fields"]
        source_context = "Unwrapped 'parsed_fields'"
    elif isinstance(source_data, dict) and "core" in source_data:
        source_fields = source_data["core"]
        source_context = "Unwrapped 'core'"
    else:
        source_fields = source_data if isinstance(source_data, dict) else {}
        source_context = f"Raw dict ({type(source_data).__name__})"

    lines.append(f" Context       : {source_context}")
    lines.append(f" Source Keys   : {len(source_fields)} available")
    lines.append("-" * 78)
    lines.append(f"{'STATUS':<14} | {'SOURCE FIELD':<24} -> {'TARGET FIELD':<22} | {'VALUE / DETAILS'}")
    lines.append("-" * 78)

    rules = mapping_config.get("field_rules", [])
    mapped_count, fallback_count = 0, 0
    matched_source_keys = set()

    for rule in rules:
        src_key = rule.get("source_field", "")
        tgt_key = rule.get("target_field", "")
        d_type = rule.get("data_type", "string")
        fallback = rule.get("default_fallback")

        if src_key in source_fields:
            mapped_count += 1
            matched_source_keys.add(src_key)
            raw_val = source_fields[src_key]
            lines.append(f"{'[MATCH]':<14} | {src_key:<24} -> {tgt_key:<22} | {repr(raw_val)} [{d_type}]")
        else:
            fallback_count += 1
            lines.append(f"{'[MISSING]':<14} | {src_key:<24} -> {tgt_key:<22} | {repr(fallback)} [FALLBACK]")

    unmapped_source_keys = set(source_fields.keys()) - matched_source_keys
    lines.append("-" * 78)
    if unmapped_source_keys:
        lines.append(f" UNMAPPED SOURCE KEYS ({len(unmapped_source_keys)}):")
        for u_key in sorted(unmapped_source_keys):
            lines.append(f"   - {u_key}: {repr(source_fields[u_key])}")
        lines.append("-" * 78)

    coverage_pct = (mapped_count / len(rules) * 100) if rules else 0.0
    lines.append(" SUMMARY STATISTICS:")
    lines.append(f"   * Total Rules Evaluated : {len(rules)}")
    lines.append(f"   * Successfully Mapped   : {mapped_count} ({coverage_pct:.1f}%)")
    lines.append(f"   * Fallbacks Triggered   : {fallback_count}")
    lines.append(f"   * Unmapped Source Keys  : {len(unmapped_source_keys)}")
    lines.append("=" * 78)
    return "\n".join(lines)


class FormatMapper:
    """Orchestrates schema translations by dispatching to modular directional mappers 
    and linking to spec-specific binary writers.
    """

    def __init__(self, mappings: Dict[str, str] | None = None):
        self.mappings = mappings if mappings is not None else {}
        self._registry = {
            ("opentag_v2_003", "openprinttag_v1"): OpenTagToOpenPrintTagMapper(),
            ("openprinttag_v1", "opentag_v2_003"): OpenPrintTagToOpenTagMapper(),
        }

    @staticmethod
    def debug_mapping_coverage(source_data: dict, mapping_config: dict) -> str:
        return debug_mapping_coverage(source_data, mapping_config)

    @staticmethod
    def hex_to_rgba(hex_str: str) -> List[int]:
        if not isinstance(hex_str, str):
            return [0, 0, 0, 0]
        cleaned = hex_str.lstrip("#").strip()
        if len(cleaned) == 6:
            cleaned += "FF"
        if len(cleaned) != 8:
            return [0, 0, 0, 0]
        try:
            return [int(cleaned[i:i + 2], 16) for i in (0, 2, 4, 6)]
        except ValueError:
            return [0, 0, 0, 0]

    @staticmethod
    def rgba_to_hex(rgba: List[int], prefix: str = "#") -> str:
        if not isinstance(rgba, (list, tuple)) or len(rgba) < 3:
            return f"{prefix}000000FF"
        a = rgba[3] if len(rgba) >= 4 else 255
        return f"{prefix}{rgba[0]:02X}{rgba[1]:02X}{rgba[2]:02X}{a:02X}"

    def _resolve_schema_id(self, schema_id: str, schema_def: dict | None = None) -> str:
        """Resolves custom schema GUIDs or IDs to their parent standard schema ID."""
        if schema_def and isinstance(schema_def, dict):
            metadata = schema_def.get("metadata", {})
            parent_id = metadata.get("derived_from") or metadata.get("base_spec")
            if parent_id:
                return str(parent_id)

        if "_custom" in schema_id:
            return schema_id.split("_custom")[0]

        return schema_id

    def translate(
        self,
        source_data: dict,
        target_schema_fields: list | dict | None = None,
        source_schema_id: str = "opentag_v2_003",
        target_schema_id: str = "openprinttag_v1",
        source_schema_def: dict | None = None,
        target_schema_def: dict | None = None,
    ) -> Tuple[dict, List[str]]:
        """Dispatches translation to registered directional mappers."""
        resolved_src = self._resolve_schema_id(source_schema_id, source_schema_def)
        resolved_tgt = self._resolve_schema_id(target_schema_id, target_schema_def)

        if resolved_src == resolved_tgt:
            return source_data, []

        mapper_key = (resolved_src, resolved_tgt)
        if mapper_key in self._registry:
            return self._registry[mapper_key].translate(source_data)

        logger.warning(
            f"No directional mapper registered for {source_schema_id} ({resolved_src}) -> "
            f"{target_schema_id} ({resolved_tgt}). Triggering passthrough fallback."
        )
        return source_data, [
            f"Warning: Fallback passthrough used for {source_schema_id} -> {target_schema_id}"
        ]

    def get_writer(self, target_schema_id: str, target_schema_def: dict) -> BaseWriter:
        """Instantiates the matching spec-specific writer for binary encoding."""
        resolved_id = self._resolve_schema_id(target_schema_id, target_schema_def)
        return get_writer_for_schema(resolved_id, target_schema_def)

    def to_scaled_model(
        self,
        human_readable_model: dict,
        target_schema_fields: List[dict | str] | dict,
    ) -> dict:
        """Normalizes field key names for target schema while preserving unscaled values."""
        scaled = {}
        if isinstance(target_schema_fields, dict):
            fields_list = target_schema_fields.get("fields", target_schema_fields.get("core", {}).get("fields", []))
        else:
            fields_list = target_schema_fields

        for item in fields_list:
            if isinstance(item, dict):
                field_name = item.get("name")
                field_id = item.get("id")
                default_val = item.get("default", 0)
            elif isinstance(item, str):
                field_name = item
                field_id = item
                default_val = 0
            else:
                continue

            if not field_name and not field_id:
                continue

            val = None
            candidates = [c for c in [field_name, field_id] if c]
            for c in candidates:
                if c in human_readable_model:
                    val = human_readable_model[c]
                    break

            if val is None:
                for k, v in human_readable_model.items():
                    if any(k.lower() == c.lower() for c in candidates if c):
                        val = v
                        break

            if val is None:
                val = default_val

            # Preserve unscaled float/int values for binary encoder
            if field_name:
                scaled[field_name] = val
            if field_id:
                scaled[field_id] = val

        return scaled

    def translate_with_mapping(self, source_data: dict, mapping_config: dict) -> Tuple[dict, List[str]]:
        src_id = mapping_config.get("source_schema", "opentag_v2_003")
        tgt_id = mapping_config.get("target_schema", "openprinttag_v1")
        return self.translate(source_data, source_schema_id=src_id, target_schema_id=tgt_id)