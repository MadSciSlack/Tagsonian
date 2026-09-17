# gui/tabs/__init__.py
from .raw_inspector_tab import RawInspectorTab
from .standard_editor_tab import StandardEditorTab
from .standard_editor_v2_tab import StandardEditorV2Tab
from .tag_editor_tab import TagEditorTab

__all__ = [
    "TagEditorTab",
    "RawInspectorTab",
    "StandardEditorTab",
    "StandardEditorV2Tab",
]