# gui/tabs/standard_editor_v2_tab.py
import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gui.dialogs.field_editor_dialog import FieldEditorDialog
from gui.widgets.memory_visualizer import MemoryVisualizerWidget
from hardware.chip_profiles import CHIP_PROFILES


class StandardEditorV2Tab(QWidget):
    """Tab 4: Interactive, Visual Tag Standard Editor (V2)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_schema_path = None
        self.current_schema_data = {}
        self.fields = []
        self.official_format_lock = False

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Top Header & Hardware Bar ---
        top_bar = QHBoxLayout()

        self.lbl_schema_name = QLabel("Active Schema: None")
        self.lbl_schema_name.setStyleSheet("font-weight: bold;")
        top_bar.addWidget(self.lbl_schema_name)

        top_bar.addStretch()

        top_bar.addWidget(QLabel("Target Chip Hardware:"))
        self.combo_chip_type = QComboBox()
        for chip_key in CHIP_PROFILES:
            self.combo_chip_type.addItem(chip_key)
        self.combo_chip_type.currentTextChanged.connect(self._on_chip_selection_changed)
        top_bar.addWidget(self.combo_chip_type)

        self.chk_4byte_align = QCheckBox("Force 4-Byte Block Alignment")
        self.chk_4byte_align.setChecked(False)
        self.chk_4byte_align.stateChanged.connect(self.run_validation)
        top_bar.addWidget(self.chk_4byte_align)

        self.chk_format_lock = QCheckBox("Official Format Lock")
        self.chk_format_lock.setEnabled(False)
        top_bar.addWidget(self.chk_format_lock)

        self.btn_clone_schema = QPushButton("Clone as Custom Schema...")
        self.btn_clone_schema.clicked.connect(self.handle_clone_schema)
        top_bar.addWidget(self.btn_clone_schema)

        main_layout.addLayout(top_bar)

        # --- Main Splitter (Table + Visualizer top / Console bottom) ---
        v_splitter = QSplitter(Qt.Vertical)

        # Top Container: Action Buttons + Table + Visualizer
        top_container = QWidget()
        top_layout = QVBoxLayout(top_container)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Action Buttons
        action_bar = QHBoxLayout()
        self.btn_add_field = QPushButton("Add Field...")
        self.btn_add_field.clicked.connect(self.handle_add_field)
        action_bar.addWidget(self.btn_add_field)

        self.btn_auto_organize = QPushButton("Auto-Organize Offsets")
        self.btn_auto_organize.clicked.connect(self.handle_auto_organize)
        action_bar.addWidget(self.btn_auto_organize)

        action_bar.addStretch()
        top_layout.addLayout(action_bar)

        # Field Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["Field Name", "Type", "Start", "Length", "Unit", "Default", "Actions", ""]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        top_layout.addWidget(self.table)

        # Visual Memory Preview Group
        group_vis = QGroupBox("Tag User Memory Map & Overlap Inspector")
        group_vis_layout = QVBoxLayout(group_vis)
        self.visualizer = MemoryVisualizerWidget()
        group_vis_layout.addWidget(self.visualizer)
        top_layout.addWidget(group_vis)

        v_splitter.addWidget(top_container)

        # Console / Log View
        group_log = QGroupBox("Schema Validation Console & Conflict Log")
        group_log_layout = QVBoxLayout(group_log)
        self.txt_log = QTextEdit()
        mono_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        mono_font.setPointSize(9)
        self.txt_log.setFont(mono_font)
        self.txt_log.setReadOnly(True)
        group_log_layout.addWidget(self.txt_log)

        v_splitter.addWidget(group_log)
        v_splitter.setSizes([450, 150])

        main_layout.addWidget(v_splitter)

        # Bottom Save Bar
        bottom_bar = QHBoxLayout()
        self.btn_save_schema = QPushButton("Save Schema Changes")
        self.btn_save_schema.clicked.connect(self.handle_save_schema)
        bottom_bar.addWidget(self.btn_save_schema)

        bottom_bar.addStretch()
        main_layout.addLayout(bottom_bar)

    def load_schema(self, schema_path: Path):
        self.current_schema_path = schema_path
        if not schema_path.exists():
            return

        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                self.current_schema_data = json.load(f)

            self.official_format_lock = self.current_schema_data.get("official_format_lock", False)
            if "opentag" in schema_path.name.lower() or "openprinttag" in schema_path.name.lower():
                self.official_format_lock = self.current_schema_data.get("official_format_lock", True)

            self.chk_format_lock.setChecked(self.official_format_lock)
            self.lbl_schema_name.setText(f"Active Schema: {schema_path.name}")

            # Load fields list
            if "core" in self.current_schema_data and "fields" in self.current_schema_data["core"]:
                self.fields = self.current_schema_data["core"]["fields"]
            else:
                self.fields = self.current_schema_data.get("fields", [])

            # Load hardware info
            hw_info = self.current_schema_data.get("hardware", {})
            supported_chips = hw_info.get("supported_chips", ["NTAG215"])
            if supported_chips:
                chip_idx = self.combo_chip_type.findText(supported_chips[0])
                if chip_idx >= 0:
                    self.combo_chip_type.setCurrentIndex(chip_idx)

            self.refresh_table()
            self.apply_lock_state()

        except Exception as e:
            QMessageBox.critical(self, "Schema Load Error", f"Failed to load schema JSON:\n{e}")

    def refresh_table(self):
        self.table.setRowCount(len(self.fields))
        for row, field in enumerate(self.fields):
            self.table.setItem(row, 0, QTableWidgetItem(str(field.get("name", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(field.get("type", "utf8"))))

            start_val = field.get("start", "0x00")
            self.table.setItem(row, 2, QTableWidgetItem(str(start_val)))

            length_val = field.get("length", field.get("max_bytes", 1))
            self.table.setItem(row, 3, QTableWidgetItem(str(length_val)))

            self.table.setItem(row, 4, QTableWidgetItem(str(field.get("unit", ""))))
            self.table.setItem(row, 5, QTableWidgetItem(str(field.get("default", ""))))

            # Edit Button
            btn_edit = QPushButton("Edit")
            btn_edit.clicked.connect(lambda _, r=row: self.handle_edit_field(r))
            self.table.setCellWidget(row, 6, btn_edit)

            # Delete Button
            btn_del = QPushButton("Delete")
            btn_del.clicked.connect(lambda _, r=row: self.handle_delete_field(r))
            self.table.setCellWidget(row, 7, btn_del)

        self.run_validation()

    def run_validation(self):
        chip_key = self.combo_chip_type.currentText()
        chip_info = CHIP_PROFILES.get(chip_key, CHIP_PROFILES["NTAG215"])
        max_bytes = chip_info["total_user_bytes"]

        self.txt_log.clear()
        self.log_message(f"Validating schema against hardware profile '{chip_key}' ({max_bytes} user bytes available)...")

        conflicts = []
        occupied_spans = []

        for idx, field in enumerate(self.fields):
            start_raw = field.get("start", 0)
            start = int(start_raw, 16) if isinstance(start_raw, str) and start_raw.startswith("0x") else int(start_raw or 0)
            length = int(field.get("length", field.get("max_bytes", 1)))
            end = start + length - 1

            # Check total space overrun
            if end >= max_bytes:
                msg = f"OVERFLOW: Field '{field.get('name')}' spans bytes {start}-{end}, exceeding {chip_key} limit ({max_bytes} bytes)."
                self.log_message(msg, level="ERROR")

            # Check field overlaps
            for prev_name, prev_start, prev_end in occupied_spans:
                if max(start, prev_start) <= min(end, prev_end):
                    conflicts.append((field.get("name"), prev_name))
                    msg = f"CONFLICT: Field '{field.get('name')}' ({start}-{end}) overlaps with '{prev_name}' ({prev_start}-{prev_end})."
                    self.log_message(msg, level="ERROR")

            occupied_spans.append((field.get("name"), start, end))

        if not conflicts:
            self.log_message("Validation passed: No memory address overlaps detected.", level="INFO")

        self.visualizer.update_memory_map(self.fields, max_bytes, conflicts)

    def handle_auto_organize(self):
        if self.official_format_lock:
            QMessageBox.warning(self, "Format Locked", "Cannot auto-organize official locked schemas. Clone a Custom Schema to edit.")
            return

        force_4byte = self.chk_4byte_align.isChecked()
        running_offset = 0

        for field in self.fields:
            field["start"] = f"0x{running_offset:02X}"
            length = int(field.get("length", field.get("max_bytes", 1)))
            running_offset += length

            if force_4byte and (running_offset % 4 != 0):
                running_offset += 4 - (running_offset % 4)

        self.refresh_table()
        self.log_message("Auto-organized all field start addresses sequentially.", level="INFO")

    def handle_add_field(self):
        if self.official_format_lock:
            QMessageBox.warning(self, "Format Locked", "Cannot add fields to official locked schemas.  Clone a Custom Schema to edit.")
            return

        dialog = FieldEditorDialog(self)
        if dialog.exec():
            new_field = dialog.get_data()
            self.fields.append(new_field)
            self.refresh_table()

    def handle_edit_field(self, row: int):
        if self.official_format_lock:
            QMessageBox.warning(self, "Format Locked", "Cannot edit fields in official locked schemas.  Clone a Custom Schema to edit.")
            return

        dialog = FieldEditorDialog(self, field_data=self.fields[row], is_edit=True)
        if dialog.exec():
            self.fields[row] = dialog.get_data()
            self.refresh_table()

    def handle_delete_field(self, row: int):
        if self.official_format_lock:
            QMessageBox.warning(self, "Format Locked", "Cannot delete fields from official locked schemas.  Clone a Custom Schema to edit.")
            return

        del self.fields[row]
        self.refresh_table()

    def _on_chip_selection_changed(self, chip_key: str):
        self.run_validation()

    def apply_lock_state(self):
        is_locked = self.official_format_lock
        self.btn_add_field.setEnabled(not is_locked)
        self.btn_auto_organize.setEnabled(not is_locked)
        self.btn_save_schema.setEnabled(not is_locked)

    def handle_clone_schema(self):
        if not self.current_schema_data:
            return

        default_name = f"custom_{self.current_schema_path.name if self.current_schema_path else 'schema.json'}"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Editable Clone Schema", default_name, "JSON Specification (*.json)"
        )

        if file_path:
            cloned_data = dict(self.current_schema_data)
            cloned_data["official_format_lock"] = False

            try:
                path = Path(file_path)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(cloned_data, f, indent=2)

                mw = self.window()
                mw.populate_spec_dropdown()
                self.load_schema(path)
                mw.log_message(f"Cloned official schema to editable custom file '{path.name}'.")

            except Exception as e:
                QMessageBox.critical(self, "Clone Error", f"Failed to save cloned schema:\n{e}")

    def handle_save_schema(self):
        if self.official_format_lock:
            QMessageBox.warning(self, "Format Locked", "Official format standards cannot be modified directly.  Clone a Custom Schema to edit.")
            return

        try:
            if "core" in self.current_schema_data:
                self.current_schema_data["core"]["fields"] = self.fields
            else:
                self.current_schema_data["fields"] = self.fields

            with open(self.current_schema_path, "w", encoding="utf-8") as f:
                json.dump(self.current_schema_data, f, indent=2)

            mw = self.window()
            mw.status_bar.showMessage(f"Schema '{self.current_schema_path.name}' saved successfully.")
            self.log_message(f"Saved changes to schema '{self.current_schema_path.name}'.")

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save schema file:\n{e}")

    def log_message(self, message: str, level: str = "INFO"):
        self.txt_log.append(f"[{level}] {message}")