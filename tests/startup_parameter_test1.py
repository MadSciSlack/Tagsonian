# startup_parameter_test1.py
import json
import sys
import subprocess
import tempfile
from pathlib import Path

def test_spoolsonian_launch():
    dummy_payload = {
        "action": "write_request",
        "source_app": "Spoolsonian Test Script",
        "request_id": "req_test_001",
        "hardware": {
            "writer_device_id": "ACR122U",
            "target_chip_type": "NTAG215"
        },
        "schema": {
            "name": "OpenTag3D V2",
            "file": "opentag_v2_003.json"
        },
        "payload_data": {
            "material": {
                "material_type": "PETG",
                "vendor_name": "TestMaker",
                "brand_color_name": "Test Red"
            },
            "spool": {
                "initial_weight_g": 1000,
                "filament_diameter_mm": 1.75
            }
        }
    }

    temp_dir = Path(tempfile.gettempdir())
    payload_file = temp_dir / "test_write_request.json"
    
    with open(payload_file, "w", encoding="utf-8") as f:
        json.dump(dummy_payload, f, indent=4)

    print(f"Created dummy payload at: {payload_file}")

    main_script = Path(__file__).resolve().parent / "main.py"
    
    # sys.executable uses the virtual environment's Python interpreter
    python_exe = sys.executable 
    
    print(f"Launching Tagsonian: {python_exe} {main_script.name} {payload_file}")
    
    try:
        subprocess.Popen([python_exe, str(main_script), str(payload_file)])
        print("Launch signal sent successfully.")
    except Exception as e:
        print(f"Failed to launch Tagsonian: {e}")

if __name__ == "__main__":
    test_spoolsonian_launch()