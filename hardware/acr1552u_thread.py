# hardware/acr1552u_thread.py
import time
from PySide6.QtCore import QThread, Signal
from hardware.acr1552u import ACR1552UReader

class ACR1552UThread(QThread):
    tag_detected = Signal(bytearray, str)  # raw_memory, detected_chip_type
    write_success = Signal()
    error_occurred = Signal(str)

    def __init__(self, mode="read", payload=None, target_pages=135):
        super().__init__()
        self.mode = mode
        self.payload = payload
        self.target_pages = target_pages
        self.running = True

    def run(self):
        reader = ACR1552UReader()
        try:
            matched_name = reader.find_reader()
            if not matched_name:
                self.error_occurred.emit("ACR1552U reader not found on PC/SC bus.")
                return

            reader.connect()

            # Poll for tag presence
            uid = None
            retries = 0
            while self.running and not uid and retries < 20:
                try:
                    uid = reader.read_uid()
                except Exception:
                    time.sleep(0.2)
                    retries += 1

            if not uid:
                self.error_occurred.emit("Timeout: No NFC tag detected on ACR1552U.")
                reader.disconnect()
                return

            if self.mode == "read":
                # Read total memory pages from page 0
                raw_data = reader.read_pages(0, self.target_pages)
                self.tag_detected.emit(raw_data, "NTAG215")

            elif self.mode == "write":
                if not self.payload:
                    self.error_occurred.emit("Write failed: Payload buffer is empty.")
                    reader.disconnect()
                    return

                # Write page by page starting at page 4 (skipping manufacturer header)
                chunk_size = 4
                start_page = 4
                for i in range(0, len(self.payload), chunk_size):
                    chunk = self.payload[i:i + chunk_size]
                    if len(chunk) < 4:
                        chunk = chunk.ljust(4, b'\x00')
                    
                    target_page = start_page + (i // 4)
                    reader.write_page(target_page, chunk)

                self.write_success.emit()

            reader.disconnect()

        except Exception as e:
            self.error_occurred.emit(f"ACR1552U Error: {str(e)}")
            try:
                reader.disconnect()
            except Exception:
                pass

    def stop(self):
        self.running = False