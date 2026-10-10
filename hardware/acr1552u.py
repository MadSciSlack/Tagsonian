# hardware/acr1552u.py
from smartcard.System import readers
from smartcard.Exceptions import CardConnectionException, NoCardException
from hardware.base import BaseNFCThread


class ACR1552UThread(BaseNFCThread):
    """ACR1552U hardware implementation using standard PC/SC APDUs."""

    def run(self):
        connection = None
        try:
            r_list = readers()
            if not r_list:
                self.error_occurred.emit("No NFC reader hardware detected.")
                return

            target_reader = next((r for r in r_list if "1552" in str(r)), None)
            if not target_reader:
                self.error_occurred.emit("ACR1552U reader not found on PC/SC bus.")
                return

            try:
                connection = target_reader.createConnection()
                connection.connect()
            except (CardConnectionException, NoCardException):
                # Idle pass when no tag is on reader
                return
            except Exception as e:
                self.error_occurred.emit(f"Reader connection error: {str(e)}")
                return

            if self.mode == "read":
                self._read_tag(connection)
            elif self.mode == "write":
                self._write_tag(connection)

        except Exception as e:
            self.error_occurred.emit(f"Hardware Error: {str(e)}")
        finally:
            if connection is not None:
                try:
                    connection.disconnect()
                except Exception:
                    pass

    def _read_tag(self, connection):
        raw_bytes = bytearray()

        for p in range(0, 135, 4):
            if not self._running:
                return
            apdu = [0xFF, 0xB0, 0x00, p, 0x10]
            data, sw1, sw2 = connection.transmit(apdu)

            if sw1 == 0x90 and sw2 == 0x00:
                raw_bytes.extend(data)
            else:
                break

        if raw_bytes:
            self.tag_detected.emit(raw_bytes, "Type 2 Tag", "NTAG215")

    def _write_tag(self, connection):
        if not self.payload:
            self.error_occurred.emit("No payload provided for writing.")
            return

        cc_apdu = [0xFF, 0xD6, 0x00, 0x03, 0x04, 0xE1, 0x10, 0x3E, 0x00]
        data, sw1, sw2 = connection.transmit(cc_apdu)
        if not (sw1 == 0x90 and sw2 == 0x00):
            self.error_occurred.emit(f"Failed CC write at Page 3 (SW: {sw1:02X}{sw2:02X})")
            return

        padded = bytearray(self.payload)
        while len(padded) % 4 != 0:
            padded.append(0x00)

        page = 4
        for i in range(0, len(padded), 4):
            if not self._running:
                return
            page_bytes = list(padded[i : i + 4])
            apdu = [0xFF, 0xD6, 0x00, page, 0x04] + page_bytes
            data, sw1, sw2 = connection.transmit(apdu)

            if not (sw1 == 0x90 and sw2 == 0x00):
                self.error_occurred.emit(f"Failed write at Page {page} (SW: {sw1:02X}{sw2:02X})")
                return
            page += 1

        self.write_success.emit()