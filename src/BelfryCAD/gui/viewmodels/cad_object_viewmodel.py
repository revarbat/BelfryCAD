"""
CAD Object ViewModel for BelfryCAD.

This ViewModel handles presentation logic for individual CAD objects and emits signals
for UI updates when object properties change.
"""

from typing import List, Tuple, Optional
from PySide6.QtCore import QObject, Signal, QPointF
from PySide6.QtWidgets import QGraphicsSceneMouseEvent

from ...models.cad_object import CadObject
from ...cad_geometry import Point2D


class CADObjectViewModel(QObject):
    """Presentation logic for individual CAD objects with signals"""
    
    # Object signals
    object_moved = Signal(str, QPointF)  # object_id, new_position
    object_selected = Signal(str, bool)  # object_id, is_selected
    object_modified = Signal(str)  # object_id
    control_points_changed = Signal(str, list)  # object_id, control_points
    
    def __init__(self, cad_object: CadObject):
        super().__init__()
        self._cad_object = cad_object
        self._is_selected = False
        self._control_points = []
        self._update_control_points()
    
    @property
    def object_id(self) -> str:
        """Get object ID"""
        return self._cad_object.object_id
    
    @property
    def is_selected(self) -> bool:
        """Get selection state"""
        return self._is_selected
    
    @is_selected.setter
    def is_selected(self, value: bool):
        """Set selection state and emit signal"""
        if self._is_selected != value:
            self._is_selected = value
            self.object_selected.emit(self.object_id, value)
    
    @property
    def is_visible(self) -> bool:
        """Get visibility state"""
        return self._cad_object.visible
    
    @property
    def is_locked(self) -> bool:
        """Get lock state"""
        return self._cad_object.locked
    
    def translate(self, dx: float, dy: float):
        """Move object by delta and emit signal"""
        if dx != 0 or dy != 0:
            self._cad_object.translate(dx, dy)
            new_pos = self._get_position()
            self.object_moved.emit(self.object_id, new_pos)
            self._update_control_points()
            self.object_modified.emit(self.object_id)
    
    def get_position(self) -> QPointF:
        """Get object position"""
        return self._get_position()
    
    def set_position(self, pos: QPointF):
        """Set object position"""
        current_pos = self._get_position()
        dx = pos.x() - current_pos.x()
        dy = pos.y() - current_pos.y()
        self.translate(dx, dy)
    
    def get_control_points(self) -> List[Tuple[float, float, str]]:
        """Get control points for this object"""
        return self._control_points.copy()
    
    def move_control_point(self, cp_index: int, x: float, y: float):
        """Move a control point"""
        self._cad_object.move_control_point(cp_index, x, y)
        self._update_control_points()
        self.object_modified.emit(self.object_id)
    
    def get_bounds(self):
        """Get object bounds"""
        return self._cad_object.get_bounds()
    
    def contains_point(self, point: QPointF, tolerance: float = 5.0) -> bool:
        """Check if object contains point"""
        model_point = Point2D(point.x(), point.y())
        return self._cad_object.contains_point(model_point, tolerance)
    
    def get_points(self) -> List[QPointF]:
        """Get object points as QPointF"""
        return [QPointF(p.x, p.y) for p in self._cad_object.points]
    
    def set_points(self, points: List[QPointF]):
        """Set object points"""
        model_points = [Point2D(p.x(), p.y()) for p in points]
        if model_points != self._cad_object.points:
            self._cad_object.points = model_points
            self._update_control_points()
            self.object_modified.emit(self.object_id)
    
    def get_property(self, key: str):
        """Get object property"""
        return self._cad_object.properties.get(key)
    
    def set_property(self, key: str, value):
        """Set object property"""
        if (
            key not in self._cad_object.properties or
            self._cad_object.properties[key] != value
        ):
            self._cad_object.properties[key] = value
            self.object_modified.emit(self.object_id)
    
    def _get_position(self) -> QPointF:
        """Get object position based on its points"""
        if self._cad_object.points:
            # Use first point as position for most objects
            first_point = self._cad_object.points[0]
            return QPointF(first_point.x, first_point.y)
        return QPointF(0, 0)
    
    def _update_control_points(self):
        """Update control points and emit signal if changed"""
        old_control_points = self._control_points
        self._control_points = self._cad_object.get_control_points()
        
        if old_control_points != self._control_points:
            self.control_points_changed.emit(self.object_id, self._control_points)
