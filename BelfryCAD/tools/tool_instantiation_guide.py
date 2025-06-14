"""
Tool Instantiation Guide for BelfryCAD

This guide explains how Tool classes should be properly instantiated with CadScene
instead of QGraphicsScene to ensure all CadScene-specific functionality works.

PROBLEM:
Tool instances are being created with QGraphicsScene when they should be 
instantiated with CadScene for proper functionality.

SOLUTION:
Tools must be instantiated with a CadScene instance that provides:
- removeItemsByTags() method
- tagAsConstruction() method  
- addEllipse() with proper tagging support
- Other CadScene-specific functionality
"""

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from BelfryCAD.gui.cad_scene import CadScene
    from BelfryCAD.core.document import Document
    from BelfryCAD.tools.base import Tool


class ToolInstantiationManager:
    """Manages proper tool instantiation with CadScene."""
    
    def __init__(self, cad_scene: 'CadScene', document: 'Document'):
        """Initialize with CadScene and Document."""
        self.cad_scene = cad_scene
        self.document = document
        self._active_tool: 'Tool' = None
    
    def create_tool(self, tool_class: type, **kwargs) -> 'Tool':
        """
        Create a tool instance with proper CadScene and Document.
        
        Args:
            tool_class: The Tool class to instantiate
            **kwargs: Additional arguments for tool initialization
            
        Returns:
            Properly configured Tool instance
        """
        # Ensure we have required parameters
        tool_kwargs = {
            'scene': self.cad_scene,  # Use CadScene, not QGraphicsScene
            'document': self.document,
            **kwargs
        }
        
        # Validate CadScene has required methods
        self._validate_cad_scene()
        
        # Create tool instance
        tool = tool_class(**tool_kwargs)
        
        # Verify tool was created properly
        self._validate_tool(tool)
        
        return tool
    
    def _validate_cad_scene(self):
        """Validate that the scene is a proper CadScene."""
        required_methods = [
            'removeItemsByTags',
            'tagAsConstruction', 
            'addEllipse'
        ]
        
        for method_name in required_methods:
            if not hasattr(self.cad_scene, method_name):
                raise ValueError(
                    f"Scene missing required CadScene method: {method_name}. "
                    f"Ensure you're using CadScene, not QGraphicsScene."
                )
    
    def _validate_tool(self, tool: 'Tool'):
        """Validate that the tool was created properly."""
        if not hasattr(tool, 'scene'):
            raise ValueError("Tool missing 'scene' attribute")
        
        if not hasattr(tool.scene, 'removeItemsByTags'):
            raise ValueError(
                "Tool.scene is not a CadScene - missing removeItemsByTags method"
            )
    
    def set_active_tool(self, tool_class: type, **kwargs) -> 'Tool':
        """Set the active tool, creating it with proper parameters."""
        # Deactivate current tool if any
        if self._active_tool:
            self._active_tool.cancel()
        
        # Create and activate new tool
        self._active_tool = self.create_tool(tool_class, **kwargs)
        self._active_tool.activate()
        
        return self._active_tool
    
    @property
    def active_tool(self) -> 'Tool':
        """Get the currently active tool."""
        return self._active_tool


# Example usage for tests and application
def create_tool_with_cad_scene(tool_class: type, cad_scene: 'CadScene', 
                              document: 'Document', **kwargs) -> 'Tool':
    """
    Convenience function to create a tool with proper CadScene.
    
    Usage:
        from BelfryCAD.tools.circle import CircleTool
        from BelfryCAD.gui.cad_scene import CadScene
        
        # Correct instantiation
        cad_scene = CadScene(...)
        document = Document(...)
        tool = create_tool_with_cad_scene(CircleTool, cad_scene, document)
        
        # NOT: tool = CircleTool(graphics_scene, document)  # Wrong!
    """
    manager = ToolInstantiationManager(cad_scene, document)
    return manager.create_tool(tool_class, **kwargs)


# Testing utilities
def create_mock_cad_scene():
    """Create a mock CadScene for testing purposes."""
    from unittest.mock import Mock
    
    mock_scene = Mock()
    
    # Add required CadScene methods
    mock_scene.removeItemsByTags = Mock()
    mock_scene.tagAsConstruction = Mock()
    mock_scene.addEllipse = Mock()
    mock_scene.addItem = Mock()
    mock_scene.removeItem = Mock()
    
    return mock_scene


def test_tool_instantiation():
    """Test that tools are properly instantiated with CadScene."""
    from BelfryCAD.tools.circle import CircleTool
    from unittest.mock import Mock
    
    # Create mock CadScene with required methods
    cad_scene = create_mock_cad_scene()
    document = Mock()
    document.objects = Mock()
    document.objects.get_next_id = Mock(return_value=1)
    document.objects.current_layer = "Layer1"
    
    # Test proper instantiation
    try:
        tool = create_tool_with_cad_scene(CircleTool, cad_scene, document)
        print("✅ Tool instantiated successfully with CadScene")
        
        # Verify tool has proper scene
        assert hasattr(tool.scene, 'removeItemsByTags'), "Tool scene missing CadScene methods"
        print("✅ Tool scene has required CadScene methods")
        
        return True
        
    except Exception as e:
        print(f"❌ Tool instantiation failed: {e}")
        return False


if __name__ == "__main__":
    # Run the test
    test_tool_instantiation()
    
    print("""
SUMMARY - Tool Instantiation Best Practices:

1. ✅ CORRECT: Use CadScene when creating tools
   tool = CircleTool(scene=cad_scene, document=document)

2. ❌ INCORRECT: Using QGraphicsScene
   tool = CircleTool(scene=graphics_scene, document=document)

3. 🔧 For Testing: Use create_mock_cad_scene()
   mock_scene = create_mock_cad_scene()
   tool = CircleTool(scene=mock_scene, document=mock_doc)

4. 🏭 In Production: Use ToolInstantiationManager
   manager = ToolInstantiationManager(cad_scene, document)
   tool = manager.create_tool(CircleTool)

5. 🎯 Key Point: CadScene provides specialized methods like:
   - removeItemsByTags()
   - tagAsConstruction()
   - Enhanced addEllipse() with tagging
""")