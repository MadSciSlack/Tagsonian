# gui/dialogs/field_editor_dialog.py
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)


class FieldEditorDialog(QDialog):
    def __init__(self, parent=None, field_data=None, is_edit=False):
        super().__init__(parent)
        self.setWindowTitle("Edit Field Data Point" if is_edit else "Add New Field Data Point")
        self.resize(450, 400)

        self.field_data = field_data or {}
        self.setup_ui()
        self.populate_fields()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.txt_name = QLineEdit()
        form.addRow("Field Name:", self.txt_name)

        self.txt_id = QLineEdit()
        form.addRow("Field ID / Slug:", self.txt_id)

        self.combo_type = QComboBox()
        self.combo_type.addItems(["utf8", "int", "int_scale", "rgba", "date", "time", "enum"])
        form.addRow("Data Type:", self.combo_type)

        # Address & Length Management
        addr_layout = QHBoxLayout()
        self.spin_start = QSpinBox()
        self.spin_start.setRange(0, 4096)
        self.spin_start.valueChanged.connect(self._on_start_or_length_changed)
        addr_layout.addWidget(self.spin_start)

        addr_layout.addWidget(QLabel("Length (Bytes):"))
        self.spin_length = QSpinBox()
        self.spin_length.setRange(1, 1024)
        self.spin_length.setValue(1)
        self.spin_length.valueChanged.connect(self._on_start_or_length_changed)
        addr_layout.addWidget(self.spin_length)

        form.addRow("Start Address / Length:", addr_layout)

        self.lbl_end_addr = QLabel("End Address: 0x00 (Byte 0)")
        form.addRow("Calculated End:", self.lbl_end_addr)

        self.txt_unit = QLineEdit()
        form.addRow("Unit (e.g. mm, °C):", self.txt_unit)

        self.txt_scaling = QLineEdit("1.0")
        form.addRow("Scaling Multiplier:", self.txt_scaling)

        self.txt_default = QLineEdit()
        form.addRow("Default Value:", self.txt_default)

        self.txt_examples = QLineEdit()
        self.txt_examples.setPlaceholderText("Comma-separated (e.g. 210, 215)")
        form.addRow("Examples:", self.txt_examples)

        self.txt_description = QLineEdit()
        form.addRow("Description:", self.txt_description)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_start_or_length_changed(self):
        start = self.spin_start.value()
        length = self.spin_length.value()
        end = max(0, start + length - 1)
        self.lbl_end_addr.setText(f"End Address: 0x{end:02X} (Byte {end})")

    def populate_fields(self):
        if not self.field_data:
            return

        self.txt_name.setText(str(self.field_data.get("name", "")))
        self.txt_id.setText(str(self.field_data.get("id", "")))
        
        type_idx = self.combo_type.findText(str(self.field_data.get("type", "utf8")))
        if type_idx >= 0:
            self.combo_type.setCurrentIndex(type_idx)

        # Handle Start Address (Hex or Int)
        start_val = self.field_data.get("start", "0x00")
        start_int = int(start_val, 16) if isinstance(start_val, str) and start_val.startswith("0x") else int(start_val or 0)
        self.spin_start.setValue(start_int)

        length_val = int(self.field_data.get("length", self.field_data.get("max_bytes", 1)))
        self.spin_length.setValue(length_val)

        self.txt_unit.setText(str(self.field_data.get("unit", "")))
        self.txt_scaling.setText(str(self.field_data.get("scaling", 1.0)))
        self.txt_default.setText(str(self.field_data.get("default", "")))

        examples = self.field_data.get("examples", [])
        self.txt_examples.setText(", ".join(str(x) for x in examples) if isinstance(examples, list) else str(examples))
        self.txt_description.setText(str(self.field_data.get("description", "")))

        self._on_start_or_length_changed()

    def get_data(self) -> dict:
        start_hex = f"0x{self.spin_start.value():02X}"
        examples_raw = self.txt_examples.text().strip()
        examples_list = [e.strip() for e in examples_raw.split(",") if e.strip()] if examples_raw else []

        try:
            scale_val = float(self.txt_scaling.text().strip())
        except ValueError:
            scale_val = 1.0

        return {
            "name": self.txt_name.text().strip(),
            "id": self.txt_id.text().strip() or self.txt_name.text().lower().replace(" ", "_"),
            "type": self.combo_type.currentText(),
            "start": start_hex,
            "length": self.spin_length.value(),
            "max_bytes": self.spin_length.value(),
            "unit": self.txt_unit.text().strip(),
            "scaling": scale_val,
            "default": self.txt_default.text().strip(),
            "examples": examples_list,
            "description": self.txt_description.text().strip(),
        }