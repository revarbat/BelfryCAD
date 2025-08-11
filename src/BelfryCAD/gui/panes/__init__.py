"""
Panes package for BelfryCAD GUI components.

This package contains all the pane-related GUI components including
info panes, configuration panes, snaps panes, and tool palettes.
"""

from .info_pane import InfoPane, create_info_pane
from .config_pane import ConfigPane
from .snaps_pane import SnapsToolBar, SnapsPaneInfo, create_snaps_toolbar
from .tool_palette import ToolPalette
from .object_tree_pane import ObjectTreePane


__all__ = [
    'InfoPane',
    'create_info_pane',
    'ConfigPane',
    'SnapsToolBar',
    'SnapsPaneInfo',
    'create_snaps_toolbar',
    'ToolPalette',
    'ObjectTreePane'
]
