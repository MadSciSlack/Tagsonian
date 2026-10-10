# startup_parameter_test2.py

dummy_payload = {
    "action": "write_request",
    "source_app": "Spoolsonian Test Script",
    "request_id": "spool_tx_20260917_201500",
    "timestamp": "2026-09-17T20:15:00Z",
    "hardware": {
        "writer_device_id": "ACR122U",
        "target_chip_type": "NTAG215",
        "force_4byte_alignment": True  # Changed from true to True
    },
    "schema": {
        "name": "OpenTag3D V2 Spec",
        "id": "opentag3d_v2",
        "version": "2.003",
        "file": "opentag_v2_003.json"
    },
    "payload_data": {
        "core": {
            "tag_version": 2000,
            "material": "PLA",
            "material_mod": "Matte",
            "manufacturer": "Polymaker",
            "color_name": "Navy Blue",
            "color_1": [29, 42, 68, 255],
            "color_2": [0, 0, 0, 0],
            "color_3": [0, 0, 0, 0],
            "color_4": [0, 0, 0, 0],
            "serial": "2026-09-17-00892",
            "sku": "PM-PLA-MAT-NVY",
            "barcode": 123456789012,
            "mfg_date": [2026, 9, 17],
            "mfg_time": [20, 15, 0],
            "diameter": 1750,
            "tolerance": 2,
            "nozzle_diameter": 4,
            "print_temp": 42,
            "min_print_temp": 38,
            "max_print_temp": 45,
            "chamber_temp": 0,
            "bed_temp": 10,
            "min_bed_temp": 8,
            "max_bed_temp": 12,
            "target_vso": 80,
            "min_vso": 20,
            "max_vso": 120,
            "max_dry_temp": 10,
            "dry_time": 6,
            "density": 1240,
            "weight": 1000,
            "empty_spool_weight": 220,
            "measured_length": 330,
            "measured_weight": 1000,
            "spool_core_diameter": 90,
            "td": 118,
            "mfi_temp": 42,
            "mfi_load": 216,
            "mfi_value": 63,
            "data_url": "pfil.us?i=8078-RQSR"
        },
        "web_api": {
            "opentag_version": "2.003",
            "has_ui": True,  # Changed from true to True
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