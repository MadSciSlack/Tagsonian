# gui/dialogs/write_queue_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt
from core.write_queue_manager import WriteQueueManager
from models.write_task import TaskStatus, WriteTask
from hardware.tap_to_write_worker import TapToWriteWorker


class WriteQueueDialog(QDialog):
    def __init__(self, parent_main_window, queue_manager: WriteQueueManager):
        super().__init__(parent_main_window)
        self.main_window = parent_main_window
        self.queue_mgr = queue_manager
        self.tap_worker: TapToWriteWorker | None = None

        self.setWindowTitle("Tagsonian Write Spooler Queue")
        self.resize(720, 480)
        # Option C: Floating non-modal window model
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)

        self.setup_ui()
        self.connect_signals()
        self.refresh_table()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header Bar & Mode Toggles
        header_layout = QHBoxLayout()
        self.lbl_status = QLabel("Queue Idle")
        self.lbl_status.setStyleSheet("font-weight: bold; color: #2b78e4;")
        header_layout.addWidget(self.lbl_status)
        header_layout.addStretch()

        self.chk_always_on_top = QCheckBox("Keep On Top")
        self.chk_always_on_top.toggled.connect(self.toggle_on_top)
        header_layout.addWidget(self.chk_always_on_top)

        layout.addLayout(header_layout)

        # Spooler Items Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Status", "Source", "Title / Material", "Schema", "Error / Details"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)

        # Controls Toolbar
        btn_layout = QHBoxLayout()

        self.btn_start_tap = QPushButton("Start Tap-to-Write")
        self.btn_start_tap.setStyleSheet("font-weight: bold; background-color: #16a34a; color: white;")
        self.btn_start_tap.clicked.connect(self.toggle_tap_to_write)

        self.btn_move_up = QPushButton("▲ Move Up")
        self.btn_move_up.clicked.connect(lambda: self.move_selected(-1))

        self.btn_move_down = QPushButton("▼ Move Down")
        self.btn_move_down.clicked.connect(lambda: self.move_selected(1))

        self.btn_remove = QPushButton("Remove Task")
        self.btn_remove.clicked.connect(self.remove_selected)

        self.btn_clear = QPushButton("Clear Completed")
        self.btn_clear.clicked.connect(self.queue_mgr.clear_completed)

        btn_layout.addWidget(self.btn_start_tap)
        btn_layout.addWidget(self.btn_move_up)
        btn_layout.addWidget(self.btn_move_down)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addWidget(self.btn_clear)

        layout.addLayout(btn_layout)

    def connect_signals(self):
        self.queue_mgr.task_added.connect(lambda _: self.refresh_table())
        self.queue_mgr.task_removed.connect(lambda _: self.refresh_table())
        self.queue_mgr.task_updated.connect(lambda _: self.refresh_table())
        self.queue_mgr.queue_cleared.connect(self.refresh_table)
        self.queue_mgr.queue_reordered.connect(self.refresh_table)

    def toggle_on_top(self, checked: bool):
        if checked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()

    def refresh_table(self):
        tasks = self.queue_mgr.get_all_tasks()
        self.table.setRowCount(len(tasks))

        for row, task in enumerate(tasks):
            item_status = QTableWidgetItem(task.status.value)
            if task.status == TaskStatus.COMPLETED:
                item_status.setForeground(Qt.green)
            elif task.status == TaskStatus.FAILED:
                item_status.setForeground(Qt.red)
            elif task.status == TaskStatus.WRITING:
                item_status.setForeground(Qt.blue)

            self.table.setItem(row, 0, item_status)
            self.table.setItem(row, 1, QTableWidgetItem(task.source.value))
            self.table.setItem(row, 2, QTableWidgetItem(task.title))
            self.table.setItem(row, 3, QTableWidgetItem(task.schema_id))
            
            detail_msg = task.error_message if task.error_message else (f"UID: {task.written_uid}" if task.written_uid else "")
            self.table.setItem(row, 4, QTableWidgetItem(detail_msg))
            self.table.item(row, 0).setData(Qt.UserRole, task.task_id)

    def move_selected(self, direction: int):
        row = self.table.currentRow()
        if row < 0:
            return
        task_id = self.table.item(row, 0).data(Qt.UserRole)
        self.queue_mgr.move_task(task_id, direction)

    def remove_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        task_id = self.table.item(row, 0).data(Qt.UserRole)
        self.queue_mgr.remove_task(task_id)

    def toggle_tap_to_write(self):
        if self.tap_worker and self.tap_worker.isRunning():
            self.tap_worker.stop()
            self.tap_worker.wait(2000)
            self.tap_worker = None
            self.btn_start_tap.setText("Start Tap-to-Write")
            self.btn_start_tap.setStyleSheet("font-weight: bold; background-color: #16a34a; color: white;")
            self.lbl_status.setText("Tap-to-Write Paused.")
        else:
            self.tap_worker = TapToWriteWorker(self.queue_mgr, self.main_window, self)
            self.tap_worker.status_changed.connect(self.lbl_status.setText)
            self.tap_worker.start()
            self.btn_start_tap.setText("Pause Tap-to-Write")
            self.btn_start_tap.setStyleSheet("font-weight: bold; background-color: #dc2626; color: white;")

    def closeEvent(self, event):
        if self.tap_worker and self.tap_worker.isRunning():
            self.tap_worker.stop()
            self.tap_worker.wait(1000)
        event.accept()