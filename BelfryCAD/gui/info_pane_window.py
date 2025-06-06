"""
Info Pane Window for PyTkCAD.

This module provides a PySide6/Qt GUI window for displaying mouse position,
dimensions, and action information. It's a direct translation of the original
TCL infopanewin.tcl functionality.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPalette

from typing import Optional


class InfoPaneWindow(QWidget):
    """
    A window that displays real-time information about mouse position,
    dimensions, and current action status.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the info pane window.
        
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
        
        # Create info frame (left side)
        self.info_frame = self._create_info_frame()
        main_layout.addWidget(self.info_frame, 0)
        
        # Create conf frame (right side) - expandable
        self.conf_frame = self._create_conf_frame()
        main_layout.addWidget(self.conf_frame, 1)
        
    def _create_info_frame(self) -> QFrame:
        """
        Create the information display frame with position and dimension labels.
        
        Returns:
            QFrame containing the info display widgets
        """
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        
        # Create layout with specific spacing and alignment
        layout = QVBoxLayout()
        frame.setLayout(layout)
        
        # Set font for all labels
        font = QFont("Courier", 11)
        
        # Create position labels (X, Y)
        self.xpos_label = QLabel("X:")
        self.xpos_label.setFont(font)
        self.xpos_label.setStyleSheet("color: #8B0000;")  # red3 equivalent
        
        self.xpos_value = QLabel("")
        self.xpos_value.setFont(font)
        self.xpos_value.setStyleSheet("color: #8B0000;")  # red3 equivalent
        self.xpos_value.setAlignment(Qt.AlignRight)
        
        self.ypos_label = QLabel("Y:")
        self.ypos_label.setFont(font)
        self.ypos_label.setStyleSheet("color: #228B22;")  # green4 equivalent
        
        self.ypos_value = QLabel("")
        self.ypos_value.setFont(font)
        self.ypos_value.setStyleSheet("color: #228B22;")  # green4 equivalent
        self.ypos_value.setAlignment(Qt.AlignRight)
        
        # Create dimension labels (W, H)
        self.wid_label = QLabel("W:")
        self.wid_label.setFont(font)
        
        self.wid_value = QLabel("")
        self.wid_value.setFont(font)
        self.wid_value.setAlignment(Qt.AlignRight)
        
        self.hgt_label = QLabel("H:")
        self.hgt_label.setFont(font)
        
        self.hgt_value = QLabel("")
        self.hgt_value.setFont(font)
        self.hgt_value.setAlignment(Qt.AlignRight)
        
        # Create action label
        self.action_label = QLabel("")
        self.action_label.setFont(font)
        self.action_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        
        # Create horizontal layouts for label/value pairs
        x_layout = QHBoxLayout()
        x_layout.addWidget(self.xpos_label)
        x_layout.addWidget(self.xpos_value)
        
        y_layout = QHBoxLayout()
        y_layout.addWidget(self.ypos_label)
        y_layout.addWidget(self.ypos_value)
        
        w_layout = QHBoxLayout()
        w_layout.addWidget(self.wid_label)
        w_layout.addWidget(self.wid_value)
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.hgt_label)
        h_layout.addWidget(self.hgt_value)
        
        # Add layouts to main layout
        layout.addLayout(x_layout)
        layout.addLayout(y_layout)
        layout.addLayout(w_layout)
        layout.addLayout(h_layout)
        layout.addStretch()  # Equivalent to grid rowconfigure weight
        layout.addWidget(self.action_label)
        
        return frame
        
    def _create_conf_frame(self) -> QFrame:
        """
        Create the configuration frame (expandable area).
        
        Returns:
            QFrame for configuration content
        """
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        
        # Create layout
        layout = QVBoxLayout()
        frame.setLayout(layout)
        
        return frame
        
    def get_info_pane(self) -> QFrame:
        """
        Get the info display pane.
        
        Returns:
            The info frame widget
        """
        return self.info_frame
        
    def get_conf_pane(self) -> QFrame:
        """
        Get the configuration pane.
        
        Returns:
            The configuration frame widget
        """
        return self.conf_frame
        
    def update_mouse_pos(self, real_x: float, real_y: float, unit: str = ""):
        """
        Update the mouse position display.
        
        Args:
            real_x: X coordinate value
            real_y: Y coordinate value
            unit: Unit string to display
        """
        self.xpos_value.setText(f"{real_x:7.4f} {unit}")
        self.ypos_value.setText(f"{real_y:7.4f} {unit}")
        
    def clear_width_height(self):
        """Clear the width and height display."""
        self.wid_value.setText("")
        self.hgt_value.setText("")
        
    def update_width_height(self, real_x: float, real_y: float, unit: str = ""):
        """
        Update the width and height display.
        
        Args:
            real_x: Width value
            real_y: Height value
            unit: Unit string to display
        """
        self.wid_value.setText(f"{real_x:7.4f}{unit}")
        self.hgt_value.setText(f"{real_y:7.4f}{unit}")
        
    def update_action_str(self, action_str: str):
        """
        Update the action status string.
        
        Args:
            action_str: Action description to display
        """
        self.action_label.setText(action_str)


# Module-level initialization (equivalent to infopanewin_init in TCL)
def init_info_pane_window():
    """Initialize the info pane window system."""
    # In the original TCL, this just initialized global variables
    # In Python, this could be used for any module-level setup
    pass


def create_info_pane_window(parent: Optional[QWidget] = None) -> InfoPaneWindow:
    """
    Create and return a new info pane window.
    
    Args:
        parent: Parent widget for the new window
        
    Returns:
        A new InfoPaneWindow instance
    """
    return InfoPaneWindow(parent)


# Initialize the module
init_info_pane_window()


if __name__ == "__main__":
    """Test the info pane window independently."""
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Create and show the info pane window
    window = create_info_pane_window()
    window.show()
    
    # Test the functionality
    window.update_mouse_pos(123.4567, 987.6543, "mm")
    window.update_width_height(45.6789, 78.9012, "mm")
    window.update_action_str("Drawing line...")
    
    sys.exit(app.exec())
