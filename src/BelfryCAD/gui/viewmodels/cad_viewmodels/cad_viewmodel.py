"""
CadViewModel base class for BelfryCAD.

This base class provides the common interface that all CAD object viewmodels should implement.
It defines the standard signals, properties, and methods for managing CAD objects in the UI.
"""

from typing import List, Tuple, TYPE_CHECKING
from PySide6.QtCore import QObject, Signal, QPointF
from PySide6.QtWidgets import QGraphicsScene

if TYPE_CHECKING:
    from ....models.cad_object import CadObject
    from ....gui.document_window import DocumentWindow


class CadViewModel(QObject):
    """
    Base class for CAD object viewmodels.
    
    This class defines the common interface that all CAD object viewmodels should implement.
    It provides standard signals, properties, and methods for managing CAD objects in the UI.
    """
    
    # Standard signals that all CAD viewmodels should emit
    object_moved = Signal(QPointF)  # new position
    object_selected = Signal(bool)  # is_selected
    object_modified = Signal()  # object changed
    control_points_updated = Signal()  # control points updated
    
    def __init__(self, document_window: 'DocumentWindow', cad_object: 'CadObject'):
        """
        Initialize the CAD viewmodel.
        
        Args:
            document_window: Reference to the document window for accessing preferences and other UI state
            cad_object: The CAD object model that this viewmodel represents
        """
        super().__init__()
        self._document_window = document_window
        self._cad_object = cad_object
        self._is_selected = False
        self._view_items = []
        self._decorations = []
        self._controls = []
        self._controls = []
    
    # Abstract methods that subclasses must implement
    
    def update_view(self, scene: QGraphicsScene):
        """
        Creates and/or updates the view items for this CAD object.
        This is called when the object is added to the scene, and when the object is modified.
        
        Args:
            scene: The graphics scene to add view items to
        """
        raise NotImplementedError("Subclasses must implement update_view")
    
    def show_decorations(self, scene: QGraphicsScene):
        """
        Show the decorations for this object.
        This is called when this object is selected.
        
        Args:
            scene: The graphics scene to add decoration items to
        """
        raise NotImplementedError("Subclasses must implement show_decorations")
    
    def hide_decorations(self, scene: QGraphicsScene):
        """
        Hide the decorations for this object.
        This is called when this object is deselected.
        
        Args:
            scene: The graphics scene to remove decoration items from
        """
        raise NotImplementedError("Subclasses must implement hide_decorations")
    
    def update_decorations(self, scene: QGraphicsScene):
        """
        Update the decorations for this object.
        This is called when this object is modified.
        
        Args:
            scene: The graphics scene containing the decoration items
        """
        raise NotImplementedError("Subclasses must implement update_decorations")
    
    def show_controls(self, scene: QGraphicsScene):
        """
        Show the controls for this object.
        This is called when this object becomes the only object selected.
        
        Args:
            scene: The graphics scene to add control items to
        """
        raise NotImplementedError("Subclasses must implement show_controls")
    
    def hide_controls(self, scene: QGraphicsScene):
        """
        Hide the controls for this object.
        This is called when this object is deselected, or when an additional object becomes selected.
        
        Args:
            scene: The graphics scene to remove control items from
        """
        raise NotImplementedError("Subclasses must implement hide_controls")
    
    def update_controls(self, scene: QGraphicsScene):
        """
        Update the controls for this object.
        This is called when this object is modified.
        
        Args:
            scene: The graphics scene containing the control items
        """
        raise NotImplementedError("Subclasses must implement update_controls")
    
    def update_all(self):
        """Update the view and controls"""
        scene = self._document_window.cad_scene
        if scene:
            self.update_view(scene)
            self.update_controls(scene)
    
    def get_bounds(self) -> Tuple[float, float, float, float]:
        """
        Get the bounding box of this object.
        
        Returns:
            Tuple of (min_x, min_y, max_x, max_y) coordinates
        """
        raise NotImplementedError("Subclasses must implement get_bounds")
    
    def contains_point(self, point: QPointF, tolerance: float = 5.0) -> bool:
        """
        Check if a point is near this object.
        
        Args:
            point: The point to check
            tolerance: Distance tolerance for hit testing
            
        Returns:
            True if the point is within tolerance of this object
        """
        raise NotImplementedError("Subclasses must implement contains_point")
    
    # Standard properties that all CAD viewmodels should have
    
    @property
    def object_id(self) -> str:
        """Get the object ID from the model"""
        return self._cad_object.object_id
    
    @property
    def object_type(self) -> str:
        """Get the object type - subclasses should override this"""
        return "cad_object"
    
    @property
    def is_selected(self) -> bool:
        """Get the selection state"""
        return self._is_selected
    
    @is_selected.setter
    def is_selected(self, value: bool):
        """Set the selection state and emit signal"""
        if self._is_selected != value:
            self._is_selected = value
            self.object_selected.emit(value)
    
    @property
    def is_visible(self) -> bool:
        """Get the visibility state from the model"""
        return self._cad_object.visible
    
    @property
    def is_locked(self) -> bool:
        """Get the lock state from the model"""
        return self._cad_object.locked
    
    @property
    def color(self) -> str:
        """Get the color from the model"""
        return self._cad_object.color
    
    @color.setter
    def color(self, value: str):
        """Set the color in the model and emit signal"""
        if self._cad_object.color != value:
            self._cad_object.color = value
            self.object_modified.emit()
    
    # Standard transformation methods that all CAD viewmodels should have
    
    def translate(self, dx: float, dy: float):
        """
        Move the object by the given offset.
        
        Args:
            dx: X offset to move by
            dy: Y offset to move by
        """
        # Subclasses should override this to implement specific translation logic
        pass
    
    def scale(self, scale_factor: float, center: QPointF):
        """
        Scale the object around the given center.
        
        Args:
            scale_factor: Factor to scale by
            center: Center point for scaling
        """
        # Subclasses should override this to implement specific scaling logic
        pass
    
    def rotate(self, angle: float, center: QPointF):
        """
        Rotate the object around the given center.
        
        Args:
            angle: Angle to rotate by (in degrees)
            center: Center point for rotation
        """
        # Subclasses should override this to implement specific rotation logic
        pass
    
    # Helper methods for managing view items
    
    def _add_view_items_to_scene(self, scene: QGraphicsScene):
        """Add all view items to the scene and set viewmodel reference."""
        from PySide6.QtWidgets import QGraphicsItem
        
        for item in self._view_items:
            if item and item.scene() != scene:
                scene.addItem(item)
            if item:
                # Store reference to this viewmodel in data slot 0
                item.setData(0, self)
                
                # Ensure all graphics items have proper selection flags
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
    
    def _clear_view_items(self, scene: QGraphicsScene):
        """Remove all view items from the scene."""
        for item in self._view_items:
            if item and item.scene() == scene:
                scene.removeItem(item)
        self._view_items.clear()
    
    def _add_decorations_to_scene(self, scene: QGraphicsScene):
        """Add all decoration items to the scene and set viewmodel reference."""
        for item in self._decorations:
            if item and item.scene() != scene:
                scene.addItem(item)
            if item:
                # Store reference to this viewmodel in data slot 0
                item.setData(0, self)
    
    def _clear_decorations(self, scene: QGraphicsScene):
        """Remove all decoration items from the scene."""
        for item in self._decorations:
            if item and item.scene() == scene:
                scene.removeItem(item)
        self._decorations.clear()
    
    def _add_controls_to_scene(self, scene: QGraphicsScene):
        """Add all control items to the scene and set viewmodel reference."""
        for item in self._controls:
            if item and item.scene() != scene:
                scene.addItem(item)
            if item:
                # Store reference to this viewmodel in data slot 0
                item.setData(0, self)
    
    def _clear_controls(self, scene: QGraphicsScene):
        """Remove all control items from the scene."""
        for item in self._controls:
            if item and item.scene() == scene:
                scene.removeItem(item)
        self._controls.clear()
    
    # Helper methods for accessing common properties
    
    @property
    def document_window(self) -> 'DocumentWindow':
        """Get the document window reference."""
        return self._document_window
    
    @property
    def cad_object(self) -> 'CadObject':
        """Get the CAD object model"""
        return self._cad_object
    
    @property
    def view_items(self) -> List:
        """Get the list of view items"""
        return self._view_items
    
    @property
    def decorations(self) -> List:
        """Get the list of decoration items"""
        return self._decorations
    
    @property
    def controls(self) -> List:
        """Get the list of control items"""
        return self._controls
        