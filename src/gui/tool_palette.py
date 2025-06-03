"""
Floating Tool Palette

A popup widget that shows all tools in a specific category
"""

from PySide6.QtWidgets import (
    QHBoxLayout, QToolButton, QFrame
)
from PySide6.QtCore import Qt, Signal, QSize
from typing import List
from src.tools.base import ToolDefinition, ToolCategory


class ToolPalette(QFrame):
    """Floating palette showing tools for a specific category"""
    
    # Signal emitted when a tool is selected
    tool_selected = Signal(str)  # tool_token
    
    def __init__(self, category: ToolCategory, tools: List[ToolDefinition], 
                 icon_loader, parent=None):
        super().__init__(parent)
        self.category = category
        self.tools = tools
        self.icon_loader = icon_loader
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the palette UI"""
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(1)
        
        # Create horizontal layout for tool buttons (single row)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create buttons for each tool in a single horizontal row
        for tool_def in self.tools:
            button = QToolButton()
            button.setFixedSize(48, 48)
            button.setIconSize(QSize(48, 48))  # Ensure icons are 48x48
            button.setToolTip(tool_def.name)
            
            # Load icon
            icon = self.icon_loader(tool_def.icon)
            if icon:
                button.setIcon(icon)
            else:
                button.setText(tool_def.name[:2])  # First 2 chars as fallback
            
            # Connect click to tool selection
            button.clicked.connect(
                lambda checked, token=tool_def.token:
                self._on_tool_clicked(token)
            )
            
            # Add to horizontal layout
            layout.addWidget(button)
        
        # Style the palette
        self.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #888;
            }
            QToolButton {
                border: none;
                background-color: white;
                margin: 0px;
                padding: 0px;
            }
            QToolButton:hover {
                background-color: #e0e0e0;
            }
            QToolButton:pressed {
                background-color: #d0d0d0;
            }
        """)

    def _on_tool_clicked(self, tool_token: str):
        """Handle tool button click"""
        self.tool_selected.emit(tool_token)
        self.hide()
    
    def show_at_position(self, global_pos):
        """Show the palette at the specified global position"""
        self.move(global_pos)
        self.show()
        self.raise_()
        self.activateWindow()
