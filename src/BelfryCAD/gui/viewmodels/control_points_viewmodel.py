"""
Control Points ViewModel for BelfryCAD.

This ViewModel manages control points for selected objects and emits signals
for UI updates when control points change.
"""

from typing import List, Dict, Tuple, Optional
from PySide6.QtCore import QObject, Signal, QPointF
from PySide6.QtWidgets import QGraphicsSceneMouseEvent

from ...models.cad_object import CADObject, Point


class ControlPointsViewModel(QObject):
    """Manages control points for all selected objects with signals"""
    
    # Control point signals
    control_points_created = Signal(str, list)  # object_id, control_points
    control_points_removed = Signal(str)  # object_id
    control_point_moved = Signal(str, int, QPointF)  # object_id, cp_index, new_pos
    control_point_selected = Signal(str, int)  # object_id, cp_index
    control_point_deselected = Signal(str, int)  # object_id, cp_index
    
    def __init__(self):
        super().__init__()
        self._selected_objects: Dict[str, CADObject] = {}
        self._control_points: Dict[str, List[Tuple[float, float, str]]] = {}
        self._selected_control_point: Optional[Tuple[str, int]] = None  # (object_id, cp_index)
    
    def add_selected_object(self, object_id: str, cad_object: CADObject):
        """Add object to selection and create control points"""
        self._selected_objects[object_id] = cad_object
        self._create_control_points_for_object(object_id, cad_object)
    
    def remove_selected_object(self, object_id: str):
        """Remove object from selection"""
        if object_id in self._selected_objects:
            del self._selected_objects[object_id]
            self._remove_control_points_for_object(object_id)
    
    def clear_selection(self):
        """Clear all selected objects"""
        for object_id in list(self._selected_objects.keys()):
            self.remove_selected_object(object_id)
    
    def get_control_points_for_object(self, object_id: str) -> List[Tuple[float, float, str]]:
        """Get control points for a specific object"""
        return self._control_points.get(object_id, [])
    
    def get_all_control_points(self) -> Dict[str, List[Tuple[float, float, str]]]:
        """Get all control points for all selected objects"""
        return self._control_points.copy()
    
    def move_control_point(self, object_id: str, cp_index: int, new_pos: QPointF):
        """Move a control point and update the underlying model"""
        if object_id in self._selected_objects:
            cad_object = self._selected_objects[object_id]
            
            # Update the model
            cad_object.move_control_point(cp_index, new_pos.x(), new_pos.y())
            
            # Update our control points cache
            self._update_control_points_for_object(object_id, cad_object)
            
            # Emit signal
            self.control_point_moved.emit(object_id, cp_index, new_pos)
    
    def select_control_point(self, object_id: str, cp_index: int):
        """Select a specific control point"""
        if object_id in self._selected_objects:
            control_points = self.get_control_points_for_object(object_id)
            if 0 <= cp_index < len(control_points):
                self._selected_control_point = (object_id, cp_index)
                self.control_point_selected.emit(object_id, cp_index)
    
    def deselect_control_point(self):
        """Deselect the currently selected control point"""
        if self._selected_control_point:
            object_id, cp_index = self._selected_control_point
            self.control_point_deselected.emit(object_id, cp_index)
            self._selected_control_point = None
    
    def get_selected_control_point(self) -> Optional[Tuple[str, int]]:
        """Get the currently selected control point"""
        return self._selected_control_point
    
    def handle_control_point_drag(self, object_id: str, cp_index: int, new_pos: QPointF):
        """Handle dragging of a control point"""
        self.move_control_point(object_id, cp_index, new_pos)
    
    def update_object_control_points(self, object_id: str):
        """Update control points for an object (e.g., after object modification)"""
        if object_id in self._selected_objects:
            cad_object = self._selected_objects[object_id]
            self._update_control_points_for_object(object_id, cad_object)
    
    def _create_control_points_for_object(self, object_id: str, cad_object: CADObject):
        """Create control points for an object"""
        control_points = cad_object.get_control_points()
        self._control_points[object_id] = control_points
        self.control_points_created.emit(object_id, control_points)
    
    def _update_control_points_for_object(self, object_id: str, cad_object: CADObject):
        """Update control points for an object"""
        old_control_points = self._control_points.get(object_id, [])
        new_control_points = cad_object.get_control_points()
        
        if old_control_points != new_control_points:
            self._control_points[object_id] = new_control_points
            self.control_points_created.emit(object_id, new_control_points)
    
    def _remove_control_points_for_object(self, object_id: str):
        """Remove control points for an object"""
        if object_id in self._control_points:
            del self._control_points[object_id]
            self.control_points_removed.emit(object_id)
    
    def get_control_point_at_position(self, scene_pos: QPointF, tolerance: float = 5.0) -> Optional[Tuple[str, int]]:
        """Find control point at a specific scene position"""
        for object_id, control_points in self._control_points.items():
            for cp_index, (x, y, cp_type) in enumerate(control_points):
                cp_pos = QPointF(x, y)
                if (cp_pos - scene_pos).manhattanLength() <= tolerance:
                    return (object_id, cp_index)
        return None
    
    def get_control_point_position(self, object_id: str, cp_index: int) -> Optional[QPointF]:
        """Get the position of a specific control point"""
        control_points = self.get_control_points_for_object(object_id)
        if 0 <= cp_index < len(control_points):
            x, y, cp_type = control_points[cp_index]
            return QPointF(x, y)
        return None
    
    def get_control_point_type(self, object_id: str, cp_index: int) -> Optional[str]:
        """Get the type of a specific control point"""
        control_points = self.get_control_points_for_object(object_id)
        if 0 <= cp_index < len(control_points):
            x, y, cp_type = control_points[cp_index]
            return cp_type
        return None 