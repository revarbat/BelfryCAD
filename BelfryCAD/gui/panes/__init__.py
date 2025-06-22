"""
Panes package for BelfryCAD GUI components.

This package contains all the pane-related GUI components including
info panes, configuration panes, layer panes, snaps panes, and tool palettes.
"""

from .info_pane import InfoPane, create_info_pane
from .config_pane import ConfigPane
from .layer_pane import LayerPane, LayerPaneInfo
from .snaps_pane import SnapsPane, SnapsPaneInfo, create_snaps_pane
from .tool_palette import ToolPalette
from .category_button import CategoryToolButton

__all__ = [
    'InfoPane',
    'create_info_pane',
    'ConfigPane',
    'LayerPane',
    'LayerPaneInfo',
    'SnapsPane',
    'SnapsPaneInfo',
    'create_snaps_pane',
    'ToolPalette',
    'CategoryToolButton',
]
