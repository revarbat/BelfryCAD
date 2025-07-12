"""
Snaps Toolbar for BelfryCad.

This module provides a PySide6/Qt toolbar for managing snap settings
in the CAD application.
"""

import os
import sys
import platform

from typing import Optional, List, Tuple

from PySide6.QtWidgets import (
    QToolBar, QToolButton, QApplication, QMenu
)
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtGui import QKeySequence, QShortcut, QFont, QIcon, QAction

from ..icon_manager import get_icon


class SnapsPaneInfo:
    """Global snap pane information storage."""

    def __init__(self):
        self.snap_types = [
            ("grid", "&Grid", True, "snap-grid"),
            ("controlpoints", "Contro&l Points", True, "snap-controlpoints"),
            ("midpoints", "&Midpoints", True, "snap-midpoint"),
            ("quadrants", "&Quadrants", True, "snap-quadrant"),
            ("tangents", "&Tangents", False, "snap-tangent"),
            ("contours", "C&ontours", False, "snap-contours"),
            ("intersect", "&Intersections", False, "snap-intersection"),
            ("perpendicular", "&Perpendicular", False, "snap-perpendicular"),
            ("angles", "A&ngles", False, "snap-angles"),
        ]
        self.snap_states = {}
        self.snap_all = True
        self.snap_buttons = {}  # Changed from checkboxes to buttons
        self.update_timer = None


# Global instance
snaps_pane_info = SnapsPaneInfo()


class SnapsToolBar(QToolBar):
    """
    Snap settings toolbar for managing CAD snap modes.
    """

    # Signals
    snap_changed = Signal(str, bool)  # snap_type, enabled
    all_snaps_changed = Signal(bool)  # all_enabled

    def __init__(self, canvas=None, parent: Optional[QToolBar] = None):
        """
        Initialize the snap toolbar.

        Args:
            canvas: Canvas object reference
            parent: Parent widget, if any
        """
        super().__init__(parent)
        self.iconsize = 36
        self.canvas = canvas
        self._init_ui()
        self._setup_shortcuts()

        # Schedule initial update
        QTimer.singleShot(1000, self.update_snaps)

    def _init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Snaps")
        self.setIconSize(QSize(self.iconsize, self.iconsize))
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.setMovable(True)
        
        # Apply custom stylesheet
        self.setStyleSheet("""
            QToolBar {
                margin: 0px;
                border: 1px solid #cccccc;
                spacing: 2px;
            }
            QToolButton {
                margin: 0px;
                padding: 0px;
                border: none;
                background-color: #dddddd;
            }
            QToolButton:hover {
                background-color: #e0e0e0;
            }
            QToolButton:pressed {
                background-color: #d0d0d0;
            }
            QToolButton:checked {
                background-color: #ccccff;
            }
            QToolButton:disabled {
                background-color: #eeeeee;
                border: 1px solid #cccccc;
            }
        """)

        # Create two-column widget for snaps
        from ..views.widgets.columnar_toolbar import ColumnarToolbarWidget
        self.snaps_widget = ColumnarToolbarWidget()
        self.addWidget(self.snaps_widget)
        
        # Initialize snap buttons
        self._create_snap_buttons()
        
        # Set up context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts for snap toggles."""
        # Alt+A for "All Snaps"
        all_shortcut = QShortcut(QKeySequence("Alt+A"), self)
        all_shortcut.activated.connect(self.all_snaps_button.toggle)

        # Setup shortcuts for individual snaps
        for snap_type, snap_name, default_val, icon_name in snaps_pane_info.snap_types:
            self._setup_snap_shortcut(snap_type, snap_name)

    def _setup_snap_shortcut(self, snap_type: str, snap_name: str):
        """Setup keyboard shortcut for a specific snap type."""
        accel = self._extract_accelerator(snap_name)
        if accel:
            shortcut = QShortcut(QKeySequence(f"Alt+{accel.upper()}"), self)
            shortcut.activated.connect(
                lambda st=snap_type: self._toggle_snap(st)
            )

    def _extract_accelerator(self, name: str) -> Optional[str]:
        """Extract accelerator key from name with & marker."""
        pos = name.find("&")
        if pos >= 0 and pos + 1 < len(name):
            return name[pos + 1].lower()
        return None

    def _process_display_name(self, snap_name: str) -> str:
        """Process snap name to create display name with accelerator."""
        display_name = snap_name.replace("&", "")
        accel = self._extract_accelerator(snap_name)
        if accel:
            alt_rep = "⌥" if platform.system() == "Darwin" else "Alt+"
            display_name = f"Snap to {display_name} ({alt_rep}{accel.upper()})"
        return display_name

    def _create_button_with_icon(self, icon_name: str, tooltip: str, 
                                checked: bool = False, text_fallback: str = "") -> QToolButton:
        """Create a button with icon or text fallback."""
        button = QToolButton()
        button.setCheckable(True)
        button.setChecked(checked)
        button.setToolTip(tooltip)
        #button.setFixedSize(QSize(self.iconsize, self.iconsize))

        # Load and set icon
        icon = get_icon(icon_name)
        if not icon.isNull():
            button.setIcon(icon)
            button.setIconSize(QSize(self.iconsize, self.iconsize))
        else:
            # If no icon, use text on button
            button.setText(text_fallback or tooltip[:2].upper())
            button.setFont(QFont("Arial", 8))

        return button

    def _create_snap_buttons(self):
        """Create buttons for all snap types."""
        alt_rep = "⌥" if platform.system() == "Darwin" else "Alt+"

        # Create "All Snaps" icon button at the beginning
        self.all_snaps_button = self._create_button_with_icon(
            "snap-enable" if snaps_pane_info.snap_all else "snap-disable",
            f"Snaps Enabled ({alt_rep}A)" if snaps_pane_info.snap_all else f"Snaps Disabled ({alt_rep}A)",
            snaps_pane_info.snap_all,
            "All"
        )
        
        # Connect to state change to update icon
        self.all_snaps_button.toggled.connect(self._update_all_snaps_icon)
        self.all_snaps_button.toggled.connect(self._on_all_snaps_changed)
        
        # Add to two-column widget
        self.snaps_widget.add_button(self.all_snaps_button)

        for snap_type, snap_name, default_val, icon_name in snaps_pane_info.snap_types:
            # Initialize snap state
            if snap_type not in snaps_pane_info.snap_states:
                snaps_pane_info.snap_states[snap_type] = default_val

            # Create button using helper method
            display_name = self._process_display_name(snap_name)
            button = self._create_button_with_icon(
                icon_name, display_name, 
                snaps_pane_info.snap_states[snap_type],
                display_name[:2].upper()
            )

            button.toggled.connect(
                lambda checked, st=snap_type: self._on_snap_changed(st, checked)
            )

            # Add to two-column widget
            self.snaps_widget.add_button(button)
            snaps_pane_info.snap_buttons[snap_type] = button

    def _toggle_snap(self, snap_type: str):
        """Toggle a specific snap type."""
        if snap_type in snaps_pane_info.snap_buttons:
            button = snaps_pane_info.snap_buttons[snap_type]
            button.toggle()

    def _on_all_snaps_changed(self, checked: bool):
        """Handle "All Snaps" button change."""
        snaps_pane_info.snap_all = checked

        # Enable/disable individual snap buttons
        for snap_type, button in snaps_pane_info.snap_buttons.items():
            button.setEnabled(checked)

        self.all_snaps_changed.emit(checked)

    def _on_snap_changed(self, snap_type: str, checked: bool):
        """Handle individual snap button change."""
        snaps_pane_info.snap_states[snap_type] = checked
        self.snap_changed.emit(snap_type, checked)
    
    def _update_all_snaps_icon(self):
        """Update the All Snaps button icon and tooltip based on its state."""
        is_checked = self.all_snaps_button.isChecked()
        icon_name = "snap-enable" if is_checked else "snap-disable"
        alt_rep = "⌥" if platform.system() == "Darwin" else "Alt+"
        tooltip_text = f"Snaps Enabled ({alt_rep}A)" if is_checked else f"Snaps Disabled ({alt_rep}A)"

        # Update icon using helper method
        new_button = self._create_button_with_icon(icon_name, tooltip_text, is_checked, "All")
        self.all_snaps_button.setIcon(new_button.icon())
        self.all_snaps_button.setToolTip(tooltip_text)

    def update_snaps(self):
        """Update snap buttons based on current state."""
        # Check if we have focus and a valid canvas
        if not self.canvas:
            QTimer.singleShot(1000, self.update_snaps)
            return

        # Update all snaps button state
        for snap_type, button in snaps_pane_info.snap_buttons.items():
            if snaps_pane_info.snap_all:
                button.setEnabled(True)
            else:
                button.setEnabled(False)

    def get_snap_types(self) -> List[Tuple[str, str, bool, str]]:
        """
        Get list of snap types.

        Returns:
            List of tuples (snap_type, snap_name, default_value, icon_name)
        """
        return snaps_pane_info.snap_types.copy()

    def snap_exists(self, snap_type: str) -> bool:
        """
        Check if a snap type exists.

        Args:
            snap_type: The snap type to check

        Returns:
            True if snap type exists
        """
        return snap_type in snaps_pane_info.snap_states

    def add_snap(self, snap_type: str, snap_name: str, default_val: bool,
                 icon_name: str = ""):
        """
        Add a new snap type.

        Args:
            snap_type: Internal snap type identifier
            snap_name: Display name for the snap
            default_val: Default enabled state
            icon_name: Icon file name (without extension)
        """
        snaps_pane_info.snap_types.append((snap_type, snap_name, default_val, icon_name))
        snaps_pane_info.snap_states[snap_type] = default_val

        # If toolbar is already created, add the button
        if hasattr(self, 'all_snaps_button'):
            self._add_snap_button(snap_type, snap_name, default_val, icon_name)

    def _add_snap_button(
            self, snap_type: str, snap_name: str, default_val: bool,
            icon_name: str = ""):
        """Add a button for a new snap type."""
        # Create button using helper method
        display_name = self._process_display_name(snap_name)
        button = self._create_button_with_icon(
            icon_name, display_name, default_val, display_name[:2].upper()
        )

        button.toggled.connect(
            lambda checked: self._on_snap_changed(snap_type, checked)
        )

        # Add to two-column widget
        self.snaps_widget.add_button(button)
        snaps_pane_info.snap_buttons[snap_type] = button

        # Setup shortcut for new snap
        self._setup_snap_shortcut(snap_type, snap_name)

    def is_snap_enabled(self, snap_type: str) -> bool:
        """
        Check if a snap type is enabled.

        Args:
            snap_type: The snap type to check

        Returns:
            True if snap is enabled, False otherwise
        """
        return snaps_pane_info.snap_states.get(snap_type, False)

    def set_snap_enabled(self, snap_type: str, enabled: bool):
        """
        Set the enabled state of a snap type.

        Args:
            snap_type: The snap type to modify
            enabled: New enabled state
        """
        if snap_type in snaps_pane_info.snap_states:
            snaps_pane_info.snap_states[snap_type] = enabled
            if snap_type in snaps_pane_info.snap_buttons:
                button = snaps_pane_info.snap_buttons[snap_type]
                button.setChecked(enabled)

    def get_enabled_snaps(self) -> List[str]:
        """
        Get list of currently enabled snap types.

        Returns:
            List of enabled snap type identifiers
        """
        return [snap_type for snap_type, enabled in
                snaps_pane_info.snap_states.items() if enabled]

    def set_all_snaps_enabled(self, enabled: bool):
        """
        Set the "All Snaps" state.

        Args:
            enabled: Whether all snaps should be enabled
        """
        snaps_pane_info.snap_all = enabled
        self.all_snaps_button.setChecked(enabled)
        self._on_all_snaps_changed(enabled)

    def _show_context_menu(self, position):
        """Show context menu for the toolbar."""
        context_menu = QMenu(self)
        
        # Add "All Snaps" action
        all_snaps_action = QAction("All Snaps", self)
        all_snaps_action.setCheckable(True)
        all_snaps_action.setChecked(snaps_pane_info.snap_all)
        all_snaps_action.triggered.connect(self.all_snaps_button.toggle)
        context_menu.addAction(all_snaps_action)
        
        context_menu.addSeparator()
        
        # Add individual snap actions
        for snap_type, snap_name, default_val, icon_name in snaps_pane_info.snap_types:
            action = QAction(snap_name.replace("&", ""), self)
            action.setCheckable(True)
            action.setChecked(snaps_pane_info.snap_states.get(snap_type, default_val))
            # Use a closure to properly capture the snap_type
            def make_toggle_function(snap_type):
                return lambda checked: self._toggle_snap(snap_type)
            action.triggered.connect(make_toggle_function(snap_type))
            context_menu.addAction(action)
        
        # Show the context menu
        context_menu.exec(self.mapToGlobal(position))


def create_snaps_toolbar(
        canvas=None, parent: Optional[QToolBar] = None
) -> SnapsToolBar:
    """
    Create and return a new snaps toolbar.

    Args:
        canvas: Canvas object reference
        parent: Parent widget for the new toolbar

    Returns:
        A new SnapsToolBar instance
    """
    return SnapsToolBar(canvas, parent)


if __name__ == "__main__":
    """Test the snaps toolbar independently."""
    app = QApplication(sys.argv)

    # Create and show the snaps toolbar
    snaps_toolbar = create_snaps_toolbar()
    snaps_toolbar.show()

    # Connect signals for testing
    snaps_toolbar.snap_changed.connect(
        lambda snap_type, enabled: print(f"Snap {snap_type}: {enabled}")
    )
    snaps_toolbar.all_snaps_changed.connect(
        lambda enabled: print(f"All snaps: {enabled}")
    )

    # Test adding a custom snap
    snaps_toolbar.add_snap("custom", "&Custom Snap", False)

    sys.exit(app.exec())
