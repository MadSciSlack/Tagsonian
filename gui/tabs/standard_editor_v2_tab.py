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
    QScrollArea,
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

        # --- Main Vertical Splitter (Table / Visualizer / Console) ---
        main_v_splitter = QSplitter(Qt.Vertical)

        # 1. Top Section: Field Table + Action Bar
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        action_bar = QHBoxLayout()
        self.btn_add_field = QPushButton("Add Field...")
        self.btn_add_field.clicked.connect(self.handle_add_field)
        action_bar.addWidget(self.btn_add_field)

        self.btn_auto_organize = QPushButton("Auto-Organize Offsets")
        self.btn_auto_organize.clicked.connect(self.handle_auto_organize)
        action_bar.addWidget(self.btn_auto_organize)

        action_bar.addStretch()
        table_layout.addLayout(action_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["Field Name", "Type", "Start", "Length", "Unit", "Default", "Actions", ""]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table_layout.addWidget(self.table)

        main_v_splitter.addWidget(table_container)

       # 2. Middle Section: Scrollable Visual Memory Preview Group
        group_vis = QGroupBox("Tag User Memory Map & Overlap Inspector")
        group_vis_layout = QVBoxLayout(group_vis)

        # Dual-View Mode Toggle Bar
        view_toggle_bar = QHBoxLayout()
        self.btn_view_draft = QPushButton("In-Editing Draft View")
        self.btn_view_draft.setCheckable(True)
        self.btn_view_draft.setChecked(True)
        self.btn_view_draft.clicked.connect(lambda: self.switch_visualizer_view("draft"))
        view_toggle_bar.addWidget(self.btn_view_draft)

        self.btn_view_target = QPushButton("Target Spec Translation View")
        self.btn_view_target.setCheckable(True)
        self.btn_view_target.setChecked(False)
        self.btn_view_target.clicked.connect(lambda: self.switch_visualizer_view("target_spec"))
        view_toggle_bar.addWidget(self.btn_view_target)

        view_toggle_bar.addStretch()
        group_vis_layout.addLayout(view_toggle_bar)

        self.visual_scroll_area = QScrollArea()
        self.visual_scroll_area.setWidgetResizable(True)
        self.visual_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.visual_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.visualizer = MemoryVisualizerWidget()
        self.visual_scroll_area.setWidget(self.visualizer)

        group_vis_layout.addWidget(self.visual_scroll_area)
        main_v_splitter.addWidget(group_vis)

        # 3. Bottom Section: Console / Validation Log
        group_log = QGroupBox("Schema Validation Console & Conflict Log")
        group_log_layout = QVBoxLayout(group_log)
        self.txt_log = QTextEdit()
        mono_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        mono_font.setPointSize(9)
        self.txt_log.setFont(mono_font)
        self.txt_log.setReadOnly(True)
        group_log_layout.addWidget(self.txt_log)

        main_v_splitter.addWidget(group_log)

        main_v_splitter.setSizes([250, 200, 100])
        main_layout.addWidget(main_v_splitter)

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

            if "core" in self.current_schema_data and "fields" in self.current_schema_data["core"]:
                self.fields = self.current_schema_data["core"]["fields"]
            else:
                self.fields = self.current_schema_data.get("fields", [])

            hw_info = self.current_schema_data.get("hardware", {})
            supported_chips = hw_info.get("supported_chips", ["NTAG215"])
            
            # Block dropdown signals to prevent initial popup during load_schema
            self.combo_chip_type.blockSignals(True)
            if supported_chips:
                chip_idx = self.combo_chip_type.findText(supported_chips[0])
                if chip_idx >= 0:
                    self.combo_chip_type.setCurrentIndex(chip_idx)
            self.combo_chip_type.blockSignals(False)

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

            btn_edit = QPushButton("Edit")
            btn_edit.clicked.connect(lambda _, r=row: self.handle_edit_field(r))
            self.table.setCellWidget(row, 6, btn_edit)

            btn_del = QPushButton("Delete")
            btn_del.clicked.connect(lambda _, r=row: self.handle_delete_field(r))
            self.table.setCellWidget(row, 7, btn_del)

        self.run_validation()

    def run_validation(self) -> bool:
        """Validates in-progress fields against the selected tag capacity.
        
        Returns True if all fields fit within tag capacity, False if an overflow occurs.
        """
        chip_key = self.combo_chip_type.currentText()
        chip_info = CHIP_PROFILES.get(chip_key, CHIP_PROFILES["NTAG215"])
        max_bytes = chip_info["total_user_bytes"]

        self.txt_log.clear()
        self.log_message(f"Validating in-progress schema against tag profile '{chip_key}' ({max_bytes} user bytes available)...")

        conflicts = []
        occupied_spans = []
        has_overflow = False

        for idx, field in enumerate(self.fields):
            start_raw = field.get("start", 0)
            start = int(start_raw, 16) if isinstance(start_raw, str) and start_raw.startswith("0x") else int(start_raw or 0)
            length = int(field.get("length", field.get("max_bytes", 1)))
            end = start + length - 1

            # Check capacity overrun against in-progress fields
            if end >= max_bytes:
                has_overflow = True
                msg = f"CAPACITY OVERFLOW: Field '{field.get('name')}' spans bytes {start}-{end}, which exceeds the {chip_key} limit ({max_bytes} bytes)."
                self.log_message(msg, level="ERROR")

            # Check field address overlaps
            for prev_name, prev_start, prev_end in occupied_spans:
                if max(start, prev_start) <= min(end, prev_end):
                    conflicts.append((field.get("name"), prev_name))
                    msg = f"CONFLICT: Field '{field.get('name')}' ({start}-{end}) overlaps with '{prev_name}' ({prev_start}-{prev_end})."
                    self.log_message(msg, level="ERROR")

            occupied_spans.append((field.get("name"), start, end))

        if not conflicts and not has_overflow:
            self.log_message("Validation passed: All fields fit with no memory address overlaps.", level="INFO")

        self.visualizer.update_memory_map(self.fields, max_bytes, conflicts)
        return not has_overflow

    def _on_chip_selection_changed(self, chip_key: str):
        fits = self.run_validation()
        if not fits:
            chip_info = CHIP_PROFILES.get(chip_key, CHIP_PROFILES["NTAG215"])
            max_bytes = chip_info["total_user_bytes"]
            
            # Calculate required bytes for popup message
            required_bytes = 0
            for field in self.fields:
                start_raw = field.get("start", 0)
                start = int(start_raw, 16) if isinstance(start_raw, str) and start_raw.startswith("0x") else int(start_raw or 0)
                length = int(field.get("length", field.get("max_bytes", 1)))
                required_bytes = max(required_bytes, start + length)

            QMessageBox.warning(
                self,
                "Insufficient Tag Capacity",
                f"The selected tag type '{chip_key}' only provides {max_bytes} user bytes.\n\n"
                f"Your in-progress schema requires at least {required_bytes} bytes. "
                f"Some fields will be truncated or fail to write to this tag.",
            )

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
            QMessageBox.warning(self, "Format Locked", "Cannot add fields to official locked schemas. Clone a Custom Schema to edit.")
            return

        dialog = FieldEditorDialog(self)
        if dialog.exec():
            new_field = dialog.get_data()
            self.fields.append(new_field)
            self.refresh_table()

    def handle_edit_field(self, row: int):
        if self.official_format_lock:
            QMessageBox.warning(self, "Format Locked", "Cannot edit fields in official locked schemas. Clone a Custom Schema to edit.")
            return

        dialog = FieldEditorDialog(self, field_data=self.fields[row], is_edit=True)
        if dialog.exec():
            self.fields[row] = dialog.get_data()
            self.refresh_table()

    def handle_delete_field(self, row: int):
        if self.official_format_lock:
            QMessageBox.warning(self, "Format Locked", "Cannot delete fields from official locked schemas. Clone a Custom Schema to edit.")
            return

        del self.fields[row]
        self.refresh_table()

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
            QMessageBox.warning(self, "Format Locked", "Official format standards cannot be modified directly. Clone a Custom Schema to edit.")
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

    def switch_visualizer_view(self, mode: str):
    #"""Handles toggling between draft workspace view and translated target spec layout."""
        if mode == "draft":
            self.btn_view_draft.setChecked(True)
            self.btn_view_target.setChecked(False)
            self.visualizer.set_view_mode("draft")
            self.run_validation()
        elif mode == "target_spec":
            self.btn_view_draft.setChecked(False)
            self.btn_view_target.setChecked(True)
            self.visualizer.set_view_mode("target_spec")
            # Re-render visualizer using target schema translated structure
            self.run_validation()

    def _clone_schema_for_editing(self, source_schema: dict) -> dict:
        #"""Clones a locked official spec into an editable user draft schema."""
        cloned_schema = copy.deepcopy(source_schema)
        cloned_schema["official_spec_lock"] = False  # Unlock for editing
        cloned_schema["uuid"] = str(uuid.uuid4())
        
        # Ensure all original base fields explicitly carry is_custom = False
        for field in cloned_schema.get("core", {}).get("fields", []):
            if "is_custom" not in field:
                field["is_custom"] = False

        return cloned_schema            