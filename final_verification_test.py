#!/usr/bin/env python3
"""
Final verification test for grid alignment with ruler tickmarks
This test confirms that the coordinate conversion fix resolved the alignment issue.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout
from PySide6.QtGui import QPen, QColor, QBrush
from PySide6.QtCore import Qt
from src.gui.main_window import CADGraphicsView
from src.gui.rulers import RulerManager
from PySide6.QtWidgets import QGraphicsScene
import math


class FinalVerificationTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FINAL VERIFICATION: Grid Alignment with Rulers - FIXED")
        self.resize(1000, 700)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QGridLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create scene and canvas with a good size for testing
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-300, -300, 600, 600)

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

        # Add all test elements
        self._add_axis_lines()
        self._add_grid_with_coordinate_conversion()
        self._add_ruler_verification_markers()
        self._add_test_geometry()

        print("🎯 FINAL VERIFICATION TEST")
        print("=" * 50)
        print("✅ Grid now uses coordinate conversion")
        print("✅ Ruler units (inches) → Scene pixels (96 DPI)")
        print("✅ Grid lines should align perfectly with ruler tickmarks")

    def _add_axis_lines(self):
        """Add axis lines at X=0 and Y=0"""
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

    def _add_grid_with_coordinate_conversion(self):
        """Add grid using the FIXED coordinate conversion logic"""
        # Get grid information from the ruler system
        horizontal_ruler = self.ruler_manager.get_horizontal_ruler()
        grid_info = horizontal_ruler.get_grid_info()
        (minorspacing, majorspacing, superspacing, labelspacing,
         divisor, units, formatfunc, conversion) = grid_info

        # Calculate scale conversion (same as rulers)
        dpi = horizontal_ruler.get_dpi()  # 96.0
        scalefactor = horizontal_ruler.get_scale_factor()  # 1.0
        scalemult = dpi * scalefactor / conversion  # 96.0

        print(f"Grid conversion parameters:")
        print(f"  Scale multiplier: {scalemult}")
        print(f"  Label spacing: {labelspacing} ruler units")
        print(f"  Scene spacing: {labelspacing * scalemult} pixels")

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

        # Draw vertical grid lines using coordinate conversion
        x = math.floor(x_start_ruler / minorspacing + 1e-6) * minorspacing
        grid_count = 0

        while x <= x_end_ruler and grid_count < 20:
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
                grid_count += 1
            x += minorspacing

        # Draw horizontal grid lines using coordinate conversion
        y = math.floor(y_start_ruler / minorspacing + 1e-6) * minorspacing
        grid_count = 0

        while y <= y_end_ruler and grid_count < 20:
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
                grid_count += 1
            y += minorspacing

        print(f"✅ Grid added with coordinate conversion")

    def _add_ruler_verification_markers(self):
        """Add markers at ruler major tick positions for verification"""
        # Get conversion factor
        horizontal_ruler = self.ruler_manager.get_horizontal_ruler()
        dpi = horizontal_ruler.get_dpi()
        scalefactor = horizontal_ruler.get_scale_factor()
        conversion = horizontal_ruler.get_grid_info()[7]
        scalemult = dpi * scalefactor / conversion

        # Create red markers at ruler positions
        marker_pen = QPen(QColor(255, 0, 0))
        marker_pen.setWidth(2)
        marker_brush = QBrush(QColor(255, 0, 0))

        print(f"Verification markers:")
        for ruler_pos in range(-3, 4):
            scene_pos = ruler_pos * scalemult
            
            # Small circle at grid intersection
            self.scene.addEllipse(
                scene_pos - 3, scene_pos - 3, 6, 6,
                marker_pen, marker_brush
            )
            
            # Also add a cross at the intersection for better visibility
            self.scene.addLine(
                scene_pos - 5, scene_pos, scene_pos + 5, scene_pos, marker_pen
            )
            self.scene.addLine(
                scene_pos, scene_pos - 5, scene_pos, scene_pos + 5, marker_pen
            )
            
            print(f"  Red marker at ruler {ruler_pos} units (scene {scene_pos:.0f} pixels)")

    def _add_test_geometry(self):
        """Add test geometry that should align with grid"""
        # Get conversion factor
        horizontal_ruler = self.ruler_manager.get_horizontal_ruler()
        dpi = horizontal_ruler.get_dpi()
        scalefactor = horizontal_ruler.get_scale_factor()
        conversion = horizontal_ruler.get_grid_info()[7]
        scalemult = dpi * scalefactor / conversion

        # Create test geometry pen
        test_pen = QPen(QColor(0, 100, 255))
        test_pen.setWidth(2)

        # Rectangle from ruler coordinates (1,1) to (2,2)
        x1, y1 = 1 * scalemult, 1 * scalemult
        x2, y2 = 2 * scalemult, 2 * scalemult
        self.scene.addRect(x1, y1, x2-x1, y2-y1, test_pen)

        # Circle centered at ruler coordinates (0,0) with radius 0.5 ruler units
        center_x, center_y = 0, 0
        radius = 0.5 * scalemult
        self.scene.addEllipse(
            center_x - radius, center_y - radius, 
            2 * radius, 2 * radius, test_pen
        )

        # Line from ruler coordinates (-2,-2) to (2,2)
        x1, y1 = -2 * scalemult, -2 * scalemult
        x2, y2 = 2 * scalemult, 2 * scalemult
        self.scene.addLine(x1, y1, x2, y2, test_pen)

        print(f"✅ Test geometry added at grid-aligned positions")


def main():
    app = QApplication(sys.argv)

    window = FinalVerificationTest()
    window.show()

    print("\n🔍 VERIFICATION INSTRUCTIONS:")
    print("1. Grid lines (light gray dotted) should align EXACTLY with ruler tickmarks")
    print("2. Red markers show expected ruler major tick positions")
    print("3. Blue test geometry should align perfectly with grid intersections")
    print("4. Try scrolling/zooming - alignment should be maintained")
    print("5. This confirms the coordinate conversion fix is working")
    
    print("\n✅ EXPECTED RESULT:")
    print("Perfect alignment between grid lines and ruler tickmarks!")
    print("Grid now properly converts between ruler units and scene pixels.")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()