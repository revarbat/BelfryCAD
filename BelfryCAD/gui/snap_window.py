"""
Snap Settings Window for PyTkCAD.

This module provides a PySide6/Qt GUI window for managing snap settings
in the CAD application. It's a direct translation of the original TCL
snapswin.tcl functionality.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QCheckBox, QLabel,
    QFrame, QGroupBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QKeySequence, QShortcut, QFont

from typing import Dict, Any, Optional, List, Tuple


class SnapWindowInfo:
    """Global snap window information storage."""

    def __init__(self):
        self.snap_types = [
            ("grid", "&Grid", True),
            ("controlpoints", "Control &Points", True),
            ("midpoints", "&Midpoints", True),
            ("quadrants", "&Quadrants", True),
            ("intersect", "In&tersections", False),
            ("contours", "&Lines and Arcs", False),
            ("centerlines", "&Centerlines", False),
            ("tangents", "&Tangents", False),
        ]
        self.snap_states = {}
        self.snap_all = True
        self.checkboxes = {}
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
        self.setWindowTitle("Snap Settings")
        self.setContentsMargins(5, 8, 5, 8)

        # Create main layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # Configure grid columns
        self.layout.setColumnMinimumWidth(0, 10)
        self.layout.setColumnMinimumWidth(2, 10)
        self.layout.setColumnStretch(4, 1)

        # Create "All Snaps" checkbox
        self.all_snaps_checkbox = QCheckBox("All Snaps")
        self.all_snaps_checkbox.setFont(QFont("TkSmallCaptionFont"))
        self.all_snaps_checkbox.setChecked(snap_window_info.snap_all)
        self.all_snaps_checkbox.toggled.connect(self._on_all_snaps_changed)

        self.layout.addWidget(self.all_snaps_checkbox, 0, 0, 1, 2, Qt.AlignLeft)

        # Initialize snap checkboxes
        self._create_snap_checkboxes()

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts for snap toggles."""
        # Alt+A for "All Snaps"
        all_shortcut = QShortcut(QKeySequence("Alt+A"), self)
        all_shortcut.activated.connect(self.all_snaps_checkbox.toggle)

        # Setup shortcuts for individual snaps
        for snap_type, snap_name, default_val in snap_window_info.snap_types:
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

    def _create_snap_checkboxes(self):
        """Create checkboxes for all snap types."""
        col = self.current_col
        row = self.current_row

        for snap_type, snap_name, default_val in snap_window_info.snap_types:
            # Initialize snap state
            if snap_type not in snap_window_info.snap_states:
                snap_window_info.snap_states[snap_type] = default_val

            # Extract display name and underline position
            display_name = snap_name.replace("&", "")
            underline_pos = snap_name.find("&")

            # Create checkbox
            checkbox = QCheckBox(display_name)
            checkbox.setFont(QFont("TkSmallCaptionFont"))
            checkbox.setChecked(snap_window_info.snap_states[snap_type])
            checkbox.toggled.connect(
                lambda checked, st=snap_type: self._on_snap_changed(st, checked)
            )

            # Set underline if needed (Qt doesn't have direct underline support,
            # but we can use HTML in setText if needed)
            if underline_pos >= 0:
                html_name = display_name[:underline_pos] + \
                           f"<u>{display_name[underline_pos]}</u>" + \
                           display_name[underline_pos + 1:]
                checkbox.setText(html_name)

            self.layout.addWidget(checkbox, row, col, Qt.AlignLeft)
            snap_window_info.checkboxes[snap_type] = checkbox

            # Move to next position
            col += 2
            if col >= 4:
                col = 1
                row += 1

        self.current_col = col
        self.current_row = row

    def _toggle_snap(self, snap_type: str):
        """Toggle a specific snap type."""
        if snap_type in snap_window_info.checkboxes:
            checkbox = snap_window_info.checkboxes[snap_type]
            checkbox.toggle()

    def _on_all_snaps_changed(self, checked: bool):
        """Handle "All Snaps" checkbox change."""
        snap_window_info.snap_all = checked

        # Enable/disable individual snap checkboxes
        for snap_type, checkbox in snap_window_info.checkboxes.items():
            checkbox.setEnabled(checked)

        self.all_snaps_changed.emit(checked)

    def _on_snap_changed(self, snap_type: str, checked: bool):
        """Handle individual snap checkbox change."""
        snap_window_info.snap_states[snap_type] = checked
        self.snap_changed.emit(snap_type, checked)

    def update_snaps(self):
        """Update snap checkboxes based on current state."""
        # Check if we have focus and a valid canvas
        if not self.canvas:
            QTimer.singleShot(1000, self.update_snaps)
            return

        # Update all snaps checkbox state
        for snap_type, checkbox in snap_window_info.checkboxes.items():
            if snap_window_info.snap_all:
                checkbox.setEnabled(True)
            else:
                checkbox.setEnabled(False)

    def get_snap_types(self) -> List[Tuple[str, str, bool]]:
        """
        Get list of snap types.

        Returns:
            List of tuples (snap_type, snap_name, default_value)
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

    def add_snap(self, snap_type: str, snap_name: str, default_val: bool):
        """
        Add a new snap type.

        Args:
            snap_type: Internal snap type identifier
            snap_name: Display name for the snap
            default_val: Default enabled state
        """
        snap_window_info.snap_types.append((snap_type, snap_name, default_val))
        snap_window_info.snap_states[snap_type] = default_val

        # If window is already created, add the checkbox
        if hasattr(self, 'layout'):
            self._add_snap_checkbox(snap_type, snap_name, default_val)

    def _add_snap_checkbox(self, snap_type: str, snap_name: str, default_val: bool):
        """Add a checkbox for a new snap type."""
        # Extract display name and underline position
        display_name = snap_name.replace("&", "")
        underline_pos = snap_name.find("&")

        # Create checkbox
        checkbox = QCheckBox(display_name)
        checkbox.setFont(QFont("TkSmallCaptionFont"))
        checkbox.setChecked(default_val)
        checkbox.toggled.connect(
            lambda checked: self._on_snap_changed(snap_type, checked)
        )

        # Set underline if needed
        if underline_pos >= 0:
            html_name = display_name[:underline_pos] + \
                       f"<u>{display_name[underline_pos]}</u>" + \
                       display_name[underline_pos + 1:]
            checkbox.setText(html_name)

        # Add to layout at current position
        self.layout.addWidget(checkbox, self.current_row, self.current_col, Qt.AlignLeft)
        snap_window_info.checkboxes[snap_type] = checkbox

        # Update position for next checkbox
        self.current_col += 2
        if self.current_col >= 4:
            self.current_col = 1
            self.current_row += 1

        # Setup shortcut for new snap
        accel = self._extract_accelerator(snap_name)
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
            if snap_type in snap_window_info.checkboxes:
                checkbox = snap_window_info.checkboxes[snap_type]
                checkbox.setChecked(enabled)

    def get_enabled_snaps(self) -> List[str]:
        """
        Get list of currently enabled snap types.

        Returns:
            List of enabled snap type identifiers
        """
        return [snap_type for snap_type, enabled in snap_window_info.snap_states.items()
                if enabled]

    def set_all_snaps_enabled(self, enabled: bool):
        """
        Set the "All Snaps" state.

        Args:
            enabled: Whether all snaps should be enabled
        """
        snap_window_info.snap_all = enabled
        self.all_snaps_checkbox.setChecked(enabled)
        self._on_all_snaps_changed(enabled)


def create_snap_window(canvas=None, parent: Optional[QWidget] = None) -> SnapWindow:
    """
    Create and return a new snap window.

    Args:
        canvas: Canvas object reference
        parent: Parent widget for the new window

    Returns:
        A new SnapWindow instance
    """
    return SnapWindow(canvas, parent)


def snap_types() -> List[Tuple[str, str, bool]]:
    """
    Get list of snap types.

    Returns:
        List of tuples (snap_type, snap_name, default_value)
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


def snap_add(snap_type: str, snap_name: str, default_val: bool):
    """
    Add a new snap type.

    Args:
        snap_type: Internal snap type identifier
        snap_name: Display name for the snap
        default_val: Default enabled state
    """
    snap_window_info.snap_types.append((snap_type, snap_name, default_val))
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
    import sys
    from PySide6.QtWidgets import QApplication

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
