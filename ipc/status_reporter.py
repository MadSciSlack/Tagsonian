# ipc/status_reporter.py
import json
import logging
from typing import Dict, Any, Optional
from PySide6.QtNetwork import QLocalSocket

logger = logging.getLogger(__name__)


class IPCStatusReporter:
    """
    Handles sending asynchronous status payload messages back across the
    QLocalSocket connection to Spoolsonian or external IPC callers.
    """

    @staticmethod
    def send_status(
        socket: Optional[QLocalSocket],
        status: str,
        request_id: Optional[str] = None,
        uid: Optional[str] = None,
        error_message: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Formats and transmits an asynchronous JSON return payload over the socket.
        Status types: 'write_success', 'error_occurred', 'canceled', 'queued', 'in_progress'
        """
        if not socket or socket.state() != QLocalSocket.LocalSocketState.ConnectedState:
            logger.warning("[IPCStatusReporter] Socket is not connected. Unable to send status.")
            return False

        payload = {
            "event": "write_status_response",
            "status": status,
            "request_id": request_id,
            "uid": uid,
            "error_message": error_message,
        }

        if extra_data:
            payload["details"] = extra_data

        try:
            raw_bytes = (json.dumps(payload) + "\n").encode("utf-8")
            socket.write(raw_bytes)
            socket.flush()
            logger.info(f"[IPCStatusReporter] Sent status '{status}' (Req ID: {request_id})")
            return True
        except Exception as e:
            logger.error(f"[IPCStatusReporter] Failed to send status back over socket: {e}")
            return False