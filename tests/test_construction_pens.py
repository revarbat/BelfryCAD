"""
Test the construction pen methods on CadItem.
"""

import sys
import os
import unittest

# Add the src directory to the path so we can import BelfryCAD modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPen, Qt

from BelfryCAD.gui.views.graphics_items.cad_item import CadItem


class TestConstructionPens(unittest.TestCase):
    """Test the construction pen methods."""

    def test_get_dashed_construction_pen(self):
        """Test that get_dashed_construction_pen returns the correct pen."""
        cad_item = CadItem()
        pen = cad_item.get_dashed_construction_pen()
        
        # Check color (#7f7f7f)
        self.assertEqual(pen.color().red(), 0x7f)
        self.assertEqual(pen.color().green(), 0x7f)
        self.assertEqual(pen.color().blue(), 0x7f)
        
        # Check line width
        self.assertEqual(pen.widthF(), 2.0)
        
        # Check cosmetic style
        self.assertTrue(pen.isCosmetic())
        
        # Check dash style
        self.assertEqual(pen.style(), Qt.PenStyle.DashLine)

    def test_get_solid_construction_pen(self):
        """Test that get_solid_construction_pen returns the correct pen."""
        cad_item = CadItem()
        pen = cad_item.get_solid_construction_pen()
        
        # Check color (#7f7f7f)
        self.assertEqual(pen.color().red(), 0x7f)
        self.assertEqual(pen.color().green(), 0x7f)
        self.assertEqual(pen.color().blue(), 0x7f)
        
        # Check line width
        self.assertEqual(pen.widthF(), 2.0)
        
        # Check cosmetic style
        self.assertTrue(pen.isCosmetic())
        
        # Check solid style
        self.assertEqual(pen.style(), Qt.PenStyle.SolidLine)

    def test_pen_colors_match_hex_value(self):
        """Test that the pen colors match the #7f7f7f hex value."""
        cad_item = CadItem()
        
        # Test dashed pen
        dashed_pen = cad_item.get_dashed_construction_pen()
        expected_color = QColor(0x7f, 0x7f, 0x7f)
        self.assertEqual(dashed_pen.color(), expected_color)
        
        # Test solid pen
        solid_pen = cad_item.get_solid_construction_pen()
        self.assertEqual(solid_pen.color(), expected_color)


if __name__ == '__main__':
    unittest.main() 