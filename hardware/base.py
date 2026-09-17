# hardware/base.py
from abc import ABCMeta, abstractmethod
from PySide6.QtCore import QThread, Signal


class QABCMeta(type(QThread), ABCMeta):
    """Combined metaclass resolving conflict between QThread (Shiboken) and ABCMeta."""
    pass


class BaseNFCThread(QThread, metaclass=QABCMeta):
    """Abstract worker thread for NFC hardware operations."""

    tag_detected = Signal(bytearray)
    write_success = Signal()
    error_occurred = Signal(str)

    def __init__(self, mode="read", payload=None):
        super().__init__()
        self.mode = mode  # "read" or "write"
        self.payload = payload
        self._running = True

    def stop(self):
        self._running = False

    @abstractmethod
    def run(self):
        pass