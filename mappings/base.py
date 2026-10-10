from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, List

class BaseMapper(ABC):
    """Abstract base contract for directional schema mappers."""
    
    @property
    @abstractmethod
    def source_schema_id(self) -> str:
        pass

    @property
    @abstractmethod
    def target_schema_id(self) -> str:
        pass

    @abstractmethod
    def translate(self, source_data: dict) -> Tuple[dict, List[str]]:
        """Translates source data model to target schema model."""
        pass

    @staticmethod
    def debug_mapping_coverage(source_data: dict, mapping_config: dict) -> str:
        """Enhanced diagnostic coverage report tracking matched, missing, and unmapped keys."""
        pass