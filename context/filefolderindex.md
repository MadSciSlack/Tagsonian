##### File and Folder Index (SSOT)

--------------------------------------------------------------------------------

###### Root Modules
###### config.py - Global Configuration & Settings Management
*   **Module Purpose:**   Manages global application configuration, user preferences, and runtime settings.
*   **Input & Source:**   Environment variables, user configuration files, and settings dialog inputs.
*   **Output & Handoff:**   Provides setting values and preference states across application modules.
*   **Conversions & Transformations:**   Parses raw configuration text streams into structured key-value dictionaries.
*   **Validation & Governance Gates:**   Validates configuration option types and bounds against default fallback specifications.
*   **Exception-Handling Protocol:**   Traps file permission errors or malformed configuration JSON; falls back to default system settings and logs a warning.

###### main.py - Application Entry Point & Server
*   **Module Purpose:**   Initializes the PySide6 application lifecycle, sets up IPC server endpoints, and launches the main window.
*   **Input & Source:**   CLI startup arguments and incoming IPC socket messages from running instances of Spoolsonian.
*   **Output & Handoff:**   Instantiates the PySide6 event loop, initializes MainWindow, and starts asynchronous IPC listener threads.
*   **Conversions & Transformations:**   Translates raw external CLI/IPC payloads into application initialization triggers.
*   **Validation & Governance Gates:**   Validates startup environment states and verifies that required SSOT schema files are accessible before opening windows.
*   **Exception-Handling Protocol:**   Traps startup initialization failures and logs critical failure telemetry.

###### json_importer.py - Raw JSON Ingestion Engine
*   **Module Purpose:**   Ingests raw .json files, external JSON strings, or raw dictionary payloads into native application state.
*   **Input & Source:**   Raw .json files, external JSON strings, or raw dictionary payloads.
*   **Output & Handoff:**   Populates self.original_raw_model in its native incoming state.
*   **Conversions & Transformations:**   Decodes raw text streams into Python dictionaries without premature scaling transformations.
*   **Validation & Governance Gates:**   Validates JSON syntax and basic structural integrity upon ingestion.
*   **Exception-Handling Protocol:**   Traps JSONDecodeError and raises human-readable file read errors.

###### nfc_reader.py - Core Reader Coordinator
*   **Module Purpose:**   Acts as the high-level coordination wrapper unifying background reader threads and application event loops.
*   **Input & Source:**   Hardware signal emissions from active reader threads (acr1552u_thread.py) and UI commands.
*   **Output & Handoff:**   Dispatches raw page buffers and tag presence states to parsers and GUI tabs.
*   **Conversions & Transformations:**   Wraps raw byte arrays into high-level event objects for UI consumption.
*   **Validation & Governance Gates:**   Enforces connection state checks before dispatching read/write commands.
*   **Exception-Handling Protocol:**   Traps hardware disconnect signals and emits status bar warning events.

###### tag_encoder.py - Encoder Router Controller
*   **Module Purpose:**   Controls and routes payload encoding requests between internal data models and binary writers.
*   **Input & Source:**   Normalized internal application models (self.common_data_model).
*   **Output & Handoff:**   Routes structured dictionaries to specific encoders (encoders/opentag_encoder.py) to generate binary outputs.
*   **Conversions & Transformations:**   Orchestrates data transformation from model dictionaries to encoder-ready structures.
*   **Validation & Governance Gates:**   Checks model schema compliance before passing data down to binary encoders.
*   **Exception-Handling Protocol:**   Traps unregistered schema types and blocks payload encoding.

###### translate.py - High-Level Pipeline Orchestrator
*   **Module Purpose:**   Coordinates cross-schema translation pipelines and high-level conversion hooks.
*   **Input & Source:**   Internal data models and target translation spec identifiers.
*   **Output & Handoff:**   Hands off source models to mappings/mapper.py and returns translated dictionaries.
*   **Conversions & Transformations:**   Directs format conversion requests across disparate schema specifications.
*   **Validation & Governance Gates:**   Verifies that source and target format specs are registered in the mapping engine.
*   **Exception-Handling Protocol:**   Traps mapping execution exceptions and returns diagnostic error reports.

--------------------------------------------------------------------------------

###### Core & Management (tagsonian/core/)
###### tagsonian/core/write_queue_manager.py - Thread-Safe Unified Write Task Queue Manager
*   **Module Purpose:**   Manages thread-safe task queueing, state mutations, and Qt signal dispatches for GUI and external IPC write requests.
*   **Input & Source:**   WriteTask objects created from GUI editor views or validated Spoolsonian IPC requests.
*   **Output & Handoff:**   Dispatches pending tasks to TapToWriteWorker and emits status update signals to WriteQueueWidget.
*   **Conversions & Transformations:**   Enqueues tasks and maintains task execution states without altering payload values.
*   **Validation & Governance Gates:**   Enforces QMutex thread locking across concurrent IPC listener threads and hardware worker threads.
*   **Exception-Handling Protocol:**   Traps lock timeout exceptions and logs queued thread collisions.

--------------------------------------------------------------------------------

###### Models (tagsonian/models/)
###### tagsonian/models/write_task.py - Write Task Data Model & Enums
*   **Module Purpose:**   Defines the WriteTask dataclass, TaskStatus, and TaskSource enumeration specs for batch and IPC queueing.
*   **Input & Source:**   Pre-encoded payload bytes, schema identifiers, and common data model snapshots.
*   **Output & Handoff:**   Standardized task representation passed through WriteQueueManager.
*   **Conversions & Transformations:**   Generates UUID v4 task identifiers and timestamps.
*   **Validation & Governance Gates:**   Enforces schema specification identifier tagging per task.
*   **Exception-Handling Protocol:**   Traps invalid enum instantiation inputs and raises ValueError.

--------------------------------------------------------------------------------

###### Exporters (exporters/)
###### exporters/__init__.py - Package Initializer
*   **Module Purpose:**   Exposes exporter namespaces.
*   **Input & Source:**   Package import triggers.
*   **Output & Handoff:**   Exposed module symbols.
*   **Conversions & Transformations:**   None.
*   **Validation & Governance Gates:**   None.
*   **Exception-Handling Protocol:**   Traps missing submodule import errors.

###### exporters/file_exporter.py - Exporter Module
*   **Module Purpose:**   Serializes normalized application state (self.common_data_model) to formatted files or diagnostic reports.
*   **Input & Source:**   Normalized application state (self.common_data_model) and raw memory buffers.
*   **Output & Handoff:**   Formatted .json files, structured .txt reports combining key-value pairs with raw memory hex dumps, or binary image files.
*   **Conversions & Transformations:**   Serializes structured dictionaries and hex byte arrays into formatted human-readable text and JSON files.
*   **Validation & Governance Gates:**   Checks write permissions and valid directory paths before file creation.
*   **Exception-Handling Protocol:**   Traps disk I/O errors and permission denied exceptions, presenting file write failure dialogs to the user.

--------------------------------------------------------------------------------

###### Encoders & Writers (encoders/, writers/)
###### encoders/__init__.py - Package Initializer
*   **Module Purpose:**   Exposes encoder namespaces.
*   **Input & Source:**   Package import triggers.
*   **Output & Handoff:**   Exposed module symbols.
*   **Conversions & Transformations:**   None.
*   **Validation & Governance Gates:**   None.
*   **Exception-Handling Protocol:**   Traps missing submodule import errors.

###### encoders/base.py - Abstract Base Encoder Interface
*   **Module Purpose:**   Defines core serialization contracts and shared byte-formatting utilities across all binary payload encoders.
*   **Input & Source:**   Inheriting encoder classes and internal models.
*   **Output & Handoff:**   Standardized encoding methods and shared byte-formatting utilities.
*   **Conversions & Transformations:**   Provides abstract serialization stubs.
*   **Validation & Governance Gates:**   Enforces implementation of required serialization hooks across subclasses.
*   **Exception-Handling Protocol:**   Raises NotImplementedError if required abstract methods are unfulfilled.

###### encoders/openprinttag_encoder.py - OpenPrintTag CBOR Binary Encoder
*   **Module Purpose:**   Encodes internal models into binary CBOR/structured payloads for OpenPrintTag specifications.
*   **Input & Source:**   Internal data models structured for OpenPrintTag.
*   **Output & Handoff:**   Encoded binary CBOR or structured byte payloads.
*   **Conversions & Transformations:**   Converts Python data types into CBOR binary structures according to OpenPrintTag specifications.
*   **Validation & Governance Gates:**   Validates model fields against OpenPrintTag schema constraints prior to encoding.
*   **Exception-Handling Protocol:**   Traps CBOR encoding errors and returns empty byte buffers with diagnostic logs.

###### encoders/opentag_encoder.py - OpenTag Binary NDEF/TLV Encoder
*   **Module Purpose:**   Serializes normalized data models into binary NDEF and TLV packet streams for OpenTag specifications.
*   **Input & Source:**   Unscaled application floating-point values from common_data_model.
*   **Output & Handoff:**   Binary NDEF and TLV byte streams ready for tag writing.
*   **Conversions & Transformations:**   Applies target SSOT schema scaling factors to derive scaled integers, then packs them into byte arrays matching schema bit/byte offsets.
*   **Validation & Governance Gates:**   Validates bit length limits and payload byte capacity before binary packing.
*   **Exception-Handling Protocol:**   Traps bit packing overflow errors and out-of-bounds scalar values.

###### writers/__init__.py - Package Initializer
*   **Module Purpose:**   Exposes writer namespaces.
*   **Input & Source:**   Package import triggers.
*   **Output & Handoff:**   Exposed module symbols.
*   **Conversions & Transformations:**   None.
*   **Validation & Governance Gates:**   None.
*   **Exception-Handling Protocol:**   Traps missing submodule import errors.

###### writers/base.py - Abstract Base Writer Interface
*   **Module Purpose:**   Defines standardized write execution contracts and hardware validation hooks.
*   **Input & Source:**   Inheriting writer classes and binary byte arrays.
*   **Output & Handoff:**   Standardized write execution contracts.
*   **Conversions & Transformations:**   Provides abstract writing stubs.
*   **Validation & Governance Gates:**   Enforces implementation of hardware write validation methods.
*   **Exception-Handling Protocol:**   Raises NotImplementedError on missing implementations.

###### writers/opentag_writer.py - Binary Writer & Payload Encoder
*   **Module Purpose:**   Packs scaled values, strings, and NDEF headers into binary byte arrays matching SSOT schema byte offsets.
*   **Input & Source:**   Unscaled application data models (common_data_model) and target chip capacity specs.
*   **Output & Handoff:**   Bytearray binary image matching SSOT schema byte offsets.
*   **Conversions & Transformations:**   Accepts unscaled application floating-point values, applies target SSOT schema scaling factors to derive scaled integers, and packs them into binary byte arrays.
*   **Validation & Governance Gates:**   Validates chip byte capacity using BaseNFCReader.validate_chip_for_spec() prior to transmission.
*   **Exception-Handling Protocol:**   Traps byte overflow errors and out-of-bounds scalar values.

--------------------------------------------------------------------------------

###### Parsers (parsers/)
###### parsers/__init__.py - Package Initializer
*   **Module Purpose:**   Exposes parser namespaces.
*   **Input & Source:**   Package import triggers.
*   **Output & Handoff:**   Exposed module symbols.
*   **Conversions & Transformations:**   None.
*   **Validation & Governance Gates:**   None.
*   **Exception-Handling Protocol:**   Traps missing submodule import errors.

###### parsers/openprinttag_parser.py - OpenPrintTag CBOR Binary Parser
*   **Module Purpose:**   Parses CBOR and raw serialized OpenPrintTag data formats into internal models.
*   **Input & Source:**   Raw serialized OpenPrintTag data streams or file buffers.
*   **Output & Handoff:**   Unpacked internal dictionary models populated with unscaled values.
*   **Conversions & Transformations:**   Decodes CBOR binary structures into Python key-value dictionaries.
*   **Validation & Governance Gates:**   Validates incoming payload headers against OpenPrintTag specification rules.
*   **Exception-Handling Protocol:**   Traps CBOR decode exceptions gracefully without breaking caller threads.

###### parsers/opentag_parser.py - OpenTag Binary TLV/NDEF Parser
*   **Module Purpose:**   Decodes binary TLV and NDEF streams for OpenTag formats, extracting MIME types and mapping raw payloads using active SSOT schemas.
*   **Input & Source:**   Raw binary tag memory buffers or NDEF byte streams.
*   **Output & Handoff:**   Populates self.original_raw_model and structured internal models with unscaled floating-point values.
*   **Conversions & Transformations:**   Extracts MIME types, parses NDEF records, decodes TLV blocks, and multiplies scaled binary integers by schema scaling factors to yield unscaled floats.
*   **Validation & Governance Gates:**   Checks magic headers and TLV terminator blocks to ensure valid OpenTag formatting.
*   **Exception-Handling Protocol:**   Traps truncated TLV blocks and corrupted MIME record headers.

--------------------------------------------------------------------------------

###### Mappers (mappings/)
###### mappings/__init__.py - Package Initializer
*   **Module Purpose:**   Exposes mapping namespaces.
*   **Input & Source:**   Package import triggers.
*   **Output & Handoff:**   Exposed module symbols.
*   **Conversions & Transformations:**   None.
*   **Validation & Governance Gates:**   None.
*   **Exception-Handling Protocol:**   Traps missing submodule import errors.

###### mappings/base.py - Abstract Base Mapper Interface
*   **Module Purpose:**   Enforces standardized contracts for translation, type conversion, and coverage diagnostics across all translators.
*   **Input & Source:**   Inheriting directional mapper classes, source schemas, and target schemas.
*   **Output & Handoff:**   Standardized translation execution stubs and diagnostic dictionaries.
*   **Conversions & Transformations:**   Translates field key structures and executes cross-spec unit conversions between disparate schemas. Accepts unscaled source models and returns unscaled target models without applying native binary schema scaling factors.
*   **Validation & Governance Gates:**   Enforces implementation of translate() across all directional mappers and tracks mapping coverage.
*   **Exception-Handling Protocol:**   Traps missing key mappings and logs unmapped field telemetry.

###### mappings/mapper.py - Central Orchestrator & Registry Dispatcher
*   **Module Purpose:**   Acts as the central translation coordinator and registry dispatcher.
*   **Input & Source:**   Source format identifiers, target format identifiers, source models, and schemas.
*   **Output & Handoff:**   Dispatches translation requests to directional submodules and returns translated models.
*   **Conversions & Transformations:**   Inspects source/target registry pairs and routes execution paths dynamically. Bypasses directional mappers for native single-spec operations.
*   **Validation & Governance Gates:**   Raises explicit errors if no directional mapper is registered for a requested translation path.
*   **Exception-Handling Protocol:**   Traps KeyErrors for unregistered direction pairs and returns unmapped fallback models.

###### Directional Submodules (mappings/directional/)
###### mappings/directional/__init__.py - Package Initializer
*   **Module Purpose:**   Exposes directional mapping namespaces.
*   **Input & Source:**   Package import triggers.
*   **Output & Handoff:**   Exposed module symbols.
*   **Conversions & Transformations:**   None.
*   **Validation & Governance Gates:**   None.
*   **Exception-Handling Protocol:**   Traps missing submodule import errors.

###### mappings/directional/openprinttag_to_opentag.py - OpenPrintTag V1 to OpenTag V2 Directional Mapper
*   **Module Purpose:**   OpenPrintTag V1 to OpenTag V2 directional schema mapper.
*   **Input & Source:**   Source dictionary conforming to OpenPrintTag V1 schema.
*   **Output & Handoff:**   Unscaled target dictionary conforming to OpenTag V2 schema.
*   **Conversions & Transformations:**   Converts OpenPrintTag parameter keys and data structures into OpenTag V2 equivalents.
*   **Validation & Governance Gates:**   Executes debug_mapping_coverage() to systematically track mapping gaps, missing keys, and dropped telemetry.
*   **Exception-Handling Protocol:**   Traps missing source fields and inserts schema fallback default values.

###### mappings/directional/opentag_to_openprinttag.py - OpenTag V2 to OpenPrintTag V1 Directional Mapper
*   **Module Purpose:**   OpenTag V2 to OpenPrintTag V1 directional schema mapper.
*   **Input & Source:**   Source dictionary conforming to OpenTag V2 schema.
*   **Output & Handoff:**   Unscaled target dictionary conforming to OpenPrintTag V1 schema.
*   **Conversions & Transformations:**   Reverse-maps OpenTag V2 nested fields back into OpenPrintTag flat properties.
*   **Validation & Governance Gates:**   Runs debug_mapping_coverage() to verify mapping completeness.
*   **Exception-Handling Protocol:**   Traps structural key mismatches and records unmapped field logs.

###### mappings/directional/opentag_to_openspool.py - OpenTag V2 to OpenSpool V1 Directional Mapper
*   **Module Purpose:**   OpenTag V2 to OpenSpool V1 directional schema mapper.
*   **Input & Source:**   Source dictionary conforming to OpenTag V2 schema.
*   **Output & Handoff:**   Unscaled target dictionary conforming to OpenSpool V1 schema.
*   **Conversions & Transformations:**   Translates OpenTag payload nodes into Spool-compatible inventory attributes.
*   **Validation & Governance Gates:**   Runs debug_mapping_coverage() for coverage validation.
*   **Exception-Handling Protocol:**   Traps missing spool attributes and populates schema defaults.

###### mappings/directional/opentag_to_nfctools.py - OpenTag V2 to NFC Tools Directional Mapper
*   **Module Purpose:**   OpenTag V2 to NFC Tools format directional mapper.
*   **Input & Source:**   Source dictionary conforming to OpenTag V2 schema.
*   **Output & Handoff:**   Target dictionary formatted for NFC Tools layout requirements.
*   **Conversions & Transformations:**   Maps internal fields to NFC Tools record expectations.
*   **Validation & Governance Gates:**   Runs debug_mapping_coverage() to track translation gaps.
*   **Exception-Handling Protocol:**   Traps payload length mismatches for record entries.

###### Mappings Configuration Rules (mappings/*.json)
###### mappings/openprinttagv1_to_opentagv2003.json - Legacy Static Mapping Rule Config
*   **Module Purpose:**   Static JSON mapping table for OpenPrintTag V1 to OpenTag V2 fallback routes.
*   **Input & Source:**   Static JSON file.
*   **Output & Handoff:**   Field-to-field fallback rule map.
*   **Conversions & Transformations:**   None.
*   **Validation & Governance Gates:**   Validates static mapping JSON syntax.
*   **Exception-Handling Protocol:**   Logs syntax errors during static rule loading.

###### mappings/opentagv2003_to_openspoolv1.json - Legacy Static Mapping Rule Config
*   **Module Purpose:**   Static JSON mapping table for OpenTag V2 to OpenSpool V1 fallback routes.
*   **Input & Source:**   Static JSON file.
*   **Output & Handoff:**   Field-to-field fallback rule map.
*   **Conversions & Transformations:**   None.
*   **Validation & Governance Gates:**   Validates static mapping JSON syntax.
*   **Exception-Handling Protocol:**   Logs syntax errors during static rule loading.

###### mappings/opentag_to_nfctools.json - Legacy Static Mapping Rule Config
*   **Module Purpose:**   Static JSON mapping table for OpenTag to NFC Tools fallback routes.
*   **Input & Source:**   Static JSON file.
*   **Output & Handoff:**   Field-to-field fallback rule map.
*   **Conversions & Transformations:**   None.
*   **Validation & Governance Gates:**   Validates static mapping JSON syntax.
*   **Exception-Handling Protocol:**   Logs syntax errors during static rule loading.

--------------------------------------------------------------------------------

###### Schemas (schemas/)
###### schemas/__init__.py - Package Initializer
*   **Module Purpose:**   Exposes schema namespaces.
*   **Input & Source:**   Package import triggers.
*   **Output & Handoff:**   Exposed module symbols.
*   **Conversions & Transformations:**   None.
*   **Validation & Governance Gates:**   None.
*   **Exception-Handling Protocol:**   Traps missing submodule import errors.

###### schemas/openprinttag_v1.json - OpenPrintTag V1 Data Layout Specification
*   **Module Purpose:**   Official OpenPrintTag V1 data layout and validation boundaries specification.
*   **Input & Source:**   Static JSON document.
*   **Output & Handoff:**   Schema definition dictionary passed to parsers, UI engines, and mappers.
*   **Conversions & Transformations:**   None (read-only reference).
*   **Validation & Governance Gates:**   Serves as the structural validation standard for OpenPrintTag V1 data.
*   **Exception-Handling Protocol:**   Traps malformed JSON syntax on schema load.

###### schemas/openprinttagv1_schema.py - OpenPrintTag V1 Schema Helper Module
*   **Module Purpose:**   Helper utilities and validation routines supporting OpenPrintTag V1 structures.
*   **Input & Source:**   OpenPrintTag schema definitions.
*   **Output & Handoff:**   Helper validation functions and property accessors.
*   **Conversions & Transformations:**   Transforms raw JSON definitions into queryable helper objects.
*   **Validation & Governance Gates:**   Enforces structural integrity checks for OpenPrintTag models.
*   **Exception-Handling Protocol:**   Traps schema lookup KeyErrors.

###### schemas/openslack_0.01.json - OpenSlack Format Schema Specification
*   **Module Purpose:**   External OpenSlack format schema specification.
*   **Input & Source:**   Static JSON document.
*   **Output & Handoff:**   Schema definition dictionary.
*   **Conversions & Transformations:**   None.
*   **Validation & Governance Gates:**   Acts as validation reference for external OpenSlack schemas.
*   **Exception-Handling Protocol:**   Traps JSON load syntax errors.

###### schemas/openspool_v1.json - OpenSpool V1 Data Layout Specification
*   **Module Purpose:**   OpenSpool V1 data layout and validation boundaries specification.
*   **Input & Source:**   Static JSON document.
*   **Output & Handoff:**   Schema definition dictionary.
*   **Conversions & Transformations:**   None.
*   **Validation & Governance Gates:**   Acts as validation reference for OpenSpool V1 data models.
*   **Exception-Handling Protocol:**   Traps JSON load syntax errors.

###### schemas/opentag_v2_003.json - Immutable V2 Official Spec SSOT
*   **Module Purpose:**   Immutable V2 Official Spec holding official locked SSOT status defining bit/byte offsets, scaling factors, units, tooltips, and validation boundaries.
*   **Input & Source:**   Static JSON document containing "official_spec_lock": true.
*   **Output & Handoff:**   Defines schema contracts for UI, mappers, and writers.
*   **Conversions & Transformations:**   None.
*   **Validation & Governance Gates:**   Enforces global application-wide immutability (official_spec_lock: true) preventing any module from mutating, deleting, or overriding its fields.
*   **Exception-Handling Protocol:**   Traps modification attempts on locked fields and raises PermissionError.

--------------------------------------------------------------------------------

###### Translators (translators/)
###### translators/__init__.py - Package Initializer
*   **Module Purpose:**   Exposes translator namespaces.
*   **Input & Source:**   Package import triggers.
*   **Output & Handoff:**   Exposed module symbols.
*   **Conversions & Transformations:**   None.
*   **Validation & Governance Gates:**   None.
*   **Exception-Handling Protocol:**   Traps missing submodule import errors.

###### translators/base.py - Abstract Translator Base Class
*   **Module Purpose:**   Abstract translator base class defining core external file formatting contracts.
*   **Input & Source:**   Internal data models.
*   **Output & Handoff:**   Standardized translator interface stubs.
*   **Conversions & Transformations:**   Abstract method stubs.
*   **Validation & Governance Gates:**   Enforces implementation of external serialization formats across subclasses.
*   **Exception-Handling Protocol:**   Raises NotImplementedError on missing abstract methods.

###### translators/nfc_tools_desktop.py - NFC Tools Desktop Translator
*   **Module Purpose:**   NFC Tools desktop format translator.
*   **Input & Source:**   Internal data models and NFC Tools desktop JSON files.
*   **Output & Handoff:**   Serialized NFC Tools Desktop JSON output strings.
*   **Conversions & Transformations:**   Translates core internal properties into NFC Tools desktop record arrays.
*   **Validation & Governance Gates:**   Validates output structure against NFC Tools desktop specifications.
*   **Exception-Handling Protocol:**   Traps key formatting errors during export.

###### translators/nfc_tools_mobile.py - NFC Tools Mobile Translator
*   **Module Purpose:**   NFC Tools mobile format translator.
*   **Input & Source:**   Internal data models and mobile format payloads.
*   **Output & Handoff:**   Serialized mobile-compatible JSON structures.
*   **Conversions & Transformations:**   Formats data fields to meet mobile app parsing constraints.
*   **Validation & Governance Gates:**   Validates structural compatibility for mobile targets.
*   **Exception-Handling Protocol:**   Traps field length overflow errors.

###### translators/opentag_json.py - OpenTag JSON Translator
*   **Module Purpose:**   OpenTag JSON serialization translator.
*   **Input & Source:**   Internal models and raw OpenTag JSON representations.
*   **Output & Handoff:**   Serialized OpenTag JSON payloads.
*   **Conversions & Transformations:**   Serializes and deserializes core OpenTag dictionary structures.
*   **Validation & Governance Gates:**   Enforces OpenTag schema conformance during translation.
*   **Exception-Handling Protocol:**   Traps invalid key formats during JSON serialization.

--------------------------------------------------------------------------------

###### Hardware Drivers & Interfaces (hardware/)
###### hardware/base.py & hardware/base_reader.py - Abstract Reader Interface & Base Reader
*   **Module Purpose:**   Defines abstract hardware interfaces, background PySide6 worker thread signal routines, chip signature verifications, and payload-to-chip capacity validation rules (validate_chip_for_spec()).
*   **Input & Source:**   Physical reader PCSC command streams and PySide6 worker signals.
*   **Output & Handoff:**   Emits raw page buffers, UID strings, connection states, and write outcomes.
*   **Conversions & Transformations:**   Converts low-level APDU response bytes into high-level application events.
*   **Validation & Governance Gates:**   Implements validate_chip_for_spec() to enforce physical chip capacity limits before write execution.
*   **Exception-Handling Protocol:**   Traps low-level SmartcardExceptions and emits reader disconnected signals.

###### hardware/acr122u.py - ACR122U PCSC Smartcard Driver
*   **Module Purpose:**   PCSC smartcard communication driver for ACR122U readers.
*   **Input & Source:**   APDU command calls and reader byte streams.
*   **Output & Handoff:**   Raw memory block buffers and hardware status codes.
*   **Conversions & Transformations:**   Translates high-level read/write requests into ACR122U-specific APDU command bytes.
*   **Validation & Governance Gates:**   Verifies PCSC connection health and reader response error codes.
*   **Exception-Handling Protocol:**   Traps command timeout errors and resets reader connection handles.

###### hardware/acr1552u.py & hardware/acr1552u_thread.py - ACR1552U PCSC Driver & Worker Thread
*   **Module Purpose:**   PCSC reader communication driver and background thread worker for ACR1552U hardware operations.
*   **Input & Source:**   Asynchronous reader polling triggers and write requests.
*   **Output & Handoff:**   Background thread signals carrying raw memory blocks and tag presence states.
*   **Conversions & Transformations:**   Manages non-blocking thread execution for continuous NFC tag polling.
*   **Validation & Governance Gates:**   Enforces thread-safe locking during concurrent read/write operations.
*   **Exception-Handling Protocol:**   Traps worker thread termination exceptions safely.

###### hardware/chip_profiles.py - NFC Chip Capacity Configuration Profiles
*   **Module Purpose:**   Defines NFC chip memory limits and capacity configuration profiles (e.g., NTAG215).
*   **Input & Source:**   Chip UID headers and type detection codes.
*   **Output & Handoff:**   Chip capacity dictionaries (e.g., user memory page limits, total byte capacities).
*   **Conversions & Transformations:**   Maps chip type codes to structural memory parameters.
*   **Validation & Governance Gates:**   Provides lookup boundaries used by chip validation gates.
*   **Exception-Handling Protocol:**   Traps unknown chip UIDs and returns default NTAG215 profiles.

###### hardware/reader_factory.py - Reader Driver Factory Loader
*   **Module Purpose:**   Dynamically loads and instantiates hardware reader drivers based on connection configurations.
*   **Input & Source:**   Configuration settings specifying reader hardware models.
*   **Output & Handoff:**   Instantiated reader driver objects (ACR122U or ACR1552U).
*   **Conversions & Transformations:**   Dynamically instantiates the correct driver class based on connection strings.
*   **Validation & Governance Gates:**   Validates that requested hardware drivers are supported and available on the system.
*   **Exception-Handling Protocol:**   Traps unsupported hardware models and raises ValueError.

--------------------------------------------------------------------------------

###### GUI Windows, Tabs, Dialogs & Widgets (gui/)
###### gui/main_window.py - Main GUI Application Window Manager
*   **Module Purpose:**   Core QMainWindow coordinating the header action bar, bottom controls, and central QTabWidget layout.
*   **Input & Source:**   User interactions, menu clicks, and background thread signals.
*   **Output & Handoff:**   Coordinates state between header action bars, bottom controls, and central tabs.
*   **Conversions & Transformations:**   Translates window events into pipeline actions.
*   **Validation & Governance Gates:**   Manages window focus and modal dialog states.
*   **Exception-Handling Protocol:**   Traps unhandled UI thread exceptions to prevent application crashes.

###### gui/dialogs/field_editor_dialog.py - Field Editor Modal Dialog
*   **Module Purpose:**   Modal dialog for editing individual schema fields.
*   **Input & Source:**   Field metadata, current values, and user input edits.
*   **Output & Handoff:**   Updated field values returned to active editors.
*   **Conversions & Transformations:**   Converts raw user string inputs into typed schema values.
*   **Validation & Governance Gates:**   Enforces field-level type and range validation before acceptance.
*   **Exception-Handling Protocol:**   Displays input error tooltips on validation failure.

###### gui/dialogs/settings_dialog.py - Application Settings Dialog
*   **Module Purpose:**   Application settings configuration dialog.
*   **Input & Source:**   User preference inputs and current config values.
*   **Output & Handoff:**   Updated configuration parameters saved to config.py.
*   **Conversions & Transformations:**   Converts UI toggles into configuration variables.
*   **Validation & Governance Gates:**   Validates setting parameter ranges before saving.
*   **Exception-Handling Protocol:**   Restores default settings if invalid configurations are entered.

###### gui/dialogs/write_file_request_dialog.py - External Write Request Confirmation Modal
*   **Module Purpose:**   Pre-execution confirmation modal handling external Spoolsonian write requests.
*   **Input & Source:**   External write queue payloads and user confirmation clicks.
*   **Output & Handoff:**   User authorization signals (Begin Writing or Cancel Operation).
*   **Conversions & Transformations:**   Presents raw queue payloads into human-readable summary modals.
*   **Validation & Governance Gates:**   Acts as a mandatory human confirmation gate before executing physical tag writes.
*   **Exception-Handling Protocol:**   Aborts write queuing automatically if closed or cancelled.

###### gui/tabs/raw_inspector_tab.py - Raw Data Inspector Tab
*   **Module Purpose:**   GUI tab displaying raw NDEF memory hex dumps and decoded structure interpretations. Functions as a read-only raw memory inspection interface, independent of layout visualizer widgets.
*   **Input & Source:**   Raw memory byte buffers from reader threads.
*   **Output & Handoff:**   Visual hex grid and parsed NDEF breakdown displays.
*   **Conversions & Transformations:**   Formats raw byte arrays into hexadecimal grid layouts via utils/hex_formatter.py.
*   **Validation & Governance Gates:**   Read-only inspection interface preventing accidental raw memory corruption.
*   **Exception-Handling Protocol:**   Traps raw payload decode exceptions gracefully without crashing the UI thread.

###### gui/tabs/standard_editor_tab.py - Standard Editor V1 Tab
*   **Module Purpose:**   V1 visual schema editor tab enforcing official specification locks.
*   **Input & Source:**   V1 data models and schemas.
*   **Output & Handoff:**   User-edited V1 application models.
*   **Conversions & Transformations:**   Maps UI controls to V1 schema fields.
*   **Validation & Governance Gates:**   Enforces V1 schema validation rules.
*   **Exception-Handling Protocol:**   Traps form field validation errors and highlights invalid spinboxes.

###### gui/tabs/standard_editor_v2_tab.py - Advanced Schema Editor V2 Tab
*   **Module Purpose:**   Advanced schema editor and field builder tab (V2) hosting the Memory Visualizer. Manages dual-view toggling between Target Schema translation layouts and active "in-editing" draft schemas while preserving active state. Enforces official specification locks (official_spec_lock: true), routing edits exclusively through the schema cloning workflow.
*   **Input & Source:**   V2 schemas, translated data models, and user customization inputs.
*   **Output & Handoff:**   Cloned draft schemas and customized model data.
*   **Conversions & Transformations:**   Handles schema cloning workflows and dual-view visualizer state switching.
*   **Validation & Governance Gates:**   Enforces official spec locks (official_spec_lock: true) and validates target spec layout translation constraints.
*   **Exception-Handling Protocol:**   Traps schema validation syntax errors gracefully.

###### gui/tabs/tag_editor_tab.py - Dynamic Tag Editor Tab
*   **Module Purpose:**   Dynamic form and field table tab driven strictly by target schema definitions.
*   **Input & Source:**   Target SSOT schemas and normalized internal models.
*   **Output & Handoff:**   Fully validated user models ready for encoding and writing.
*   **Conversions & Transformations:**   Dynamically renders UI spinboxes, text fields, and dropdowns based on schema metadata.
*   **Validation & Governance Gates:**   Performs real-time field range checking and byte-length limits directly inside UI editors.
*   **Exception-Handling Protocol:**   Traps input data type mismatches and reverts to previous valid field states.

###### gui/widgets/memory_visualizer.py - NFC Memory Visualizer Widget
*   **Module Purpose:**   NFC memory block grid visualizer hosted inside Standard Editor V2. Renders target schema layout allocations, translated model byte boundaries, and field conflict overlays independently of raw byte inspection values.
*   **Input & Source:**   Target schema field definitions and translated model layout structures.
*   **Output & Handoff:**   Color-coded grid widget displaying target layout structures and conflict overlays.
*   **Conversions & Transformations:**   Maps byte offsets to visual grid color blocks and conflict overlays.
*   **Validation & Governance Gates:**   Highlights memory overflow or collision zones across schema layouts in real time.
*   **Exception-Handling Protocol:**   Gracefully handles unmapped byte ranges and schema offset boundary mismatches.

--------------------------------------------------------------------------------

###### Utils, Tests & Sample Data (utils/, tests/, tag_samples/)
###### utils/hex_formatter.py - Hexadecimal Formatting Utility
*   **Module Purpose:**   Formatting utilities for hexadecimal strings and memory byte arrays.
*   **Input & Source:**   Raw byte arrays or integer values.
*   **Output & Handoff:**   Formatted hex strings.
*   **Conversions & Transformations:**   Converts binary data into readable hexadecimal text.
*   **Validation & Governance Gates:**   Sanitizes input types before formatting.
*   **Exception-Handling Protocol:**   Traps non-bytes inputs and returns empty hex strings.

###### tests/ - Integration & Unit Test Suite
*   **Module Purpose:**   CLI startup parameter test suite and IPC transmission integration tests (startup_parameter_test1.py, startup_parameter_test2.py, testsend2.py).
*   **Input & Source:**   CLI argument strings and mock IPC socket payloads.
*   **Output & Handoff:**   Test execution success/failure status codes.
*   **Conversions & Transformations:**   Simulates runtime inputs for validation.
*   **Validation & Governance Gates:**   Asserts expected behaviors against test specifications.
*   **Exception-Handling Protocol:**   Reports assertion failures with detailed tracebacks.

###### tag_samples/ - Sample Payload Baseline Data
*   **Module Purpose:**   Sample desktop, mobile, and diagnostic test payloads (.json, .nfctools-desktop.json, .nfctools-mobile.json).
*   **Input & Source:**   Static test data files.
*   **Output & Handoff:**   Sample JSON models loaded by test routines or parsers.
*   **Conversions & Transformations:**   None.
*   **Validation & Governance Gates:**   Used as reference baselines for parsing and translation regression testing.
*   **Exception-Handling Protocol:**   Logs file read errors if sample files are missing.