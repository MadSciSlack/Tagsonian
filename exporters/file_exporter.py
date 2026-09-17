# exporters/file_exporter.py
import json
import re
from datetime import datetime
from pathlib import Path
from utils.hex_formatter import HexFormatter


class FileExporter:
    """Manages file exports for text dumps, binary payloads, and mapped JSON specs."""

    @staticmethod
    def sanitize_filename(name: str) -> str:
        """Removes illegal characters from filename strings."""
        return re.sub(r'[\\/*?:"<>|]', "", name).strip().replace(" ", "_")

    @classmethod
    def generate_default_filename(cls, model_data: dict, extension: str) -> str:
        """Generates a default filename like: OpenTag_Prusa_PLA_2026-09-17_Dump.txt"""
        mfg = cls.sanitize_filename(str(model_data.get("Filament Manufacturer", "Unknown")))
        mat = cls.sanitize_filename(str(model_data.get("Base Material Name", "Filament")))
        date_str = datetime.now().strftime("%Y-%m-%d")

        ext = extension.lstrip(".")
        return f"OpenTag_{mfg}_{mat}_{date_str}.{ext}"

    @staticmethod
    def export_text_dump(file_path: str | Path, raw_memory: bytes | bytearray, model_data: dict | None = None):
        """Exports raw hex dump along with header tag information to a text file."""
        path = Path(file_path)
        full_dump = HexFormatter.to_full_dump(raw_memory)

        header = []
        header.append("=" * 60)
        header.append(f" OpenTag Raw Memory Dump - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if model_data:
            header.append(f" Manufacturer : {model_data.get('Filament Manufacturer', 'N/A')}")
            header.append(f" Material     : {model_data.get('Base Material Name', 'N/A')}")
            header.append(f" Color        : {model_data.get('Color Name', 'N/A')}")
        header.append("=" * 60)
        header.append("")

        content = "\n".join(header) + full_dump

        path.write_text(content, encoding="utf-8")

    @staticmethod
    def export_binary(file_path: str | Path, raw_payload: bytes | bytearray):
        """Exports raw NDEF binary payload to disk."""
        Path(file_path).write_bytes(bytes(raw_payload))

    @staticmethod
    def export_json(file_path: str | Path, mapped_data: dict):
        """Exports formatted JSON dictionary."""
        Path(file_path).write_text(json.dumps(mapped_data, indent=2), encoding="utf-8")