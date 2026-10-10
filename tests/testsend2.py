# testsend.py
import sys
import json
from PySide6.QtCore import QCoreApplication
from PySide6.QtNetwork import QLocalSocket

SOCKET_NAME = "Tagsonian_IPC_Server"

# IPC payload sending human-readable values aligned with FormatMapper.flatten_opentag_v2
dummy_payload = {
    "action": "write_request",
    "source_app": "Spoolsonian Test Script",
    "request_id": "spool_tx_20260917_201500",
    "timestamp": "2026-09-17T20:15:00Z",
    "hardware": {
        "writer_device_id": "ACR122U",
        "target_chip_type": "NTAG215",
        "force_4byte_alignment": True
    },
    "schema": {
        "name": "OpenTag3D V2 Spec",
        "id": "opentag3d_v2",
        "version": "2.003",
        "file": "opentag_v2_003.json"
    },
    "payload_data": {
        "core": {
            "Tag Version": 2.0,
            "Base Material Name": "PLA",
            "Material Modifiers": "Pro",
            "Filament Manufacturer": "Polymaker",
            "Color Name": "Blach",
            "Color 1 Hex": [15, 18, 15, 255],
            "Color 2 Hex": [0, 0, 0, 0],
            "Color 3 Hex": [0, 0, 0, 0],
            "Color 4 Hex": [0, 0, 0, 0],
            "Serial Number / Batch ID": "2026-09-17-00892",
            "SKU": "PM-PLA-MAT-NVY",
            "Barcode": 123456789012,
            "Manufacture Date": "2026-09-17",
            "Manufacture Time": "20:15:00",
            "Filament Diameter": 1.75,
            "Target Print Temperature": 210,
            "Minimum Print Temperature": 190,
            "Maximum Print Temperature": 220,
            "Target Bed Temperature": 55,
            "Minimum Bed Temperature": 40,
            "Maximum Bed Temperature": 60,
            "Target Volumetric Speed": 12,
            "Minimum Volumetric Speed": 8,
            "Maximum Volumetric Speed": 16,
            "Dry Time": 6,
            "Density": 1.23,
            "Target Weight": 1000,
            "Empty Spool Weight": 140,
            "Measured Filament Length": 338,
            "Measured Filament Weight": 1000,
            "Spool Core Diameter": 55,
            "Transmission Distance (TD)": 0.3,
            "Online Data URL": "pfil.us?i=8078-RQSR"
        },
        "web_api": {
            "opentag_version": "2.003",
            "has_ui": True,
            "price": {
                "us": "$24.99",
                "eu": "€22.99",
                "global": "$24.99"
            },
            "product_url": {
                "us": ["https://polymaker.com/product/polyterra-pla/"]
            },
            "product_photos": [
                "https://polymaker.com/wp-content/uploads/navy_blue_spool.png"
            ],
            "qa_status": "Pass",
            "notes": "Batch QA verified on 2026-09-17. Store in cool, dry location."
        }
    }
}

app = QCoreApplication(sys.argv)

socket = QLocalSocket()
print(f"[Test Sender] Attempting connection to: {SOCKET_NAME}")
socket.connectToServer(SOCKET_NAME)

if socket.waitForConnected(2000):
    print("[Test Sender] Connected to server successfully!")
    payload_bytes = json.dumps(dummy_payload).encode("utf-8")
    socket.write(payload_bytes)
    if socket.waitForBytesWritten(2000):
        print(f"[Test Sender] Successfully sent {len(payload_bytes)} bytes.")
    else:
        print(f"[Test Sender] Write error: {socket.errorString()}")
    socket.disconnectFromServer()
else:
    print(f"[Test Sender] Connection failed: {socket.errorString()}")