"""
Comprehensive test script to verify that escape key properly cancels tool operations.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtWidgets import QApplication, QGraphicsSceneMouseEvent
from PySide6.QtCore import QPointF
from PySide6.QtGui import Qt, QKeyEvent

from BelfryCAD.gui.document_window import DocumentWindow
from BelfryCAD.models.document import Document
from BelfryCAD.gui.viewmodels.preferences_viewmodel import PreferencesViewModel
from BelfryCAD.models.preferences import PreferencesModel
from BelfryCAD.config import AppConfig


def test_escape_key_comprehensive():
    """Test that escape key properly cancels operations for multiple tools."""
    
    # Create QApplication if it doesn't exist
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create required components
    config = AppConfig()
    preferences_model = PreferencesModel(config)
    preferences = PreferencesViewModel(preferences_model)
    document = Document()
    
    # Create document window
    window = DocumentWindow(config, preferences, document)
    
    # Show the window
    window.show()
    
    # Test tools to verify
    test_tools = ["LINE", "CIRCLE", "POINT", "RECTANGLE"]
    
    for tool_token in test_tools:
        print(f"\n=== Testing {tool_token} Tool ===")
        
        # Activate the tool
        window.activate_tool(tool_token)
        
        # Get the active tool and scene
        active_tool = window.tool_manager.get_active_tool()
        scene = window.cad_scene
        
        print(f"Active tool: {active_tool.__class__.__name__}")
        print(f"Initial tool state: {active_tool.state}")
        
        # Simulate a mouse press to start drawing
        scene_pos = QPointF(100, 100)
        mouse_event = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMousePress)
        mouse_event.setScenePos(scene_pos)
        mouse_event.setButton(Qt.MouseButton.LeftButton)
        mouse_event.setButtons(Qt.MouseButton.LeftButton)
        
        scene.mousePressEvent(mouse_event)
        print(f"Tool state after mouse press: {active_tool.state}")
        print(f"Points collected: {len(active_tool.points)}")
        
        # Simulate escape key press through scene
        key_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        scene.keyPressEvent(key_event)
        
        print(f"Tool state after escape key: {active_tool.state}")
        print(f"Points collected after escape: {len(active_tool.points)}")
        print(f"Temp objects after escape: {len(active_tool.temp_objects)}")
        
        # Verify the tool was properly reset
        if active_tool.state.name == "ACTIVE" and len(active_tool.points) == 0 and len(active_tool.temp_objects) == 0:
            print(f"✅ {tool_token} tool escape key handling: PASSED")
        else:
            print(f"❌ {tool_token} tool escape key handling: FAILED")
    
    print("\n=== All Tests Completed ===")
    
    # Keep the window open for a moment to see the result
    import time
    time.sleep(2)
    
    window.close()


if __name__ == "__main__":
    test_escape_key_comprehensive() 