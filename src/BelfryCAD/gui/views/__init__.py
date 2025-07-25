"""
Views for BelfryCAD.

This package contains pure UI components that display data from ViewModels.
All views should be framework-specific (PySide6) and contain no business logic.
"""

from .graphics_items import *
from .preferences_dialog import PreferencesDialog

__all__ = [
    # Graphics items
    'CadItem',
    'LineCadItem',
    'CircleCenterRadiusCadItem',
    'RectangleCadItem',
    # Dialogs
    'PreferencesDialog'
] 