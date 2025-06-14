#!/usr/bin/env python3
"""
Test tool instantiation with proper CadScene.

This test demonstrates the issue where tools are instantiated with QGraphicsScene
instead of CadScene, and shows how to fix it.
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestToolInstantiation(unittest.TestCase):
    """Test proper tool instantiation with CadScene."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock document
        self.mock_document = Mock()
        self.mock_document.objects = Mock()
        self.mock_document.objects.get_next_id = Mock(return_value=1)
        self.mock_document.objects.current_layer = "Layer1"
        self.mock_document.objects.add_object = Mock()

    def create_mock_cad_scene(self):
        """Create a proper mock CadScene with required methods."""
        mock_scene = Mock()
        
        # Add CadScene-specific methods that tools expect
        mock_scene.removeItemsByTags = Mock()
        mock_scene.tagAsConstruction = Mock() 
        mock_scene.addEllipse = Mock()
        mock_scene.addItem = Mock()
        mock_scene.removeItem = Mock()
        
        # Add some basic QGraphicsScene methods
        mock_scene.sceneRect = Mock()
        mock_scene.views = Mock(return_value=[])
        
        return mock_scene

    def create_mock_graphics_scene(self):
        """Create a basic QGraphicsScene mock (missing CadScene methods)."""
        mock_scene = Mock()
        
        # Only basic QGraphicsScene methods
        mock_scene.addItem = Mock()
        mock_scene.removeItem = Mock()
        mock_scene.sceneRect = Mock()
        mock_scene.views = Mock(return_value=[])
        
        # Missing CadScene-specific methods:
        # - removeItemsByTags
        # - tagAsConstruction
        # - enhanced addEllipse
        
        return mock_scene

    def test_circle_tool_with_cad_scene(self):
        """Test CircleTool instantiation with proper CadScene."""
        from BelfryCAD.tools.circle import CircleTool
        
        # Create proper CadScene mock
        cad_scene = self.create_mock_cad_scene()
        
        # Instantiate tool with CadScene
        tool = CircleTool(scene=cad_scene, document=self.mock_document)
        
        # Verify tool was created successfully
        self.assertIsNotNone(tool)
        self.assertEqual(tool.scene, cad_scene)
        self.assertEqual(tool.document, self.mock_document)
        
        # Verify scene has required CadScene methods
        self.assertTrue(hasattr(tool.scene, 'removeItemsByTags'))
        self.assertTrue(hasattr(tool.scene, 'tagAsConstruction'))
        
        print("✅ CircleTool instantiated successfully with CadScene")

    def test_circle_tool_with_graphics_scene_fails(self):
        """Test that CircleTool fails gracefully with QGraphicsScene."""
        from BelfryCAD.tools.circle import CircleTool
        
        # Create basic QGraphicsScene mock (missing CadScene methods)
        graphics_scene = self.create_mock_graphics_scene()
        
        # Instantiate tool with basic QGraphicsScene
        tool = CircleTool(scene=graphics_scene, document=self.mock_document)
        
        # Tool should be created but scene lacks CadScene methods
        self.assertIsNotNone(tool)
        self.assertEqual(tool.scene, graphics_scene)
        
        # Verify scene is missing CadScene methods
        self.assertFalse(hasattr(tool.scene, 'removeItemsByTags'))
        self.assertFalse(hasattr(tool.scene, 'tagAsConstruction'))
        
        print("⚠️  CircleTool created with QGraphicsScene (missing CadScene methods)")

    def test_tool_validation_method(self):
        """Test validation method to check if tool has proper CadScene."""
        from BelfryCAD.tools.circle import CircleTool
        
        def validate_tool_scene(tool):
            """Validate that tool has proper CadScene."""
            required_methods = ['removeItemsByTags', 'tagAsConstruction']
            
            for method in required_methods:
                if not hasattr(tool.scene, method):
                    return False, f"Missing method: {method}"
            
            return True, "Tool has proper CadScene"
        
        # Test with proper CadScene
        cad_scene = self.create_mock_cad_scene()
        good_tool = CircleTool(scene=cad_scene, document=self.mock_document)
        
        is_valid, message = validate_tool_scene(good_tool)
        self.assertTrue(is_valid)
        print(f"✅ CadScene validation: {message}")
        
        # Test with basic QGraphicsScene
        graphics_scene = self.create_mock_graphics_scene()
        bad_tool = CircleTool(scene=graphics_scene, document=self.mock_document)
        
        is_valid, message = validate_tool_scene(bad_tool)
        self.assertFalse(is_valid)
        print(f"❌ QGraphicsScene validation: {message}")

    def test_tool_factory_pattern(self):
        """Test tool factory pattern with proper CadScene."""
        from BelfryCAD.tools.circle import CircleTool, Circle2PTTool, Circle3PTTool
        
        class ToolFactory:
            """Factory for creating tools with proper CadScene."""
            
            def __init__(self, cad_scene, document):
                self.cad_scene = cad_scene
                self.document = document
            
            def create_tool(self, tool_class):
                """Create tool with validated CadScene."""
                # Validate CadScene has required methods
                required_methods = ['removeItemsByTags', 'tagAsConstruction']
                for method in required_methods:
                    if not hasattr(self.cad_scene, method):
                        raise ValueError(f"CadScene missing method: {method}")
                
                # Create tool with proper parameters
                return tool_class(scene=self.cad_scene, document=self.document)
        
        # Test factory with proper CadScene
        cad_scene = self.create_mock_cad_scene()
        factory = ToolFactory(cad_scene, self.mock_document)
        
        # Test creating different tool types
        tools_to_test = [CircleTool, Circle2PTTool, Circle3PTTool]
        
        for tool_class in tools_to_test:
            tool = factory.create_tool(tool_class)
            self.assertIsNotNone(tool)
            self.assertEqual(tool.scene, cad_scene)
            print(f"✅ {tool_class.__name__} created via factory")
        
        # Test factory with invalid scene
        graphics_scene = self.create_mock_graphics_scene()
        bad_factory = ToolFactory(graphics_scene, self.mock_document)
        
        with self.assertRaises(ValueError):
            bad_factory.create_tool(CircleTool)
        print("✅ Factory properly rejects QGraphicsScene")

    def test_main_window_integration_pattern(self):
        """Test how tools should be integrated in main window."""
        
        class MockMainWindow:
            """Mock main window with proper tool management."""
            
            def __init__(self):
                # Create CadScene (not QGraphicsScene)
                self.cad_scene = self.create_mock_cad_scene()
                self.document = Mock()
                self.document.objects = Mock()
                self.document.objects.get_next_id = Mock(return_value=1)
                self.document.objects.current_layer = "Layer1"
                
                self.active_tool = None
            
            def create_mock_cad_scene(self):
                """Create mock CadScene for main window."""
                mock_scene = Mock()
                mock_scene.removeItemsByTags = Mock()
                mock_scene.tagAsConstruction = Mock()
                mock_scene.addEllipse = Mock()
                mock_scene.addItem = Mock()
                mock_scene.removeItem = Mock()
                return mock_scene
            
            def activate_tool(self, tool_class):
                """Activate a tool with proper CadScene."""
                # Deactivate current tool
                if self.active_tool:
                    self.active_tool.cancel()
                
                # Create new tool with CadScene
                self.active_tool = tool_class(
                    scene=self.cad_scene,  # Use CadScene, not QGraphicsScene
                    document=self.document
                )
                
                # Activate the tool
                self.active_tool.activate()
                
                return self.active_tool
        
        # Test main window pattern
        from BelfryCAD.tools.circle import CircleTool
        
        main_window = MockMainWindow()
        tool = main_window.activate_tool(CircleTool)
        
        self.assertIsNotNone(tool)
        self.assertEqual(tool.scene, main_window.cad_scene)
        self.assertTrue(hasattr(tool.scene, 'removeItemsByTags'))
        
        print("✅ Main window integration pattern works correctly")


def print_instantiation_summary():
    """Print summary of proper tool instantiation patterns."""
    
    summary = """
=== TOOL INSTANTIATION SUMMARY ===

PROBLEM: Tools instantiated with QGraphicsScene instead of CadScene

SOLUTION: Always use CadScene when creating tools

✅ CORRECT PATTERNS:

1. Direct Instantiation:
   cad_scene = CadScene(...)
   tool = CircleTool(scene=cad_scene, document=document)

2. Factory Pattern:
   factory = ToolFactory(cad_scene, document)
   tool = factory.create_tool(CircleTool)

3. Main Window Integration:
   # In main window __init__:
   self.cad_scene = CadScene(...)  # Not QGraphicsScene!
   
   # When activating tools:
   tool = CircleTool(scene=self.cad_scene, document=self.document)

❌ INCORRECT PATTERNS:

1. Using QGraphicsScene:
   graphics_scene = QGraphicsScene()  # Missing CadScene methods!
   tool = CircleTool(scene=graphics_scene, document=document)

2. Missing validation:
   # No check that scene has removeItemsByTags(), tagAsConstruction()

🔍 REQUIRED CADSCENE METHODS:
- removeItemsByTags(tags)
- tagAsConstruction(item)
- addEllipse() with tagging support

🧪 FOR TESTING:
Use mock CadScene with all required methods:
   mock_scene = Mock()
   mock_scene.removeItemsByTags = Mock()
   mock_scene.tagAsConstruction = Mock()
   tool = CircleTool(scene=mock_scene, document=mock_doc)
"""
    
    print(summary)


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2, exit=False)
    
    # Print summary
    print_instantiation_summary()