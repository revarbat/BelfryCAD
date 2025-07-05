"""
Dialogs package for BelfryCAD.

This package contains all dialog windows and wizards including:
- Tool table and specification dialogs
- Preferences dialog
- G-code backtracer dialog
- Gear wizard dialog
- Feed wizard dialog
"""

from .tool_table_dialog import ToolTableDialog
from .tool_spec_dialog import ToolSpecDialog
from .gcode_backtracer_dialog import GCodeBacktracerDialog
from .gear_wizard_dialog import GearWizardDialog
from .preferences_dialog import PreferencesDialog
from .feed_wizard import FeedWizardDialog

__all__ = [
    'ToolTableDialog',
    'ToolSpecDialog', 
    'GCodeBacktracerDialog',
    'GearWizardDialog',
    'PreferencesDialog',
    'FeedWizardDialog'
] 