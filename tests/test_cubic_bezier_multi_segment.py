#!/usr/bin/env python3
"""
Test script for the new multi-segment CubicBezierCadItem.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BelfryCAD'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

from BelfryCAD.gui.cad_scene import CadScene
from BelfryCAD.gui.cad_view import CadView
from BelfryCAD.gui.caditems.cubic_bezier_cad_item import CubicBezierCadItem


def main():
    app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Multi-Segment Cubic Bezier Test")
    window.resize(800, 600)
    
    # Create central widget
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)
    
    # Create CAD scene and view
    scene = CadScene()
    view = CadView(scene)
    layout.addWidget(view)
    
    # Test 1: Simple 2-segment curve
    print("Creating 2-segment cubic Bezier curve...")
    points_2seg = [
        QPointF(0, 0),      # 1st path point
        QPointF(1, 1),      # control1 for 1st segment
        QPointF(2, -1),     # control2 for 1st segment
        QPointF(3, 0),      # 2nd path point
        QPointF(4, 1),      # control1 for 2nd segment
        QPointF(5, -1),     # control2 for 2nd segment
        QPointF(6, 0),      # 3rd path point
    ]
    
    bezier_2seg = CubicBezierCadItem(points=points_2seg, color=QColor(0, 0, 255))
    scene.addItem(bezier_2seg)
    
    # Test 2: 3-segment curve
    print("Creating 3-segment cubic Bezier curve...")
    points_3seg = [
        QPointF(0, 2),      # 1st path point
        QPointF(1, 3),      # control1 for 1st segment
        QPointF(2, 1),      # control2 for 1st segment
        QPointF(3, 2),      # 2nd path point
        QPointF(4, 3),      # control1 for 2nd segment
        QPointF(5, 1),      # control2 for 2nd segment
        QPointF(6, 2),      # 3rd path point
        QPointF(7, 3),      # control1 for 3rd segment
        QPointF(8, 1),      # control2 for 3rd segment
        QPointF(9, 2),      # 4th path point
    ]
    
    bezier_3seg = CubicBezierCadItem(points=points_3seg, color=QColor(255, 0, 0))
    scene.addItem(bezier_3seg)
    
    # Test 3: Single segment (original behavior)
    print("Creating single-segment cubic Bezier curve...")
    points_1seg = [
        QPointF(0, -2),     # 1st path point
        QPointF(1, -1),     # control1 for 1st segment
        QPointF(2, -3),     # control2 for 1st segment
        QPointF(3, -2),     # 2nd path point
    ]
    
    bezier_1seg = CubicBezierCadItem(points=points_1seg, color=QColor(0, 255, 0))
    scene.addItem(bezier_1seg)
    
    # Test 4: Add a segment dynamically
    print("Adding a segment to the 2-segment curve...")
    bezier_2seg.add_segment(
        QPointF(7, 1),      # control1 for new segment
        QPointF(8, -1),     # control2 for new segment
        QPointF(9, 0)       # new path point
    )
    
    # Print information about the curves
    print(f"\n2-segment curve:")
    print(f"  Total points: {len(bezier_2seg.points)}")
    print(f"  Segments: {bezier_2seg.segment_count}")
    print(f"  Path points: {len(bezier_2seg.get_path_points())}")
    print(f"  Control points: {len(bezier_2seg.get_control_points())}")
    
    print(f"\n3-segment curve:")
    print(f"  Total points: {len(bezier_3seg.points)}")
    print(f"  Segments: {bezier_3seg.segment_count}")
    print(f"  Path points: {len(bezier_3seg.get_path_points())}")
    print(f"  Control points: {len(bezier_3seg.get_control_points())}")
    
    print(f"\n1-segment curve:")
    print(f"  Total points: {len(bezier_1seg.points)}")
    print(f"  Segments: {bezier_1seg.segment_count}")
    print(f"  Path points: {len(bezier_1seg.get_path_points())}")
    print(f"  Control points: {len(bezier_1seg.get_control_points())}")
    
    # Test point_at_parameter for different segments
    print(f"\nTesting point_at_parameter:")
    for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
        point = bezier_3seg.point_at_parameter(t)
        print(f"  t={t}: {point.x():.2f}, {point.y():.2f}")
    
    # Test tangent_at_parameter
    print(f"\nTesting tangent_at_parameter:")
    for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
        tangent = bezier_3seg.tangent_at_parameter(t)
        print(f"  t={t}: {tangent.x():.2f}, {tangent.y():.2f}")
    
    # Set view to show all curves
    view.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
    
    window.show()
    
    # Select the first curve to show control points
    scene.clearSelection()
    bezier_2seg.setSelected(True)
    
    return app.exec()


if __name__ == "__main__":
    main() 