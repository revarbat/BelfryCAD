"""
Test for control point visibility fix.

This test verifies that control points are properly hidden when CAD objects
are deselected, fixing the bug where control points would remain visible
after clicking elsewhere.
"""

import pytest
import sys
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

# Add the source directory to Python path for imports
sys.path.insert(0, 'src')

from BelfryCAD.gui.widgets.cad_scene import CadScene
from BelfryCAD.gui.document_window import DocumentWindow
from BelfryCAD.gui.viewmodels.cad_viewmodels.circle_viewmodel import CircleViewModel
from BelfryCAD.models.cad_objects.circle_cad_object import CircleCadObject
from BelfryCAD.config import AppConfig
from BelfryCAD.gui.viewmodels.preferences_viewmodel import PreferencesViewModel
from BelfryCAD.models.document import Document
from BelfryCAD.cad_geometry import Point2D


class TestControlPointVisibilityFix:
    """Test control point visibility behavior after the fix."""
    
    @pytest.fixture
    def app(self):
        """Create QApplication for testing."""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        return app
        
    @pytest.fixture 
    def mock_config(self):
        """Create a mock config object."""
        config = Mock(spec=AppConfig)
        config.APP_NAME = "BelfryCAD Test"
        return config
        
    @pytest.fixture
    def mock_preferences(self):
        """Create a mock preferences viewmodel."""
        return Mock(spec=PreferencesViewModel)
        
    @pytest.fixture
    def document(self):
        """Create a test document."""
        return Document()
        
    @pytest.fixture
    def scene(self):
        """Create a test CAD scene."""
        return CadScene()
        
    @pytest.fixture
    def circle_viewmodel(self, mock_config, mock_preferences, document):
        """Create a circle viewmodel for testing."""
        # Create a circle CAD object
        circle_obj = CircleCadObject(
            document=document,
            center_point=Point2D(0, 0),
            radius=5.0
        )
        
        # Create a mock document window
        mock_doc_window = Mock()
        mock_doc_window.cad_scene = Mock()
        mock_doc_window.cad_scene.get_precision.return_value = 3
        mock_doc_window.grid_info = Mock()
        mock_doc_window.grid_info.format_label.return_value = "5.000"
        mock_doc_window.grid_info.unit_scale = 1.0
        
        # Create the viewmodel
        viewmodel = CircleViewModel(circle_obj, mock_doc_window)
        return viewmodel
        
    def test_scene_no_longer_has_control_point_dictionaries(self, scene):
        """Test that the scene no longer has the problematic control point dictionaries."""
        # The scene should not have _control_points or _control_datums attributes
        assert not hasattr(scene, '_control_points'), "Scene should not have _control_points dictionary"
        assert not hasattr(scene, '_control_datums'), "Scene should not have _control_datums dictionary"
        
    def test_scene_no_longer_has_hide_all_control_points_method(self, scene):
        """Test that the problematic _hide_all_control_points method was removed."""
        assert not hasattr(scene, '_hide_all_control_points'), "Scene should not have _hide_all_control_points method"
        
    def test_scene_no_longer_has_show_control_points_for_viewmodel_method(self, scene):
        """Test that the problematic _show_control_points_for_viewmodel method was removed."""
        assert not hasattr(scene, '_show_control_points_for_viewmodel'), "Scene should not have _show_control_points_for_viewmodel method"
        
    def test_viewmodel_control_point_management_still_works(self, app, scene, circle_viewmodel):
        """Test that viewmodel control point management still works properly."""
        # Show controls
        circle_viewmodel.show_controls(scene)
        
        # Should have created control points
        controls = circle_viewmodel.controls
        assert len(controls) == 2, "Circle should have 2 control points"
        
        # Control points should be added to scene
        scene_items = scene.items()
        control_points_in_scene = [item for item in scene_items if item in controls]
        assert len(control_points_in_scene) == 2, "Both control points should be in scene"
        
        # Hide controls
        circle_viewmodel.hide_controls(scene)
        
        # Control points should be removed from scene
        scene_items_after = scene.items()
        control_points_in_scene_after = [item for item in scene_items_after if item in controls]
        assert len(control_points_in_scene_after) == 0, "Control points should be removed from scene"
        
        # Controls list should be cleared
        assert len(circle_viewmodel.controls) == 0, "Controls list should be cleared"
        
    def test_scene_selection_changed_signal_still_emitted(self, scene):
        """Test that the scene still emits selection changed signals properly."""
        # Mock an item with viewmodel data
        mock_item = Mock()
        mock_viewmodel = Mock()
        mock_viewmodel.is_selected = False
        mock_viewmodel._cad_object = Mock()
        mock_viewmodel._cad_object.object_id = "test_obj"
        mock_item.data.return_value = mock_viewmodel
        
        # Mock selectedItems to return our mock item
        scene.selectedItems = Mock(return_value=[mock_item])
        scene.items = Mock(return_value=[mock_item])
        
        # Mock the signal emission
        scene.scene_selection_changed = Mock()
        
        # Trigger selection change
        scene._on_selection_changed()
        
        # Verify signal was emitted with correct object ID
        scene.scene_selection_changed.emit.assert_called_once()
        emitted_args = scene.scene_selection_changed.emit.call_args[0]
        assert len(emitted_args) == 1
        selected_ids = emitted_args[0]
        assert "test_obj" in selected_ids
        
        # Verify viewmodel selection state was updated
        assert mock_viewmodel.is_selected == True
        
    def test_control_point_dragging_flag_still_works(self, scene):
        """Test that the control point dragging flag mechanism still works."""
        # Initially not dragging
        assert scene._control_point_dragging == False
        
        # Set dragging
        scene.set_control_point_dragging(True)
        assert scene._control_point_dragging == True
        
        # Clear dragging  
        scene.set_control_point_dragging(False)
        assert scene._control_point_dragging == False
        
    def test_on_selection_changed_respects_dragging_flag(self, scene):
        """Test that _on_selection_changed respects the dragging flag."""
        # Set dragging flag
        scene._control_point_dragging = True
        
        # Mock the signal emission
        scene.scene_selection_changed = Mock()
        
        # Trigger selection change - should return early due to dragging flag
        scene._on_selection_changed()
        
        # Signal should not be emitted
        scene.scene_selection_changed.emit.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 