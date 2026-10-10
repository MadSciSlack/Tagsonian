# hardware/reader_factory.py
import config
from smartcard.System import readers
from hardware.acr122u import ACR122UThread
from hardware.acr1552u import ACR1552UThread

def get_reader_thread(mode="read", payload=None):
    """Instantiates the correct NFC worker thread based on persistent settings and connected hardware."""
    preferred = config.get_selected_reader()

    if preferred == "ACR122U":
        return ACR122UThread(mode=mode, payload=payload)
    elif preferred == "ACR1552U":
        return ACR1552UThread(mode=mode, payload=payload)

    # Fallback to Auto-Detect scanning PC/SC bus
    r_list = readers()
    for r in r_list:
        if "1552" in str(r):
            return ACR1552UThread(mode=mode, payload=payload)
        elif "122" in str(r):
            return ACR122UThread(mode=mode, payload=payload)

    # Default fallback
    return ACR122UThread(mode=mode, payload=payload)