"""
Two Column Toolbar Widget

A custom widget that provides a two-column layout for toolbar buttons.
"""

from PySide6.QtWidgets import QWidget, QGridLayout, QToolButton
from PySide6.QtCore import Qt, QSize


class ColumnarToolbarWidget(QWidget):
    """
    A widget that provides a two-column layout for toolbar buttons.
    """
    
    def __init__(self, parent=None, max_cols=2):
        super().__init__(parent)
        self.buttons = []
        self.max_cols = max_cols
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
            btn_cnt = len(self.buttons)
            row = len(self.buttons) // self.max_cols
            column = btn_cnt % self.max_cols
        
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
    
    def set_max_columns(self, max_cols: int):
        """Update the maximum number of columns and reorganize the layout."""
        if self.max_cols != max_cols:
            self.max_cols = max_cols
            
            # Clear the current layout
            for button in self.buttons:
                self._layout.removeWidget(button)
            
            # Re-add all buttons with the new column layout
            for i, button in enumerate(self.buttons):
                row = i // self.max_cols
                column = i % self.max_cols
                self._layout.addWidget(button, row, column)
            
            # Update column stretches
            for col in range(self.max_cols):
                self._layout.setColumnStretch(col, 0) 