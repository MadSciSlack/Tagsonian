# writers/openprinttag_writer.py
import logging
from typing import Dict, Any, Tuple
from writers.base import BaseWriter
from encoders.openprinttag_encoder import OpenPrintTagEncoder

logger = logging.getLogger(__name__)


class OpenPrintTagWriter(BaseWriter):
    """
    Native binary writer for OpenPrintTag V1 specifications.
    """

    def __init__(self, schema_def: Dict[str, Any]):
        super().__init__(schema_def)
        self.encoder = OpenPrintTagEncoder()

    def encode(self, model: Dict[str, Any]) -> bytearray:
        """
        Encodes OpenPrintTag dictionary values into standard CBOR/binary payload format.
        """
        raw_payload = self.encoder.encode_payload(model)
        if not isinstance(raw_payload, bytearray):
            raw_payload = bytearray(raw_payload)
        return raw_payload

    def validate_payload_size(self, encoded_bytes: bytearray, chip_capacity: int) -> Tuple[bool, str]:
        """
        Validates payload size against target RFID tag capacity.
        """
        payload_len = len(encoded_bytes)
        if payload_len > chip_capacity:
            return False, f"OpenPrintTag payload ({payload_len} bytes) exceeds chip capacity ({chip_capacity} bytes)."
        return True, "Payload size valid."