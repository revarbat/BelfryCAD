#!/usr/bin/env python3
"""
Test the coordinate transformation integration with tools.
This script creates a minimal test environment to verify that mouse events
are correctly transformed from Qt coordinates to CAD coordinates.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QMouseEvent

from gui.drawing_manager import DrawingManager, DrawingContext
from gui.main_window import CADGraphicsView
from PySide6.QtWidgets import QGraphicsScene
from core.document import Document
from core.preferences import Preferences
from tools.tool_manager import ToolManager
from tools.point import PointTool
from tools.line import LineTool

class TestTool:
    """Simple test tool to capture coordinate information"""

    def __init__(self, info_label):
        self.info_label = info_label
        self.last_coordinates = []

    def handle_mouse_down(self, event):
        """Capture mouse down event coordinates"""
        cad_x, cad_y = event.x, event.y
        self.last_coordinates.append(f"Mouse Down: CAD({cad_x:.4f}, {cad_y:.4f})")
        self._update_display()

    def handle_mouse_move(self, event):
        """Capture mouse move event coordinates"""
        cad_x, cad_y = event.x, event.y
        if len(self.last_coordinates) >= 10:
            self.last_coordinates.pop(0)  # Keep only last 10 events
        self.last_coordinates.append(f"Mouse Move: CAD({cad_x:.4f}, {cad_y:.4f})")
        self._update_display()

    def _update_display(self):
        """Update the info display"""
        if self.info_label:
            info_text = "Tool Coordinate Events:\n" + "\n".join(self.last_coordinates[-5:])
            self.info_label.setText(info_text)

class MockToolManager:
    """Mock tool manager for testing"""

    def __init__(self, test_tool):
        self.active_tool = test_tool

    def get_active_tool(self):
        return self.active_tool

class TestWindow(QMainWindow):
    """Test window for coordinate transformation with tools"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tool Coordinate Transform Test")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create info label
        self.info_label = QLabel("Move mouse and click in the graphics view to test tool coordinate transformation")
        self.info_label.setWordWrap(True)
        self.info_label.setMinimumHeight(120)
        layout.addWidget(self.info_label)

        # Create graphics scene
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-500, -500, 1000, 1000)

        # Create CAD graphics view (the one we modified)
        self.graphics_view = CADGraphicsView()
        self.graphics_view.setScene(self.scene)
        layout.addWidget(self.graphics_view)

        # Create drawing manager
        drawing_context = DrawingContext(
            scene=self.scene,
            dpi=72.0,
            scale_factor=1.0,
            show_grid=True,
            show_origin=True
        )
        self.drawing_manager = DrawingManager(drawing_context)

        # Connect drawing manager to graphics view
        self.graphics_view.set_drawing_manager(self.drawing_manager)

        # Create test tool and mock tool manager
        self.test_tool = TestTool(self.info_label)
        self.tool_manager = MockToolManager(self.test_tool)

        # Connect tool manager to graphics view
        self.graphics_view.set_tool_manager(self.tool_manager)

        # Add reference objects
        self._add_reference_objects()

        print("Test Window Created")
        print("- Graphics view has drawing manager connected")
        print("- Tool manager is connected with test tool")
        print("- Mouse events should be transformed from Qt to CAD coordinates")

    def _add_reference_objects(self):
        """Add reference objects to help visualize coordinate system"""
        from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsTextItem
        from PySide6.QtGui import QPen, QColor

        # Add coordinate axes (in Qt coordinates)
        pen_x = QPen(QColor(255, 0, 0), 2)  # Red for X-axis
        pen_y = QPen(QColor(0, 255, 0), 2)  # Green for Y-axis

        # X-axis (horizontal line)
        x_line = QGraphicsLineItem(-400, 0, 400, 0)
        x_line.setPen(pen_x)
        self.scene.addItem(x_line)

        # Y-axis (vertical line)
        y_line = QGraphicsLineItem(0, -400, 0, 400)
        y_line.setPen(pen_y)
        self.scene.addItem(y_line)

        # Add labels to indicate coordinate system
        text_item = QGraphicsTextItem("Qt Scene: Red=X, Green=Y\nTool receives CAD coords\nMove mouse and click to test")
        text_item.setPos(-380, -380)
        self.scene.addItem(text_item)

def main():
    app = QApplication(sys.argv)

    # Create and show test window
    window = TestWindow()
    window.show()

    print("\nTool Coordinate Transform Test")
    print("=" * 40)
    print("This test verifies that:")
    print("1. Mouse events are captured by CADGraphicsView")
    print("2. Qt scene coordinates are converted to CAD coordinates")
    print("3. Tools receive the correct CAD coordinate system")
    print("4. Y-axis is properly flipped (CAD Y+ is up, Qt Y+ is down)")
    print("\nMove the mouse in the graphics view and click to see coordinate events.")
    print("The tool should receive CAD coordinates where:")
    print("- Moving UP increases Y")
    print("- Moving DOWN decreases Y")
    print("- Moving RIGHT increases X")
    print("- Moving LEFT decreases X")

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
