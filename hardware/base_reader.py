# hardware/base_reader.py

class BaseNFCReader:
    """Base hardware interface for NFC readers (ACR122U, ACR1552U, PN532, etc.)."""

    @staticmethod
    def validate_chip_for_spec(chip_type: str, spec_schema: dict, payload_len: int = 0) -> tuple[bool, str]:
        """Validates whether the detected physical tag matches spec chip requirements and capacity."""
        hw_reqs = spec_schema.get("hardware", {})
        allowed_chips = hw_reqs.get("supported_chips", [])

        if allowed_chips and chip_type not in allowed_chips:
            return False, (
                f"Spec '{spec_schema.get('display_name', spec_schema.get('schema_id'))}' "
                f"requires chip type(s) {allowed_chips}, but detected chip is {chip_type}."
            )

        if payload_len > 0 and chip_type == "NTAG215" and payload_len > 504:
            return False, f"Payload size ({payload_len} bytes) exceeds NTAG215 capacity (504 bytes)."

        return True, ""