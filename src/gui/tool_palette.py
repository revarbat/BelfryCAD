"""
Floating Tool Palette

A popup widget that shows all tools in a specific category
"""

from PySide6.QtWidgets import (
    QHBoxLayout, QToolButton, QFrame
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QKeyEvent
from typing import List, Dict
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
        self.tool_buttons = []  # Store references to tool buttons
        self.secondary_key_mappings = self._create_secondary_key_mappings()

        self._setup_ui()

    def _create_secondary_key_mappings(self) -> Dict[str, str]:
        """Create secondary key mappings for tools within this category"""
        mappings = {}

        # Map the tools from this palette to their secondary keys
        for tool_def in self.tools:
            # Special case for ellipses 
            if (self.category == ToolCategory.ELLIPSES and 
                    tool_def.token == "ELLIPSEOPTAN"):
                mappings["O"] = "ELLIPSEOPTAN"
            elif tool_def.secondary_key:
                mappings[tool_def.secondary_key] = tool_def.token

        return mappings

    def _setup_ui(self):
        """Set up the palette UI"""
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(1)

        # Enable keyboard focus for the palette
        self.setFocusPolicy(Qt.StrongFocus)

        # Create horizontal layout for tool buttons (single row)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create buttons for each tool in a single horizontal row
        for tool_def in self.tools:
            button = QToolButton()
            button.setFixedSize(48, 48)
            button.setIconSize(QSize(48, 48))  # Ensure icons are 48x48

            # Create tooltip with secondary shortcut if available
            tooltip = tool_def.name
            secondary_key = self._get_secondary_key_for_tool(tool_def.token)
            if secondary_key:
                tooltip += f" ({secondary_key})"
            button.setToolTip(tooltip)

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
            self.tool_buttons.append(button)

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

    def _get_secondary_key_for_tool(self, tool_token: str) -> str:
        """Get the secondary key for a specific tool token"""
        for key, token in self.secondary_key_mappings.items():
            if token == tool_token:
                return key
        return ""

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard events for secondary tool selection"""
        key_text = event.text().upper()

        # Check if the pressed key matches any secondary shortcut
        if key_text in self.secondary_key_mappings:
            tool_token = self.secondary_key_mappings[key_text]
            self._on_tool_clicked(tool_token)
            return

        # Handle Escape key to close palette
        if event.key() == Qt.Key_Escape:
            self.hide()
            return

        # Pass other events to parent
        super().keyPressEvent(event)

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
        # Set focus to enable keyboard input
        self.setFocus()
