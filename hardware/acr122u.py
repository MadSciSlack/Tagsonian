from smartcard.System import readers
from hardware.base import BaseNFCThread
from hardware.base_reader import BaseNFCReader


class ACR122UThread(BaseNFCThread):
    """ACR122U hardware implementation for reading and writing NTAG215 tags."""

    def run(self):
        try:
            r = readers()
            if not r:
                self.error_occurred.emit("No NFC reader hardware detected.")
                return

            connection = r[0].createConnection()
            connection.connect()

            if self.mode == "read":
                self._read_tag(connection)
            elif self.mode == "write":
                self._write_tag(connection)

        except Exception as e:
            self.error_occurred.emit(f"Hardware Error: {str(e)}")

    def _read_tag(self, connection):
        raw_bytes = bytearray(b"\x00" * 16)  # 16-byte offset representing Pages 0-3
        
        # Read 16 bytes (4 pages) per APDU command, stepping page index by 4
        for p in range(4, 135, 4):
            if not self._running:
                return
            apdu = [0xFF, 0xB0, 0x00, p, 0x10]  # Read 16 bytes starting at Page p
            data, sw1, sw2 = connection.transmit(apdu)
            if sw1 == 0x90 and sw2 == 0x00:
                raw_bytes.extend(data)
            else:
                # Reached end of readable memory or tag removed
                break
                
        self.tag_detected.emit(raw_bytes)


    def _write_tag(self, connection):
        if not self.payload:
            self.error_occurred.emit("No payload provided for writing.")
            return

        # Ensure Capability Container (CC) is present on Page 3 for NTAG215
        # [E1 (Magic), 10 (NFC Forum v1.0), 3E (NTAG215 memory size), 00 (Read/Write)]
        cc_apdu = [0xFF, 0xD6, 0x00, 0x03, 0x04, 0xE1, 0x10, 0x3E, 0x00]
        connection.transmit(cc_apdu)

        # Pad payload to 4-byte NTAG page boundary
        padded = bytearray(self.payload)
        while len(padded) % 4 != 0:
            padded.append(0x00)

        # Write NDEF payload starting at Page 4
        page = 4
        for i in range(0, len(padded), 4):
            if not self._running:
                return
            page_bytes = list(padded[i : i + 4])
            apdu = [0xFF, 0xD6, 0x00, page, 0x04] + page_bytes
            data, sw1, sw2 = connection.transmit(apdu)

            if not (sw1 == 0x90 and sw2 == 0x00):
                self.error_occurred.emit(f"Failed write at Page {page}")
                return
            page += 1

        self.write_success.emit()