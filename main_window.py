# main_window.py
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

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

from exporters.file_exporter import FileExporter
from gui.tabs import RawInspectorTab, StandardEditorTab, StandardEditorV2Tab, TagEditorTab
from hardware.acr122u import ACR122UThread
from hardware.base_reader import BaseNFCReader
from json_importer import JSONImporter
from mappings.mapper import FormatMapper
from parsers import OpenTagParser
from writers.opentag_writer import OpenTagWriter


class MainWindow(QMainWindow):
    def __init__(self, spec_path="schemas/opentag_v2_003.json"):
        super().__init__()
        resolved_spec = SCRIPT_DIR / spec_path
        self.spec_path = resolved_spec if resolved_spec.exists() else Path(spec_path)

        self.common_data_model = {}
        self.original_raw_model = {}
        self.raw_memory_buffer = bytearray()
        self.detected_spec_name = "None"
        self.active_thread = None
        self.mapper = FormatMapper()

        self.setWindowTitle("Tagsonian (V0.20-B0010)")
        self.resize(1050, 750)

        self.setup_ui()
        self.populate_spec_dropdown()
        self.handle_clear()
        self.log_message(f"Tagsonian initialized with OpenTag3D target schema: {self.spec_path.name}")

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

        self.tabs.addTab(self.tab_editor, "Tag Editor (OpenTag3D)")
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

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def log_message(self, message: str, level: str = "INFO"):
        self.tab_editor.log_message(message, level)

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
                        self.combo_target_spec.addItem(spec_file.name, userData=spec_file)

        index = self.combo_target_spec.findText(self.spec_path.name)
        if index >= 0:
            self.combo_target_spec.setCurrentIndex(index)

        self.combo_target_spec.blockSignals(False)

    def on_target_spec_changed(self, index: int):
        selected_file = self.combo_target_spec.itemData(index)
        if selected_file and selected_file.exists():
            self.spec_path = selected_file
            self.sync_table_to_model()

            parser = OpenTagParser(self.spec_path)
            self.log_message(f"Mapping data to target schema '{self.spec_path.name}'...")

            translated_data, warnings = self.mapper.translate(
                self.common_data_model, target_schema_fields=parser.fields
            )
            self.common_data_model = translated_data

            if warnings:
                msg_summary = f"Target Spec applied with {len(warnings)} warning(s)."
                self.status_bar.showMessage(msg_summary)
                self.log_message(msg_summary, level="WARN")
                for w in warnings:
                    self.log_message(f" -> {w}", level="WARN")
            else:
                self.status_bar.showMessage(f"Target Spec set to: {self.spec_path.name}")
                self.log_message(f"Successfully mapped to target schema '{self.spec_path.name}'.")

            self.load_model_into_ui(self.common_data_model)
            self.refresh_raw_inspector()

            if hasattr(self, "tab_standard_editor") and self.tab_standard_editor:
                self.tab_standard_editor.load_schema(self.spec_path)
            if hasattr(self, "tab_standard_editor_v2") and self.tab_standard_editor_v2:
                self.tab_standard_editor_v2.load_schema(self.spec_path)

    def sync_table_to_model(self):
        parser = OpenTagParser(self.spec_path)
        schema_lookup = {f["name"]: f for f in parser.fields}
        self.common_data_model = self.tab_editor.sync_table_to_model(self.common_data_model, schema_lookup)

    def load_model_into_ui(self, model: dict):
        parser = OpenTagParser(self.spec_path)
        schema_lookup = {f["name"]: f for f in parser.fields}
        self.tab_editor.load_model_into_ui(model, schema_lookup)

    def refresh_raw_inspector(self):
        self.tab_inspector.refresh(
            self.original_raw_model,
            self.raw_memory_buffer,
            self.common_data_model,
            self.spec_path,
            self.detected_spec_name,
        )

    def handle_clear(self):
        parser = OpenTagParser(self.spec_path)
        self.common_data_model = {f["name"]: "" for f in parser.fields}
        self.original_raw_model = {}
        self.raw_memory_buffer = bytearray()
        self.detected_spec_name = "None"

        self.lbl_detected_spec.setText("Detected Spec: None")
        self.load_model_into_ui(self.common_data_model)
        self.refresh_raw_inspector()

        if hasattr(self, "tab_standard_editor") and self.tab_standard_editor:
            self.tab_standard_editor.load_schema(self.spec_path)
        if hasattr(self, "tab_standard_editor_v2") and self.tab_standard_editor_v2:
            self.tab_standard_editor_v2.load_schema(self.spec_path)

        self.status_bar.showMessage("Cleared all fields.")
        self.log_message("Form cleared and state reset.")

    def handle_read_hardware(self):
        self.status_bar.showMessage("Polling reader... Present tag to READ.")
        self.log_message("Initiated NFC tag read poll...")
        self._set_buttons_enabled(False)

        self.active_thread = ACR122UThread(mode="read")
        self.active_thread.tag_detected.connect(self.on_tag_read_success)
        self.active_thread.error_occurred.connect(self.on_hardware_error)
        self.active_thread.finished.connect(lambda: self._set_buttons_enabled(True))
        self.active_thread.start()

    def handle_write_hardware(self):
        self.sync_table_to_model()

        try:
            writer = OpenTagWriter()
            full_memory_dump = writer.encode(self.common_data_model, self.spec_path)
        except Exception as e:
            self.log_message(f"Encoding payload failed: {e}", level="ERROR")
            QMessageBox.critical(self, "Encoding Error", f"Cannot encode payload for target spec:\n{e}")
            return

        self.status_bar.showMessage("Polling reader... Present tag to WRITE.")
        self.log_message(
            f"Initiated NFC write poll for target spec '{self.spec_path.name}' ({len(full_memory_dump)} bytes)..."
        )
        self._set_buttons_enabled(False)

        self.active_thread = ACR122UThread(mode="write", payload=full_memory_dump)
        self.active_thread.write_success.connect(self.on_write_success)
        self.active_thread.error_occurred.connect(self.on_hardware_error)
        self.active_thread.finished.connect(lambda: self._set_buttons_enabled(True))
        self.active_thread.start()

    def on_tag_read_success(self, raw_memory: bytearray, detected_chip_type: str = "NTAG215"):
        self.raw_memory_buffer = raw_memory

        parser = OpenTagParser(self.spec_path)
        spec_schema = parser.spec_data if hasattr(parser, "spec_data") else {}

        is_valid, chip_err = BaseNFCReader.validate_chip_for_spec(detected_chip_type, spec_schema)
        if not is_valid:
            self.log_message(f"Chip Compatibility Warning: {chip_err}", level="WARN")
            QMessageBox.warning(self, "Hardware Compatibility Warning", chip_err)

        mime_type, payload = parser.extract_ndef_payload(raw_memory)

        if payload:
            self.detected_spec_name = mime_type if mime_type else "OpenTag3D"
            self.lbl_detected_spec.setText(f"Detected Spec: {self.detected_spec_name}")

            raw_parsed = parser.parse(payload, mime_type=mime_type)
            self.original_raw_model = raw_parsed

            translated_model, warnings = self.mapper.translate(
                raw_parsed, target_schema_fields=parser.fields
            )
            self.common_data_model = translated_model

            if warnings:
                self.log_message(f"Read mapping warning(s): {len(warnings)} issue(s)", level="WARN")
                for w in warnings:
                    self.log_message(f" -> {w}", level="WARN")

            self.load_model_into_ui(self.common_data_model)
            self.refresh_raw_inspector()
            self.status_bar.showMessage(f"Successfully read tag! ({self.detected_spec_name})")
            self.log_message(f"Read payload ({self.detected_spec_name}) and mapped to OpenTag3D.")
        else:
            self.log_message("Read warning: No valid payload extracted from tag.", level="WARN")
            QMessageBox.warning(self, "Read Warning", "No valid payload found on tag.")

    def on_write_success(self):
        QMessageBox.information(self, "Success", "Payload written to tag successfully!")
        self.status_bar.showMessage("Tag written successfully.")
        self.log_message("NFC tag write operation completed successfully.")

    def handle_import_json(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import JSON", "", "JSON Files (*.json)")
        if not file_path:
            return
        try:
            parser = OpenTagParser(self.spec_path)
            raw_data = JSONImporter.load_from_file(file_path, parser.fields)

            self.detected_spec_name = f"JSON ({Path(file_path).name})"
            self.raw_memory_buffer = bytearray()
            self.original_raw_model = raw_data

            translated_data, warnings = self.mapper.translate(
                raw_data, target_schema_fields=parser.fields
            )
            self.common_data_model = translated_data

            if warnings:
                self.log_message(f"Import mapping warning(s): {len(warnings)} issue(s)", level="WARN")
                for w in warnings:
                    self.log_message(f" -> {w}", level="WARN")

            self.lbl_detected_spec.setText(f"Detected Spec: {self.detected_spec_name}")
            self.load_model_into_ui(self.common_data_model)
            self.refresh_raw_inspector()
            self.status_bar.showMessage(f"Imported JSON: {Path(file_path).name}")
            self.log_message(f"Imported JSON from '{Path(file_path).name}' and mapped to OpenTag3D.")
        except Exception as e:
            self.log_message(f"Failed to import JSON: {e}", level="ERROR")
            QMessageBox.critical(self, "Import Error", f"Failed to load JSON: {e}")

    def handle_export_file(self):
        self.sync_table_to_model()

        default_name = FileExporter.generate_default_filename(self.common_data_model, "json")
        filters = "JSON File (*.json);;Raw NDEF Binary (*.bin);;Text Summary & Dump (*.txt)"

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Export Tag Data", default_name, filters
        )

        if not file_path:
            return

        try:
            path = Path(file_path)
            if "Binary" in selected_filter or path.suffix == ".bin":
                writer = OpenTagWriter()
                raw_payload = writer.encode(self.common_data_model, self.spec_path)
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