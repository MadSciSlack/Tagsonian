# gui/tabs/raw_inspector_tab.py
import json
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from exporters.file_exporter import FileExporter
from utils.hex_formatter import HexFormatter
from writers.opentag_writer import OpenTagWriter


class RawInspectorTab(QWidget):
    """Tab 2: Raw Data Inspector with source & translated hex actions and balanced split layouts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.target_binary_buffer = bytearray()
        self.setup_ui()

    def setup_ui(self):
        inspector_layout = QVBoxLayout(self)

        mono_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        mono_font.setPointSize(9)

        # --- Source Actions Bar ---
        source_btn_layout = QHBoxLayout()
        self.btn_copy_raw_hex = QPushButton("Copy Source Hex")
        self.btn_copy_raw_hex.clicked.connect(self.handle_copy_raw_hex)
        source_btn_layout.addWidget(self.btn_copy_raw_hex)

        self.btn_copy_full_dump = QPushButton("Copy Source Dump")
        self.btn_copy_full_dump.clicked.connect(self.handle_copy_full_dump)
        source_btn_layout.addWidget(self.btn_copy_full_dump)

        self.btn_save_dump = QPushButton("Save Source Dump...")
        self.btn_save_dump.clicked.connect(self.handle_save_source_dump)
        source_btn_layout.addWidget(self.btn_save_dump)

        source_btn_layout.addStretch()

        # --- Target Actions Bar ---
        self.btn_copy_target_hex = QPushButton("Copy Target Hex")
        self.btn_copy_target_hex.clicked.connect(self.handle_copy_target_hex)
        source_btn_layout.addWidget(self.btn_copy_target_hex)

        self.btn_save_target_dump = QPushButton("Save Target Dump...")
        self.btn_save_target_dump.clicked.connect(self.handle_save_target_dump)
        source_btn_layout.addWidget(self.btn_save_target_dump)

        inspector_layout.addLayout(source_btn_layout)

        # --- Inspector Splitter ---
        self.inspector_splitter = QSplitter(Qt.Horizontal)

        # Source Panel
        group_source = QGroupBox("Source Data Payload / Summary")
        group_source_layout = QVBoxLayout(group_source)
        group_source_layout.setContentsMargins(6, 6, 6, 6)
        self.txt_hex_dump_source = QTextEdit()
        self.txt_hex_dump_source.setFont(mono_font)
        self.txt_hex_dump_source.setReadOnly(True)
        self.txt_hex_dump_source.setLineWrapMode(QTextEdit.NoWrap)
        group_source_layout.addWidget(self.txt_hex_dump_source)
        self.inspector_splitter.addWidget(group_source)

        # Target Panel
        self.group_target = QGroupBox("Translated OpenTag3D Payload")
        group_target_layout = QVBoxLayout(self.group_target)
        group_target_layout.setContentsMargins(6, 6, 6, 6)
        self.txt_hex_dump_target = QTextEdit()
        self.txt_hex_dump_target.setFont(mono_font)
        self.txt_hex_dump_target.setReadOnly(True)
        self.txt_hex_dump_target.setLineWrapMode(QTextEdit.NoWrap)
        group_target_layout.addWidget(self.txt_hex_dump_target)
        self.inspector_splitter.addWidget(self.group_target)

        # Fix uneven sizing by forcing equal 50/50 stretch ratios and equal initial sizes
        self.inspector_splitter.setStretchFactor(0, 1)
        self.inspector_splitter.setStretchFactor(1, 1)
        self.inspector_splitter.setSizes([500, 500])

        inspector_layout.addWidget(self.inspector_splitter)

    def refresh(
        self,
        original_raw_model: dict,
        raw_memory_buffer: bytearray,
        common_data_model: dict,
        spec_path: Path,
        detected_spec_name: str,
    ):
        is_matching = (
            detected_spec_name.lower() in spec_path.name.lower()
            or detected_spec_name == "None"
        )

        # Build Source View
        source_sections = []
        if original_raw_model:
            source_sections.append("=== ORIGINAL PARSED FIELDS ===")
            source_sections.append(json.dumps(original_raw_model, indent=2))
            source_sections.append("")

        if raw_memory_buffer:
            source_sections.append("=== RAW MEMORY BINARY DUMP ===")
            source_sections.append(HexFormatter.to_full_dump(raw_memory_buffer))

        source_text = "\n".join(source_sections) if source_sections else "(No data currently loaded)"
        self.txt_hex_dump_source.setText(source_text)

        # Build Target View
        self.target_binary_buffer = bytearray()
        if is_matching:
            self.group_target.setVisible(False)
            self.btn_copy_target_hex.setEnabled(False)
            self.btn_save_target_dump.setEnabled(False)
        else:
            self.group_target.setVisible(True)
            self.btn_copy_target_hex.setEnabled(True)
            self.btn_save_target_dump.setEnabled(True)
            try:
                writer = OpenTagWriter()
                self.target_binary_buffer = writer.encode(common_data_model, spec_path)
                self.txt_hex_dump_target.setText(HexFormatter.to_full_dump(self.target_binary_buffer))
            except Exception as e:
                self.txt_hex_dump_target.setText(f"Encoding target payload failed:\n{e}")

    # Action Handlers
    def handle_copy_raw_hex(self):
        mw = self.window()
        raw_hex = HexFormatter.to_raw_hex(mw.raw_memory_buffer)
        QApplication.clipboard().setText(raw_hex)
        mw.status_bar.showMessage("Copied raw source hex string to clipboard.")
        mw.log_message("Copied raw source hex string to system clipboard.")

    def handle_copy_full_dump(self):
        mw = self.window()
        full_dump = HexFormatter.to_full_dump(mw.raw_memory_buffer)
        QApplication.clipboard().setText(full_dump)
        mw.status_bar.showMessage("Copied formatted source hex dump to clipboard.")
        mw.log_message("Copied formatted source memory dump to system clipboard.")

    def handle_save_source_dump(self):
        mw = self.window()
        default_name = FileExporter.generate_default_filename(mw.common_data_model, "txt")
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Source Memory Dump", default_name, "Text Files (*.txt);;Raw Binary (*.bin)"
        )
        if file_path:
            path = Path(file_path)
            if path.suffix == ".bin":
                FileExporter.export_binary(path, mw.raw_memory_buffer)
            else:
                FileExporter.export_text_dump(path, mw.raw_memory_buffer, mw.common_data_model)
            mw.status_bar.showMessage(f"Source dump saved to {path.name}")
            mw.log_message(f"Source memory dump saved to file '{path.name}'.")

    def handle_copy_target_hex(self):
        mw = self.window()
        if not self.target_binary_buffer:
            QMessageBox.warning(self, "No Target Data", "No target translation binary available to copy.")
            return
        target_hex = HexFormatter.to_raw_hex(self.target_binary_buffer)
        QApplication.clipboard().setText(target_hex)
        mw.status_bar.showMessage("Copied target hex string to clipboard.")
        mw.log_message("Copied target raw hex string to system clipboard.")

    def handle_save_target_dump(self):
        mw = self.window()
        if not self.target_binary_buffer:
            QMessageBox.warning(self, "No Target Data", "No target translation binary available to save.")
            return
        default_name = f"target_dump_{mw.spec_path.stem}.bin"
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Save Target Binary Dump", default_name, "Raw Binary (*.bin);;Text Dump (*.txt)"
        )
        if file_path:
            path = Path(file_path)
            if "Text" in selected_filter or path.suffix == ".txt":
                FileExporter.export_text_dump(path, self.target_binary_buffer, mw.common_data_model)
            else:
                FileExporter.export_binary(path, self.target_binary_buffer)
            mw.status_bar.showMessage(f"Target dump saved to {path.name}")
            mw.log_message(f"Target memory dump saved to file '{path.name}'.")