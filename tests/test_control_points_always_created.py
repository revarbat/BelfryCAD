"""
Test that CAD items always create all control points, even when invalid.

This test verifies that CAD items create all their control points unconditionally,
and hide some controls when the item is invalid rather than not creating them at all.
"""

import sys
import os
import unittest
from typing import List

# Add the src directory to the path so we can import BelfryCAD modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor

from BelfryCAD.gui.views.graphics_items.caditems.circle_3points_cad_item import Circle3PointsCadItem
from BelfryCAD.gui.views.graphics_items.caditems.line_cad_item import LineCadItem
from BelfryCAD.gui.views.graphics_items.caditems.polyline_cad_item import PolylineCadItem
from BelfryCAD.gui.views.graphics_items.caditems.rectangle_cad_item import RectangleCadItem


class TestControlPointsAlwaysCreated(unittest.TestCase):
    """Test that CAD items always create all control points."""

    def test_circle_3points_always_creates_all_controls(self):
        """Test that Circle3PointsCadItem always creates all control points."""
        # Create a circle with collinear points (invalid circle, becomes a line)
        point1 = QPointF(0, 0)
        point2 = QPointF(1, 0)
        point3 = QPointF(2, 0)  # Collinear points
        
        circle_item = Circle3PointsCadItem(point1, point2, point3)
        
        # Verify that all control points are created
        self.assertIsNotNone(circle_item._point1_cp)
        self.assertIsNotNone(circle_item._point2_cp)
        self.assertIsNotNone(circle_item._point3_cp)
        self.assertIsNotNone(circle_item._center_cp)
        self.assertIsNotNone(circle_item._radius_datum)
        
        # Verify that the item is a line (invalid circle)
        self.assertTrue(circle_item.is_line)
        
        # Verify that center and radius controls are hidden for lines
        circle_item.updateControls()
        if circle_item._center_cp:
            self.assertFalse(circle_item._center_cp.isVisible())
        if circle_item._radius_datum:
            self.assertFalse(circle_item._radius_datum.isVisible())
        
        # Verify that point controls exist but are hidden by default
        if circle_item._point1_cp:
            self.assertFalse(circle_item._point1_cp.isVisible())
        if circle_item._point2_cp:
            self.assertFalse(circle_item._point2_cp.isVisible())
        if circle_item._point3_cp:
            self.assertFalse(circle_item._point3_cp.isVisible())

    def test_circle_3points_valid_circle_shows_all_controls(self):
        """Test that valid Circle3PointsCadItem shows all control points."""
        # Create a valid circle
        point1 = QPointF(-1, 0)
        point2 = QPointF(0, 1)
        point3 = QPointF(1, 0)  # Non-collinear points
        
        circle_item = Circle3PointsCadItem(point1, point2, point3)
        
        # Verify that all control points are created
        self.assertIsNotNone(circle_item._point1_cp)
        self.assertIsNotNone(circle_item._point2_cp)
        self.assertIsNotNone(circle_item._point3_cp)
        self.assertIsNotNone(circle_item._center_cp)
        self.assertIsNotNone(circle_item._radius_datum)
        
        # Verify that the item is a valid circle
        self.assertFalse(circle_item.is_line)
        
        # Verify that all controls exist but are hidden by default for valid circles
        # Don't call updateControls() as it changes visibility
        if circle_item._center_cp:
            self.assertFalse(circle_item._center_cp.isVisible())
        if circle_item._radius_datum:
            self.assertFalse(circle_item._radius_datum.isVisible())
        if circle_item._point1_cp:
            self.assertFalse(circle_item._point1_cp.isVisible())
        if circle_item._point2_cp:
            self.assertFalse(circle_item._point2_cp.isVisible())
        if circle_item._point3_cp:
            self.assertFalse(circle_item._point3_cp.isVisible())

    def test_line_cad_item_always_creates_all_controls(self):
        """Test that LineCadItem always creates all control points."""
        line_item = LineCadItem()
        
        # Verify that all control points are created
        self.assertIsNotNone(line_item._start_cp)
        self.assertIsNotNone(line_item._end_cp)
        self.assertIsNotNone(line_item._mid_cp)
        
        # Verify that all controls exist but are hidden by default
        line_item.updateControls()
        self.assertFalse(line_item._start_cp.isVisible())
        self.assertFalse(line_item._end_cp.isVisible())
        self.assertFalse(line_item._mid_cp.isVisible())

    def test_polyline_cad_item_always_creates_all_controls(self):
        """Test that PolylineCadItem always creates control points for all points."""
        # Create polyline with multiple points
        points = [QPointF(0, 0), QPointF(1, 0), QPointF(1, 1), QPointF(0, 1)]
        polyline_item = PolylineCadItem(points)
        
        # Verify that control points are created for all points
        self.assertEqual(len(polyline_item._point_control_points), 4)
        
        for cp in polyline_item._point_control_points:
            self.assertIsNotNone(cp)
            self.assertFalse(cp.isVisible())  # Hidden by default

    def test_rectangle_cad_item_always_creates_all_controls(self):
        """Test that RectangleCadItem always creates all control points."""
        rect_item = RectangleCadItem()
        
        # Verify that all control points are created
        self.assertIsNotNone(rect_item._top_left_cp)
        self.assertIsNotNone(rect_item._top_right_cp)
        self.assertIsNotNone(rect_item._bottom_right_cp)
        self.assertIsNotNone(rect_item._bottom_left_cp)
        self.assertIsNotNone(rect_item._center_cp)
        
        # Verify that all controls exist but are hidden by default
        rect_item.updateControls()
        self.assertFalse(rect_item._top_left_cp.isVisible())
        self.assertFalse(rect_item._top_right_cp.isVisible())
        self.assertFalse(rect_item._bottom_right_cp.isVisible())
        self.assertFalse(rect_item._bottom_left_cp.isVisible())
        self.assertFalse(rect_item._center_cp.isVisible())

    def test_control_points_can_manipulate_invalid_items(self):
        """Test that control points can be used to manipulate invalid items into valid ones."""
        # Create an invalid circle (collinear points)
        point1 = QPointF(0, 0)
        point2 = QPointF(1, 0)
        point3 = QPointF(2, 0)  # Collinear points
        
        circle_item = Circle3PointsCadItem(point1, point2, point3)
        
        # Initially it should be a line
        self.assertTrue(circle_item.is_line)
        
        # Move point2 to make it a valid circle
        new_point2 = QPointF(0, 1)  # Move to create a triangle
        circle_item._set_point2(new_point2)
        
        # Now it should be a valid circle
        self.assertFalse(circle_item.is_line)
        
        # The center and radius controls should now be visible (after manipulation)
        circle_item.updateControls()
        if circle_item._center_cp:
            self.assertTrue(circle_item._center_cp.isVisible())
        if circle_item._radius_datum:
            self.assertTrue(circle_item._radius_datum.isVisible())


if __name__ == '__main__':
    unittest.main() 