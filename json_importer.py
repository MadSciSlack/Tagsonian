# json_importer.py
import json
from pathlib import Path

# Importer Implementations
# from translators.nfc_tools_mobile import NFCToolsMobileImporter
from translators.nfc_tools_desktop import NFCToolsDesktopImporter
from translators.opentag_json import OpenTagJSONImporter


class JSONImporterDispatcher:
    """Dispatcher that inspects file structure and delegates to the appropriate importer."""

    def __init__(self):
        # Order matters: Specific format detectors first, generic fallback last
        self.importers = [
            NFCToolsMobileImporter(),
            NFCToolsDesktopImporter(),
            OpenTagJSONImporter(),  # Generic fallback
        ]

    def load_from_file(self, file_path: str | Path, schema_fields: list[dict]) -> dict:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        # Dispatch to the first importer that claims support
        for importer in self.importers:
            if importer.can_handle(raw_data):
                return importer.parse(raw_data, schema_fields)

        raise ValueError(f"No suitable translator found for file: {path.name}")


# Static interface wrapper to maintain compatibility with main_window.py
class JSONImporter:
    @staticmethod
    def load_from_file(file_path: str | Path, schema_fields: list[dict]) -> dict:
        dispatcher = JSONImporterDispatcher()
        return dispatcher.load_from_file(file_path, schema_fields)