#!/usr/bin/env python3
"""
Test to verify setPen functionality with DimensionLineComposite.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QGraphicsView, QGraphicsScene
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPen
from PySide6.QtCore import Qt

# Import the dimension line composite
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'BelfryCAD', 'gui', 'views', 'graphics_items'))
from dimension_line_composite import DimensionLineComposite, DimensionLineOrientation


class DimensionLineSetPenTest(QMainWindow):
    """Test widget to verify setPen functionality."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dimension Line SetPen Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Create graphics view
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        layout.addWidget(self.view)
        
        # Create dimension line
        start_point = QPointF(0, 0)
        end_point = QPointF(100, 50)
        
        # Create a red pen with width 2
        pen = QPen(QColor(255, 0, 0), 2.0)
        
        self.dimension_line = DimensionLineComposite(
            start_point=start_point,
            end_point=end_point,
            extension=20.0,
            orientation=DimensionLineOrientation.ANGLED,
            excess=10.0,
            gap=5.0,
            pen=pen,
            show_text=True,
            text_format_callback=lambda length: f"{length:.1f}",
            text_rotation=0.0,
            opposite_side=False
        )
        
        self.scene.addItem(self.dimension_line)
        
        # Test buttons
        self.red_button = QPushButton("Red Pen")
        self.red_button.clicked.connect(self.set_red_pen)
        layout.addWidget(self.red_button)
        
        self.blue_button = QPushButton("Blue Pen")
        self.blue_button.clicked.connect(self.set_blue_pen)
        layout.addWidget(self.blue_button)
        
        self.green_button = QPushButton("Green Pen")
        self.green_button.clicked.connect(self.set_green_pen)
        layout.addWidget(self.green_button)
        
        self.dashed_button = QPushButton("Toggle Dashed")
        self.dashed_button.clicked.connect(self.toggle_dashed)
        layout.addWidget(self.dashed_button)
        
        self.thick_button = QPushButton("Toggle Thick")
        self.thick_button.clicked.connect(self.toggle_thick)
        layout.addWidget(self.thick_button)
        
        self.test_button = QPushButton("Test Pen Properties")
        self.test_button.clicked.connect(self.test_pen_properties)
        layout.addWidget(self.test_button)
        
        # Set up the view
        self.view.setSceneRect(-50, -50, 200, 150)
        self.view.setRenderHint(self.view.renderHints().Antialiasing)
        
        print("Dimension Line SetPen Test")
        print("Red dimension line should be visible")
        print("Click buttons to test different pen settings")

    def set_red_pen(self):
        """Set red pen."""
        pen = QPen(QColor(255, 0, 0), 2.0)
        self.dimension_line.setPen(pen)
        print("Set red pen")

    def set_blue_pen(self):
        """Set blue pen."""
        pen = QPen(QColor(0, 0, 255), 2.0)
        self.dimension_line.setPen(pen)
        print("Set blue pen")

    def set_green_pen(self):
        """Set green pen."""
        pen = QPen(QColor(0, 255, 0), 2.0)
        self.dimension_line.setPen(pen)
        print("Set green pen")

    def toggle_dashed(self):
        """Toggle dashed style."""
        current_pen = self.dimension_line.pen()
        if current_pen.style() == Qt.PenStyle.SolidLine:
            current_pen.setStyle(Qt.PenStyle.DashLine)
        else:
            current_pen.setStyle(Qt.PenStyle.SolidLine)
        self.dimension_line.setPen(current_pen)
        print("Toggled dashed style")

    def toggle_thick(self):
        """Toggle thick line."""
        current_pen = self.dimension_line.pen()
        if current_pen.widthF() == 2.0:
            current_pen.setWidthF(5.0)
        else:
            current_pen.setWidthF(2.0)
        self.dimension_line.setPen(current_pen)
        print("Toggled line thickness")

    def test_pen_properties(self):
        """Test that pen properties are correctly applied."""
        pen = self.dimension_line.pen()
        print(f"Current pen color: {pen.color().name()}")
        print(f"Current pen width: {pen.widthF()}")
        print(f"Current pen style: {pen.style()}")
        print(f"Current pen is dashed: {pen.style() == Qt.PenStyle.DashLine}")
        
        # Test that internal properties match pen
        print(f"Internal color: {self.dimension_line._color.name()}")
        print(f"Internal line width: {self.dimension_line._line_width}")
        print(f"Internal is dashed: {self.dimension_line._is_dashed}")
        
        # Test that pen matches internal properties
        color_match = pen.color() == self.dimension_line._color
        width_match = pen.widthF() == self.dimension_line._line_width
        style_match = (pen.style() == Qt.PenStyle.DashLine) == self.dimension_line._is_dashed
        
        print(f"Color matches: {color_match}")
        print(f"Width matches: {width_match}")
        print(f"Style matches: {style_match}")


def main():
    """Run the dimension line setPen test."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    widget = DimensionLineSetPenTest()
    widget.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 