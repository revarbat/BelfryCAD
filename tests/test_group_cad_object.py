"""
Test for GroupCadObject functionality.
"""

import unittest
from src.BelfryCAD.models.document import Document
from src.BelfryCAD.models.cad_objects.group_cad_object import GroupCadObject
from src.BelfryCAD.models.cad_objects.line_cad_object import LineCadObject
from src.BelfryCAD.utils.geometry import Point2D


class TestGroupCadObject(unittest.TestCase):
    """Test cases for GroupCadObject functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.document = Document()

    def test_create_group(self):
        """Test creating a group."""
        group_id = self.document.create_group("Test Group")
        group = self.document.get_object(group_id)
        
        self.assertIsInstance(group, GroupCadObject)
        self.assertEqual(group.name, "Test Group")
        self.assertEqual(len(group.children), 0)
        self.assertTrue(group.is_root())

    def test_add_object_to_group(self):
        """Test adding an object to a group."""
        # Create a group
        group_id = self.document.create_group("Test Group")
        
        # Create a line
        line_id = self.document.create_line(Point2D(0, 0), Point2D(10, 10))
        
        # Add line to group
        success = self.document.add_to_group(line_id, group_id)
        self.assertTrue(success)
        
        # Check that the line is in the group
        group = self.document.get_object(group_id)
        self.assertIn(line_id, group.children)
        
        # Check that the line has the group as parent
        line = self.document.get_object(line_id)
        self.assertEqual(line.parent_id, group_id)

    def test_nested_groups(self):
        """Test nested groups."""
        # Create parent group
        parent_group_id = self.document.create_group("Parent Group")
        
        # Create child group
        child_group_id = self.document.create_group("Child Group")
        
        # Add child group to parent group
        success = self.document.add_to_group(child_group_id, parent_group_id)
        self.assertTrue(success)
        
        # Check hierarchy
        parent_group = self.document.get_object(parent_group_id)
        child_group = self.document.get_object(child_group_id)
        
        self.assertIn(child_group_id, parent_group.children)
        self.assertEqual(child_group.parent_id, parent_group_id)
        self.assertFalse(child_group.is_root())
        self.assertTrue(parent_group.is_root())

    def test_remove_from_group(self):
        """Test removing an object from a group."""
        # Create a group and add a line to it
        group_id = self.document.create_group("Test Group")
        line_id = self.document.create_line(Point2D(0, 0), Point2D(10, 10))
        self.document.add_to_group(line_id, group_id)
        
        # Remove line from group
        success = self.document.remove_from_group(line_id)
        self.assertTrue(success)
        
        # Check that the line is no longer in the group
        group = self.document.get_object(group_id)
        self.assertNotIn(line_id, group.children)
        
        # Check that the line has no parent
        line = self.document.get_object(line_id)
        self.assertIsNone(line.parent_id)

    def test_group_bounds(self):
        """Test that group bounds are calculated from children."""
        # Create a group
        group_id = self.document.create_group("Test Group")
        
        # Create lines that form a rectangle
        line1_id = self.document.create_line(Point2D(0, 0), Point2D(10, 0))
        line2_id = self.document.create_line(Point2D(10, 0), Point2D(10, 10))
        line3_id = self.document.create_line(Point2D(10, 10), Point2D(0, 10))
        line4_id = self.document.create_line(Point2D(0, 10), Point2D(0, 0))
        
        # Add lines to group
        for line_id in [line1_id, line2_id, line3_id, line4_id]:
            self.document.add_to_group(line_id, group_id)
        
        # Check group bounds
        group = self.document.get_object(group_id)
        bounds = group.get_bounds()
        
        # Expected bounds: (0, 0, 10, 10)
        self.assertEqual(bounds, (0, 0, 10, 10))

    def test_group_transformation(self):
        """Test that group transformations affect all children."""
        # Create a group with a line
        group_id = self.document.create_group("Test Group")
        line_id = self.document.create_line(Point2D(0, 0), Point2D(10, 10))
        self.document.add_to_group(line_id, group_id)
        
        # Get initial line points
        line = self.document.get_object(line_id)
        initial_start = line.start_point
        initial_end = line.end_point
        
        # Translate the group
        group = self.document.get_object(group_id)
        group.translate(5, 5)
        
        # Check that the line was translated
        self.assertEqual(line.start_point, initial_start + Point2D(5, 5))
        self.assertEqual(line.end_point, initial_end + Point2D(5, 5))

    def test_delete_group_with_children(self):
        """Test deleting a group with children."""
        # Create a group with a line
        group_id = self.document.create_group("Test Group")
        line_id = self.document.create_line(Point2D(0, 0), Point2D(10, 10))
        self.document.add_to_group(line_id, group_id)
        
        # Delete the group
        self.document.remove_object(group_id)
        
        # Check that the line still exists but is now a root object
        line = self.document.get_object(line_id)
        self.assertIsNotNone(line)
        self.assertIsNone(line.parent_id)
        
        # Check that the group is gone
        group = self.document.get_object(group_id)
        self.assertIsNone(group)


if __name__ == '__main__':
    unittest.main() 