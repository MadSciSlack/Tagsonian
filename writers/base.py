from abc import ABC, abstractmethod


class BaseWriter(ABC):
    """Abstract base class for formatting payloads to be written to hardware."""

    @abstractmethod
    def encode(self, common_data_model: dict, schema_fields: list[dict]) -> bytearray:
        """Converts common data model into hardware-ready binary memory dump."""
        pass