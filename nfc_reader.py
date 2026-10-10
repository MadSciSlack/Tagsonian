# nfc_reader.py
from PySide6.QtCore import QThread, Signal
from smartcard.System import readers
from smartcard.util import toHexString


class NFCReaderThread(QThread):
    """Worker thread to poll for NTAG215 cards on an ACR122U and read memory."""
    tag_detected = Signal(bytearray)
    error_occurred = Signal(str)

    def __init__(self, start_page: int = 4, total_pages: int = 132):
        super().__init__()
        self.start_page = start_page
        self.total_pages = total_pages
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        try:
            r = readers()
            if not r:
                self.error_occurred.emit("No NFC reader hardware detected.")
                return

            reader = r[0]
            connection = reader.createConnection()
            connection.connect()

            # Read user memory in 4-page (16-byte) blocks using standard READ APDU [0xFF, 0xB0, 0x00, page, 0x10]
            raw_bytes = bytearray()
            # Padding bytes 0-15 (Pages 0-3 reserved for UID/Config)
            raw_bytes.extend(b"\x00" * 16)

            for p in range(self.start_page, self.start_page + self.total_pages, 4):
                if not self._running:
                    return
                
                # Command to read 16 bytes starting at page p
                apdu = [0xFF, 0xB0, 0x00, p, 0x10]
                data, sw1, sw2 = connection.transmit(apdu)

                if sw1 == 0x90 and sw2 == 0x00:
                    raw_bytes.extend(data)
                else:
                    self.error_occurred.emit(f"Failed page read at Page {p} (SW: {sw1:02X}{sw2:02X})")
                    return

            self.tag_detected.emit(raw_bytes)

        except Exception as e:
            self.error_occurred.emit(f"Hardware Error: {str(e)}")