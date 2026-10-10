# writers/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple

class BaseWriter(ABC):
    """
    Abstract base interface for all schema-specific tag writers.
    """
    def __init__(self, schema_def: Dict[str, Any]):
        self.schema_def = schema_def

    @abstractmethod
    def encode(self, model: Dict[str, Any]) -> bytearray:
        """
        Packs internal scaled model data into a format-native byte sequence or payload buffer.
        """
        pass

    @abstractmethod
    def validate_payload_size(self, encoded_bytes: bytearray, chip_capacity: int) -> Tuple[bool, str]:
        """
        Validates whether the packed binary payload fits within the physical chip's memory limits.
        """
        pass