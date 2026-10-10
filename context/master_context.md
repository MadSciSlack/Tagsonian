# Tagsonian System Master Context Document (`master_context.md`)

## 1. Governance & Immutability Rules
*   **Human Approval Authority:** Documents, files, and modules designated as Single Source of Truth (SSOT) can only be updated with explicit approval by the human.
*   **Hierarchy Resolution:** The Agent must not make assumptions about directory or module hierarchy. If hierarchy is unspecified, the Agent must request clarification and present options for approval before generating code.
*   **Dependency Restrictions:** The Agent must not specify the installation or addition of third-party dependencies without prior discussion with the human.
*   **Code Location Specificity:** The Agent must explicitly specify which module or file provided code should be implemented into, supplying line numbers or identifiable code landmarks to assist in locating update locations.
*   **File Index Governance:** `filefolderindex.md` is the absolute SSOT for what files and folders exist within the project repository. Whenever a new file is specified, a folder is created, or files are moved, `filefolderindex.md` must be updated with full descriptive summaries following the type-specific guidelines below.
*   **Artifact Prohibition:** Provided code and text must not contain artifact strings or citations in the generated codebase or documentation responses.

---

## 2. Directory-to-Context Selection Matrix

When executing tasks, writing code, or evaluating architectural changes, the Agent must locate and reference the context document corresponding strictly to the target repository folder:

### `schemas/` → `context_schemas.md`
*   **Target Directory:** `schemas/`
*   **Operational Scope:** Structural definitions of bit/byte offsets, data types, field names, scaling factors, units, tooltips, and validation boundaries.
*   **Agent Reference Criteria:** Reference when viewing, creating, or validating schema specifications (e.g., `opentag_v2_003.json`, `openprinttag_v1.json`), enforcing `official_spec_lock` immutability, or executing the schema cloning workflow with RFC 4122 compliant UUID v4 generation (`metadata.guid`).

### `tagsonian/models/` → `context_models.md`
*   **Target Directory:** `tagsonian/models/`
*   **Operational Scope:** Internal data structures, write task representations, status enumerations, and runtime models.
*   **Agent Reference Criteria:** Reference when modifying task data structures (e.g., `write_task.py`), `TaskStatus`/`TaskSource` enums, or queue payload state management.

### `ingestion/` → `context_ingestion.md`
*   **Target Directory:** `ingestion/`
*   **Operational Scope:** Entry point file readers, raw dictionary loaders, and initial incoming memory allocation.
*   **Agent Reference Criteria:** Reference when modifying raw `.json` file readers, `JSONImporter` pipelines, or initial unmapped incoming state allocation (`self.original_raw_model`).

### `parsers/` → `context_parsers.md`
*   **Target Directory:** `parsers/`
*   **Operational Scope:** Binary stream decoding, NDEF record extraction, TLV block parsing, and MIME payload extraction.
*   **Agent Reference Criteria:** Reference when modifying binary parsing logic (e.g., `openprinttag_parser.py`), verifying pipeline isolation (ensuring decoders never invoke mappers or inject aliases), or processing raw byte arrays.

### `encoders/` → `context_encoders.md`
*   **Target Directory:** `encoders/`
*   **Operational Scope:** Binary structure packing, NDEF/TLV stream encoding, and binary payload generation.
*   **Agent Reference Criteria:** Reference when constructing binary memory buffers from normalized data models or checking chip memory bounds before binary output.

### `writers/` → `context_writers.md`
*   **Target Directory:** `writers/`
*   **Operational Scope:** Binary image generation matching byte offsets, abstract writer interfaces, and scaling execution.
*   **Agent Reference Criteria:** Reference when modifying hardware write routines, scaling unscaled floats into binary integer byte arrays, or running chip capacity verification (`validate_chip_for_spec()`).

### `exporters/` → `context_exporters.md`
*   **Target Directory:** `exporters/`
*   **Operational Scope:** Serializing state to formatted files (`.json`, `.txt`), generating hex memory diagnostic dumps, and file I/O handling.
*   **Agent Reference Criteria:** Reference when modifying output report generation, `file_exporter.py`, disk error exception handling, or saving formatted outputs.

### `mappings/` & `mappings/directional/` → `context_mappings.md`
*   **Target Directory:** `mappings/` and `mappings/directional/`
*   **Operational Scope:** Cross-schema translation dispatching, abstract mapper interfaces (`BaseMapper`), and directional mapping submodules.
*   **Agent Reference Criteria:** Reference when modifying the central translation dispatcher (`mappings/mapper.py`), implementing or altering directional mappers, tracking zero-telemetry mapping coverage (`debug_mapping_coverage()`), or managing unscaled schema translations.

### `translators/` → `context_translators.md`
*   **Target Directory:** `translators/`
*   **Operational Scope:** Format translation adapters for external target tools outside core internal models.
*   **Agent Reference Criteria:** Reference when editing third-party file formats like NFC Tools Desktop/Mobile (`nfc_tools_desktop.py`, `nfc_tools_mobile.py`) or OpenTag JSON translators.

### `hardware/` → `context_hardware.md`
*   **Target Directory:** `hardware/`
*   **Operational Scope:** PCSC reader communication drivers, PySide6 background worker threads, and hardware validation layers.
*   **Agent Reference Criteria:** Reference when updating physical card reader drivers (e.g., `acr122u.py`, `acr1552u.py`), worker thread signal routines, or chip signature validation logic.

### `gui/` → `context_gui.md`
*   **Target Directory:** `gui/`
*   **Operational Scope:** Visual components, window layout management, editor tabs, form generation, and pre-execution confirmation modals.
*   **Agent Reference Criteria:** Reference when editing PySide6 UI views, dynamic schema-driven form generation, or pre-execution confirmation dialogs (`write_file_request_dialog.py`).

### `ipc/` & `cli/` → `context_ipc.md`
*   **Target Directory:** Root execution files, IPC socket handlers, and CLI parameter processors.
*   **Operational Scope:** Inter-process communication with Spoolsonian, command-line launch parameter handling, and payload validation gates.
*   **Agent Reference Criteria:** Reference when editing IPC socket server endpoints in `main.py`, processing `--write-request <path>` CLI flags, or validating Spoolsonian queue payloads against active SSOT schemas before opening confirmation modals.

### `tag_samples/` & `tests/` → `context_testing.md`
*   **Target Directory:** `tag_samples/` and `tests/`
*   **Operational Scope:** Test payload baseline files, automated unit/integration test routines, and regression testing.
*   **Agent Reference Criteria:** Reference when writing or running test cases (e.g., `startup_parameter_test1.py`) or verifying sample payloads (`.nfctools-desktop.json`, `.bin`) against expected parsing and translation outputs.

---

## 3. Description Guidelines for `filefolderindex.md`

Whenever `filefolderindex.md` is created or updated, file entries must explicitly identify their module type and conform to the following description requirements:

1.  **Mappers & Directional Submodules (`mappings/`, `mappings/directional/`):** Must explicitly state the source and target schema standards using a directional format (e.g., `openprinttag_to_opentag.py - OpenPrintTag V1 to OpenTag V2 directional mapper`).
2.  **Parsers (`parsers/`) & Encoders (`encoders/`):** Must specify the exact data serialization format, binary structure, or protocol being parsed or generated (e.g., `openprinttag_parser.py - CBOR parser for OpenPrintTag formats`).
3.  **Schemas (`schemas/`):** Must identify the standard name, version, and whether the schema holds official locked SSOT status (e.g., `opentag_v2_003.json - Immutable V2 Official Spec SSOT`).
4.  **Hardware Drivers & Interfaces (`hardware/`):** Must specify the exact hardware device model, communication protocol, or abstraction layer (e.g., `acr1552u.py - ACR1552U PCSC reader communication driver`).
5.  **GUI Windows, Tabs, Dialogs & Widgets (`gui/`):** Must designate the UI container category (tab, dialog, window, widget) and its functional purpose (e.g., `write_file_request_dialog.py - Pre-execution confirmation modal for external write requests`).
6.  **Translators (`translators/`) & Exporters/Writers (`exporters/`, `writers/`):** Must state the external file schema or output medium targeted outside core internal models (e.g., `nfc_tools_desktop.py - NFC Tools desktop format translator`).
7.  **Tests (`tests/`):** Must state the feature set, CLI parameter combination, or integration routine being validated (e.g., `startup_parameter_test1.py - Startup CLI parameter test suite 1`).