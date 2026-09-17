# gui/widgets/memory_visualizer.py
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class MemoryVisualizerWidget(QWidget):
    """Renders tag user memory blocks and visually flags memory overlaps in red."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.total_memory_bytes = 504  # Default NTAG215
        self.block_size = 4
        self.fields = []
        self.conflicts = []
        self.setMinimumHeight(120)

    def update_memory_map(self, fields: list[dict], total_bytes: int, conflicts: list[tuple]):
        self.fields = fields
        self.total_memory_bytes = total_bytes
        self.conflicts = conflicts
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Build byte allocation map: 0 = Free, 1 = Used, 2 = Conflict
        byte_map = [0] * self.total_memory_bytes
        
        for field in self.fields:
            start_raw = field.get("start", 0)
            start = int(start_raw, 16) if isinstance(start_raw, str) and start_raw.startswith("0x") else int(start_raw or 0)
            length = int(field.get("length", field.get("max_bytes", 1)))

            for b in range(start, min(start + length, self.total_memory_bytes)):
                byte_map[b] = byte_map[b] + 1

        # Calculate grid cell dimensions
        cols = 32  # 32 bytes per row
        rows = (self.total_memory_bytes + cols - 1) // cols
        
        cell_w = max(4, self.width() // cols)
        cell_h = 10

        for b in range(self.total_memory_bytes):
            r = b // cols
            c = b % cols

            x = c * cell_w
            y = r * (cell_h + 2)

            usage = byte_map[b]
            if usage == 0:
                color = QColor(230, 230, 230)  # Free (Gray)
            elif usage == 1:
                color = QColor(76, 175, 80)    # Used (Green)
            else:
                color = QColor(244, 67, 54)    # Overlap / Conflict (Red)

            painter.setBrush(color)
            painter.setPen(QPen(Qt.black, 0.5))
            painter.drawRect(x, y, cell_w - 1, cell_h)