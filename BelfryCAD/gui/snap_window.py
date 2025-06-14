"""
Snaps Pane for PyTkCAD.

This module provides a PySide6/Qt GUI window for managing snap settings
in the CAD application. It's a direct translation of the original TCL
snapswin.tcl functionality.
"""

import sys

from PySide6.QtWidgets import (
    QWidget, QGridLayout, QPushButton, QCheckBox, QVBoxLayout,
    QScrollArea, QSpacerItem, QSizePolicy,
    QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtGui import QKeySequence, QShortcut, QFont, QIcon

from typing import Optional, List, Tuple
import os


class SnapWindowInfo:
    """Global snap window information storage."""

    def __init__(self):
        self.snap_types = [
            ("grid", "&Grid", True, "snap-grid"),
            ("controlpoints", "Contro&l Points", True, "snap-controlpoints"),
            ("endpoint", "&Endpoints", False, "snap-endpoint"),
            ("midpoints", "&Midpoints", True, "snap-midpoint"),
            ("center", "&Centers", False, "snap-center"),
            ("quadrants", "&Quadrants", True, "snap-quadrant"),
            ("centerlines", "Centerline&s", False, "snap-centerlines"),
            ("tangents", "&Tangents", False, "snap-tangent"),
            ("contours", "C&ontours", False, "snap-contours"),
            ("perpendicular", "&Perpendicular", False, "snap-perpendicular"),
            ("intersect", "&Intersections", False, "snap-intersection"),
            ("nearest", "&Nearest", False, "snap-nearest"),
        ]
        self.snap_states = {}
        self.snap_all = True
        self.snap_buttons = {}  # Changed from checkboxes to buttons
        self.update_timer = None


# Global instance
snap_window_info = SnapWindowInfo()


class SnapWindow(QWidget):
    """
    Snap settings window for managing CAD snap modes.
    """

    # Signals
    snap_changed = Signal(str, bool)  # snap_type, enabled
    all_snaps_changed = Signal(bool)  # all_enabled

    def __init__(self, canvas=None, parent: Optional[QWidget] = None):
        """
        Initialize the snap window.

        Args:
            canvas: Canvas object reference
            parent: Parent widget, if any
        """
        super().__init__(parent)
        self.canvas = canvas
        self.current_row = 1
        self.current_col = 1
        self._init_ui()
        self._setup_shortcuts()

        # Schedule initial update
        QTimer.singleShot(1000, self.update_snaps)

    def _init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Snaps")
        self.setContentsMargins(0, 0, 0, 0)
        self.setMaximumHeight(160)
        self.setMinimumHeight(160)
        self.setMinimumWidth(250)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(3)
        self.setLayout(main_layout)

        # Create "All Snaps" checkbox at the top
        self.all_snaps_checkbox = QCheckBox("All Snaps")
        self.all_snaps_checkbox.setChecked(snap_window_info.snap_all)
        self.all_snaps_checkbox.toggled.connect(self._on_all_snaps_changed)
        main_layout.addWidget(self.all_snaps_checkbox)

        # Create scroll area for snap checkboxes
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        main_layout.addWidget(self.scroll_area)

        # Create scrollable content widget
        self.scroll_content = QWidget()
        self.scroll_layout = QGridLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(5, 5, 0, 0)
        self.scroll_layout.setSpacing(3)
        self.scroll_area.setWidget(self.scroll_content)
        self.scroll_area.setFrameShape(self.scroll_area.Shape.NoFrame)

        # Initialize snap checkboxes
        self._create_snap_checkboxes()

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts for snap toggles."""
        # Alt+A for "All Snaps"
        all_shortcut = QShortcut(QKeySequence("Alt+A"), self)
        all_shortcut.activated.connect(self.all_snaps_checkbox.toggle)

        # Setup shortcuts for individual snaps
        for snap_type, snap_name, default_val, icon_name in snap_window_info.snap_types:
            accel = self._extract_accelerator(snap_name)
            if accel:
                shortcut = QShortcut(QKeySequence(
                    f"Alt+{accel.upper()}"), self)
                shortcut.activated.connect(
                    lambda st=snap_type: self._toggle_snap(st)
                )

    def _extract_accelerator(self, name: str) -> Optional[str]:
        """Extract accelerator key from name with & marker."""
        pos = name.find("&")
        if pos >= 0 and pos + 1 < len(name):
            return name[pos + 1].lower()
        return None

    def _create_snap_checkboxes(self):
        """Create buttons for all snap types in columns."""
        row = 0
        col = 0

        for snap_type, snap_name, default_val, icon_name in snap_window_info.snap_types:
            # Initialize snap state
            if snap_type not in snap_window_info.snap_states:
                snap_window_info.snap_states[snap_type] = default_val

            # Extract display name
            display_name = snap_name.replace("&", "")
            accel = self._extract_accelerator(snap_name)
            if accel:
                display_name = f"Snap to {display_name} ({accel.upper()})"

            # Create toggle button instead of checkbox
            button = QPushButton()
            button.setCheckable(True)  # Make it toggleable
            button.setChecked(snap_window_info.snap_states[snap_type])
            button.setToolTip(display_name)
            button.setContentsMargins(0, 0, 0, 0)
            
            # Set button size to 36x36 for icons with padding
            button.setFixedSize(QSize(36, 36))
            button.setStyleSheet("""
                QPushButton {
                    border: 0;
                    margin: 0;
                    padding: 0;
                    border: 1px solid #aaaaaa;
                    border-radius: 5px;
                    background-color: #dddddd;
                }
                QPushButton:checked {
                    background-color: #bbbbbb;
                }
            """)

            # Load and set icon
            icon = self._load_snap_icon(icon_name)
            if not icon.isNull():
                button.setIcon(icon)
                button.setIconSize(QSize(24, 24))  # Smaller icon for padding
            else:
                # If no icon, use text on button
                button.setText(display_name[:2].upper())  # Use first 2 letters
                button.setFont(QFont("Sans Serif", 8))
                
            button.toggled.connect(
                lambda checked, st=snap_type: self._on_snap_changed(
                    st, checked)
            )

            # Add to grid layout in two columns
            self.scroll_layout.addWidget(button, row, col)
            snap_window_info.snap_buttons[snap_type] = button

            # Move to next position
            col += 1
            if col >= 5:
                col = 0
                row += 1

        # Add stretchy spacer at the bottom to push buttons to the top
        spacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding)
        self.scroll_layout.addItem(spacer, row + 1, 0, 1, 2)

    def _toggle_snap(self, snap_type: str):
        """Toggle a specific snap type."""
        if snap_type in snap_window_info.snap_buttons:
            button = snap_window_info.snap_buttons[snap_type]
            button.toggle()

    def _on_all_snaps_changed(self, checked: bool):
        """Handle "All Snaps" checkbox change."""
        snap_window_info.snap_all = checked

        # Enable/disable individual snap buttons
        for snap_type, button in snap_window_info.snap_buttons.items():
            button.setEnabled(checked)

        self.all_snaps_changed.emit(checked)

    def _on_snap_changed(self, snap_type: str, checked: bool):
        """Handle individual snap checkbox change."""
        snap_window_info.snap_states[snap_type] = checked
        self.snap_changed.emit(snap_type, checked)

    def update_snaps(self):
        """Update snap buttons based on current state."""
        # Check if we have focus and a valid canvas
        if not self.canvas:
            QTimer.singleShot(1000, self.update_snaps)
            return

        # Update all snaps checkbox state
        for snap_type, button in snap_window_info.snap_buttons.items():
            if snap_window_info.snap_all:
                button.setEnabled(True)
            else:
                button.setEnabled(False)

    def get_snap_types(self) -> List[Tuple[str, str, bool, str]]:
        """
        Get list of snap types.

        Returns:
            List of tuples (snap_type, snap_name, default_value, icon_name)
        """
        return snap_window_info.snap_types.copy()

    def snap_exists(self, snap_type: str) -> bool:
        """
        Check if a snap type exists.

        Args:
            snap_type: The snap type to check

        Returns:
            True if snap type exists
        """
        return snap_type in snap_window_info.snap_states

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
        snap_window_info.snap_types.append((snap_type, snap_name, default_val, icon_name))
        snap_window_info.snap_states[snap_type] = default_val

        # If window is already created, add the button
        if hasattr(self, 'scroll_layout'):
            self._add_snap_button(snap_type, snap_name, default_val, icon_name)

    def _add_snap_button(
            self, snap_type: str, snap_name: str, default_val: bool,
            icon_name: str = ""):
        """Add a button for a new snap type."""
        # Extract display name
        display_name = snap_name.replace("&", "")
        accel = self._extract_accelerator(snap_name)
        if accel:
            display_name = display_name + f" ({accel.upper()})"

        # Create toggle button
        button = QPushButton()
        button.setCheckable(True)
        button.setChecked(default_val)
        button.setToolTip(display_name)
        button.setFixedSize(QSize(36, 36))
        button.setStyleSheet("""
            QPushButton { border: 0; margin: 0; padding: 0; }
            QPushButton:checked { background-color: lightblue; }
        """)

        # Load and set icon
        icon = self._load_snap_icon(icon_name)
        if not icon.isNull():
            button.setIcon(icon)
            button.setIconSize(QSize(24, 24))  # Icon with padding
        else:
            # If no icon, use text on button
            button.setText(display_name[:2].upper())
            button.setFont(QFont("Sans Serif", 10))

        button.toggled.connect(
            lambda checked: self._on_snap_changed(snap_type, checked)
        )

        # Add to grid layout
        self.scroll_layout.addWidget(button)
        snap_window_info.snap_buttons[snap_type] = button

        # Setup shortcut for new snap
        if accel:
            shortcut = QShortcut(QKeySequence(f"Alt+{accel.upper()}"), self)
            shortcut.activated.connect(
                lambda: self._toggle_snap(snap_type)
            )

    def is_snap_enabled(self, snap_type: str) -> bool:
        """
        Check if a snap type is enabled.

        Args:
            snap_type: The snap type to check

        Returns:
            True if snap is enabled, False otherwise
        """
        return snap_window_info.snap_states.get(snap_type, False)

    def set_snap_enabled(self, snap_type: str, enabled: bool):
        """
        Set the enabled state of a snap type.

        Args:
            snap_type: The snap type to modify
            enabled: New enabled state
        """
        if snap_type in snap_window_info.snap_states:
            snap_window_info.snap_states[snap_type] = enabled
            if snap_type in snap_window_info.snap_buttons:
                button = snap_window_info.snap_buttons[snap_type]
                button.setChecked(enabled)

    def get_enabled_snaps(self) -> List[str]:
        """
        Get list of currently enabled snap types.

        Returns:
            List of enabled snap type identifiers
        """
        return [snap_type for snap_type, enabled in 
                snap_window_info.snap_states.items() if enabled]

    def set_all_snaps_enabled(self, enabled: bool):
        """
        Set the "All Snaps" state.

        Args:
            enabled: Whether all snaps should be enabled
        """
        snap_window_info.snap_all = enabled
        self.all_snaps_checkbox.setChecked(enabled)
        self._on_all_snaps_changed(enabled)

    def _load_snap_icon(self, icon_name: str) -> QIcon:
        """Load snap icon from resources."""
        if not icon_name:
            return QIcon()

        # Try different possible paths for the snap icons
        icon_paths = [
            f"BelfryCAD/resources/icons/{icon_name}.svg",
            f"resources/icons/{icon_name}.svg", 
            f"images/{icon_name}.svg",  # Legacy fallback
            f"icons/{icon_name}.svg",   # Legacy fallback
            icon_name  # Direct path
        ]

        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                if not icon.isNull():
                    return icon

        # Return empty icon if not found
        return QIcon()


def create_snap_window(
        canvas=None, parent: Optional[QWidget] = None
) -> SnapWindow:
    """
    Create and return a new snap window.

    Args:
        canvas: Canvas object reference
        parent: Parent widget for the new window

    Returns:
        A new SnapWindow instance
    """
    return SnapWindow(canvas, parent)


def snap_types() -> List[Tuple[str, str, bool, str]]:
    """
    Get list of snap types.

    Returns:
        List of tuples (snap_type, snap_name, default_value, icon_name)
    """
    return snap_window_info.snap_types.copy()


def snap_exists(snap_type: str) -> bool:
    """
    Check if a snap type exists.

    Args:
        snap_type: The snap type to check

    Returns:
        True if snap type exists
    """
    return snap_type in snap_window_info.snap_states


def snap_add(snap_type: str, snap_name: str, default_val: bool, 
             icon_name: str = ""):
    """
    Add a new snap type.

    Args:
        snap_type: Internal snap type identifier
        snap_name: Display name for the snap
        default_val: Default enabled state
        icon_name: Icon file name (without extension)
    """
    snap_window_info.snap_types.append((snap_type, snap_name, default_val, icon_name))
    snap_window_info.snap_states[snap_type] = default_val


def snap_is_enabled(snap_type: str) -> bool:
    """
    Check if a snap type is enabled.

    Args:
        snap_type: The snap type to check

    Returns:
        True if snap is enabled, False otherwise
    """
    return snap_window_info.snap_states.get(snap_type, False)


if __name__ == "__main__":
    """Test the snap window independently."""
    app = QApplication(sys.argv)

    # Create and show the snap window
    snap_window = create_snap_window()
    snap_window.show()

    # Connect signals for testing
    snap_window.snap_changed.connect(
        lambda snap_type, enabled: print(f"Snap {snap_type}: {enabled}")
    )
    snap_window.all_snaps_changed.connect(
        lambda enabled: print(f"All snaps: {enabled}")
    )

    # Test adding a custom snap
    snap_window.add_snap("custom", "&Custom Snap", False)

    sys.exit(app.exec())
