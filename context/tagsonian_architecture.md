TAGSONIAN SYSTEM ARCHITECTURE & SPECIFICATION NOTEBOOK

1. CORE ARCHITECTURAL PARADIGMS & IMMUTABILITY RULES
- Architectural Scope & System Boundaries:
  * Tagsonian: The core standalone desktop engine, GUI application, SSOT schema parser, translation pipeline, and hardware reader interface responsible for editing, encoding, and programming NFC tags directly.
  * Spoolsonian: The broader parent inventory management ecosystem. Spoolsonian interacts with Tagsonian asynchronously via local IPC server endpoints and external queue payloads, leveraging Tagsonian's hardware writing pipelines and safety confirmation modals (write_file_request_dialog.py) to execute batch inventory updates.
  - IPC Payload Validation Gate: Incoming write requests and queue payloads received from Spoolsonian via local IPC server endpoints must be validated against the active SSOT schema model prior to opening write_file_request_dialog.py to ensure malformed or out-of-bounds data is blocked before reaching human confirmation modals.
- Schemas as Single Source of Truth (SSOT): All bit/byte offsets, data types, field names, scaling factors, units, tooltips, and validation boundaries are strictly defined in schemas/*.json. UI forms, binary parsers, binary writers, and validation logic are fully dynamically generated and driven by the active schema JSON. Hardcoding field names or offsets in Python code is explicitly prohibited.
- Application-Wide Immutability of Official Schemas: Official standards (e.g., opentag_v2_003.json) include "official_spec_lock": true in their root schema definition.
STRICT IMMUTABILITY RULE: Any schema marked with "official_spec_lock": true MUST remain strictly immutable across every single module in the application (UI editors, parsers, mappers, and IPC handlers).
No module or feature inside Tagsonian is permitted to mutate, override, delete, or append fields to an official locked schema file or its in-memory instance. UI field editing, field additions, field deletions, bit-offset modifications, and scaling updates are hard-disabled globally whenever an official schema is loaded.
- Schema Cloning Workflow: To modify or extend an official locked schema, the UI provides an explicit "Clone Schema" action. Cloning creates a separate, editable draft copy (e.g., opentag_v2_003_custom.json), sets "official_spec_lock": false, updates internal metadata GUIDs, and opens the new draft in an editable state inside the Standard Editor tabs.
- Schema Cloning UUID Uniqueness: When a custom draft schema is generated via the cloning workflow, the system must automatically generate a unique RFC 4122 compliant UUID v4 string for its internal metadata identifier (metadata.guid) to prevent collision conflicts with the official parent schema when loaded into the mapper registry.
- Pipeline Isolation Rule: Native schema parsers (OpenTag, OpenPrintTag) must operate entirely self-contained. Binary decoders and parsers must strictly resolve fields to their canonical display names and must never inject cross-schema database IDs, snake_case aliases, or invoke cross-schema translation mappers during a direct file read.
- Single-Responsibility Principle for Mappers: Directional format mappers (FormatMapper and its subclasses) are strictly downstream orchestrators invoked exclusively when converting between different schema standards. They must remain completely isolated and dormant during native read, parse, or write workflows for a single schema.




2. DATA INGESTION & HARDWARE READING PIPELINES
- File Import Pipeline: Input Formats : Raw .json files, .bin NDEF payloads, or raw dictionary payloads. Ingestion Flow: JSONImporter or raw loader reads data directly into self.original_raw_model. Data is kept in its native incoming state (unscaled or scaled depending on source) prior to mapping.
- Hardware Read Pipeline (NFC Tag): Input : Physical NFC tag memory array over reader interface. Execution Flow: 1. BaseNFCReader worker thread captures raw byte memory array into self.raw_memory_buffer. 2. OpenTagParser.extract_ndef_payload() locates NDEF records, parses headers, and extracts MIME type and raw payload bytes. 3. OpenTagParser.parse() uses the active SSOT schema to unpack binary fields (applying byte offsets, bit masks, and string decodings) and populates self.original_raw_model.

3. TRANSLATION & DATA NORMALIZATION PIPELINE
Translation is decoupled from raw parsing and ingestion and organized into modular single-responsibility components:
- Modular Translation Engine (`mappings/`):
  * Orchestrator (`mappings/mapper.py`): Acts as the central registry and pipeline dispatcher, coordinating schema selection and routing input models to the correct directional translator.
  * Base Contract (`mappings/base.py`): Defines the abstract base mapper interface enforcing standardized scaling normalization, type conversions, and coverage metrics across all translators.
  * Directional Submodules (`mappings/directional/`): Self-contained translation modules handle specific schema pairs (e.g., OpenPrintTag <-> OpenTag V2, opentag_to_openspool.py, opentag_to_nfctools.py) independently to prevent regression bugs.
  * Diagnostics & Scaling Norm.: Converts binary scaled integers (e.g., temperature 2100 with 0.1 scale) to human-readable floats (210.0°C) for presentation. Each directional module integrates with `debug_mapping_coverage()` to output granular tracking of mapped versus unmapped fields, missing keys, and dropped telemetry.
  *  Value Scaling Ownership & Pipeline Boundaries: Value scaling responsibilities are strictly partitioned across pipeline layers to prevent double-scaling errors:
    *  Native Serialization Layer (Encoders & Parsers): Native encoders and parsers hold exclusive ownership of native binary scaling defined in schema JSON files (schemas/*.json). Encoders convert unscaled application floating-point values into scaled binary integers during byte array packing. Parsers convert scaled binary integers from tag memory into unscaled floating-point values during tag ingestion.
    *  Directional Translation Layer (Mappers): Directional mappers (mappings/directional/*) manage cross-specification unit transformations and field key translation between distinct schema standards. Directional translators operate exclusively on unscaled data inputs and produce unscaled target models. Directional translators must never execute native schema binary integer scaling that target native encoders perform.
    *  Orchestration Layer (Central Mapper Dispatcher): The central mapper dispatcher (mappings/mapper.py) coordinates cross-spec routing. Single-schema native workflows completely bypass directional mappers to pass unscaled internal models directly to native encoders or parsers.


4. EGRESS, EXPORT & HARDWARE WRITING PIPELINES
- File Export Pipeline: Input : self.common_data_model (UI state). Processing :
    * JSON Export : Serializes normalized data directly to formatted JSON.
    * TXT Export : Generates text reports containing formatted key-value pairs combined with raw memory hex dumps.
    * Binary Export: Uses OpenTagWriter.encode() to pack current model values directly into NDEF-compliant binary dumps based on SSOT schema byte offsets.
- Hardware Write Pipeline: Input : self.common_data_model. Execution Flow: 
  a. Directional mappers (via mappings/mapper.py and BaseMapper contracts) convert user UI floats/doubles into scaled integer bit representations using target schema scaling parameters.
  b. OpenTagWriter.encode() packs scaled values, string headers, and NDEF headers into a bytearray binary image matching schema bit offsets.
  c. BaseNFCReader.validate_chip_for_spec() validates that the packed payload size fits within target chip constraints (e.g., NTAG215's 504-byte user memory limit).
  d. Asynchronous write thread (get_reader_thread(mode="write")) programs memory pages block-by-block.

5. GUI HIERARCHY & COMPONENT STRUCTURE
MainWindow (QMainWindow)
├── Header Bar (Detected Spec Label, Settings Button, Target Spec Combo)
├── QTabWidget
│    ├── Tab 1: TagEditorTab (Dynamic Form & Field Table)
│    ├── Tab 2: RawInspectorTab (Hex Dump & Parsed NDEF Structures)
│    ├── Tab 3: StandardEditorTab (Schema Standard Editor - V1)
│    └── Tab 4: StandardEditorV2Tab (Advanced Schema Editor, Field Builder & Memory Visualizer - V2)
└── Bottom Action Bar (Read NFC, Write NFC, Import JSON, Export File, Clear)
- Key Tab Modules:
    * Tag Editor Tab (TagEditorTab): Renders dynamic UI widgets (spinboxes, text fields, dropdowns) based strictly on field definitions in the target schema. Performs real-time validation checking field ranges and byte-length limits.
    * Raw Data Inspector (RawInspectorTab): Displays raw NDEF memory hex dumps alongside decoded structure interpretations as a read-only raw memory inspection interface, completely decoupled from layout visualizer widgets.
    * Standard Editors (StandardEditorTab, StandardEditorV2Tab): Visual schema builders for editing, creating, and cloning schemas. StandardEditorV2Tab serves as the host container for the Memory Visualizer and manages dual-view toggling between Target Schema translation layouts and active "in-editing" draft schemas while preserving active edit states. Enforces global official_spec_lock rules.
- Memory Visualizer Details & Requirements:
    * Grid Rendering Engine : Renders physical NFC memory blocks/pages as a continuous visual grid (e.g., 4-byte pages for NTAG215).
    * Color-Coded Mapping : Highlights byte regions based on schema assignment (NDEF Header = Yellow, UID/Manufacturer = Gray, Filament Data = Blue, Vendor Custom = Purple).
    * Spec & Draft Toggle: Allows switching view modes between "Target Spec / Schema" (translated data layout) and "In-Editing Draft Schema" without losing uncommitted user changes in the draft workspace.
    * Layout Validation & Conflict Overlay : Validates dynamic data layouts to verify that translation pipelines produce zero field collisions or boundary overlaps. Highlights overlapping field offset definitions or payloads exceeding physical chip boundaries in bold red stripes.
    * Independence from Raw Inspector: Operates strictly on target schema specifications and translated layout structures, completely independent of raw binary values or hex dumps rendered in RawInspectorTab.

6. HARDWARE ARCHITECTURE & DRIVER HIERARCHY
BaseNFCReader (Abstract Reader Interface)
├── ACR1552UReader (PCSC / SmartCard / PySCard API)
├── ACR122UReader (PCSC / SmartCard / PySCard API)
└── DummyReader (Hardware Mock / Automated Testing)
- Thread Handling (get_reader_thread): All NFC operations run off the main GUI thread using PySide6 QThread workers. Emits signals (tag_detected, write_success, error_occurred) to keep the UI fully responsive during hardware polling.
- Hardware Validation Rules: Hardware reader checks chip signatures (UID, ATQA, SAK) to identify hardware targets. Blocks write operations if payload byte length exceeds physical chip capacities prior to sending write commands over the wire.
- Error Propagation & Exception Handling: If a hardware timeout, PCSC communication failure, or unexpected exception occurs during background QThread execution, the worker thread must catch the exception, cleanly release any active device transaction locks, and emit a standardized error_occurred(str) signal back to the main GUI thread to maintain application responsiveness and prevent UI deadlocks.


7. MODULE CATALOG & OPERATIONAL SCOPE SPECIFICATIONS

- Root Configuration & Application Entry Points
  * `config.py` - Global Configuration
    - Module Purpose: Manages global application constants, environment overrides, and file system path resolutions.
    - Input & Source: Environment variables, default constant definitions, and startup arguments.
    - Output & Handoff: Exports path configurations and global constants to runtime modules (`main.py`, `hardware/`).
    - Conversions & Transformations: Resolves relative system paths into absolute runtime file paths.
    - Validation & Governance Gates: Verifies that core project directories (`schemas/`, `mappings/`) exist prior to application launch.
  * `main.py` - Application Entry Point & Server
    - Module Purpose: Initializes the PySide6 application lifecycle, sets up IPC server endpoints, and launches the main window.
    - Input & Source: CLI startup arguments and incoming IPC socket messages from running instances of Spoolsonian.
    - Output & Handoff: Instantiates the PySide6 event loop, initializes `MainWindow`, and starts asynchronous IPC listener threads.
    - Conversions & Transformations: Translates raw external CLI/IPC payloads into application initialization triggers.
    - Validation & Governance Gates: Validates startup environment states and verifies that required SSOT schema files are accessible before opening windows.
  * `nfc_reader.py` - Core Reader Coordinator
    - Module Purpose: Acts as the high-level coordination wrapper unifying background reader threads and application event loops.
    - Input & Source: Hardware signal emissions from active reader threads (`acr1552u_thread.py`) and UI commands.
    - Output & Handoff: Dispatches raw page buffers and tag presence states to parsers and GUI tabs.
    - Conversions & Transformations: Wraps raw byte arrays into high-level event objects for UI consumption.
    - Validation & Governance Gates: Enforces connection state checks before dispatching read/write commands.
  * `tag_encoder.py` - Encoder Router Controller
    - Module Purpose: Controls and routes payload encoding requests between internal data models and binary writers.
    - Input & Source: Normalized internal application models (`self.common_data_model`).
    - Output & Handoff: Routes structured dictionaries to specific encoders (`encoders/opentag_encoder.py`) to generate binary outputs.
    - Conversions & Transformations: Orchestrates data transformation from model dictionaries to encoder-ready structures.
    - Validation & Governance Gates: Checks model schema compliance before passing data down to binary encoders.
  * `translate.py` - High-Level Pipeline Orchestrator
    - Module Purpose: Coordinates cross-schema translation pipelines and high-level conversion hooks.
    - Input & Source: Internal data models and target translation spec identifiers.
    - Output & Handoff: Hands off source models to `mappings/mapper.py` and returns translated dictionaries.
    - Conversions & Transformations: Directs format conversion requests across disparate schema specifications.
    - Validation & Governance Gates: Verifies that source and target format specs are registered in the mapping engine.
  * `json_importer.py` - Ingestion Engine
    - Module Purpose: Ingests raw `.json` files, external JSON strings, or raw dictionary payloads.
    - Input & Source: Raw `.json` files, external JSON strings, or raw dictionary payloads.
    - Output & Handoff: Populates `self.original_raw_model` in its native incoming state.
    - Conversions & Transformations: Decodes raw text streams into Python dictionaries without premature scaling transformations.
    - Validation & Governance Gates: Validates JSON syntax and basic structural integrity upon ingestion.

- Binary Encoders (`encoders/`)
  * `encoders/__init__.py` - Package Initializer
    - Module Purpose: Exposes encoder namespaces.
  * `encoders/base.py` - Abstract Base Encoder Interface
    - Module Purpose: Defines core serialization contracts and shared byte-formatting utilities across all binary payload encoders.
    - Input & Source: Inheriting encoder classes and internal models.
    - Output & Handoff: Standardized encoding methods and shared byte-formatting utilities.
    - Conversions & Transformations: Provides abstract serialization stubs.
    - Validation & Governance Gates: Enforces implementation of required serialization hooks across subclasses.
  * `encoders/openprinttag_encoder.py` - Binary Encoder
    - Module Purpose: Encodes internal models into binary CBOR/structured payloads for OpenPrintTag specifications.
    - Input & Source: Internal data models structured for OpenPrintTag.
    - Output & Handoff: Encoded binary CBOR or structured byte payloads.
    - Conversions & Transformations: Serializes dictionary key-values into compressed binary formats.
    - Validation & Governance Gates: Verifies field type compliance against OpenPrintTag schemas before encoding.
  * `encoders/opentag_encoder.py` - Binary Encoder
    - Module Purpose: Serializes normalized data models into binary NDEF and TLV packet streams for OpenTag specifications.
    - Input & Source: Normalized OpenTag data models.
    - Output & Handoff: Binary NDEF and TLV packet streams ready for tag writing.
    - Conversions & Transformations: Packs dictionary values into binary byte structures according to schema offsets.
    - Validation & Governance Gates: Validates byte-length limits against target chip capacities prior to final encoding.

- File Exporters & Writers (`exporters/`, `writers/`)
  * `exporters/file_exporter.py` - Exporter Module
    - Module Purpose: Serializes normalized application state (`self.common_data_model`) to formatted files or diagnostic reports.
    - Input & Source: Normalized application state (`self.common_data_model`) and raw memory buffers.
    - Output & Handoff: Formatted `.json` files, structured `.txt` reports combining key-value pairs with raw memory hex dumps, or binary image files.
    - Conversions & Transformations: Serializes structured dictionaries and hex byte arrays into formatted human-readable text and JSON files.
    - Validation & Governance Gates: Checks write permissions and valid directory paths before file creation.
  * `writers/base.py` - Abstract Base Writer Interface
    - Module Purpose: Defines standardized write execution contracts and hardware validation hooks.
    - Input & Source: Inheriting writer classes and binary byte arrays.
    - Output & Handoff: Standardized write execution contracts.
    - Conversions & Transformations: Provides abstract writing stubs.
    - Validation & Governance Gates: Enforces implementation of hardware write validation methods.
*  writers/opentag_writer.py - Binary Writer
        *  Module Purpose: Packs scaled values, strings, and NDEF formatting headers into a bytearray binary image matching SSOT schema byte offsets.
        *  Input & Source: Unscaled application data models and target chip capacity specs.
        *  Output & Handoff: A bytearray binary image matching SSOT schema byte offsets.
        *  Conversions & Transformations: Converts unscaled application floats into scaled integer bit representations using target schema scaling parameters, then packs them into byte arrays.
        *  Validation & Governance Gates: Executes BaseNFCReader.validate_chip_for_spec() to verify payload size fits within physical chip constraints before transmitting over the wire.

- Parsers (`parsers/`)
  * `parsers/__init__.py` - Package Initializer
    - Module Purpose: Exposes parser namespaces.
  * `parsers/openprinttag_parser.py` - Parser
    - Module Purpose: Parses CBOR and raw serialized OpenPrintTag data formats into internal models.
    - Input & Source: Raw serialized OpenPrintTag data streams or file buffers.
    - Output & Handoff: Unpacked internal dictionary models.
    - Conversions & Transformations: Decodes CBOR binary structures into Python key-value dictionaries.
    - Validation & Governance Gates: Validates incoming payload headers against OpenPrintTag specification rules.
  * `parsers/opentag_parser.py` - Parser
    - Module Purpose: Decodes binary TLV and NDEF streams for OpenTag formats, extracting MIME types and mapping raw payloads using active SSOT schemas.
    - Input & Source: Raw binary tag memory buffers or NDEF byte streams.
    - Output & Handoff: Populates `self.original_raw_model` and structured internal models.
    - Conversions & Transformations: Extracts MIME types, parses NDEF records, decodes TLV blocks, and maps raw payloads using active SSOT schemas.
    - Validation & Governance Gates: Checks magic headers and TLV terminator blocks to ensure valid OpenTag formatting.

- Schemas (`schemas/`)
  * `schemas/openprinttag_v1.json` - Schema Specification
    - Module Purpose: Official OpenPrintTag V1 data layout and validation boundaries specification.
    - Input & Source: Static JSON document.
    - Output & Handoff: Schema definition dictionary passed to parsers, UI engines, and mappers.
    - Conversions & Transformations: None (read-only reference).
    - Validation & Governance Gates: Serves as the structural validation standard for OpenPrintTag V1 data.
  * `schemas/openprinttagv1_schema.py` - Schema Helper Module
    - Module Purpose: Helper utilities and validation routines supporting OpenPrintTag V1 structures.
    - Input & Source: OpenPrintTag schema definitions.
    - Output & Handoff: Helper validation functions and property accessors.
    - Conversions & Transformations: Transforms raw JSON definitions into queryable helper objects.
    - Validation & Governance Gates: Enforces structural integrity checks for OpenPrintTag models.
  * `schemas/openslack_0.01.json` - Schema Specification
    - Module Purpose: External OpenSlack format schema specification.
    - Input & Source: Static JSON document.
    - Output & Handoff: Schema definition dictionary.
    - Conversions & Transformations: None.
    - Validation & Governance Gates: Acts as validation reference for external OpenSlack schemas.
  * `schemas/openspool_v1.json` - Schema Specification
    - Module Purpose: OpenSpool V1 data layout and validation boundaries specification.
    - Input & Source: Static JSON document.
    - Output & Handoff: Schema definition dictionary.
    - Conversions & Transformations: None.
    - Validation & Governance Gates: Acts as validation reference for OpenSpool V1 data models.
  * `schemas/opentag_v2_003.json` - Immutable V2 Official Spec (Locked SSOT)
    - Module Purpose: Immutable V2 Official Spec holding official locked SSOT status defining bit/byte offsets, scaling factors, units, tooltips, and validation boundaries.
    - Input & Source: Static JSON document containing `"official_spec_lock": true`.
    - Output & Handoff: Defines schema contracts for UI, mappers, and writers.
    - Conversions & Transformations: None.
    - Validation & Governance Gates: **Global Immutability Lock:** Prohibits any module from mutating, overriding, or appending fields. Modifications require the explicit schema cloning workflow.

- Mappers & Translation Submodules (`mappings/`)
  * `mappings/__init__.py` - Package Initializer
    - Module Purpose: Exposes mapping namespaces.
  *  mappings/base.py - Abstract Base Mapper Interface (BaseMapper)
        *  Module Purpose: Enforces standardized contracts for translation, type conversion, and coverage diagnostics across all translators.
        *  Input & Source: Inheriting directional mapper classes, source schemas, and target schemas.
        *  Output & Handoff: Standardized translation execution stubs and diagnostic dictionaries.
        *  Conversions & Transformations: Provides shared utilities for key translation and cross-spec unit conversions. Operates strictly on unscaled data models, leaving native binary integer scaling to encoders.
        *  Validation & Governance Gates: Enforces implementation of translate() across all directional mappers and tracks mapping coverage.
    - Input & Source: Inheriting directional mapper classes, source schemas, and target schemas.
    - Output & Handoff: Standardized translation execution stubs, scaling methods, and diagnostic dictionaries.
   
  * `mappings/mapper.py` - Central Orchestrator & Registry Dispatcher
    - Module Purpose: Acts as the central translation coordinator and registry dispatcher.
    - Input & Source: Source format identifiers, target format identifiers, source models, and schemas.
    - Output & Handoff: Dispatches translation requests to directional submodules and returns translated models.
    - Conversions & Transformations: Inspects source/target registry pairs and routes execution paths dynamically.
    - Validation & Governance Gates: Raises explicit errors if no directional mapper is registered for a requested translation path.
  * `mappings/directional/openprinttag_to_opentag.py` - Directional Mapper
    - Module Purpose: OpenPrintTag V1 to OpenTag V2 directional schema translation module.
    - Input & Source: Source dictionary conforming to OpenPrintTag schema.
    - Output & Handoff: Target dictionary conforming to OpenTag V2 schema.
    - Conversions & Transformations: Maps OpenPrintTag key aliases to OpenTag V2 nested structures.
    - Validation & Governance Gates: Runs `debug_mapping_coverage()` to verify zero telemetry loss during translation.
  * `mappings/directional/opentag_to_openprinttag.py` - Directional Mapper
    - Module Purpose: OpenTag V2 to OpenPrintTag V1 directional schema translation module.
    - Input & Source: Source dictionary conforming to OpenTag V2 schema.
    - Output & Handoff: Target dictionary conforming to OpenPrintTag schema.
    - Conversions & Transformations: Reverse-maps OpenTag V2 nested fields back into OpenPrintTag flat/structured properties.
    - Validation & Governance Gates: Runs `debug_mapping_coverage()` to verify mapping completeness.
  * `mappings/directional/opentag_to_openspool.py` - Directional Mapper
    - Module Purpose: OpenTag V2 to OpenSpool V1 directional schema translation module.
    - Input & Source: Source dictionary conforming to OpenTag V2 schema.
    - Output & Handoff: Target dictionary conforming to OpenSpool V1 schema.
    - Conversions & Transformations: Translates OpenTag payload nodes into Spool-compatible inventory attributes.
    - Validation & Governance Gates: Runs `debug_mapping_coverage()` for coverage validation.
  * `mappings/directional/opentag_to_nfctools.py` - Directional Mapper
    - Module Purpose: OpenTag V2 to NFC Tools format mapping module.
    - Input & Source: Source dictionary conforming to OpenTag V2 schema.
    - Output & Handoff: Target dictionary formatted for NFC Tools layout requirements.
    - Conversions & Transformations: Maps internal fields to NFC Tools record expectations.
    - Validation & Governance Gates: Runs `debug_mapping_coverage()` to track translation gaps.
  * `mappings/openprinttagv1_to_opentagv2003.json`, `opentagv2003_to_openspoolv1.json`, `opentag_to_nfctools.json` - Mapping Configurations
    - Module Purpose: Static mapping configuration files for legacy or fallback translation routes.
    - Input & Source: Static JSON mapping tables.
    - Output & Handoff: Field-to-field mapping rules for legacy fallback paths.
    - Conversions & Transformations: None.
    - Validation & Governance Gates: Validates static mapping syntax.

- Translators (`translators/`)
  * `translators/base.py` - Abstract Translator Base Class
    - Module Purpose: Defines core interface hooks for external format translators.
    - Input & Source: Inheriting translator classes and internal models.
    - Output & Handoff: Standardized translation execution hooks.
    - Conversions & Transformations: Abstract method stubs.
    - Validation & Governance Gates: Enforces subclass implementation of external serialization contracts.
  * `translators/nfc_tools_desktop.py` - Translator
    - Module Purpose: NFC Tools desktop format translator.
    - Input & Source: Internal data models and NFC Tools desktop JSON files.
    - Output & Handoff: Serialized NFC Tools Desktop JSON output strings.
    - Conversions & Transformations: Translates core internal properties into NFC Tools desktop record arrays.
    - Validation & Governance Gates: Validates output structure against NFC Tools desktop specifications.
  * `translators/nfc_tools_mobile.py` - Translator
    - Module Purpose: NFC Tools mobile format translator.
    - Input & Source: Internal data models and mobile format payloads.
    - Output & Handoff: Serialized mobile-compatible JSON structures.
    - Conversions & Transformations: Formats data fields to meet mobile app parsing constraints.
    - Validation & Governance Gates: Validates structural compatibility for mobile targets.
  * `translators/opentag_json.py` - Translator
    - Module Purpose: OpenTag JSON serialization translator.
    - Input & Source: Internal models and raw OpenTag JSON representations.
    - Output & Handoff: Serialized OpenTag JSON payloads.
    - Conversions & Transformations: Serializes and deserializes core OpenTag dictionary structures.
    - Validation & Governance Gates: Enforces OpenTag schema conformance during translation.

- Hardware Drivers & Interfaces (`hardware/`)
  * `hardware/base.py` & `hardware/base_reader.py` - Abstract Reader Interface
    - Module Purpose: Defines abstract hardware interfaces, background PySide6 worker thread signal routines, chip signature verifications, and payload-to-chip capacity validation rules (`validate_chip_for_spec()`).
    - Input & Source: Physical reader PCSC command streams and PySide6 worker signals.
    - Output & Handoff: Emits raw page buffers, UID strings, connection states, and write outcomes.
    - Conversions & Transformations: Converts low-level APDU response bytes into high-level application events.
    - Validation & Governance Gates: Implements `validate_chip_for_spec()` to enforce physical chip capacity limits before write execution.
  * `hardware/acr122u.py` - Hardware Driver
    - Module Purpose: PCSC smartcard communication driver for ACR122U readers.
    - Input & Source: APDU command calls and reader byte streams.
    - Output & Handoff: Raw memory block buffers and hardware status codes.
    - Conversions & Transformations: Translates high-level read/write requests into ACR122U-specific APDU command bytes.
    - Validation & Governance Gates: Verifies PCSC connection health and reader response error codes.
  * `hardware/acr1552u.py` & `hardware/acr1552u_thread.py` - Hardware Driver & Thread Worker
    - Module Purpose: PCSC reader communication driver and background thread worker for ACR1552U hardware operations.
    - Input & Source: Asynchronous reader polling triggers and write requests.
    - Output & Handoff: Background thread signals carrying raw memory blocks and tag presence states.
    - Conversions & Transformations: Manages non-blocking thread execution for continuous NFC tag polling.
    - Validation & Governance Gates: Enforces thread-safe locking during concurrent read/write operations.
  * `hardware/chip_profiles.py` - Chip Configuration Profile
    - Module Purpose: Defines NFC chip memory limits and capacity configuration profiles (e.g., NTAG215).
    - Input & Source: Chip UID headers and type detection codes.
    - Output & Handoff: Chip capacity dictionaries (e.g., user memory page limits, total byte capacities).
    - Conversions & Transformations: Maps chip type codes to structural memory parameters.
    - Validation & Governance Gates: Provides lookup boundaries used by chip validation gates.
  * `hardware/reader_factory.py` - Factory Pattern Loader
    - Module Purpose: Dynamically loads and instantiates hardware reader drivers based on connection configurations.
    - Input & Source: Configuration settings specifying reader hardware models.
    - Output & Handoff: Instantiated reader driver objects (`ACR122U` or `ACR1552U`).
    - Conversions & Transformations: Dynamically instantiates the correct driver class based on connection strings.
    - Validation & Governance Gates: Validates that requested hardware drivers are supported and available on the system.

- GUI Windows, Dialogs, Tabs & Widgets (`gui/`)
  * `gui/main_window.py` - GUI Window Manager
    - Module Purpose: Core QMainWindow coordinating the header action bar, bottom controls, and the central QTabWidget layout.
    - Input & Source: User interactions, menu clicks, and background thread signals.
    - Output & Handoff: Coordinates state between header action bars, bottom controls, and central tabs.
    - Conversions & Transformations: Translates window events into pipeline actions.
    - Validation & Governance Gates: Manages window focus and modal dialog states.
  * `gui/dialogs/field_editor_dialog.py` - GUI Dialog
    - Module Purpose: Modal dialog for editing individual schema fields.
    - Input & Source: Field metadata, current values, and user input edits.
    - Output & Handoff: Updated field values returned to active editors.
    - Conversions & Transformations: Converts raw user string inputs into typed schema values.
    - Validation & Governance Gates: Enforces field-level type and range validation before acceptance.
  * `gui/dialogs/settings_dialog.py` - GUI Dialog
    - Module Purpose: Application settings configuration dialog.
    - Input & Source: User preference inputs and current config values.
    - Output & Handoff: Updated configuration parameters saved to `config.py`.
    - Conversions & Transformations: Converts UI toggles into configuration variables.
    - Validation & Governance Gates: Validates setting parameter ranges before saving.
  * `gui/dialogs/write_file_request_dialog.py` - GUI Dialog
    - Module Purpose: Pre-execution confirmation modal handling external Spoolsonian write requests.
    - Input & Source: External write queue payloads and user confirmation clicks.
    - Output & Handoff: User authorization signals (`Begin Writing` or `Cancel Operation`).
    - Conversions & Transformations: Presents raw queue payloads into human-readable summary modals.
    - Validation & Governance Gates: Acts as a mandatory human confirmation gate before executing physical tag writes.
  * `gui/tabs/raw_inspector_tab.py` - GUI Tab
    - Module Purpose: Displays raw NDEF memory hex dumps alongside decoded structure interpretations as a read-only raw memory inspection interface, completely decoupled from visualizer widgets.
    - Input & Source: Raw memory byte buffers from reader threads.
    - Output & Handoff: Visual hex grid and parsed NDEF breakdown displays.
    - Conversions & Transformations: Formats raw byte arrays into hexadecimal grid layouts via `utils/hex_formatter.py`.
    - Validation & Governance Gates: Read-only inspection interface preventing accidental raw memory corruption.
  * `gui/tabs/standard_editor_tab.py` - GUI Tab
    - Module Purpose: V1 visual schema editor tab enforcing official specification locks.
    - Input & Source: V1 data models and schemas.
    - Output & Handoff: User-edited V1 application models.
    - Conversions & Transformations: Maps UI controls to V1 schema fields.
    - Validation & Governance Gates: Enforces V1 schema validation rules.
  * `gui/tabs/standard_editor_v2_tab.py` - GUI Tab
    - Module Purpose: Advanced schema editor and field builder tab (V2) hosting the Memory Visualizer. Manages dual-view toggling between Target Schema translation layouts and active "in-editing" draft schemas while preserving active state. Enforces official specification locks (`official_spec_lock: true`), routing edits exclusively through the schema cloning workflow.
    - Input & Source: V2 schemas, translated data models, and user customization inputs.
    - Output & Handoff: Cloned draft schemas and customized model data.
    - Conversions & Transformations: Handles schema cloning workflows and dual-view visualizer state switching.
    - Validation & Governance Gates: Enforces official spec locks (`official_spec_lock: true`) and validates target spec layout translation constraints.
  * `gui/tabs/tag_editor_tab.py` - GUI Tab
    - Module Purpose: Dynamic form and field table tab driven strictly by target schema definitions.
    - Input & Source: Target SSOT schemas and normalized internal models.
    - Output & Handoff: Fully validated user models ready for encoding and writing.
    - Conversions & Transformations: Dynamically renders UI spinboxes, text fields, and dropdowns based on schema metadata.
    - Validation & Governance Gates: Performs real-time field range checking and byte-length limits directly inside UI editors.
  * `gui/widgets/memory_visualizer.py` - GUI Widget
    - Module Purpose: NFC memory block grid visualizer hosted inside Standard Editor V2. Renders target schema layout allocations, translated model byte boundaries, and field conflict overlays independently of raw byte inspection values.
    - Input & Source: Target schema field definitions and translated model layout structures.
    - Output & Handoff: Color-coded grid widget displaying target layout structures and conflict overlays.
    - Conversions & Transformations: Maps byte offsets to visual grid color blocks and conflict overlays.
    - Validation & Governance Gates: Highlights memory overflow or collision zones across schema layouts in real time.

- Utils, Tests & Sample Data
  * `utils/hex_formatter.py` - Utility
    - Module Purpose: Formatting utilities for hexadecimal strings and memory byte arrays.
    - Input & Source: Raw byte arrays or integer values.
    - Output & Handoff: Formatted hex strings.
    - Conversions & Transformations: Converts binary data into readable hexadecimal text.
    - Validation & Governance Gates: Sanitizes input types before formatting.
  * `tests/` (`startup_parameter_test1.py`, `startup_parameter_test2.py`, `testsend2.py`) - Test Suites
    - Module Purpose: CLI startup parameter tests and IPC transmission integration test suites.
    - Input & Source: CLI argument strings and mock IPC messages.
    - Output & Handoff: Test execution success/failure status codes.
    - Conversions & Transformations: Simulates runtime inputs for validation.
    - Validation & Governance Gates: Asserts expected behaviors against test specifications.
  * `tag_samples/` - Sample Test Data
    - Module Purpose: Sample desktop, mobile, and diagnostic test payloads (`.json`, `.nfctools-desktop.json`, `.nfctools-mobile.json`).
    - Input & Source: Static test data files.
    - Output & Handoff: Sample JSON models loaded by test routines or parsers.
    - Conversions & Transformations: None.
    - Validation & Governance Gates: Used as reference baselines for parsing and translation regression testing.