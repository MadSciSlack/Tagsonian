# hardware/chip_profiles.py

CHIP_PROFILES = {
    "NTAG213": {
        "display_name": "NTAG213",
        "total_user_bytes": 144,
        "block_size_bytes": 4,
        "standard": "ISO/IEC 14443-A",
    },
    "NTAG215": {
        "display_name": "NTAG215",
        "total_user_bytes": 504,
        "block_size_bytes": 4,
        "standard": "ISO/IEC 14443-A",
    },
    "NTAG216": {
        "display_name": "NTAG216",
        "total_user_bytes": 888,
        "block_size_bytes": 4,
        "standard": "ISO/IEC 14443-A",
    },
    "ST25TN01K": {
        "display_name": "ST25TN01K",
        "total_user_bytes": 128,
        "block_size_bytes": 4,
        "standard": "ISO/IEC 15693",
    },
    "ST25TN02K": {
        "display_name": "ST25TN02K",
        "total_user_bytes": 256,
        "block_size_bytes": 4,
        "standard": "ISO/IEC 15693",
    },
}