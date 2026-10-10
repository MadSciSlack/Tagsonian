# config.py
from PySide6.QtCore import QSettings

APP_NAME = "Tagsonian"
ORGANIZATION_NAME = "Tagsonian"

def get_selected_reader() -> str:
    """Returns the user-selected reader ('Auto-Detect', 'ACR122U', or 'ACR1552U')."""
    settings = QSettings(ORGANIZATION_NAME, APP_NAME)
    return settings.value("hardware/selected_reader", "Auto-Detect", type=str)

def set_selected_reader(reader_name: str):
    """Saves the user's preferred NFC reader."""
    settings = QSettings(ORGANIZATION_NAME, APP_NAME)
    settings.setValue("hardware/selected_reader", reader_name)