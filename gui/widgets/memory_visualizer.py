# gui/widgets/memory_visualizer.py
from PySide6.QtCore import QPoint, Qt, QRect
from PySide6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QWidget


class MemoryVisualizerWidget(QWidget):
    """Renders physical NFC memory grid with color-coded region mapping and striped conflict overlays."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.total_memory_bytes = 504  # Default NTAG215 user memory
        self.reserved_header_bytes = 16  # System page memory reserve (Pages 0-3)
        self.fields = []
        self.conflicts = []
        self.view_mode = "draft"  # "draft" or "target_spec"

        # Base Palette
        self.color_free = QColor(235, 238, 240)
        self.color_reserved = QColor(180, 180, 180)  # System / Gray
        self.color_conflict_primary = QColor(229, 57, 53)  # Bright Red
        self.color_conflict_stripe = QColor(183, 28, 28)  # Dark Red Stripe

        # Color-Coded Field Mapping Palette
        self.color_ndef = QColor(255, 214, 0)       # Yellow (NDEF Header / TLV)
        self.color_filament = QColor(33, 150, 243)  # Blue (Filament Core Data)
        self.color_vendor = QColor(156, 39, 176)    # Purple (Vendor Data)
        self.color_custom = QColor(171, 71, 188)    # Bright Purple / Magenta (User Custom Field)
        self.color_default = QColor(76, 175, 80)    # Green (General User Data)

        self.setMinimumHeight(260)

    def set_view_mode(self, mode: str):
        """Switches visualizer view mode between 'draft' and 'target_spec'."""
        if mode in ("draft", "target_spec"):
            self.view_mode = mode
            self.update()

    def update_memory_map(
        self,
        fields: list[dict],
        total_bytes: int = 504,
        conflicts: list[tuple] = None,
        target_binary_buffer: bytearray = None,
    ):
        """Updates internal visualizer state and triggers visual re-render."""
        self.fields = fields or []
        self.total_memory_bytes = total_bytes
        self.conflicts = conflicts or []

        cols = 16
        total_rows = (self.total_memory_bytes + cols - 1) // cols
        calculated_height = 65 + (total_rows * 22)  # Legend + Rows offset
        self.setMinimumHeight(max(260, calculated_height))
        self.update()

    def _get_field_color(self, field: dict) -> QColor:
        """Determines visualizer region rendering color based on field metadata."""
        # 1. Check if the field is a user-added custom field
        if field.get("is_custom", False):
            return self.color_custom

        field_name = str(field.get("name", "")).lower()

        # 2. Check for filament-specific keywords
        if any(kw in field_name for kw in ["filament", "material", "temp", "color", "spool", "vendor"]):
            return self.color_filament

        # 3. Default / General Data fallback
        return self.color_default

    def _create_striped_brush(self, rect: QRect) -> QBrush:
        """Generates a bold red striped brush for rendering layout conflict overlays."""
        stripe_width = 8
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setSpread(QLinearGradient.RepeatSpread)
        
        # Tile alternating red stripes
        gradient.setColorAt(0.0, self.color_conflict_primary)
        gradient.setColorAt(0.4, self.color_conflict_primary)
        gradient.setColorAt(0.41, self.color_conflict_stripe)
        gradient.setColorAt(0.9, self.color_conflict_stripe)
        gradient.setColorAt(0.91, self.color_conflict_primary)
        
        return QBrush(gradient)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # -------------------------------------------------------------
        # 1. Render Top Color Legend
        # -------------------------------------------------------------
        legend_y = 10
        legend_items = [
            ("Free", self.color_free),
            ("NDEF", self.color_ndef),
            ("Filament", self.color_filament),
            ("User Custom", self.color_custom),
            ("General", self.color_default),
            ("Conflict", self.color_conflict_primary),
        ]

        font_legend = QFont("Segoe UI", 8)
        painter.setFont(font_legend)

        curr_x = 10
        for label, color in legend_items:
            painter.setBrush(color)
            painter.setPen(QPen(Qt.black, 0.5))
            painter.drawRect(curr_x, legend_y, 12, 12)

            painter.setPen(Qt.black)
            painter.drawText(curr_x + 16, legend_y + 10, label)
            curr_x += 95

        # View Mode Indicator
        mode_text = f"Mode: {'In-Editing Draft Schema' if self.view_mode == 'draft' else 'Target Spec Translation'}"
        painter.setPen(QPen(QColor(100, 100, 100)))
        painter.drawText(self.width() - 210, legend_y + 10, mode_text)

        # -------------------------------------------------------------
        # 2. Build Allocation Map per Byte from Target Fields
        # -------------------------------------------------------------
        byte_usage = [0] * self.total_memory_bytes
        byte_owner = [None] * self.total_memory_bytes
        byte_colors = [self.color_free] * self.total_memory_bytes

        for idx, field in enumerate(self.fields, start=1):
            if not isinstance(field, dict):
                continue
            start_raw = field.get("start", 0)
            start = (
                int(start_raw, 16)
                if isinstance(start_raw, str) and start_raw.startswith("0x")
                else int(start_raw or 0)
            )
            length = int(field.get("length", field.get("max_bytes", 1)))
            color = self._get_field_color(field)

            for b in range(start, start + length):
                if b < self.total_memory_bytes:
                    byte_usage[b] += 1
                    byte_owner[b] = idx if byte_usage[b] == 1 else "!"
                    if byte_usage[b] == 1:
                        byte_colors[b] = color
                else:
                    # Bytes overflowing chip bounds
                    pass

        # -------------------------------------------------------------
        # 3. Draw Address Rows and Memory Grid
        # -------------------------------------------------------------
        bytes_per_row = 16
        label_margin_left = 135
        cell_w = max(18, (self.width() - label_margin_left - 15) // bytes_per_row)
        cell_h = 16
        start_y = 40

        font_label = QFont("Consolas", 8, QFont.Bold)
        font_box = QFont("Consolas", 7, QFont.Bold)

        total_rows = (self.total_memory_bytes + bytes_per_row - 1) // bytes_per_row

        for r in range(total_rows):
            row_start_byte = r * bytes_per_row
            row_page = row_start_byte // 4
            row_y = start_y + (r * (cell_h + 4))

            # Address & Page Row Label
            painter.setFont(font_label)
            painter.setPen(QColor(80, 80, 80))
            address_str = f"0x{row_start_byte:04X} [Pg {row_page:02d}]:"
            painter.drawText(10, row_y + 12, address_str)

            # Draw Byte Squares
            for c in range(bytes_per_row):
                b = row_start_byte + c
                if b >= self.total_memory_bytes:
                    break

                x = label_margin_left + (c * cell_w) + ((c // 4) * 6)
                rect = QRect(x, row_y, cell_w - 1, cell_h - 1)

                usage = byte_usage[b]
                if usage > 1:
                    # Conflict / Overlap -> Bold Red Stripes
                    painter.setBrush(self._create_striped_brush(rect))
                else:
                    painter.setBrush(byte_colors[b])

                painter.setPen(QPen(Qt.black, 0.5))
                painter.drawRect(rect)

                # Draw Field Index Number Inside Box
                if usage > 0:
                    painter.setFont(font_box)
                    painter.setPen(Qt.white if usage == 1 else Qt.yellow)
                    owner_text = str(byte_owner[b])
                    painter.drawText(rect, Qt.AlignCenter, owner_text)