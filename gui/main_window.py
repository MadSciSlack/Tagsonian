# gui/main_window.py
import sys
import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

SCRIPT_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from gui.dialogs.settings_dialog import SettingsDialog
from gui.tabs import RawInspectorTab, StandardEditorTab, StandardEditorV2Tab, TagEditorTab
from hardware.base_reader import BaseNFCReader
from hardware.reader_factory import get_reader_thread
from json_importer import JSONImporter
from mappings.mapper import FormatMapper, debug_mapping_coverage
from parsers import OpenTagParser
from parsers.openprinttag_parser import OpenPrintTagParser
from writers import get_writer_for_schema
from exporters.file_exporter import FileExporter
from gui.dialogs.settings_dialog import SettingsDialog
from gui.dialogs import SettingsDialog, FieldEditorDialog, WriteQueueDialog
from core.write_queue_manager import WriteQueueManager

class MainWindow(QMainWindow):
    def __init__(self, spec_path="schemas/opentag_v2_003.json"):
        super().__init__()
        resolved_spec = SCRIPT_DIR / spec_path
        self.spec_path = resolved_spec if resolved_spec.exists() else Path(spec_path)

        self.common_data_model = {}
        self.original_raw_model = {}
        self.raw_memory_buffer = bytearray()
        self.detected_spec_name = "None"
        self.current_data_schema_id = "opentag_v2_003"  # Tracks active format of loaded data
        self.active_thread = None
        self.mapper = FormatMapper()

        # Thread-safe write queue manager and non-modal spooler dialog reference
        self.queue_manager = WriteQueueManager(self)
        self.queue_dialog = None

        self.setWindowTitle("Tagsonian (V0.22-B0025)")
        self.resize(1050, 750)

        self.setup_ui()
        self.populate_spec_dropdown()
        self.handle_clear()
        self.log_message(f"Tagsonian initialized with target schema: {self.spec_path.name}")

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Header Controls
        header_layout = QHBoxLayout()

        self.lbl_detected_spec = QLabel("Detected Spec: None")
        self.lbl_detected_spec.setStyleSheet("font-weight: bold; color: #333;")
        header_layout.addWidget(self.lbl_detected_spec)

        header_layout.addStretch()

        self.btn_settings = QPushButton("⚙ Settings")
        self.btn_settings.clicked.connect(self.open_settings)
        header_layout.addWidget(self.btn_settings)

        lbl_target = QLabel("Target Spec / Format:")
        lbl_target.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(lbl_target)

        self.combo_target_spec = QComboBox()
        self.combo_target_spec.currentIndexChanged.connect(self.on_target_spec_changed)
        header_layout.addWidget(self.combo_target_spec)

        main_layout.addLayout(header_layout)

        # Tab Widget Layout
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Instantiate Modular Tabs
        self.tab_editor = TagEditorTab()
        self.tab_inspector = RawInspectorTab()
        self.tab_standard_editor = StandardEditorTab()
        self.tab_standard_editor_v2 = StandardEditorV2Tab()

        self.tabs.addTab(self.tab_editor, "Tag Editor")
        self.tabs.addTab(self.tab_inspector, "Raw Data Inspector")
        self.tabs.addTab(self.tab_standard_editor, "Tag Standard Editor (V1)")
        self.tabs.addTab(self.tab_standard_editor_v2, "Tag Standard Editor (V2)")

        # Bottom Actions Bar
        btn_layout = QHBoxLayout()

        self.btn_read_hw = QPushButton("Read NFC Tag")
        self.btn_read_hw.clicked.connect(self.handle_read_hardware)
        btn_layout.addWidget(self.btn_read_hw)

        self.btn_write_hw = QPushButton("Write NFC Tag")
        self.btn_write_hw.setStyleSheet("font-weight: bold; background-color: #2b78e4; color: white;")
        self.btn_write_hw.clicked.connect(self.handle_write_hardware)
        btn_layout.addWidget(self.btn_write_hw)

        self.btn_enqueue = QPushButton("Enqueue Current Tag")
        self.btn_enqueue.clicked.connect(self.handle_enqueue_current)
        btn_layout.addWidget(self.btn_enqueue)

        self.btn_show_queue = QPushButton("Write Queue (0)")
        self.btn_show_queue.setStyleSheet("font-weight: bold;")
        self.btn_show_queue.clicked.connect(self.open_queue_dialog)
        btn_layout.addWidget(self.btn_show_queue)

        self.btn_import_json = QPushButton("Import JSON")
        self.btn_import_json.clicked.connect(self.handle_import_json)
        btn_layout.addWidget(self.btn_import_json)

        self.btn_export = QPushButton("Export File...")
        self.btn_export.clicked.connect(self.handle_export_file)
        btn_layout.addWidget(self.btn_export)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self.handle_clear)
        btn_layout.addWidget(self.btn_clear)

        main_layout.addLayout(btn_layout)

        # Wire Queue Signals for Label Updates
        self.queue_manager.task_added.connect(self._update_queue_btn_label)
        self.queue_manager.task_removed.connect(self._update_queue_btn_label)
        self.queue_manager.queue_cleared.connect(self._update_queue_btn_label)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def log_message(self, message: str, level: str = "INFO"):
        if hasattr(self.tab_editor, "log_message"):
            self.tab_editor.log_message(message, level)
        else:
            print(f"[{level}] {message}")

    def handle_external_write_request(self, queue_manager: WriteQueueManager):
        """Focuses main window and launches/raises the WriteQueueDialog spooler window."""
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.raise_()
        self.activateWindow()
        self.open_queue_dialog()

    def handle_enqueue_current(self):
        """Enqueues active editor form data into the unified Write Queue."""
        self.sync_table_to_model()
        title = self.common_data_model.get("material_name") or self.common_data_model.get("brand_name") or "GUI Spool Tag"
        schema_id = self.get_active_schema_id()
        task = self.queue_manager.enqueue_gui_task(title, self.common_data_model, schema_id)
        self.status_bar.showMessage(f"Enqueued '{title}' to Write Queue.")
        self.log_message(f"Enqueued GUI task '{title}' (Task ID: {task.task_id}) to Write Queue.")

    def open_queue_dialog(self):
        """Displays or focuses the non-modal Spooler Queue window."""
        if not self.queue_dialog:
            self.queue_dialog = WriteQueueDialog(self, self.queue_manager)
        self.queue_dialog.show()
        self.queue_dialog.raise_()
        self.queue_dialog.activateWindow()

    def _update_queue_btn_label(self):
        """Updates the queue count badge on the bottom action bar button."""
        count = len(self.queue_manager.get_all_tasks())
        self.btn_show_queue.setText(f"Write Queue ({count})")

    def populate_spec_dropdown(self):
        self.combo_target_spec.blockSignals(True)
        self.combo_target_spec.clear()

        search_dirs = [SCRIPT_DIR / "schemas", SCRIPT_DIR, Path("schemas"), Path(".")]
        found_specs = set()

        for s_dir in search_dirs:
            if s_dir.exists():
                for spec_file in s_dir.glob("*.json"):
                    if spec_file.name not in found_specs:
                        found_specs.add(spec_file.name)
                        schema_id = "openprinttag_v1" if "openprinttag" in spec_file.name else "opentag_v2_003"
                        self.combo_target_spec.addItem(spec_file.name, userData=(spec_file, schema_id))

        index = self.combo_target_spec.findText(self.spec_path.name)
        if index >= 0:
            self.combo_target_spec.setCurrentIndex(index)

        self.combo_target_spec.blockSignals(False)

    def get_active_schema_id(self) -> str:
        data = self.combo_target_spec.currentData()
        if isinstance(data, tuple) and len(data) == 2:
            return data[1]
        return "openprinttag_v1" if "openprinttag" in self.spec_path.name else "opentag_v2_003"

    def set_active_schema_by_filename(self, filename: str):
        self.combo_target_spec.blockSignals(True)
        for i in range(self.combo_target_spec.count()):
            item_data = self.combo_target_spec.itemData(i)
            file_path = item_data[0] if isinstance(item_data, tuple) else item_data
            if file_path and Path(file_path).name == filename:
                self.combo_target_spec.setCurrentIndex(i)
                self.spec_path = Path(file_path)
                break
        self.combo_target_spec.blockSignals(False)

        if hasattr(self, "tab_standard_editor") and self.tab_standard_editor:
            self.tab_standard_editor.load_schema(self.spec_path)
        if hasattr(self, "tab_standard_editor_v2") and self.tab_standard_editor_v2:
            self.tab_standard_editor_v2.load_schema(self.spec_path)

    def on_target_spec_changed(self, index: int):
        item_data = self.combo_target_spec.itemData(index)
        if not item_data:
            return
        
        selected_file = item_data[0] if isinstance(item_data, tuple) else item_data
        target_schema_id = item_data[1] if isinstance(item_data, tuple) else ("openprinttag_v1" if "openprinttag" in Path(selected_file).name else "opentag_v2_003")

        if selected_file and Path(selected_file).exists():
            self.sync_table_to_model()
            self.spec_path = Path(selected_file)

            parser = OpenTagParser(self.spec_path)
            self.log_message(f"Translating model from '{self.current_data_schema_id}' to target schema '{target_schema_id}'...")

            translated_data, warnings = self.mapper.translate(
                self.common_data_model,
                target_schema_fields=parser.fields,
                source_schema_id=self.current_data_schema_id,
                target_schema_id=target_schema_id
            )
            self.common_data_model = translated_data
            self.current_data_schema_id = target_schema_id 

            if warnings:
                for w in warnings:
                    self.log_message(f" -> {w}", level="WARN")

            self.status_bar.showMessage(f"Target Spec set to: {self.spec_path.name}")
            self.load_model_into_ui(self.common_data_model)
            self.refresh_raw_inspector()

            if hasattr(self, "tab_standard_editor") and self.tab_standard_editor:
                self.tab_standard_editor.load_schema(self.spec_path)
            if hasattr(self, "tab_standard_editor_v2") and self.tab_standard_editor_v2:
                self.tab_standard_editor_v2.load_schema(self.spec_path)

    def sync_table_to_model(self):
        parser = OpenTagParser(self.spec_path)
        schema_lookup = {f.get("id", f.get("name")): f for f in parser.fields if isinstance(f, dict)}
        self.common_data_model = self.tab_editor.sync_table_to_model(self.common_data_model, schema_lookup)

    def load_model_into_ui(self, model: dict):
        parser = OpenTagParser(self.spec_path)
        schema_lookup = {f.get("id", f.get("name")): f for f in parser.fields if isinstance(f, dict)}
        self.tab_editor.load_model_into_ui(model, schema_lookup)

    def refresh_raw_inspector(self):
        """
        Orchestrates target schema definition loading, encodes the target payload,
        refreshes RawInspectorTab views, and updates MemoryVisualizerWidget.
        """
        target_schema_def = {}
        if self.spec_path and self.spec_path.exists():
            try:
                with open(self.spec_path, "r", encoding="utf-8") as f:
                    target_schema_def = json.load(f)
            except Exception as e:
                self.log_message(f"Failed to parse target schema JSON: {e}", level="WARN")

        # 1. Refresh textual hex dumps & parsed model views in RawInspectorTab
        self.tab_inspector.refresh(
            self.original_raw_model,
            self.raw_memory_buffer,
            self.common_data_model,
            self.spec_path,
            self.detected_spec_name,
            target_schema_def=target_schema_def,
        )

        # 2. Extract target field definitions for visualizer offset mapping
        parser = OpenTagParser(self.spec_path)
        target_fields = parser.fields or []

        # Fallback to schema JSON field arrays if parser yields none
        if not target_fields and isinstance(target_schema_def, dict):
            target_fields = target_schema_def.get("fields", target_schema_def.get("core", {}).get("fields", []))

        # 3. Encode current translated model to target binary payload
        target_binary = bytearray()
        try:
            scaled_model = self.mapper.to_scaled_model(self.common_data_model, target_fields)
            schema_id = self.get_active_schema_id()
            writer = get_writer_for_schema(schema_id, target_schema_def)
            target_binary = writer.encode(scaled_model)
        except Exception as e:
            self.log_message(f"Visualizer payload encoding warning: {e}", level="DEBUG")

        # 4. Directly update MemoryVisualizerWidget with target layout & payload
        if hasattr(self.tab_inspector, "visualizer") and self.tab_inspector.visualizer:
            self.tab_inspector.visualizer.update_memory_map(
                fields=target_fields,
                total_bytes=504,
                conflicts=[],
                target_binary_buffer=target_binary
            )

    def handle_clear(self):
        parser = OpenTagParser(self.spec_path)
        self.common_data_model = {f.get("id", f.get("name")): "" for f in parser.fields if isinstance(f, dict)}
        
        self.original_raw_model = {}
        self.raw_memory_buffer = bytearray()
        self.detected_spec_name = "None"
        self.current_data_schema_id = self.get_active_schema_id()

        self.lbl_detected_spec.setText("Detected Spec: None")
        self.load_model_into_ui(self.common_data_model)
        self.refresh_raw_inspector()
        self.status_bar.showMessage("Cleared all fields.")
        self.log_message("Form cleared and state reset.")

    def handle_read_hardware(self):
        self.status_bar.showMessage("Polling reader... Present tag to READ.")
        self.log_message("Initiated NFC tag read poll...")
        self._set_buttons_enabled(False)

        self.active_thread = get_reader_thread(mode="read")
        self.active_thread.tag_detected.connect(self.on_tag_read_success)
        self.active_thread.error_occurred.connect(self.on_hardware_error)
        self.active_thread.finished.connect(lambda: self._set_buttons_enabled(True))
        self.active_thread.start()

    def handle_write_hardware(self):
        self.sync_table_to_model()

        try:
            with open(self.spec_path, "r", encoding="utf-8") as f:
                schema_def = json.load(f)

            parser = OpenTagParser(self.spec_path)
            scaled_model = self.mapper.to_scaled_model(self.common_data_model, parser.fields)

            schema_id = self.get_active_schema_id()
            writer = get_writer_for_schema(schema_id, schema_def)
            full_memory_dump = writer.encode(scaled_model)

            valid, msg = writer.validate_payload_size(full_memory_dump, chip_capacity=504)
            if not valid:
                self.log_message(f"Payload validation warning: {msg}", level="WARN")

        except Exception as e:
            self.log_message(f"Encoding payload failed: {e}", level="ERROR")
            QMessageBox.critical(self, "Encoding Error", f"Cannot encode payload:\n{e}")
            return

        self.status_bar.showMessage("Polling reader... Present tag to WRITE.")
        self.log_message(f"Initiated NFC write poll for target spec '{self.spec_path.name}' ({len(full_memory_dump)} bytes)...")
        self._set_buttons_enabled(False)

        self.active_thread = get_reader_thread(mode="write", payload=full_memory_dump)
        self.active_thread.write_success.connect(self.on_write_success)
        self.active_thread.error_occurred.connect(self.on_hardware_error)
        self.active_thread.finished.connect(lambda: self._set_buttons_enabled(True))
        self.active_thread.start()

    def on_tag_read_success(self, raw_memory: bytearray, generic_type: str = "Type 2 Tag", detected_chip_type: str = "NTAG215"):
        self.raw_memory_buffer = raw_memory

        active_parser = OpenTagParser(self.spec_path)
        mime_type, payload = active_parser.extract_ndef_payload(raw_memory)
        detected_schema_id = "opentag_v2_003"

        if mime_type and ("openprinttag" in mime_type.lower() or "opt1" in mime_type.lower()):
            self.detected_spec_name = "OpenPrintTag V1"
            detected_schema_id = "openprinttag_v1"
            self.set_active_schema_by_filename("openprinttag_v1.json")
            raw_parsed = OpenPrintTagParser.parse_payload(bytes(payload))["parsed_fields"]
        elif mime_type and "openspool" in mime_type.lower():
            self.detected_spec_name = "OpenSpool V1"
            detected_schema_id = "openspool_v1"
            self.set_active_schema_by_filename("openspool_v1.json")
            raw_parsed = active_parser.parse(payload, mime_type=mime_type)
        else:
            self.detected_spec_name = mime_type if mime_type else "OpenTag3D V2.003"
            detected_schema_id = "opentag_v2_003"
            self.set_active_schema_by_filename("opentag_v2_003.json")
            raw_parsed = active_parser.parse(payload, mime_type=mime_type)

        self.lbl_detected_spec.setText(f"Detected Spec: {self.detected_spec_name}")
        self.original_raw_model = raw_parsed
        self.current_data_schema_id = detected_schema_id

        target_schema_id = self.get_active_schema_id()
        parser = OpenTagParser(self.spec_path)

        translated_model, warnings = self.mapper.translate(
            raw_parsed,
            target_schema_fields=parser.fields,
            source_schema_id=detected_schema_id,
            target_schema_id=target_schema_id
        )
        self.common_data_model = translated_model

        if warnings:
            for w in warnings:
                self.log_message(f" -> {w}", level="WARN")

        self.load_model_into_ui(self.common_data_model)
        self.refresh_raw_inspector()
        self.status_bar.showMessage(f"Successfully read tag! ({self.detected_spec_name})")
        self.log_message(f"Read payload ({self.detected_spec_name}) and mapped to '{self.spec_path.name}'.")

    def on_write_success(self):
        QMessageBox.information(self, "Success", "Payload written to tag successfully!")
        self.status_bar.showMessage("Tag written successfully.")
        self.log_message("NFC tag write operation completed successfully.")

    def handle_import_json(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import JSON", "", "JSON Files (*.json)")
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                json_content = json.load(f)

            detected_file_name = "opentag_v2_003.json"
            source_schema_id = "opentag_v2_003"
            spec_display = "OpenTag3D V2.003"

            if "header" in json_content:
                header_obj = json_content["header"]
                if isinstance(header_obj, dict):
                    spec_id = header_obj.get("spec_identifier", "")
                    if spec_id == "OPT1" or "print_temperature" in json_content or "brand_name" in json_content:
                        detected_file_name = "openprinttag_v1.json"
                        source_schema_id = "openprinttag_v1"
                        spec_display = "OpenPrintTag V1"
            elif "print_temperature" in json_content or "material_name" in json_content or "brand_name" in json_content:
                detected_file_name = "openprinttag_v1.json"
                source_schema_id = "openprinttag_v1"
                spec_display = "OpenPrintTag V1"

            self.set_active_schema_by_filename(detected_file_name)
            self.detected_spec_name = f"{spec_display} ({Path(file_path).name})"
            self.lbl_detected_spec.setText(f"Detected Spec: {spec_display}")

            parser = OpenTagParser(self.spec_path)
            raw_data = JSONImporter.load_from_file(file_path, parser.fields)

            self.raw_memory_buffer = bytearray()
            self.original_raw_model = raw_data
            self.current_data_schema_id = source_schema_id

            target_schema_id = self.get_active_schema_id()
            translated_data, warnings = self.mapper.translate(
                raw_data,
                target_schema_fields=parser.fields,
                source_schema_id=source_schema_id,
                target_schema_id=target_schema_id
            )
            self.common_data_model = translated_data

            if warnings:
                for w in warnings:
                    self.log_message(f" -> {w}", level="WARN")

            self.load_model_into_ui(self.common_data_model)
            self.refresh_raw_inspector()
            self.status_bar.showMessage(f"Imported JSON: {Path(file_path).name}")
            self.log_message(f"Imported JSON from '{Path(file_path).name}' (Detected: {source_schema_id}).")
        except Exception as e:
            self.log_message(f"Failed to import JSON: {e}", level="ERROR")
            QMessageBox.critical(self, "Import Error", f"Failed to load JSON: {e}")

    def handle_export_file(self):
        self.sync_table_to_model()

        default_name = FileExporter.generate_default_filename(self.common_data_model, "json")
        filters = "JSON File (*.json);;Raw NDEF Binary (*.bin);;Text Summary & Dump (*.txt)"

        file_path, selected_filter = QFileDialog.getSaveFileName(self, "Export Tag Data", default_name, filters)
        if not file_path:
            return

        try:
            path = Path(file_path)
            parser = OpenTagParser(self.spec_path)
            
            if "Binary" in selected_filter or path.suffix == ".bin":
                with open(self.spec_path, "r", encoding="utf-8") as f:
                    schema_def = json.load(f)

                scaled_model = self.mapper.to_scaled_model(self.common_data_model, parser.fields)
                schema_id = self.get_active_schema_id()
                writer = get_writer_for_schema(schema_id, schema_def)
                raw_payload = writer.encode(scaled_model)

                FileExporter.export_binary(path, raw_payload)
            elif "Text" in selected_filter or path.suffix == ".txt":
                FileExporter.export_text_dump(path, self.raw_memory_buffer, self.common_data_model)
            else:
                FileExporter.export_json(path, self.common_data_model)

            self.status_bar.showMessage(f"Successfully exported: {path.name}")
            self.log_message(f"Exported data to file '{path.name}'.")
        except Exception as e:
            self.log_message(f"Failed to export file: {e}", level="ERROR")
            QMessageBox.critical(self, "Export Error", f"Failed to export file: {e}")

    def on_hardware_error(self, err_msg: str):
        self.log_message(f"Hardware Error: {err_msg}", level="ERROR")
        QMessageBox.warning(self, "Hardware Error", err_msg)
        self.status_bar.showMessage("Hardware operation aborted.")

    def _set_buttons_enabled(self, enabled: bool):
        self.btn_read_hw.setEnabled(enabled)
        self.btn_write_hw.setEnabled(enabled)
        self.btn_import_json.setEnabled(enabled)
        self.btn_export.setEnabled(enabled)
        self.btn_clear.setEnabled(enabled)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())