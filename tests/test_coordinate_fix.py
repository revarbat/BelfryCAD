#!/usr/bin/env python3
"""
Test the coordinate conversion fix for grid alignment
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout
from PySide6.QtGui import QPen, QColor, QBrush
from PySide6.QtCore import Qt
from BelfryCAD.gui.main_window import CADGraphicsView
from BelfryCAD.gui.rulers import RulerManager
from PySide6.QtWidgets import QGraphicsScene
import math


class CoordinateFixTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Coordinate Fix Test - Grid Alignment with Units Conversion")
        self.resize(800, 600)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QGridLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create scene and canvas
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-200, -200, 400, 400)

        self.canvas = CADGraphicsView()
        self.canvas.setScene(self.scene)

        # Create rulers
        self.ruler_manager = RulerManager(self.canvas, central_widget)
        h_ruler = self.ruler_manager.get_horizontal_ruler()
        v_ruler = self.ruler_manager.get_vertical_ruler()

        # Corner widget
        corner = QWidget()
        corner.setFixedSize(32, 32)
        corner.setStyleSheet("background-color: white; border: 1px solid black;")

        # Layout
        layout.addWidget(corner, 0, 0)
        layout.addWidget(h_ruler, 0, 1)
        layout.addWidget(v_ruler, 1, 0)
        layout.addWidget(self.canvas, 1, 1)

        layout.setColumnStretch(1, 1)
        layout.setRowStretch(1, 1)

        # Add axis lines and test coordinate conversion
        self._add_axis_lines()
        self._test_coordinate_conversion()

        print("Coordinate Fix Test Created:")
        print("- Testing coordinate conversion between ruler units and scene pixels")
        print("- Grid should now align with ruler tickmarks")

    def _add_axis_lines(self):
        """Add axis lines"""
        axis_pen = QPen(QColor(128, 128, 128))
        axis_pen.setWidth(2)

        scene_rect = self.scene.sceneRect()

        # Horizontal axis (y=0)
        h_axis = self.scene.addLine(
            scene_rect.left(), 0, scene_rect.right(), 0, axis_pen
        )
        h_axis.setZValue(-1000)

        # Vertical axis (x=0)
        v_axis = self.scene.addLine(
            0, scene_rect.top(), 0, scene_rect.bottom(), axis_pen
        )
        v_axis.setZValue(-1000)

    def _test_coordinate_conversion(self):
        """Test coordinate conversion and add grid with ruler alignment"""
        # Get grid information from the ruler system
        horizontal_ruler = self.ruler_manager.get_horizontal_ruler()
        grid_info = horizontal_ruler.get_grid_info()
        (minorspacing, majorspacing, superspacing, labelspacing,
         divisor, units, formatfunc, conversion) = grid_info

        # Calculate scale conversion (same as rulers)
        dpi = horizontal_ruler.get_dpi()  # 96.0
        scalefactor = horizontal_ruler.get_scale_factor()  # 1.0
        scalemult = dpi * scalefactor / conversion  # 96.0

        print(f"\nCoordinate Conversion Test:")
        print(f"DPI: {dpi}")
        print(f"Scale factor: {scalefactor}")
        print(f"Conversion: {conversion}")
        print(f"Scale multiplier: {scalemult}")
        print(f"Label spacing: {labelspacing} ruler units")
        print(f"Expected scene spacing: {labelspacing * scalemult} pixels")

        # Test specific conversions
        print(f"\nTest conversions:")
        for ruler_pos in [-2, -1, 0, 1, 2]:
            scene_pos = ruler_pos * scalemult
            print(f"Ruler {ruler_pos} units -> Scene {scene_pos} pixels")

        # Create grid pen
        grid_pen = QPen(QColor(200, 200, 200))
        grid_pen.setWidth(1)
        grid_pen.setStyle(Qt.DotLine)

        # Get the visible scene rectangle
        scene_rect = self.scene.sceneRect()

        # Convert scene coordinates to ruler coordinates for calculation
        x_start_ruler = scene_rect.left() / scalemult
        x_end_ruler = scene_rect.right() / scalemult
        y_start_ruler = scene_rect.top() / scalemult
        y_end_ruler = scene_rect.bottom() / scalemult

        print(f"\nScene bounds: {scene_rect.left():.1f} to {scene_rect.right():.1f} pixels")
        print(f"Ruler bounds: {x_start_ruler:.3f} to {x_end_ruler:.3f} units")

        # Draw vertical grid lines using coordinate conversion
        x = math.floor(x_start_ruler / minorspacing + 1e-6) * minorspacing
        grid_count = 0

        print(f"\nVertical grid lines:")
        while x <= x_end_ruler and grid_count < 10:
            # Test if this position would be a major tick with label
            if abs(math.floor(x / labelspacing + 1e-6) - x / labelspacing) < 1e-3:
                # Convert ruler coordinate back to scene coordinate
                x_scene = x * scalemult
                grid_line = self.scene.addLine(
                    x_scene, scene_rect.top(),
                    x_scene, scene_rect.bottom(),
                    grid_pen
                )
                grid_line.setZValue(-1001)
                print(f"  Ruler {x:.1f} units -> Scene {x_scene:.1f} pixels")
                grid_count += 1
            x += minorspacing

        # Draw horizontal grid lines using coordinate conversion
        y = math.floor(y_start_ruler / minorspacing + 1e-6) * minorspacing
        grid_count = 0

        print(f"\nHorizontal grid lines:")
        while y <= y_end_ruler and grid_count < 10:
            # Test if this position would be a major tick with label
            if abs(math.floor(y / labelspacing + 1e-6) - y / labelspacing) < 1e-3:
                # Convert ruler coordinate back to scene coordinate
                y_scene = y * scalemult
                grid_line = self.scene.addLine(
                    scene_rect.left(), y_scene,
                    scene_rect.right(), y_scene,
                    grid_pen
                )
                grid_line.setZValue(-1001)
                print(f"  Ruler {y:.1f} units -> Scene {y_scene:.1f} pixels")
                grid_count += 1
            y += minorspacing

        # Add test markers at known ruler positions for verification
        self._add_verification_markers(scalemult)

    def _add_verification_markers(self, scalemult):
        """Add verification markers at expected ruler positions"""
        marker_pen = QPen(QColor(255, 0, 0))
        marker_pen.setWidth(3)
        marker_brush = QBrush(QColor(255, 0, 0))

        print(f"\nVerification markers:")
        for ruler_pos in [-2, -1, 0, 1, 2]:
            scene_pos = ruler_pos * scalemult
            # Small circle at expected position
            self.scene.addEllipse(
                scene_pos - 2, scene_pos - 2, 4, 4,
                marker_pen, marker_brush
            )
            print(f"  Red marker at ruler {ruler_pos} units (scene {scene_pos:.1f} pixels)")


def main():
    app = QApplication(sys.argv)

    window = CoordinateFixTest()
    window.show()

    print("\nInstructions:")
    print("1. Red markers show expected ruler major tick positions")
    print("2. Grid lines should align exactly with red markers")
    print("3. Grid lines should align exactly with ruler tickmarks")
    print("4. Both should now use proper coordinate conversion")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
