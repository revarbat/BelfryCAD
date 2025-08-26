#!/usr/bin/env python3
"""
Tests for BelfryCAD XML Serializer

This module tests the XML serializer functionality including:
- Saving and loading documents
- Parameter handling
- All CAD object types
- Grouping
- Constraints
- Document preferences
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from BelfryCAD.models.document import Document
from BelfryCAD.models.cad_objects.line_cad_object import LineCadObject
from BelfryCAD.models.cad_objects.circle_cad_object import CircleCadObject
from BelfryCAD.models.cad_objects.arc_cad_object import ArcCadObject
from BelfryCAD.models.cad_objects.ellipse_cad_object import EllipseCadObject
from BelfryCAD.models.cad_objects.cubic_bezier_cad_object import CubicBezierCadObject
from BelfryCAD.models.cad_objects.gear_cad_object import GearCadObject
from BelfryCAD.models.cad_objects.group_cad_object import GroupCadObject
from BelfryCAD.utils.xml_serializer import BelfryCADXMLSerializer, save_belfrycad_document, load_belfrycad_document
from BelfryCAD.cad_geometry import Point2D
from BelfryCAD.utils.cad_expression import CadExpression


class TestXMLSerializer(unittest.TestCase):
    """Test cases for the XML serializer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.serializer = BelfryCADXMLSerializer()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)
    
    def create_test_document(self):
        """Create a test document with various objects."""
        document = Document()
        
        # Add parameters
        document.parameters = {
            'radius': '5.0',
            'height': '2 * $radius',
            'angle': '45º',
            'width': '10.0'
        }
        document.cad_expression = CadExpression(document.parameters)
        
        # Create a line
        line = LineCadObject(document, Point2D(0, 0), Point2D(10, 0), "black", 0.05)
        line.name = "Test Line"
        document.objects[line.object_id] = line
        
        # Create a circle
        # Calculate radius from center to perimeter point
        center = Point2D(5, 5)
        perimeter_point = Point2D(10, 5)
        radius = center.distance_to(perimeter_point)
        
        circle = CircleCadObject(document, center, radius, "blue", 0.1)
        circle.name = "Test Circle"
        document.objects[circle.object_id] = circle
        
        # Create an arc
        # Calculate radius and angles for a quarter circle
        center = Point2D(0, 0)
        start_point = Point2D(5, 0)
        end_point = Point2D(0, 5)
        radius = center.distance_to(start_point)
        start_degrees = (start_point - center).angle_degrees
        end_degrees = (end_point - center).angle_degrees
        span_degrees = end_degrees - start_degrees
        
        arc = ArcCadObject(document, center, radius, start_degrees, span_degrees, "red", 0.05)
        arc.name = "Test Arc"
        document.objects[arc.object_id] = arc
        
        # Create an ellipse
        # Calculate radii from center to axis points
        center = Point2D(15, 5)
        major_axis_point = Point2D(20, 5)
        minor_axis_point = Point2D(15, 7)
        radius1 = center.distance_to(major_axis_point)
        radius2 = center.distance_to(minor_axis_point)
        
        ellipse = EllipseCadObject(document, center, radius1, radius2, 0.0, "green", 0.05)
        ellipse.name = "Test Ellipse"
        document.objects[ellipse.object_id] = ellipse
        
        # Create a bezier curve
        bezier_points = [
            Point2D(0, 10),
            Point2D(2, 13),
            Point2D(8, 13),
            Point2D(10, 10)
        ]
        bezier = CubicBezierCadObject(document, bezier_points, "purple", 0.05)
        bezier.name = "Test Bezier"
        document.objects[bezier.object_id] = bezier
        
        # Create a gear
        gear = GearCadObject(document, Point2D(20, 0), 3.0, 12, 20.0, "orange", 0.05)
        gear.name = "Test Gear"
        document.objects[gear.object_id] = gear
        
        # Create a group
        group = GroupCadObject(document, "Test Group", "black", None)
        document.objects[group.object_id] = group
        
        # Add objects to group
        group_line = LineCadObject(document, Point2D(0, 15), Point2D(5, 15), "red", 0.05)
        group_line.name = "Group Line"
        group_line.parent_id = group.object_id
        document.objects[group_line.object_id] = group_line
        group.add_child(group_line.object_id)
        
        return document
    
    def test_save_and_load_basic_document(self):
        """Test saving and loading a basic document."""
        # Create document
        original_doc = self.create_test_document()
        
        # Save document
        filepath = os.path.join(self.temp_dir, "test_document.belcad")
        preferences = {
            'units': 'inches',
            'precision': 3,
            'use_fractions': False
        }
        
        success = save_belfrycad_document(original_doc, filepath, preferences)
        self.assertTrue(success, "Document save failed")
        
        # Load document
        loaded_doc = load_belfrycad_document(filepath)
        self.assertIsNotNone(loaded_doc, "Document load failed")
        
        # Verify basic properties
        self.assertEqual(len(loaded_doc.objects), len(original_doc.objects), 
                        "Object count mismatch")
        
        # Verify parameters
        self.assertEqual(loaded_doc.parameters, original_doc.parameters,
                        "Parameters mismatch")
        
        # Verify preferences
        self.assertEqual(loaded_doc.preferences['units'], 'inches')
        self.assertEqual(loaded_doc.preferences['precision'], 3)
        self.assertFalse(loaded_doc.preferences['use_fractions'])
    
    def test_all_cad_object_types(self):
        """Test that all CAD object types are saved and loaded correctly."""
        original_doc = self.create_test_document()
        filepath = os.path.join(self.temp_dir, "test_objects.belcad")
        
        # Save and load
        save_belfrycad_document(original_doc, filepath)
        loaded_doc = load_belfrycad_document(filepath)
        
        # Check that all object types are present
        original_types = {type(obj).__name__ for obj in original_doc.objects.values()}
        loaded_types = {type(obj).__name__ for obj in loaded_doc.objects.values()}
        
        self.assertEqual(original_types, loaded_types, "Object types mismatch")
        
        # Verify specific object properties
        for obj_id, original_obj in original_doc.objects.items():
            loaded_obj = loaded_doc.objects.get(obj_id)
            self.assertIsNotNone(loaded_obj, f"Object {obj_id} not found in loaded document")
            
            # Check basic properties
            self.assertEqual(loaded_obj.name, original_obj.name)
            self.assertEqual(loaded_obj.color, original_obj.color)
            self.assertEqual(loaded_obj.visible, original_obj.visible)
            self.assertEqual(loaded_obj.locked, original_obj.locked)
            
            # Check object-specific properties
            if isinstance(original_obj, LineCadObject):
                self.assertEqual(loaded_obj.start_point.x, original_obj.start_point.x)
                self.assertEqual(loaded_obj.start_point.y, original_obj.start_point.y)
                self.assertEqual(loaded_obj.end_point.x, original_obj.end_point.x)
                self.assertEqual(loaded_obj.end_point.y, original_obj.end_point.y)
            
            elif isinstance(original_obj, CircleCadObject):
                self.assertEqual(loaded_obj.center_point.x, original_obj.center_point.x)
                self.assertEqual(loaded_obj.center_point.y, original_obj.center_point.y)
                self.assertAlmostEqual(loaded_obj.radius, original_obj.radius, places=6)
            
            elif isinstance(original_obj, ArcCadObject):
                self.assertEqual(loaded_obj.center_point.x, original_obj.center_point.x)
                self.assertEqual(loaded_obj.center_point.y, original_obj.center_point.y)
                self.assertAlmostEqual(loaded_obj.radius, original_obj.radius, places=6)
                self.assertAlmostEqual(loaded_obj.start_degrees, original_obj.start_degrees, places=6)
                self.assertAlmostEqual(loaded_obj.span_degrees, original_obj.span_degrees, places=6)
            
            elif isinstance(original_obj, EllipseCadObject):
                self.assertEqual(loaded_obj.center_point.x, original_obj.center_point.x)
                self.assertEqual(loaded_obj.center_point.y, original_obj.center_point.y)
                self.assertEqual(loaded_obj.major_axis_point.x, original_obj.major_axis_point.x)
                self.assertEqual(loaded_obj.major_axis_point.y, original_obj.major_axis_point.y)
                self.assertEqual(loaded_obj.minor_axis_point.x, original_obj.minor_axis_point.x)
                self.assertEqual(loaded_obj.minor_axis_point.y, original_obj.minor_axis_point.y)
            
            elif isinstance(original_obj, CubicBezierCadObject):
                self.assertEqual(len(loaded_obj.points), len(original_obj.points))
                for i, (orig_point, loaded_point) in enumerate(zip(original_obj.points, loaded_obj.points)):
                    self.assertAlmostEqual(loaded_point.x, orig_point.x, places=6)
                    self.assertAlmostEqual(loaded_point.y, orig_point.y, places=6)
            
            elif isinstance(original_obj, GearCadObject):
                self.assertEqual(loaded_obj.center_point.x, original_obj.center_point.x)
                self.assertEqual(loaded_obj.center_point.y, original_obj.center_point.y)
                self.assertAlmostEqual(loaded_obj.pitch_radius, original_obj.pitch_radius, places=6)
                self.assertEqual(loaded_obj.num_teeth, original_obj.num_teeth)
                self.assertAlmostEqual(loaded_obj.pressure_angle, original_obj.pressure_angle, places=6)
    
    def test_grouping(self):
        """Test that grouping is preserved correctly."""
        original_doc = self.create_test_document()
        filepath = os.path.join(self.temp_dir, "test_groups.belcad")
        
        # Save and load
        save_belfrycad_document(original_doc, filepath)
        loaded_doc = load_belfrycad_document(filepath)
        
        # Find groups
        original_groups = [obj for obj in original_doc.objects.values() if isinstance(obj, GroupCadObject)]
        loaded_groups = [obj for obj in loaded_doc.objects.values() if isinstance(obj, GroupCadObject)]
        
        self.assertEqual(len(original_groups), len(loaded_groups), "Group count mismatch")
        
        # Check group properties
        for orig_group, loaded_group in zip(original_groups, loaded_groups):
            self.assertEqual(loaded_group.name, orig_group.name)
            self.assertEqual(loaded_group.children, orig_group.children)
            
            # Check that children have correct parent_id
            for child_id in orig_group.children:
                child_obj = loaded_doc.objects.get(child_id)
                self.assertIsNotNone(child_obj, f"Child object {child_id} not found")
                self.assertEqual(child_obj.parent_id, loaded_group.object_id)
    
    def test_parameters(self):
        """Test that parameters are saved and loaded correctly."""
        original_doc = self.create_test_document()
        filepath = os.path.join(self.temp_dir, "test_parameters.belcad")
        
        # Save and load
        save_belfrycad_document(original_doc, filepath)
        loaded_doc = load_belfrycad_document(filepath)
        
        # Check parameters
        self.assertEqual(loaded_doc.parameters, original_doc.parameters)
        
        # Check that CadExpression was created
        self.assertIsNotNone(loaded_doc.cad_expression)
        
        # Test parameter evaluation
        for name, expr in original_doc.parameters.items():
            original_value = original_doc.cad_expression.evaluate(expr)
            loaded_value = loaded_doc.cad_expression.evaluate(expr)
            self.assertAlmostEqual(loaded_value, original_value, places=6)
    
    def test_document_preferences(self):
        """Test that document preferences are saved and loaded correctly."""
        original_doc = self.create_test_document()
        filepath = os.path.join(self.temp_dir, "test_preferences.belcad")
        
        preferences = {
            'units': 'mm',
            'precision': 4,
            'use_fractions': True,
            'grid_visible': False,
            'show_rulers': False,
            'canvas_bg_color': '#000000',
            'grid_color': '#ff0000',
            'selection_color': '#00ff00'
        }
        
        # Save and load
        save_belfrycad_document(original_doc, filepath, preferences)
        loaded_doc = load_belfrycad_document(filepath)
        
        # Check preferences
        for key, value in preferences.items():
            self.assertEqual(loaded_doc.preferences[key], value, f"Preference {key} mismatch")
    
    def test_empty_document(self):
        """Test saving and loading an empty document."""
        document = Document()
        filepath = os.path.join(self.temp_dir, "empty_document.belcad")
        
        # Save and load
        save_belfrycad_document(document, filepath)
        loaded_doc = load_belfrycad_document(filepath)
        
        self.assertIsNotNone(loaded_doc)
        self.assertEqual(len(loaded_doc.objects), 0)
    
    def test_document_with_only_parameters(self):
        """Test document with only parameters, no objects."""
        document = Document()
        document.parameters = {
            'radius': '5.0',
            'height': '10.0',
            'area': 'pi * $radius^2'
        }
        document.cad_expression = CadExpression(document.parameters)
        
        filepath = os.path.join(self.temp_dir, "parameters_only.belcad")
        
        # Save and load
        save_belfrycad_document(document, filepath)
        loaded_doc = load_belfrycad_document(filepath)
        
        self.assertIsNotNone(loaded_doc)
        self.assertEqual(loaded_doc.parameters, document.parameters)
        self.assertEqual(len(loaded_doc.objects), 0)
    
    def test_invalid_file_handling(self):
        """Test handling of invalid files."""
        # Test non-existent file
        loaded_doc = load_belfrycad_document("nonexistent_file.belcad")
        self.assertIsNone(loaded_doc)
        
        # Test invalid zip file
        invalid_file = os.path.join(self.temp_dir, "invalid.belcad")
        with open(invalid_file, 'w') as f:
            f.write("This is not a valid zip file")
        
        loaded_doc = load_belfrycad_document(invalid_file)
        self.assertIsNone(loaded_doc)
    
    def test_serializer_class_methods(self):
        """Test the serializer class methods directly."""
        serializer = BelfryCADXMLSerializer()
        original_doc = self.create_test_document()
        filepath = os.path.join(self.temp_dir, "serializer_test.belcad")
        
        # Test save_document method
        success = serializer.save_document(original_doc, filepath)
        self.assertTrue(success)
        
        # Test load_document method
        loaded_doc = serializer.load_document(filepath)
        self.assertIsNotNone(loaded_doc)
        self.assertEqual(len(loaded_doc.objects), len(original_doc.objects))


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2) 