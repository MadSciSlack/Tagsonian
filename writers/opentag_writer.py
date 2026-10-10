# writers/opentag_writer.py
import logging
from typing import Dict, Any, Tuple
from writers.base import BaseWriter
from encoders.opentag_encoder import OpenTagEncoder
from parsers.opentag_parser import OpenTagParser

logger = logging.getLogger(__name__)


class OpenTagWriter(BaseWriter):
    """
    Native binary writer for OpenTag V2/V3 specifications.
    """

    def __init__(self, schema_def: Dict[str, Any]):
        super().__init__(schema_def)
        self.encoder = OpenTagEncoder()

    def encode(self, model: Dict[str, Any], mime_type: str = "application/opentag3d") -> bytearray:
        """
        Encodes internal scaled model data using the schema fields and wraps 
        the resulting binary payload in an NDEF TLV structure.
        """
        parser = OpenTagParser(self.schema_def)

        # 1. Encode fields into raw binary payload
        raw_payload = self.encoder.encode_payload(model, parser.fields)

        if not raw_payload:
            raise ValueError("OpenTagEncoder returned an empty binary payload. Check field key mappings.")

        logger.debug(f"[OpenTagWriter] Generated raw payload size: {len(raw_payload)} bytes")

        # 2. Wrap raw binary in NDEF MIME record + TLV container
        ndef_formatted_payload = parser.wrap_ndef_mime(raw_payload, mime_type=mime_type)

        if not ndef_formatted_payload:
            raise ValueError("OpenTagParser failed to generate NDEF MIME container structure.")

        logger.debug(f"[OpenTagWriter] Total NDEF TLV packet size: {len(ndef_formatted_payload)} bytes")

        return bytearray(ndef_formatted_payload)

    def validate_payload_size(self, encoded_bytes: bytearray, chip_capacity: int) -> Tuple[bool, str]:
        """
        Validates payload size against target RFID tag capacity.
        """
        payload_len = len(encoded_bytes)
        if payload_len > chip_capacity:
            return False, f"OpenTag payload ({payload_len} bytes) exceeds chip capacity ({chip_capacity} bytes)."
        return True, "Payload size valid."