#!/usr/bin/env python3
"""
Test mouse coordinate transformation to verify Y-axis fixes.
This script will create a simple test to verify the mouse event coordinate
transformation pipeline is working correctly.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QMouseEvent

from gui.drawing_manager import DrawingManager, DrawingContext
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView

class TestGraphicsView(QGraphicsView):
    """Test graphics view to verify coordinate transformations"""

    def __init__(self):
        super().__init__()
        self.drawing_manager = None
        self.info_label = None

    def set_drawing_manager(self, drawing_manager):
        self.drawing_manager = drawing_manager

    def set_info_label(self, label):
        self.info_label = label

    def mousePressEvent(self, event):
        """Handle mouse press events to test coordinate transformation"""
        if event.button() == Qt.LeftButton:
            # Get Qt widget coordinates
            widget_pos = event.pos()

            # Convert to scene coordinates
            scene_pos = self.mapToScene(widget_pos)
            qt_x, qt_y = scene_pos.x(), scene_pos.y()

            # Convert to CAD coordinates using drawing manager
            if self.drawing_manager:
                cad_coords = self.drawing_manager.descale_coords([qt_x, qt_y])
                cad_x, cad_y = cad_coords[0], cad_coords[1]

                # Round trip test - convert back to Qt coordinates
                qt_coords_back = self.drawing_manager.scale_coords([cad_x, cad_y])
                qt_x_back, qt_y_back = qt_coords_back[0], qt_coords_back[1]

                # Update info label
                if self.info_label:
                    info_text = f"""Mouse Coordinate Test:
Widget: ({widget_pos.x()}, {widget_pos.y()})
Qt Scene: ({qt_x:.2f}, {qt_y:.2f})
CAD: ({cad_x:.4f}, {cad_y:.4f})
Round-trip Qt: ({qt_x_back:.2f}, {qt_y_back:.2f})
Round-trip error: ({abs(qt_x - qt_x_back):.6f}, {abs(qt_y - qt_y_back):.6f})

Expected behavior:
- CAD Y should be opposite sign of Qt Y
- Round-trip error should be near zero
- Moving mouse UP should increase CAD Y
- Moving mouse DOWN should decrease CAD Y"""
                    self.info_label.setText(info_text)

        super().mousePressEvent(event)

class TestWindow(QMainWindow):
    """Test window for coordinate transformation"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mouse Coordinate Transform Test")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create info label
        self.info_label = QLabel("Click on the graphics view to test coordinate transformation")
        self.info_label.setWordWrap(True)
        self.info_label.setMinimumHeight(150)
        layout.addWidget(self.info_label)

        # Create graphics scene and view
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-500, -500, 1000, 1000)

        self.graphics_view = TestGraphicsView()
        self.graphics_view.setScene(self.scene)
        self.graphics_view.set_info_label(self.info_label)
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
        self.graphics_view.set_drawing_manager(self.drawing_manager)

        # Add some reference lines to the scene
        self._add_reference_objects()

    def _add_reference_objects(self):
        """Add reference objects to help visualize coordinate system"""
        from PySide6.QtWidgets import QGraphicsLineItem
        from PySide6.QtCore import Qt
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

        # Add grid lines
        pen_grid = QPen(QColor(200, 200, 200), 1)
        for i in range(-400, 401, 50):
            if i != 0:  # Skip the main axes
                # Vertical grid lines
                v_line = QGraphicsLineItem(i, -400, i, 400)
                v_line.setPen(pen_grid)
                self.scene.addItem(v_line)

                # Horizontal grid lines
                h_line = QGraphicsLineItem(-400, i, 400, i)
                h_line.setPen(pen_grid)
                self.scene.addItem(h_line)

        # Add labels to indicate coordinate system
        from PySide6.QtWidgets import QGraphicsTextItem
        text_item = QGraphicsTextItem("Qt Scene Coordinates\nRed=X-axis, Green=Y-axis\nClick to test CAD coordinate conversion")
        text_item.setPos(-380, -380)
        self.scene.addItem(text_item)

def main():
    app = QApplication(sys.argv)

    # Create and show test window
    window = TestWindow()
    window.show()

    print("Mouse Coordinate Transform Test")
    print("=" * 40)
    print("Click on the graphics view to test coordinate transformation.")
    print("The info panel will show:")
    print("- Widget coordinates (from Qt mouse event)")
    print("- Qt scene coordinates (after mapToScene)")
    print("- CAD coordinates (after descale_coords)")
    print("- Round-trip Qt coordinates (after scale_coords)")
    print("- Round-trip error (should be near zero)")
    print()
    print("Expected behavior:")
    print("- Moving mouse UP should INCREASE CAD Y (opposite of Qt)")
    print("- Moving mouse DOWN should DECREASE CAD Y")
    print("- Round-trip error should be very small")

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
