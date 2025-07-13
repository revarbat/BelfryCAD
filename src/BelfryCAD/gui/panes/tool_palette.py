"""
Floating Tool Palette

A popup widget that shows all tools in a specific category
"""

from typing import TYPE_CHECKING, List, Dict

from PySide6.QtWidgets import (
    QHBoxLayout, QToolButton, QFrame
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QKeyEvent

if TYPE_CHECKING:
    from ...tools.base import ToolDefinition, ToolCategory


class ToolPalette(QFrame):
    """Floating palette showing tools for a specific category"""

    # Signal emitted when a tool is selected
    tool_selected = Signal(str)  # tool_token

    def __init__(self, category: 'ToolCategory', tools: List['ToolDefinition'],
                 icon_loader, parent=None):
        super().__init__(parent)
        self.category = category
        self.tools = tools
        self.icon_loader = icon_loader
        self.tool_buttons = []  # Store references to tool buttons
        self.secondary_key_mappings = self._create_secondary_key_mappings()
        self.iconsize = 40

        self._setup_ui()

    def _create_secondary_key_mappings(self) -> Dict[str, str]:
        """Create secondary key mappings for tools within this category

        Raises:
            ValueError: If multiple tools in the same category have the same
                       secondary key
        """
        mappings = {}
        key_conflicts = {}  # Track which tools use each key

        # Map the tools from this palette to their secondary keys
        for tool_def in self.tools:
            if tool_def.secondary_key:
                key = tool_def.secondary_key
                if key in mappings:
                    # Record the conflict for error reporting
                    if key not in key_conflicts:
                        key_conflicts[key] = [mappings[key]]
                    key_conflicts[key].append(tool_def.token)
                else:
                    mappings[key] = tool_def.token

        # Check for conflicts and throw error
        if key_conflicts:
            conflict_details = []
            for key, tools in key_conflicts.items():
                conflict_details.append(f"Key '{key}': {', '.join(tools)}")

            error_msg = (
                f"Duplicate secondary shortcut keys found in "
                f"{self.category.value} category:\n"
                + "\n".join(conflict_details) +
                "\n\nEach tool in a category must have a unique secondary key."
            )
            raise ValueError(error_msg)

        return mappings

    def _setup_ui(self):
        """Set up the palette UI"""
        self.setWindowFlags(
            Qt.WindowType.Popup |
            Qt.WindowType.FramelessWindowHint
        )
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setLineWidth(1)

        # Enable keyboard focus for the palette
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Create horizontal layout for tool buttons (single row)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create buttons for each tool in a single horizontal row
        for tool_def in self.tools:
            button = QToolButton()
            button.setFixedSize(self.iconsize, self.iconsize)
            button.setIconSize(QSize(self.iconsize, self.iconsize))  # Ensure icons are 48x48

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
                margin: 0px;
                padding: 0px;
            }
            QToolButton:hover {
                background-color: #c0c0ff;
            }
            QToolButton:pressed {
                background-color: #c0c0ff;
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
        if event.key() == Qt.Key.Key_Escape:
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
