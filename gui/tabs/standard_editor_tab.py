# gui/tabs/standard_editor_tab.py
import json
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class StandardEditorTab(QWidget):
    """Tab 3: Tag Standard Editor with official_format_lock protections."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_schema_path = None
        self.current_schema_data = {}
        self.official_format_lock = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header Controls
        top_bar = QHBoxLayout()

        self.lbl_schema_name = QLabel("Active Schema: None")
        self.lbl_schema_name.setStyleSheet("font-weight: bold;")
        top_bar.addWidget(self.lbl_schema_name)

        top_bar.addStretch()

        self.chk_format_lock = QCheckBox("Official Format Lock")
        self.chk_format_lock.setEnabled(False)  # Driven strictly by schema file properties
        top_bar.addWidget(self.chk_format_lock)

        self.btn_clone_schema = QPushButton("Clone as Customizable Schema...")
        self.btn_clone_schema.clicked.connect(self.handle_clone_schema)
        top_bar.addWidget(self.btn_clone_schema)

        layout.addLayout(top_bar)

        # Editor Placeholder / Preview
        self.group_editor = QGroupBox("Schema JSON Structure")
        group_layout = QVBoxLayout(self.group_editor)

        self.txt_schema_json = QTextEdit()
        self.txt_schema_json.setPlaceholderText("Select or load a specification schema to edit...")
        group_layout.addWidget(self.txt_schema_json)

        layout.addWidget(self.group_editor)

        # Action Buttons Bar
        action_bar = QHBoxLayout()
        self.btn_save_schema = QPushButton("Save Schema Changes")
        self.btn_save_schema.clicked.connect(self.handle_save_schema)
        action_bar.addWidget(self.btn_save_schema)

        action_bar.addStretch()
        layout.addLayout(action_bar)

    def load_schema(self, schema_path: Path):
        self.current_schema_path = schema_path
        if not schema_path.exists():
            return

        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                self.current_schema_data = json.load(f)

            # Check for official format lock flag in JSON schema root
            self.official_format_lock = self.current_schema_data.get("official_format_lock", False)
            
            # Auto-lock if official filename prefix or locked flag is active
            if "opentag" in schema_path.name.lower() or "openprinttag" in schema_path.name.lower():
                self.official_format_lock = self.current_schema_data.get("official_format_lock", True)

            self.chk_format_lock.setChecked(self.official_format_lock)
            self.lbl_schema_name.setText(f"Active Schema: {schema_path.name}")

            self.txt_schema_json.setText(json.dumps(self.current_schema_data, indent=2))
            
            # Apply UI read-only state if locked
            self.apply_lock_state()

        except Exception as e:
            QMessageBox.critical(self, "Schema Load Error", f"Failed to load schema JSON:\n{e}")

    def apply_lock_state(self):
        if self.official_format_lock:
            self.txt_schema_json.setReadOnly(True)
            self.btn_save_schema.setEnabled(False)
            self.group_editor.setTitle("Schema JSON Structure (LOCKED - Official Standard)")
        else:
            self.txt_schema_json.setReadOnly(False)
            self.btn_save_schema.setEnabled(True)
            self.group_editor.setTitle("Schema JSON Structure (Custom Format - Editable)")

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
            
            if "meta" in cloned_data and isinstance(cloned_data["meta"], dict):
                cloned_data["meta"]["name"] = f"Custom {cloned_data['meta'].get('name', 'Schema')}"

            try:
                path = Path(file_path)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(cloned_data, f, indent=2)

                mw = self.window()
                mw.populate_spec_dropdown()
                self.load_schema(path)
                mw.log_message(f"Cloned official schema to editable custom file '{path.name}'.")
                mw.status_bar.showMessage(f"Created editable clone: {path.name}")

            except Exception as e:
                QMessageBox.critical(self, "Clone Error", f"Failed to save cloned schema:\n{e}")

    def handle_save_schema(self):
        if self.official_format_lock:
            QMessageBox.warning(self, "Format Locked", "Official format standards cannot be modified directly.")
            return

        try:
            raw_text = self.txt_schema_json.toPlainText()
            updated_json = json.loads(raw_text)

            with open(self.current_schema_path, "w", encoding="utf-8") as f:
                json.dump(updated_json, f, indent=2)

            mw = self.window()
            mw.status_bar.showMessage(f"Schema '{self.current_schema_path.name}' saved successfully.")
            mw.log_message(f"Saved changes to custom schema '{self.current_schema_path.name}'.")

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Invalid JSON or file write error:\n{e}")