from translators.base import BaseImporter
# from parsers.opentag_parser import OpenTagBinaryDecoder
#from parsers import OpenTagBinaryDecoder

class NFCToolsDesktopImporter(BaseImporter):
    """Handles .nfctools-desktop.json preset files with kPayload byte arrays."""

    def can_handle(self, data: dict | list) -> bool:
        if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
            return any("kRecordObject" in rec for rec in data["data"] if isinstance(rec, dict))
        return False

    def parse(self, data: dict | list, schema_fields: list[dict]) -> dict:
        for record in data.get("data", []):
            if isinstance(record, dict):
                record_obj = record.get("kRecordObject", {})
                if "kPayload" in record_obj:
                    raw_payload = bytearray(record_obj["kPayload"])
                    
                    # Extract clean payload and decode bytes
                    _, clean_payload = OpenTagBinaryDecoder.extract_ndef_payload(raw_payload)
                    target_payload = clean_payload if clean_payload else raw_payload
                    return OpenTagBinaryDecoder.parse_payload(target_payload, schema_fields)
        return {}