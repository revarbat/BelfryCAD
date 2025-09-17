"""
Test for selection animation functionality.

This test verifies that the selection animation timer is properly set up
and running to continuously animate the dashed selection outlines.
"""

import pytest
import sys
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Add the source directory to Python path for imports
sys.path.insert(0, 'src')

from BelfryCAD.gui.widgets.cad_scene import CadScene


class TestSelectionAnimation:
    """Test selection animation timer functionality."""
    
    @pytest.fixture
    def app(self):
        """Create QApplication for testing."""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        return app
        
    @pytest.fixture
    def scene(self):
        """Create a test CAD scene."""
        return CadScene()
        
    def test_animation_timer_exists(self, app, scene):
        """Test that the animation timer is created and configured correctly."""
        # Timer should exist
        assert hasattr(scene, '_selection_animation_timer')
        timer = scene._selection_animation_timer
        assert isinstance(timer, QTimer)
        
        # Timer should be active (running)
        assert timer.isActive()
        
        # Timer should have the correct interval (50ms for 20 FPS)
        assert timer.interval() == 50
        
    def test_animation_timer_connected_to_method(self, app, scene):
        """Test that the timer is connected to the animation method."""
        timer = scene._selection_animation_timer
        
        # The timer should be connected to the _animate_selection_outlines method
        assert hasattr(scene, '_animate_selection_outlines')
        
        # We can't easily test the signal connection directly, but we can verify
        # the method exists and is callable
        assert callable(scene._animate_selection_outlines)
        
    def test_animate_selection_outlines_method_works(self, app, scene):
        """Test that the _animate_selection_outlines method executes without errors."""
        # Create mock selected items
        mock_item1 = Mock()
        mock_item1.update = Mock()
        mock_item2 = Mock()
        mock_item2.update = Mock()
        
        # Mock the selectedItems method to return our mock items
        scene.selectedItems = Mock(return_value=[mock_item1, mock_item2])
        
        # Call the animation method
        scene._animate_selection_outlines()
        
        # Verify that update was called on both items
        mock_item1.update.assert_called_once()
        mock_item2.update.assert_called_once()
        
    def test_animate_selection_outlines_handles_no_selection(self, app, scene):
        """Test that the animation method handles the case when nothing is selected."""
        # Mock selectedItems to return empty list
        scene.selectedItems = Mock(return_value=[])
        
        # This should not raise any exceptions
        scene._animate_selection_outlines()
        
    def test_animate_selection_outlines_handles_items_without_update(self, app, scene):
        """Test that the animation method handles items that don't have an update method."""
        # Create mock items - one with update, one without
        mock_item_with_update = Mock()
        mock_item_with_update.update = Mock()
        
        mock_item_without_update = Mock()
        # Explicitly remove the update attribute
        if hasattr(mock_item_without_update, 'update'):
            delattr(mock_item_without_update, 'update')
        
        # Mock the selectedItems method
        scene.selectedItems = Mock(return_value=[mock_item_with_update, mock_item_without_update])
        
        # Call the animation method - should not raise exceptions
        scene._animate_selection_outlines()
        
        # Only the item with update should have had its update method called
        mock_item_with_update.update.assert_called_once()
        
    def test_timer_configuration_constants(self, app, scene):
        """Test that the timer configuration uses reasonable values."""
        timer = scene._selection_animation_timer
        
        # 50ms interval = 20 FPS, which is good for smooth animation without being too resource intensive
        assert timer.interval() == 50
        
        # Timer should be running by default
        assert timer.isActive()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 