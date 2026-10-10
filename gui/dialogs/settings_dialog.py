# gui/dialogs/settings_dialog.py
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QGroupBox,
    QFormLayout,
)
import config

class SettingsDialog(QDialog):
    """Global configuration window for Tagsonian."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(400, 200)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Hardware Options Group
        hw_group = QGroupBox("Hardware Options")
        hw_layout = QFormLayout(hw_group)

        self.combo_reader = QComboBox()
        self.combo_reader.addItems(["Auto-Detect", "ACR122U", "ACR1552U"])
        
        # Load active setting
        current_selection = config.get_selected_reader()
        index = self.combo_reader.findText(current_selection)
        if index >= 0:
            self.combo_reader.setCurrentIndex(index)

        hw_layout.addRow(QLabel("Preferred NFC Reader:"), self.combo_reader)
        main_layout.addWidget(hw_group)

        main_layout.addStretch()

        # Dialog Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Save")
        btn_save.setStyleSheet("font-weight: bold; background-color: #2b78e4; color: white;")
        btn_save.clicked.connect(self.handle_save)
        btn_layout.addWidget(btn_save)

        main_layout.addLayout(btn_layout)

    def handle_save(self):
        selected = self.combo_reader.currentText()
        config.set_selected_reader(selected)
        self.accept()