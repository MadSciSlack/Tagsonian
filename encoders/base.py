# encoders/base.py
from abc import ABC, abstractmethod


class BaseEncoder(ABC):
    """Abstract base class for format-specific binary encoders."""

    @abstractmethod
    def __init__(self, schema_input):
        """Initializes the encoder with a schema file path, dict, or field list."""
        pass

    @abstractmethod
    def encode_payload(self, model: dict) -> bytearray:
        """Packs common data model values into binary payload bytes based on schema rules."""
        pass