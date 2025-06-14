#!/usr/bin/env python3
"""
Tool CadScene Integration Fix

This module addresses the issue where Tool instances are created with 
QGraphicsScene when they should be instantiated with CadScene.

The problem: Tools expect CadScene-specific methods like removeItemsByTags()
and tagAsConstruction() but are getting basic QGraphicsScene instead.
"""

import sys
import os
from unittest.mock import Mock

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class CadSceneToolFactory:
    """Factory for creating tools with proper CadScene validation."""
    
    def __init__(self, cad_scene, document, preferences=None):
        """Initialize factory with CadScene and Document."""
        self.cad_scene = cad_scene
        self.document = document  
        self.preferences = preferences or {}
        
        # Validate that we have a real CadScene
        self._validate_cad_scene()
    
    def _validate_cad_scene(self):
        """Ensure the scene has required CadScene methods."""
        required_methods = [
            'removeItemsByTags',
            'tagAsConstruction',
            'addEllipse'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(self.cad_scene, method):
                missing_methods.append(method)
        
        if missing_methods:
            raise ValueError(
                f"Scene is missing CadScene methods: {missing_methods}. "
                "Ensure you're using CadScene, not QGraphicsScene."
            )
    
    def create_tool(self, tool_class, **extra_kwargs):
        """Create a tool with validated CadScene."""
        tool_kwargs = {
            'scene': self.cad_scene,
            'document': self.document,
            'preferences': self.preferences,
            **extra_kwargs
        }
        
        return tool_class(**tool_kwargs)


def create_mock_cad_scene():
    """Create a mock CadScene for testing with all required methods."""
    mock_scene = Mock()
    
    # Add all CadScene-specific methods
    mock_scene.removeItemsByTags = Mock()
    mock_scene.tagAsConstruction = Mock()
    mock_scene.addEllipse = Mock()
    mock_scene.addItem = Mock()
    mock_scene.removeItem = Mock()
    mock_scene.views = Mock(return_value=[])
    
    return mock_scene


def create_mock_document():
    """Create a mock Document for testing."""
    mock_doc = Mock()
    mock_doc.objects = Mock()
    mock_doc.objects.get_next_id = Mock(return_value=1)
    mock_doc.objects.current_layer = "Layer1"
    mock_doc.objects.add_object = Mock()
    
    return mock_doc


def test_tool_creation_with_cadscene():
    """Test that tools can be created properly with CadScene."""
    
    print("=== Testing Tool Creation with CadScene ===")
    
    try:
        # Import tools
        from BelfryCAD.tools.circle import CircleTool
        
        # Create mocks
        cad_scene = create_mock_cad_scene()
        document = create_mock_document()
        preferences = {}
        
        # Create factory
        factory = CadSceneToolFactory(cad_scene, document, preferences)
        
        # Create tool using factory
        tool = factory.create_tool(CircleTool)
        
        # Verify tool creation
        assert tool is not None
        assert tool.scene == cad_scene
        assert tool.document == document
        assert hasattr(tool.scene, 'removeItemsByTags')
        assert hasattr(tool.scene, 'tagAsConstruction')
        
        print("✅ CircleTool created successfully with CadScene")
        return True
        
    except Exception as e:
        print(f"❌ Tool creation failed: {e}")
        return False


def test_tool_creation_with_graphics_scene():
    """Test what happens when using QGraphicsScene instead of CadScene."""
    
    print("\n=== Testing Tool Creation with QGraphicsScene (Should Fail) ===")
    
    try:
        # Create basic QGraphicsScene mock (missing CadScene methods)
        graphics_scene = Mock()
        graphics_scene.addItem = Mock()
        graphics_scene.removeItem = Mock()
        # Missing: removeItemsByTags, tagAsConstruction
        
        document = create_mock_document()
        
        # Try to create factory with QGraphicsScene - should fail
        try:
            factory = CadSceneToolFactory(graphics_scene, document)
            print("❌ Factory should have rejected QGraphicsScene")
            return False
        except ValueError as e:
            print(f"✅ Factory correctly rejected QGraphicsScene: {e}")
            return True
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def demonstrate_proper_tool_instantiation():
    """Demonstrate how tools should be instantiated in real application."""
    
    print("\n=== Proper Tool Instantiation Patterns ===")
    
    patterns = """
1. In Main Window / Application Setup:
   
   class MainWindow:
       def __init__(self):
           # Create CadScene (not QGraphicsScene!)
           self.cad_scene = CadScene()
           self.document = Document()
           self.preferences = UserPreferences()
           
           # Create tool factory
           self.tool_factory = CadSceneToolFactory(
               self.cad_scene, 
               self.document, 
               self.preferences
           )
       
       def activate_circle_tool(self):
           # Use factory to create tool with proper CadScene
           tool = self.tool_factory.create_tool(CircleTool)
           tool.activate()
           return tool

2. In Tool Palette:
   
   def create_tool_button(tool_class, tool_factory):
       def on_clicked():
           tool = tool_factory.create_tool(tool_class)
           # ... activate tool
       
       button.clicked.connect(on_clicked)

3. In Tests:
   
   def test_circle_tool():
       cad_scene = create_mock_cad_scene()
       document = create_mock_document()
       
       factory = CadSceneToolFactory(cad_scene, document)
       tool = factory.create_tool(CircleTool)
       
       # Test tool functionality...

4. Key Points:
   - Always use CadScene, never QGraphicsScene
   - Validate scene has required methods
   - Use factory pattern for consistent creation
   - Mock CadScene methods in tests
"""
    
    print(patterns)


def check_existing_tool_files():
    """Check if existing tool files expect CadScene methods."""
    
    print("\n=== Checking Existing Tool Files ===")
    
    # Look for CadScene method usage in tool files
    tool_files = [
        "BelfryCAD/tools/circle.py",
        "BelfryCAD/tools/base.py"
    ]
    
    for file_path in tool_files:
        if os.path.exists(file_path):
            print(f"\n📄 Checking {file_path}")
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Look for CadScene-specific method calls
                cadscene_methods = [
                    'removeItemsByTags',
                    'tagAsConstruction'
                ]
                
                for method in cadscene_methods:
                    if method in content:
                        print(f"  ✅ Found {method}() - requires CadScene")
                    
            except Exception as e:
                print(f"  ❌ Error reading file: {e}")
        else:
            print(f"📄 {file_path} - File not found")


def main():
    """Run all tests and demonstrations."""
    
    print("🔧 TOOL CADSCENE INTEGRATION ANALYSIS")
    print("=" * 50)
    
    # Run tests
    test1_passed = test_tool_creation_with_cadscene()
    test2_passed = test_tool_creation_with_graphics_scene()
    
    # Show proper patterns
    demonstrate_proper_tool_instantiation()
    
    # Check existing files
    check_existing_tool_files()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)
    
    if test1_passed and test2_passed:
        print("✅ All tests passed")
        print("✅ CadScene validation working correctly")
        print("✅ Tool factory pattern works")
    else:
        print("❌ Some tests failed")
    
    print("""
🎯 ACTION ITEMS:

1. Ensure all Tool instantiation uses CadScene, not QGraphicsScene
2. Use CadSceneToolFactory for consistent tool creation
3. Update tests to use create_mock_cad_scene()
4. Validate CadScene methods before tool creation
5. Update main window to create tools through factory

🔍 LOOK FOR THESE PATTERNS TO FIX:
- tool = SomeTool(graphics_scene, ...)  # ❌ Wrong
- tool = SomeTool(cad_scene, ...)       # ✅ Right
- Missing removeItemsByTags in scene
- Missing tagAsConstruction in scene
""")


if __name__ == "__main__":
    main()