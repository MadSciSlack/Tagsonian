# models/write_task.py
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time
from typing import Dict, Any, Optional


class TaskSource(Enum):
    IPC = "IPC Request"
    GUI_EDITOR = "GUI Editor"
    GUI_BATCH = "Batch Import"


class TaskStatus(Enum):
    PENDING = "Pending"
    WRITING = "Writing..."
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


@dataclass
class WriteTask:
    title: str
    payload_data: Dict[str, Any]  # Must be scaled/mapped to the target schema_id
    schema_id: str
    target_chip_type: str = "NTAG215"
    source: TaskSource = TaskSource.GUI_EDITOR
    source_app: str = "Tagsonian"
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = TaskStatus.PENDING
    error_message: str = ""
    written_uid: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None