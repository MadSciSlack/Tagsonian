Tagsonian System Architecture & Specification Notebook

1. Core Architectural Paradigms & Governance
- Schemas as Single Source of Truth (SSOT): All bit/byte offsets, data types, field names, scaling factors, units, tooltips, and validation boundaries are strictly defined in schemas/*.json. UI forms, binary parsers, binary writers, and validation logic are fully dynamically generated and driven by the active schema JSON. Hardcoding field names or offsets in Python code is explicitly prohibited.
- official_spec_lock Standard: Official standards (e.g., opentag_v2_003.json) set "official_spec_lock": true in their root schema definition. When official_spec_lock is true, the application locks field editing, field additions, field deletions, bit-offset modifications, and scaling updates to prevent accidental mutation of published specification standards.
- Schema Cloning Workflow: To modify or extend an official locked schema, the UI provides a "Clone Schema" action. Cloning creates an editable draft copy (e.g., opentag_v2_003_custom.json), clears "official_spec_lock", updates internal metadata GUIDs (automatically generating a unique RFC 4122 compliant UUID v4 string to prevent collision conflicts in the mapper registry), and opens the schema in an editable state inside the Standard Editor tabs.
- Pipeline Isolation Rule: Native schema parsers (OpenTag, OpenPrintTag) must operate entirely self-contained. Binary decoders and parsers must strictly resolve fields to their canonical display names and must never inject cross-schema database IDs, snake_case aliases, or invoke cross-schema translation mappers during a direct file read.
- Single-Responsibility Principle for Mappers: Directional format mappers and their subclasses are strictly downstream orchestrators invoked exclusively when converting between different schema standards. They must remain completely isolated and dormant during native read, parse, or write workflows for a single schema.

2. Ingestion, Reading & Integration Pipelines
- File Import & General Ingestion Pipeline: Input Formats: Raw .json files, .bin NDEF payloads, or raw dictionary payloads. Ingestion Flow: JSONImporter or raw loader reads data directly into self.original_raw_model. Data is kept in its native incoming state (unscaled or scaled depending on source) prior to mapping.
- Hardware Read Pipeline (NFC Tag): Input: Physical NFC tag memory array over reader interface. Execution Flow: BaseNFCReader worker thread captures raw byte memory array into self.raw_memory_buffer. OpenTagParser.extract_ndef_payload() locates NDEF records, parses headers, and extracts MIME type and raw payload bytes. OpenTagParser.parse() uses the active SSOT schema to unpack binary fields (applying byte offsets, bit masks, and string decodings) and populates self.original_raw_model.
- Spoolsonian IPC & Cross-Process Integration: Tagsonian acts as both an IPC server and a deep-link target for Spoolsonian. 
┌─────────────────┐      1. CLI Launch / IPC Socket      ┌─────────────────┐
│                 ├─────────────────────────────────────►│                 │
│   Spoolsonian   │                                      │    Tagsonian    │
│  (Slicer/App)   │◄─────────────────────────────────────┤  (NFC Manager)  │
└─────────────────┘       2. Response / Write Status     └─────────────────┘
- CLI Launch Mode: Spoolsonian can launch Tagsonian via command line passing an external payload argument: python main.py --write-request <path_to_payload.json>. Tagsonian detects the argument on startup, bypasses standard blank initialization, loads the payload, and presents the write confirmation dialog immediately.
- IPC Socket Listener (Local IPC Server): Tagsonian runs an asynchronous IPC socket server listening for incoming JSON write requests from running instances of Spoolsonian. When a write request arrives, handle_external_write_request(payload_dict) validates the incoming payload against the active SSOT schema model to block malformed data, then manages UI focus and modal presentation: unminimizes, raises, and focuses the main Tagsonian window (self.show(), self.raise_(), self.activateWindow()), and opens the WriteRequestDialog modal displaying incoming Spoolsonian spool data alongside target tag memory compatibility prior to prompting the user for confirmation.

3. Translation & Data Normalization Pipeline
- Translation Decoupling: Translation is completely decoupled from raw parsing and ingestion.
- Translation Engine (`mappings/mapper.py`): Input: self.original_raw_model (Format-native dictionary). Processor: Central orchestrator and registry dispatcher routing requests to directional submodules (`mappings/directional/`). Configuration: Uses mapping configuration definitions to map source-to-field key aliases. Scaling Normalization: Converts binary scaled integers (e.g., temperature 2100 with $0.1$ scale) to human-readable floats (210.0°C) for presentation. Output: self.common_data_model structured according to the active target schema. Diagnostic Coverage Logging: Generates debug_mapping_coverage() reports to track mapped vs. unmapped fields, missing keys, and dropped telemetry.

4. Egress, Export & Writing Pipelines
- File Export Pipeline: Input: self.common_data_model (UI state). Processing: JSON Export serializes normalized data directly to formatted JSON; TXT Export generates text reports containing formatted key-value pairs combined with raw memory hex dumps; Binary Export (.bin) uses OpenTagWriter.encode() to pack current model values directly into NDEF-compliant binary dumps based on SSOT schema byte offsets.
- Hardware Write Pipeline: Input: self.common_data_model. Execution Flow: 
  1. Directional mappers (via `mappings/mapper.py` and `BaseMapper` contracts) convert user UI floats/doubles into scaled integer bit representations using target schema scaling parameters.
  2. OpenTagWriter.encode() packs scaled values, string headers, and NDEF headers into a bytearray binary image matching schema bit offsets.
  3. BaseNFCReader.validate_chip_for_spec() validates that the packed payload size fits within target chip constraints (e.g., NTAG215's 504-byte user memory limit).
  4. Asynchronous write thread (`get_reader_thread(mode="write")`) programs memory pages block-by-block.

5. GUI Hierarchy & Component Structure
MainWindow (QMainWindow)
 │
 ├── Header Bar (Detected Spec Label, Settings Button, Target Spec Combo)
 ├── QTabWidget
 │    ├── Tab 1: TagEditorTab (TagEditorTab Dynamic Form & Field Table)
 │    ├── Tab 2: RawInspectorTab (Hex Dump & Parsed NDEF Structures)
 │    ├── Tab 3: StandardEditorTab (Schema Standard Editor - V1)
 │    └── Tab 4: StandardEditorV2Tab (Advanced Schema Editor, Field Builder & Memory Visualizer - V2)
 └── Bottom Action Bar (Read NFC, Write NFC, Import JSON, Export File, Clear)
- Key Tab Modules:
    * Tag Editor Tab (TagEditorTab): Renders dynamic UI widgets (spinboxes, text fields, dropdowns) based strictly on field definitions in the target schema with real-time validation.
    * Raw Data Inspector (RawInspectorTab): Displays raw NDEF memory hex dumps alongside decoded structure interpretations as a read-only raw memory inspection interface, completely decoupled from visualizer widgets.
    * Standard Editor V1 & V2 (StandardEditorTab, StandardEditorV2Tab): Act as visual schema builders for editing, creating, and cloning schemas while enforcing official_spec_lock rules. StandardEditorV2Tab serves as the host container for the Memory Visualizer, managing state toggles between "Target Spec / Schema" (translated layout) and active "in-editing" custom draft schemas without losing uncommitted workspace edits.
- Memory Visualizer Details & Requirements:
    * Grid Rendering Engine: Renders physical NFC memory blocks/pages as a continuous visual grid (e.g., 4-byte pages for NTAG215).
    * Color-Coded Field Mapping: Highlights byte regions based on schema assignment (e.g., NDEF Header = Yellow, UID/Manufacturer = Gray, Filament Data = Blue, Vendor Custom = Purple).
    * Spec & Draft Toggle: Allows switching view modes between "Target Spec / Schema" and "In-Editing Draft Schema" while maintaining full preservation of draft form state.
    * Conflict & Overflow Overlay: Visually highlights overlapping field offset definitions or payloads exceeding physical chip boundaries in bold red stripes based on target layout specs.
    * Layout-Focused Independence: Functions independently of raw byte inspection values or hex dumps rendered in RawInspectorTab.

6. Hardware Architecture & Driver Hierarchy
BaseNFCReader (Abstract Reader Interface)
 │
 ├── ACR1552UReader (PCSC / SmartCard / PySCard API)
 ├── ACR122UReader (PCSC / SmartCard / PySCard API)
 └── DummyReader (Hardware Mock / Automated Testing)
- Thread Handling (`get_reader_thread`): All NFC operations run off the main GUI thread using PySide6 QThread workers. Emits signals (tag_detected, write_success, error_occurred) to keep UI fully responsive during hardware polling. If a hardware timeout, PCSC communication failure, or unexpected exception occurs during background execution, the worker thread cleanly releases active device locks and emits an error_occurred(str) signal back to the main thread to prevent UI deadlocks.
- Hardware Validation Rules: Hardware reader checks chip signatures (UID, ATQA, SAK) to identify hardware targets (NTAG213, NTAG215, NTAG216). Blocks write operations if payload byte length exceeds physical chip capacities prior to sending write commands over wire.