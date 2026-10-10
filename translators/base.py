# translators/base.py
from abc import ABC, abstractmethod
from pathlib import Path


class BaseImporter(ABC):
    """Abstract base class for all OpenTag import handlers."""

    @abstractmethod
    def can_handle(self, data: dict | list) -> bool:
        """Determines if this translator can parse the given JSON structure."""
        pass

    @abstractmethod
    def parse(self, data: dict | list, schema_fields: list[dict]) -> dict:
        """Extracts and maps raw data into the Common Data Model dictionary."""
        pass