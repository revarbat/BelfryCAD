#!/usr/bin/env python3
"""
Test to verify default pen functionality with DimensionLineComposite.
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


class DimensionLineDefaultPenTest(QMainWindow):
    """Test widget to verify default pen functionality."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dimension Line Default Pen Test")
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
        
        # Create dimension line with default pen (no pen argument)
        start_point = QPointF(0, 0)
        end_point = QPointF(100, 50)
        
        self.dimension_line = DimensionLineComposite(
            start_point=start_point,
            end_point=end_point,
            extension=20.0,
            orientation=DimensionLineOrientation.ANGLED,
            excess=10.0,
            gap=5.0,
            # No pen argument - should use default black pen with width 1
            show_text=True,
            text_format_callback=lambda length: f"{length:.1f}",
            text_rotation=0.0,
            opposite_side=False
        )
        
        self.scene.addItem(self.dimension_line)
        
        # Test buttons
        self.test_default_button = QPushButton("Test Default Pen Properties")
        self.test_default_button.clicked.connect(self.test_default_pen_properties)
        layout.addWidget(self.test_default_button)
        
        self.custom_pen_button = QPushButton("Set Custom Pen")
        self.custom_pen_button.clicked.connect(self.set_custom_pen)
        layout.addWidget(self.custom_pen_button)
        
        self.reset_button = QPushButton("Reset to Default Pen")
        self.reset_button.clicked.connect(self.reset_to_default)
        layout.addWidget(self.reset_button)
        
        # Set up the view
        self.view.setSceneRect(-50, -50, 200, 150)
        self.view.setRenderHint(self.view.renderHints().Antialiasing)
        
        print("Dimension Line Default Pen Test")
        print("Black dimension line with width 1 should be visible")
        print("Click buttons to test pen functionality")

    def test_default_pen_properties(self):
        """Test that default pen properties are correct."""
        pen = self.dimension_line.pen()
        print(f"Default pen color: {pen.color().name()}")
        print(f"Default pen width: {pen.widthF()}")
        print(f"Default pen style: {pen.style()}")
        print(f"Default pen is dashed: {pen.style() == Qt.PenStyle.DashLine}")
        
        # Test that internal properties match pen
        print(f"Internal color: {self.dimension_line._color.name()}")
        print(f"Internal line width: {self.dimension_line._line_width}")
        print(f"Internal is dashed: {self.dimension_line._is_dashed}")
        
        # Test that pen matches expected defaults
        color_match = pen.color() == QColor(0, 0, 0)  # Black
        width_match = pen.widthF() == 1.0
        style_match = pen.style() == Qt.PenStyle.SolidLine
        
        print(f"Color is black: {color_match}")
        print(f"Width is 1.0: {width_match}")
        print(f"Style is solid: {style_match}")
        
        # Test that pen matches internal properties
        internal_color_match = pen.color() == self.dimension_line._color
        internal_width_match = pen.widthF() == self.dimension_line._line_width
        internal_style_match = (pen.style() == Qt.PenStyle.DashLine) == self.dimension_line._is_dashed
        
        print(f"Color matches internal: {internal_color_match}")
        print(f"Width matches internal: {internal_width_match}")
        print(f"Style matches internal: {internal_style_match}")

    def set_custom_pen(self):
        """Set a custom pen."""
        custom_pen = QPen(QColor(255, 0, 255), 3.0)  # Magenta, 3px width
        custom_pen.setStyle(Qt.PenStyle.DashLine)
        self.dimension_line.setPen(custom_pen)
        print("Set custom magenta dashed pen")

    def reset_to_default(self):
        """Reset to default pen."""
        default_pen = QPen(QColor(0, 0, 0), 1.0)  # Black, 1px width
        self.dimension_line.setPen(default_pen)
        print("Reset to default black pen")


def main():
    """Run the dimension line default pen test."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    widget = DimensionLineDefaultPenTest()
    widget.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 