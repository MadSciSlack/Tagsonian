# main.py
import sys
import json
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtNetwork import QLocalServer, QLocalSocket

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from gui.main_window import MainWindow

SOCKET_NAME = "Tagsonian_IPC_Server"


def parse_request_arg():
    """Parses incoming JSON payload passed via command-line arguments."""
    for arg in sys.argv[1:]:
        if arg.startswith("--write-request="):
            json_str = arg.split("=", 1)[1]
            try:
                return json.loads(json_str)
            except Exception as e:
                print(f"[IPC Init] Failed to parse inline JSON argument: {e}")
        elif arg.endswith(".json") and Path(arg).exists():
            try:
                with open(arg, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[IPC Init] Failed to load JSON file argument: {e}")
    return None


def main():
    app = QApplication(sys.argv)

    # 1. Forward payload to existing Tagsonian instance if running
    socket = QLocalSocket()
    socket.connectToServer(SOCKET_NAME)

    if socket.waitForConnected(500):
        print("[IPC Client] Active instance detected. Forwarding payload...")
        request_data = parse_request_arg()
        if request_data:
            payload_bytes = (json.dumps(request_data) + "\n").encode("utf-8")
            socket.write(payload_bytes)
            socket.waitForBytesWritten(1000)

            # Listen for asynchronous return status responses from primary server
            while socket.waitForReadyRead(5000):
                resp = socket.readLine().data().decode("utf-8").strip()
                if resp:
                    print(f"[IPC Client] Return Status Event: {resp}")
                    try:
                        resp_obj = json.loads(resp)
                        if resp_obj.get("status") in ("write_success", "error_occurred", "canceled"):
                            break
                    except Exception:
                        pass
        else:
            print("[IPC Client] No launch request payload provided.")
        socket.disconnectFromServer()
        sys.exit(0)

    # 2. No active instance found — Initialize primary IPC server
    print("[IPC Server] Starting primary server listener...")
    QLocalServer.removeServer(SOCKET_NAME)

    server = QLocalServer()
    if server.listen(SOCKET_NAME):
        print(f"[IPC Server] Listening on socket: {SOCKET_NAME}")
    else:
        print(f"[IPC Server] Critical: Failed to listen on socket: {server.errorString()}")

    window = MainWindow()
    queue_manager = window.queue_manager  # Unified queue manager bound to main window

    def handle_new_connection():
        print("[IPC Server] Client connected...")
        client_socket = server.nextPendingConnection()
        if client_socket:
            if client_socket.waitForReadyRead(2000):
                raw_data = client_socket.readLine().data().decode("utf-8").strip()
                if raw_data:
                    try:
                        payload = json.loads(raw_data)
                        print(f"[IPC Server] Enqueuing write request from '{payload.get('source_app', 'Unknown')}'")

                        queue_manager.enqueue_ipc_payload(payload)
                        window.handle_external_write_request(queue_manager)
                    except Exception as e:
                        print(f"[IPC Server] Error parsing payload JSON: {e}")
                        client_socket.disconnectFromServer()

    server.newConnection.connect(handle_new_connection)

    # Process initial CLI request payload if provided at cold launch
    initial_request = parse_request_arg()
    if initial_request:
        queue_manager.enqueue_ipc_payload(initial_request)
        window.handle_external_write_request(queue_manager)

    window.show()

    def cleanup_ipc_server():
        print("[IPC Server] Cleaning up socket and queue manager...")
        queue_manager.cancel_all()
        if server.isListening():
            server.close()
        QLocalServer.removeServer(SOCKET_NAME)

    app.aboutToQuit.connect(cleanup_ipc_server)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()