# utils/hex_formatter.py

class HexFormatter:
    """Utilities for formatting raw bytearrays into human-readable hex dumps."""

    @staticmethod
    def to_raw_hex(data: bytes | bytearray) -> str:
        """Returns uppercase continuous hex string with no spaces or addresses."""
        return data.hex().upper() if data else ""

    @staticmethod
    def to_full_dump(data: bytes | bytearray, bytes_per_line: int = 16) -> str:
        """Generates classic side-by-side hex dump: Address | Hex Bytes | ASCII."""
        if not data:
            return "No data available."

        lines = []
        for i in range(0, len(data), bytes_per_line):
            chunk = data[i : i + bytes_per_line]
            
            # Address header
            address = f"{i:08X}"
            
            # Formatted hex bytes split into two 8-byte blocks
            hex_parts = [f"{b:02X}" for b in chunk]
            if len(hex_parts) > 8:
                hex_str = " ".join(hex_parts[:8]) + "  " + " ".join(hex_parts[8:])
            else:
                hex_str = " ".join(hex_parts)
            
            # Right-pad hex column for incomplete last line
            padding_len = (bytes_per_line * 3 + (1 if bytes_per_line > 8 else 0)) - len(hex_str) - 1
            hex_str += " " * max(0, padding_len)

            # Printable ASCII column
            ascii_str = "".join([chr(b) if 32 <= b <= 126 else "." for b in chunk])

            lines.append(f"{address}: {hex_str}  |{ascii_str}|")

        return "\n".join(lines)