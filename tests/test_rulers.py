#!/usr/bin/env python3
"""
Test script to verify rulers functionality in PyTkCAD.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from BelfryCAD.config import AppConfig
from BelfryCAD.core.preferences import PreferencesManager
from BelfryCAD.core.document import Document
from BelfryCAD.gui.main_window import MainWindow


def test_rulers():
    """Test that rulers are properly integrated and functional."""
    app = QApplication([])
    
    # Create application components
    config = AppConfig()
    preferences = PreferencesManager(config)
    document = Document()
    
    # Create main window
    main_window = MainWindow(config, preferences, document)
    main_window.show()
    
    # Verify rulers are created
    assert hasattr(main_window, 'ruler_manager'), "RulerManager should be created"
    assert main_window.ruler_manager is not None, "RulerManager should not be None"
    
    # Verify ruler widgets exist
    h_ruler = main_window.ruler_manager.get_horizontal_ruler()
    v_ruler = main_window.ruler_manager.get_vertical_ruler()
    
    assert h_ruler is not None, "Horizontal ruler should exist"
    assert v_ruler is not None, "Vertical ruler should exist"
    
    # Verify rulers are properly added to the layout
    central_widget = main_window.centralWidget()
    layout = central_widget.layout()
    
    # Check that grid layout has 4 items (corner, h_ruler, v_ruler, canvas)
    assert layout.count() == 4, f"Layout should have 4 items, has {layout.count()}"
    
    # Test mouse position updates
    print("Testing mouse position updates...")
    main_window.ruler_manager.update_mouse_position(10.5, 20.75)
    
    assert h_ruler.position == 10.5, f"Horizontal ruler position should be 10.5, is {h_ruler.position}"
    assert v_ruler.position == 20.75, f"Vertical ruler position should be 20.75, is {v_ruler.position}"
    
    print("✓ Rulers are properly integrated and functional!")
    
    # Close the application after a short delay
    QTimer.singleShot(100, app.quit)
    app.exec()


if __name__ == "__main__":
    test_rulers()
