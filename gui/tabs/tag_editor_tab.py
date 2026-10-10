# gui/tabs/tag_editor_tab.py
from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class TagEditorTab(QWidget):
    """Tab 1: Tag Editor & Activity Log."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        editor_layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Vertical)

        # Form Table
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Field Name", "Value", "Unit / Type"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table_layout.addWidget(self.table)
        splitter.addWidget(table_container)

        # Activity Log
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)

        log_label_layout = QHBoxLayout()
        lbl_log = QLabel("Activity & Mapping Log:")
        lbl_log.setStyleSheet("font-weight: bold; color: #555;")
        log_label_layout.addWidget(lbl_log)
        log_label_layout.addStretch()

        btn_clear_log = QPushButton("Clear Log")
        btn_clear_log.setMaximumHeight(22)
        btn_clear_log.clicked.connect(lambda: self.txt_activity_log.clear())
        log_label_layout.addWidget(btn_clear_log)
        log_layout.addLayout(log_label_layout)

        self.txt_activity_log = QTextEdit()
        mono_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        mono_font.setPointSize(9)
        self.txt_activity_log.setFont(mono_font)
        self.txt_activity_log.setReadOnly(True)
        log_layout.addWidget(self.txt_activity_log)

        splitter.addWidget(log_container)
        splitter.setSizes([450, 150])

        editor_layout.addWidget(splitter)

    def log_message(self, message: str, level: str = "INFO"):
        time_str = datetime.now().strftime("%H:%M:%S")
        self.txt_activity_log.append(f"[{time_str}] [{level}] {message}")

    def load_model_into_ui(self, model: dict, schema_lookup: dict):
        """Loads data model into the UI table while deduplicating display rows."""
        self.table.setRowCount(0)
        seen_canonical_ids = set()

        for field_key, val in model.items():
            field_spec = schema_lookup.get(field_key, {})
            if not field_spec:
                for f_id, f_def in schema_lookup.items():
                    if isinstance(f_def, dict) and (f_def.get("name") == field_key or f_def.get("id") == field_key):
                        field_spec = f_def
                        break

            canonical_id = field_spec.get("name", field_spec.get("id", str(field_key)))
            if canonical_id in seen_canonical_ids:
                continue
            seen_canonical_ids.add(canonical_id)

            row = self.table.rowCount()
            self.table.insertRow(row)

            display_name = field_spec.get("name", str(field_key))
            item_name = QTableWidgetItem(display_name)
            item_name.setFlags(item_name.flags() & ~Qt.ItemIsEditable)
            item_name.setData(Qt.UserRole, str(field_key))
            self.table.setItem(row, 0, item_name)

            if isinstance(val, list):
                val_str = ", ".join(str(x).replace("\x00", "") for x in val)
            elif val is not None:
                val_str = str(val).replace("\x00", "").strip()
            else:
                val_str = ""

            self.table.setItem(row, 1, QTableWidgetItem(val_str))

            unit_str = field_spec.get("unit", "")
            dtype_name = type(val).__name__ if val != "" else "empty"
            type_display = f"{unit_str} ({dtype_name})" if unit_str else dtype_name

            item_type = QTableWidgetItem(type_display)
            item_type.setFlags(item_type.flags() & ~Qt.ItemIsEditable)
            item_type.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, item_type)

    def sync_table_to_model(self, model: dict, schema_lookup: dict) -> dict:
        """Reads edited UI table values and updates the target data model dictionary."""
        new_model = dict(model)

        for row in range(self.table.rowCount()):
            field_name_item = self.table.item(row, 0)
            val_item = self.table.item(row, 1)

            if not field_name_item or not val_item:
                continue

            field_key = field_name_item.data(Qt.UserRole) or field_name_item.text()
            val_str = val_item.text().strip()

            if val_str == "":
                new_model[field_key] = ""
                continue

            field_spec = schema_lookup.get(field_key, {})
            if not field_spec:
                for f_id, f_def in schema_lookup.items():
                    if isinstance(f_def, dict) and (f_def.get("name") == field_key or f_def.get("id") == field_key):
                        field_spec = f_def
                        break

            ftype = field_spec.get("type", "utf8")

            if ftype in ("int", "int_scale"):
                try:
                    parsed_val = float(val_str) if "." in val_str else int(val_str)
                    new_model[field_key] = parsed_val
                except ValueError:
                    new_model[field_key] = val_str
            elif ftype == "rgba" and "," in val_str:
                try:
                    new_model[field_key] = [int(x.strip()) for x in val_str.split(",")]
                except ValueError:
                    new_model[field_key] = val_str
            else:
                new_model[field_key] = val_str

            # Maintain secondary standard key alias if specified in schema
            alt_key = field_spec.get("id") if field_key == field_spec.get("name") else field_spec.get("name")
            if alt_key and alt_key in new_model:
                new_model[alt_key] = new_model[field_key]

        model.clear()
        model.update(new_model)
        return model