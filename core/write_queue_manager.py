# core/write_queue_manager.py
from PySide6.QtCore import QObject, Signal, QMutex, QMutexLocker
from typing import List, Optional, Dict, Any
from models.write_task import WriteTask, TaskStatus, TaskSource


class WriteQueueManager(QObject):
    task_added = Signal(WriteTask)
    task_removed = Signal(str)
    task_updated = Signal(WriteTask)
    queue_cleared = Signal()
    queue_reordered = Signal()

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._mutex = QMutex()
        self._queue: List[WriteTask] = []

    def enqueue_gui_task(self, title: str, payload_data: dict, schema_id: str, chip_type: str = "NTAG215") -> WriteTask:
        task = WriteTask(
            title=title,
            payload_data=payload_data,
            schema_id=schema_id,
            target_chip_type=chip_type,
            source=TaskSource.GUI_EDITOR,
            source_app="Tagsonian GUI"
        )
        self.enqueue_task(task)
        return task

    def enqueue_ipc_payload(self, ipc_payload: Dict[str, Any]) -> WriteTask:
        header = ipc_payload.get("header", {})
        raw_payload_data = ipc_payload.get("payload_data", {})
        hardware_reqs = ipc_payload.get("hardware", {})
        schema_info = ipc_payload.get("schema", {})

        title = raw_payload_data.get("material_name") or raw_payload_data.get("brand_name") or f"IPC Task ({header.get('source_app', 'External')})"
        schema_id = schema_info.get("schema_id", "opentag_v2_003")
        chip_type = hardware_reqs.get("target_chip_type", "NTAG215")

        # Map and scale payload data to match the target schema prior to queueing
        mapper = Mapper()
        scaled_payload_data = mapper.to_scaled_model(raw_payload_data, schema_id)

        task = WriteTask(
            title=title,
            payload_data=scaled_payload_data,
            schema_id=schema_id,
            target_chip_type=chip_type,
            source=TaskSource.IPC,
            source_app=ipc_payload.get("source_app", "External App")
        )
        self.enqueue_task(task)
        return task

    def enqueue_task(self, task: WriteTask) -> None:
        with QMutexLocker(self._mutex):
            self._queue.append(task)
        self.task_added.emit(task)

    def remove_task(self, task_id: str) -> None:
        with QMutexLocker(self._mutex):
            self._queue = [t for t in self._queue if t.task_id != task_id]
        self.task_removed.emit(task_id)

    def move_task(self, task_id: str, direction: int) -> None:
        with QMutexLocker(self._mutex):
            idx = next((i for i, t in enumerate(self._queue) if t.task_id == task_id), -1)
            if idx == -1:
                return
            new_idx = idx + direction
            if 0 <= new_idx < len(self._queue):
                self._queue[idx], self._queue[new_idx] = self._queue[new_idx], self._queue[idx]
        self.queue_reordered.emit()

    def get_next_pending_task(self) -> Optional[WriteTask]:
        with QMutexLocker(self._mutex):
            for task in self._queue:
                if task.status == TaskStatus.PENDING:
                    return task
        return None

    def mark_task_status(self, task_id: str, status: TaskStatus, error: str = "", written_uid: Optional[str] = None) -> None:
        target_task: Optional[WriteTask] = None
        with QMutexLocker(self._mutex):
            for task in self._queue:
                if task.task_id == task_id:
                    task.status = status
                    task.error_message = error
                    if written_uid:
                        task.written_uid = written_uid
                    target_task = task
                    break
        if target_task:
            self.task_updated.emit(target_task)

    def clear_completed(self) -> None:
        with QMutexLocker(self._mutex):
            self._queue = [t for t in self._queue if t.status in (TaskStatus.PENDING, TaskStatus.WRITING)]
        self.queue_cleared.emit()

    def cancel_all(self) -> None:
        with QMutexLocker(self._mutex):
            for t in self._queue:
                if t.status == TaskStatus.PENDING:
                    t.status = TaskStatus.CANCELLED
        self.queue_cleared.emit()

    def get_all_tasks(self) -> List[WriteTask]:
        with QMutexLocker(self._mutex):
            return list(self._queue)