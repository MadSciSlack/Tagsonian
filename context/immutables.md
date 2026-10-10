Immutable Constraints:
- Documents, files, and modules specified in documentation as SSOT can only be updated with approval by the human.
- The Agent must not make assumptions about heirarchy. If the documentation in the project notebook doesn't specify the heirarchy then the agent must request clarification and must present options for approval before providing generated code.
- The Agent must specify which module / file provided code should be implemented into. The agent should provide line numbers or identifiable code landmarks to assist in locating the correct update locations.
- The Agent must reference filefolderindex.md as the SSOT for what files and folders exist within the project. The Agent will use this to prevent the creation of duplicate or redundant files.

- The Agent must provide an updated filefolderindex.md file complete with descriptive summaries whenever a new file is specified, a new folder is created, or files are moved between folders. These descriptions must explicitly identify the module type (e.g., translator, encoder, parser, schema, hardware driver, GUI component, test script) and include the information types covered below in "Description Guidelines by Module Type":
Description Guidelines by Module Type:
To maintain strict Single Source of Truth (SSOT) governance across the repository, file descriptions in `filefolderindex.md` must follow these type-specific requirements:

1. **Mappers & Directional Submodules (`mappings/`, `mappings/directional/`)**
   * *Requirement:* Must explicitly state the source and target schema standards using a clear directional format.
   * *Example:* `openprinttag_to_opentag.py - OpenPrintTag V1 to OpenTag V2 directional mapper.`
2. **Parsers (`parsers/`) & Encoders (`encoders/`)**
   * *Requirement:* Must specify the exact data serialization format, binary structure, or protocol being parsed or generated.
   * *Example:* `openprinttag_parser.py - CBOR parser for OpenPrintTag formats.`
3. **Schemas (`schemas/`)**
   * *Requirement:* Must identify the standard name, version, and whether the schema holds official locked SSOT status.
   * *Example:* `opentag_v2_003.json - Immutable V2 Official Spec SSOT.`
4. **Hardware Drivers & Interfaces (`hardware/`)**
   * *Requirement:* Must specify the exact hardware device model, communication protocol, or abstraction layer.
   * *Example:* `acr1552u.py - ACR1552U PCSC reader communication driver.`
5. **GUI Windows, Tabs, Dialogs & Widgets (`gui/`)**
   * *Requirement:* Must designate the UI container category (tab, dialog, window, widget) and its functional purpose.
   * *Example:* `write_file_request_dialog.py - Pre-execution confirmation modal for external write requests.`
6. **Translators (`translators/`) & Exporters/Writers (`exporters/`, `writers/`)**
   * *Requirement:* Must state the external file schema or output medium targeted outside core internal models.
   * *Example:* `nfc_tools_desktop.py - NFC Tools desktop format translator.`
7. **Tests (`tests/`)**
   * *Requirement:* Must state the feature set, CLI parameter combination, or integration routine being validated.
   * *Example:* `startup_parameter_test1.py - Startup CLI parameter test suite 1.`

- The Agent must not specify the installation or addition of dependencies without prior discussion with the human.
- The Agent must review the MD documentation to determine intent of each module prior to generating updates.
- The Agent must propose updates to the MD documentations when the intent of a module needs to be change as part of an update. These changes must be approved by the human.