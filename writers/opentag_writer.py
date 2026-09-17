# writers/opentag_writer.py
from pathlib import Path
from typing import Dict, Any, Union
from encoders.opentag_encoder import OpenTagEncoder
from parsers.opentag_parser import OpenTagParser

class OpenTagWriter:
    def __init__(self):
        self.encoder = OpenTagEncoder()

    def encode(
        self, 
        model: Dict[str, Any], 
        spec_path_or_parser: Union[str, Path, OpenTagParser],
        mime_type: str = "application/opentag3d"
    ) -> bytes:
        """
        Encodes the common data model using the spec fields and wraps 
        the resulting binary payload in an NDEF TLV structure.
        """
        if isinstance(spec_path_or_parser, OpenTagParser):
            parser = spec_path_or_parser
        else:
            parser = OpenTagParser(spec_path_or_parser)

        # 1. Encode fields into raw binary payload
        raw_payload = self.encoder.encode_payload(model, parser.fields)

        # 2. Wrap raw binary in NDEF MIME record + TLV container (0x03 ... 0xFE)
        ndef_formatted_payload = parser.wrap_ndef_mime(raw_payload, mime_type=mime_type)

        return ndef_formatted_payload