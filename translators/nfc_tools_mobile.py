import json
import base64
from translators.base import BaseImporter
from opentag_parser import OpenTagBinaryDecoder


class NFCToolsMobileImporter(BaseImporter):
    """Handles .nfctools-mobile.json double-nested base64 profile exports."""

    def can_handle(self, data: dict | list) -> bool:
        return isinstance(data, dict) and data.get("type") == "nfc-tools-profiles"

    def parse(self, data: dict | list, schema_fields: list[dict]) -> dict:
        try:
            profiles = data.get("profiles", [])
            if not profiles:
                return {}

            # 1. Decode Level 1: Profile 'data' string -> JSON string array
            encoded_profile_data = profiles[0].get("data", "")
            profile_json_str = base64.b64decode(encoded_profile_data).decode("utf-8")
            records_list = json.loads(profile_json_str)

            # 2. Extract the NDEFMessage base64 string
            ndef_msg_b64 = None
            for item in records_list:
                if isinstance(item, dict) and "NDEFMessage" in item:
                    ndef_msg_b64 = item["NDEFMessage"]
                    break

            if not ndef_msg_b64:
                return {}

            # 3. Decode Level 2: NDEFMessage string -> JSON record list
            ndef_json_str = base64.b64decode(ndef_msg_b64).decode("utf-8")
            ndef_records = json.loads(ndef_json_str)

            # 4. Decode Level 3: Extract raw OpenTag payload
            for rec in ndef_records:
                if isinstance(rec, dict) and "Payload" in rec:
                    raw_bytes = bytearray(base64.b64decode(rec["Payload"]))

                    # Mobile stores payload without NDEF wrapper headers; check if MIME header is present
                    mime_type, clean_payload = OpenTagImportTranslator._parse_ndef_record(raw_bytes)
                    
                    if clean_payload:
                        # Header was present in payload slice
                        target_payload = clean_payload
                    else:
                        # Pure binary payload starting at offset 0 (Tag Version)
                        target_payload = raw_bytes

                    return OpenTagImportTranslator.translate(target_payload, schema_fields)

        except Exception as e:
            print(f"NFCToolsMobileImporter Error: {e}")

        return {}