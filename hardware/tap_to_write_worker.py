# hardware/tap_to_write_worker.py
import time
import json
from PySide6.QtCore import QThread, Signal, Qt
from core.write_queue_manager import WriteQueueManager
from models.write_task import TaskStatus, WriteTask
from hardware.reader_factory import get_reader_thread
from hardware.base_reader import BaseNFCReader
from parsers import OpenTagParser
from writers import get_writer_for_schema


class TapToWriteWorker(QThread):
    task_completed = Signal(str, str)  # task_id, written_uid
    task_failed = Signal(str, str)     # task_id, error_message
    status_changed = Signal(str)
    tag_removed = Signal()

    def __init__(self, queue_manager: WriteQueueManager, main_window_ref, parent=None):
        super().__init__(parent)
        self.queue_mgr = queue_manager
        self.main_window = main_window_ref
        self._running = False
        self.last_written_uid: str | None = None

    def stop(self):
        self._running = False

    def run(self):
        self._running = True
        self.status_changed.emit("Tap-to-Write mode active. Present NFC tag...")
        current_task: WriteTask | None = None

        while self._running:
            if current_task is None:
                current_task = self.queue_mgr.get_next_pending_task()

            if not current_task:
                self.status_changed.emit("Write Queue idle. Waiting for tasks...")
                self.msleep(500)
                continue

            # Step 1: Poll Reader for Tag Presence
            poll_thread = get_reader_thread(mode="read")
            tag_data = {"detected": False, "memory": None, "chip": "NTAG215", "err": None}

            def _on_detected(raw_mem, generic_type, chip_type):
                tag_data["detected"] = True
                tag_data["memory"] = raw_mem
                tag_data["chip"] = chip_type

            def _on_error(err_str):
                tag_data["err"] = err_str

            poll_thread.tag_detected.connect(_on_detected)
            poll_thread.error_occurred.connect(_on_error)
            poll_thread.start()
            poll_thread.wait(1500)
            poll_thread.deleteLater()

            # Step 2: Handle Tag Disconnection & Debouncing Reset
            if not tag_data["detected"]:
                if self.last_written_uid is not None:
                    self.last_written_uid = None
                    self.tag_removed.emit()
                    self.status_changed.emit("Tag removed. Ready for next tag.")
                self.msleep(300)
                continue

            # Extract UID from page header
            raw_mem = tag_data["memory"]
            detected_uid = "".join([f"{b:02X}" for b in raw_mem[:7]]) if raw_mem and len(raw_mem) >= 7 else "UNKNOWN_UID"
            detected_chip = tag_data["chip"]

            # Step 3: UID Lockout Gate
            if detected_uid == self.last_written_uid:
                self.status_changed.emit(f"Tag [{detected_uid}] already written. Remove tag to continue.")
                self.msleep(500)
                continue

            # Step 4: Validate Capacity and Encode Payload
            self.queue_mgr.mark_task_status(current_task.task_id, TaskStatus.WRITING)
            self.status_changed.emit(f"Writing task '{current_task.title}' to tag [{detected_uid}]...")

            try:
                parser = OpenTagParser(self.main_window.spec_path)
                spec_schema = parser.spec_data if hasattr(parser, "spec_data") else {}

                scaled_model = self.main_window.mapper.to_scaled_model(current_task.payload_data, parser.fields)
                schema_id = current_task.schema_id or self.main_window.get_active_schema_id()

                with open(self.main_window.spec_path, "r", encoding="utf-8") as f:
                    schema_def = json.load(f)

                writer = get_writer_for_schema(schema_id, schema_def)
                full_payload = writer.encode(scaled_model)

                valid, msg = BaseNFCReader.validate_chip_for_spec(detected_chip, spec_schema, len(full_payload))
                if not valid:
                    self.queue_mgr.mark_task_status(current_task.task_id, TaskStatus.FAILED, msg)
                    self.task_failed.emit(current_task.task_id, f"Chip capacity error: {msg}")
                    current_task = None
                    self.msleep(1000)
                    continue

            except Exception as e:
                err_msg = f"Encoding failure: {e}"
                self.queue_mgr.mark_task_status(current_task.task_id, TaskStatus.FAILED, err_msg)
                self.task_failed.emit(current_task.task_id, err_msg)
                current_task = None
                self.msleep(1000)
                continue

            # Step 5: Program Tag via Write Thread
            write_thread = get_reader_thread(mode="write", payload=full_payload)
            write_res = {"success": False, "err": ""}

            def _on_write_ok():
                write_res["success"] = True

            def _on_write_err(err_str):
                write_res["err"] = err_str

            write_thread.write_success.connect(_on_write_ok)
            write_thread.error_occurred.connect(_on_write_err)
            write_thread.start()
            write_thread.wait(5000)
            write_thread.deleteLater()

            if write_res["success"]:
                self.last_written_uid = detected_uid
                self.queue_mgr.mark_task_status(current_task.task_id, TaskStatus.COMPLETED, written_uid=detected_uid)
                self.task_completed.emit(current_task.task_id, detected_uid)
                self.status_changed.emit(f"Task '{current_task.title}' successfully written to [{detected_uid}]!")
            else:
                err_msg = write_res["err"] or "Write execution failed."
                self.queue_mgr.mark_task_status(current_task.task_id, TaskStatus.FAILED, err_msg)
                self.task_failed.emit(current_task.task_id, err_msg)

            current_task = None
            self.msleep(500)