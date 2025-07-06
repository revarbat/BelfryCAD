"""
Info Pane for BelfryCad.

This module provides a PySide6/Qt GUI pane for displaying mouse position,
dimensions, and action information. It's a direct translation of the original
TCL infopanewin.tcl functionality.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)

class InfoPane(QWidget):
    """
    A pane that displays real-time information about mouse position,
    dimensions, and current action status.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the info pane.

        Args:
            parent: Parent widget, if any
        """
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Info Panel")

        # Create main layout
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Create conf frame - expandable
        self.conf_frame = self._create_conf_frame()
        main_layout.addWidget(self.conf_frame, 1)

        return self.conf_frame

    def _create_conf_frame(self) -> QFrame:
        """
        Create the configuration frame (expandable area).

        Returns:
            QFrame for configuration content
        """
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)

        # Create layout
        layout = QVBoxLayout()
        frame.setLayout(layout)

        return frame

    def get_conf_pane(self) -> QFrame:
        """
        Get the configuration pane.

        Returns:
            The configuration frame widget
        """
        return self.conf_frame

def create_info_pane(
        parent: Optional[QWidget] = None
) -> InfoPane:
    """
    Create and return a new info pane.

    Args:
        parent: Parent widget for the new pane

    Returns:
        A new InfoPane instance
    """
    return InfoPane(parent)
