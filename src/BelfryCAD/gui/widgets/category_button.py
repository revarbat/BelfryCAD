"""
Category Tool Button

A toolbar button that represents a tool category and can change its icon
to show the currently selected tool in that category.
"""

from typing import TYPE_CHECKING, List, Optional
if TYPE_CHECKING:
    from ...tools.base import ToolDefinition, ToolCategory

from PySide6.QtWidgets import QToolButton
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QMouseEvent

from ..panes.tool_palette import ToolPalette


class CategoryToolButton(QToolButton):
    """A toolbar button that represents a category and shows a tool palette"""

    # Signal emitted when a tool is selected from the palette
    tool_selected = Signal(str)  # tool_token

    # Class variable to track the currently visible palette
    _current_visible_palette = None

    @classmethod
    def _dismiss_current_palette(cls):
        """Dismiss the currently visible palette, if any"""
        if cls._current_visible_palette:
            cls._current_visible_palette.hide()
            cls._current_visible_palette = None

    def __init__(
            self,
            category: 'ToolCategory',
            tools: List['ToolDefinition'],
            icon_loader,
            parent=None
    ):
        super().__init__(parent)
        self.iconsize = 40
        self.category = category
        self.tools = tools
        self.icon_loader = icon_loader
        # Default to first tool
        self.current_tool = tools[0] if tools else None
        self.tool_palette = None
        # Track if this category's tool is currently active
        self.is_active = False

        # Timer for press-and-hold detection
        self.hold_timer = QTimer()
        self.hold_timer.setSingleShot(True)
        # Connection will be made dynamically in mousePressEvent

        self._setup_ui()

    def _setup_ui(self):
        """Set up the button UI"""
        self.setFixedSize(self.iconsize, self.iconsize)
        self.setIconSize(QSize(self.iconsize, self.iconsize))

        # Update tooltip based on whether category has one or multiple tools
        if len(self.tools) == 1:
            self.setToolTip(f"{self.tools[0].name}")
        else:
            self.setToolTip(f"{self.category.value} Tools")

        # Set initial icon (first tool in category)
        self._update_icon()

        # All categories now use press-and-hold behavior
        # handled by mouse events instead of clicked signal

        # Style the button
        self._update_stylesheet()

    def _update_stylesheet(self):
        """Update the button stylesheet based on active state"""
        if self.is_active:
            # Active state - darkened background
            self.setStyleSheet("""
                QToolButton {
                    border: none;
                    margin: 0px;
                    padding: 0px;
                    background-color: rgba(0, 0, 0, 40);
                }
                QToolButton:hover {
                    background-color: rgba(0, 0, 0, 60);
                }
                QToolButton:pressed {
                    background-color: rgba(0, 0, 0, 80);
                }
            """)
        else:
            # Normal state
            self.setStyleSheet("""
                QToolButton {
                    border: none;
                    margin: 0px;
                    padding: 0px;
                }
                QToolButton:hover {
                    background-color: rgba(255, 255, 255, 30);
                }
                QToolButton:pressed {
                    background-color: rgba(255, 255, 255, 50);
                }
            """)

    def _update_icon(self):
        """Update the button icon to show the current tool"""
        if self.current_tool:
            icon = self.icon_loader(self.current_tool.icon)
            if icon:
                self.setIcon(icon)
                # Update tooltip for single tool categories
                if len(self.tools) == 1:
                    self.setToolTip(f"{self.current_tool.name}")
                else:
                    category_name = self.category.value
                    tool_name = self.current_tool.name
                    tooltip = f"{category_name}: {tool_name}"
                    self.setToolTip(tooltip)
            else:
                self.setText(self.current_tool.name[:2])

    def _activate_single_tool(self):
        """Directly activate the single tool in this category"""
        # Dismiss any currently visible palette before activating this tool
        self._dismiss_current_palette()

        if self.current_tool:
            self.tool_selected.emit(self.current_tool.token)

    def _show_palette(self):
        """Show the tool palette"""
        # Dismiss any currently visible palette before showing this one
        self._dismiss_current_palette()

        if not self.tool_palette:
            self.tool_palette = ToolPalette(
                self.category, self.tools, self.icon_loader, self.parent()
            )
            self.tool_palette.tool_selected.connect(self._on_tool_selected)

        # Position palette to the right of this button
        button_rect = self.geometry()
        global_pos = self.parent().mapToGlobal(button_rect.topRight()) # type: ignore
        global_pos.setX(global_pos.x() + 5)  # Small gap

        # Track this palette as the currently visible one
        CategoryToolButton._current_visible_palette = self.tool_palette

        self.tool_palette.show_at_position(global_pos)

    def _on_tool_selected(self, tool_token: str):
        """Handle tool selection from palette"""
        # Find the selected tool definition
        for tool_def in self.tools:
            if tool_def.token == tool_token:
                self.current_tool = tool_def
                self._update_icon()
                break

        # Clear the tracked palette since it will be hidden
        CategoryToolButton._current_visible_palette = None

        # Emit the tool selection signal
        self.tool_selected.emit(tool_token)

    def set_current_tool(self, tool_token: str):
        """Set the current tool programmatically"""
        for tool_def in self.tools:
            if tool_def.token == tool_token:
                self.current_tool = tool_def
                self._update_icon()
                break

    def set_active(self, is_active: bool):
        """Set the active state of this category button"""
        if self.is_active != is_active:
            self.is_active = is_active
            self._update_stylesheet()

    def get_current_tool_token(self) -> Optional[str]:
        """Get the token of the currently selected tool in this category"""
        return self.current_tool.token if self.current_tool else None

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events for press-and-hold behavior"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Start timer for press-and-hold behavior (500ms = 0.5 seconds)
            # This applies to both single and multi-tool categories
            if len(self.tools) == 1:
                try:
                    self.hold_timer.timeout.disconnect()
                except (TypeError, RuntimeError):
                    pass  # No connections to disconnect
                self.hold_timer.timeout.connect(self._activate_single_tool)
            else:
                try:
                    self.hold_timer.timeout.disconnect()
                except (TypeError, RuntimeError):
                    pass  # No connections to disconnect
                self.hold_timer.timeout.connect(self._show_palette)
            self.hold_timer.start(500)

        # Call parent implementation to maintain normal button behavior
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Stop the hold timer for both single and multi-tool categories
            self.hold_timer.stop()

            if len(self.tools) == 1:
                # Single tool: activate immediately on quick click
                if self.current_tool:
                    self._dismiss_current_palette()
                    self.tool_selected.emit(self.current_tool.token)
            else:
                # Multi-tool: activate current tool on quick click
                # if palette not visible
                palette_not_visible = (not self.tool_palette or
                                       not self.tool_palette.isVisible())
                if palette_not_visible and self.current_tool:
                    self._dismiss_current_palette()
                    self.tool_selected.emit(self.current_tool.token)

        # Call parent implementation
        super().mouseReleaseEvent(event)
