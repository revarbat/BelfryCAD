"""
Test object naming patterns in the Document class.
"""

import unittest
from src.BelfryCAD.models.document import Document
from src.BelfryCAD.models.cad_objects.line_cad_object import LineCadObject
from src.BelfryCAD.models.cad_objects.circle_cad_object import CircleCadObject
from src.BelfryCAD.cad_geometry import Point2D


class TestObjectNaming(unittest.TestCase):
    """Test that objects are named correctly with sequential numbering."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.document = Document()
    
    def test_line_naming_sequence(self):
        """Test that lines are named line1, line2, line3, etc."""
        # Create multiple lines
        line1 = LineCadObject(self.document, Point2D(0, 0), Point2D(10, 10))
        line2 = LineCadObject(self.document, Point2D(5, 5), Point2D(15, 15))
        line3 = LineCadObject(self.document, Point2D(10, 10), Point2D(20, 20))
        
        # Add them to the document
        self.document.add_object(line1)
        self.document.add_object(line2)
        self.document.add_object(line3)
        
        # Check that they have the correct names
        self.assertEqual(line1.name, "line1")
        self.assertEqual(line2.name, "line2")
        self.assertEqual(line3.name, "line3")
    
    def test_circle_naming_sequence(self):
        """Test that circles are named circle1, circle2, circle3, etc."""
        # Create multiple circles
        circle1 = CircleCadObject(self.document, Point2D(0, 0), Point2D(5, 0))
        circle2 = CircleCadObject(self.document, Point2D(10, 10), Point2D(15, 10))
        circle3 = CircleCadObject(self.document, Point2D(20, 20), Point2D(25, 20))
        
        # Add them to the document
        self.document.add_object(circle1)
        self.document.add_object(circle2)
        self.document.add_object(circle3)
        
        # Check that they have the correct names
        self.assertEqual(circle1.name, "circle1")
        self.assertEqual(circle2.name, "circle2")
        self.assertEqual(circle3.name, "circle3")
    
    def test_mixed_object_naming(self):
        """Test that different object types have separate naming sequences."""
        # Create mixed objects
        line1 = LineCadObject(self.document, Point2D(0, 0), Point2D(10, 10))
        circle1 = CircleCadObject(self.document, Point2D(0, 0), Point2D(5, 0))
        line2 = LineCadObject(self.document, Point2D(5, 5), Point2D(15, 15))
        circle2 = CircleCadObject(self.document, Point2D(10, 10), Point2D(15, 10))
        
        # Add them to the document
        self.document.add_object(line1)
        self.document.add_object(circle1)
        self.document.add_object(line2)
        self.document.add_object(circle2)
        
        # Check that they have the correct names
        self.assertEqual(line1.name, "line1")
        self.assertEqual(circle1.name, "circle1")
        self.assertEqual(line2.name, "line2")
        self.assertEqual(circle2.name, "circle2")
    
    def test_name_counter_reset_on_clear(self):
        """Test that name counters reset when document is cleared."""
        # Create and add a line
        line1 = LineCadObject(self.document, Point2D(0, 0), Point2D(10, 10))
        self.document.add_object(line1)
        self.assertEqual(line1.name, "line1")
        
        # Clear the document
        self.document.clear()
        
        # Create a new line - should be line1 again
        line2 = LineCadObject(self.document, Point2D(0, 0), Point2D(10, 10))
        self.document.add_object(line2)
        self.assertEqual(line2.name, "line1")


if __name__ == '__main__':
    unittest.main() 