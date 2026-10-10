# json_importer.py
import json
from pathlib import Path
from typing import List, Dict, Any

from translators.nfc_tools_desktop import NFCToolsDesktopImporter
from translators.opentag_json import OpenTagJSONImporter


class JSONImporterDispatcher:
    """Dispatcher that inspects file structure and delegates to the appropriate importer."""

    def __init__(self):
        self.importers = [
            NFCToolsDesktopImporter(),
            OpenTagJSONImporter(),
        ]

    def load_from_file(self, file_path: str | Path, schema_fields: List[Dict[str, Any]]) -> dict:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        for importer in self.importers:
            if hasattr(importer, "can_handle") and importer.can_handle(raw_data):
                return importer.parse(raw_data, schema_fields)

        raise ValueError(f"No suitable translator found for file: {path.name}")


class JSONImporter:
    @staticmethod
    def load_from_file(file_path: str | Path, schema_fields: List[Dict[str, Any]]) -> dict:
        dispatcher = JSONImporterDispatcher()
        return dispatcher.load_from_file(file_path, schema_fields)