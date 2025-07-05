"""
Two Column Toolbar Widget

A custom widget that provides a two-column layout for toolbar buttons.
"""

from PySide6.QtWidgets import QWidget, QGridLayout, QToolButton
from PySide6.QtCore import Qt, QSize


class TwoColumnToolbarWidget(QWidget):
    """
    A widget that provides a two-column layout for toolbar buttons.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.buttons = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the two-column grid layout."""
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 0)
        self._layout = layout
    
    def add_button(self, button: QToolButton, row: int = -1, column: int = -1):
        """
        Add a button to the two-column layout.
        
        Args:
            button: The QToolButton to add
            row: Row position (0 or 1), if -1 will auto-place
            column: Column position (0 or 1), if -1 will auto-place
        """
        if row == -1 or column == -1:
            # Auto-place: find the next available position
            if len(self.buttons) % 2 == 0:
                # Even number of buttons, place in first column
                row = len(self.buttons) // 2
                column = 0
            else:
                # Odd number of buttons, place in second column
                row = len(self.buttons) // 2
                column = 1
        else:
            # Use specified position
            row = max(0, min(row, 1))  # Ensure 0 or 1
            column = max(0, min(column, 1))  # Ensure 0 or 1
        
        self._layout.addWidget(button, row, column)
        self.buttons.append(button)
    
    def clear(self):
        """Clear all buttons from the layout."""
        for button in self.buttons:
            self._layout.removeWidget(button)
            button.setParent(None)
        self.buttons.clear()
    
    def get_buttons(self):
        """Get all buttons in the widget."""
        return self.buttons.copy()
    
    def set_button_size(self, size: QSize):
        """Set the size for all buttons."""
        for button in self.buttons:
            button.setFixedSize(size)
    
    def set_icon_size(self, size: QSize):
        """Set the icon size for all buttons."""
        for button in self.buttons:
            button.setIconSize(size) 