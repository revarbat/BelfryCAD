"""
Line ViewModel for BelfryCAD.

This ViewModel handles presentation logic for line CAD objects and emits signals
for UI updates when line properties change.
"""

import math

from typing import Tuple, Optional, TYPE_CHECKING, List

from PySide6.QtCore import Qt, QPointF, Signal
from PySide6.QtGui import QColor, QTransform, QPen
from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem

from .cad_viewmodel import CadViewModel
from ...graphics_items.control_points import (
    ControlPoint,
    ControlPointShape,
    ControlDatum
)
from ...graphics_items.dimension_line_composite import (
    DimensionLineComposite
)
from ...graphics_items.cad_line_graphics_item import CadLineGraphicsItem
from ....models.cad_objects.line_cad_object import LineCadObject
from ....cad_geometry import Point2D

if TYPE_CHECKING:
    from ....gui.document_window import DocumentWindow


class LineViewModel(CadViewModel):
    """Presentation logic for line CAD objects with signals"""
    
    # Line-specific signals
    start_point_changed = Signal(QPointF)  # new start point
    end_point_changed = Signal(QPointF)  # new end point
    
    def __init__(self, document_window: 'DocumentWindow', line_object: LineCadObject):
        super().__init__(document_window, line_object)
        self._line_object = line_object  # Keep reference for type-specific access
        
    def update_view(self, scene: QGraphicsScene):
        """
        Creates and/or updates the view items for this line.
        This is called when the line is added to the scene, and when the line is modified.
        """
        self._clear_view_items(scene)

        color = QColor(self._line_object.color)
        line_width = self._line_object.line_width
        if line_width is None:
            pen = QPen(color, 1.0)
            pen.setCosmetic(True)
        else:
            pen = QPen(color, line_width)
        
        view_item = CadLineGraphicsItem(
            self._line_object.line.start.to_qpointf(),
            self._line_object.line.end.to_qpointf(),
            pen=pen
        )
        self._view_items.append(view_item)

        self._add_view_items_to_scene(scene)
        self.update_decorations(scene)
        self.update_controls(scene)
    
    def show_decorations(self, scene: QGraphicsScene):
        """
        Show or hide the decorations.
        This is called when this object is selected.
        """
        self._clear_decorations(scene)
    
    def hide_decorations(self, scene: QGraphicsScene):
        """
        Hide the decorations.
        This is called when this object is deselected.
        """
        self._clear_decorations(scene)
    
    def update_decorations(self, scene: QGraphicsScene):
        """
        Update the decorations.
        This is called when this object is modified.
        """
        if self._decorations:
            self.hide_decorations(scene)
            self.show_decorations(scene)
    
    def show_controls(self, scene: QGraphicsScene):
        """
        Show the controls.
        This is called when this object becomes the only object selected.
        """
        self._clear_controls(scene)

        # Create control points with direct setters
        start_cp = ControlPoint(
            model_view=self,
            setter=self._set_start_point,
            tool_tip=f"Line Start",
            cp_shape=ControlPointShape.SQUARE
        )
        self._controls.append(start_cp)

        end_cp = ControlPoint(
            model_view=self,
            setter=self._set_end_point,
            tool_tip=f"Line End",
            cp_shape=ControlPointShape.ROUND
        )
        self._controls.append(end_cp)

        mid_cp = ControlPoint(
            model_view=self,
            setter=self._set_mid_point,
            tool_tip=f"Line Midpoint",
            cp_shape=ControlPointShape.DIAMOND
        )
        self._controls.append(mid_cp)

        self._add_controls_to_scene(scene)

    def hide_controls(self, scene: QGraphicsScene):
        """
        Hide the controls.
        This is called when this object is deselected, or when an additional object becomes selected.
        """
        self._clear_controls(scene)

    def update_controls(self, scene: QGraphicsScene):
        """
        Update the controls.
        This is called when this object is modified.
        """
        if not self._controls:
            return

        start = self.start_point
        end = self.end_point
        mid = self.mid_point
        
        # Update control points
        self._controls[0].setPos(start)  # Start point
        self._controls[1].setPos(end)    # End point
        self._controls[2].setPos(mid)    # Mid point
        
        self.control_points_updated.emit()

    def get_properties(self) -> List[str]:
        """Get properties of the line"""
        return [ "Length", "Angle" ]
    
    def get_property_value(self, name: str) -> float:
        """Get a line property"""
        if name == "Length":
            return self.length
        elif name == "Angle":
            return self.angle_degrees
        else:
            raise ValueError(f"Invalid property name: {name}")
        
    def set_property_value(self, name: str, value: float):
        """Set a line property"""
        if name == "Length":
            self.length = value
        elif name == "Angle":
            self.angle_degrees = value
        else:
            raise ValueError(f"Invalid property name: {name}")
        
    def _format_length_text(self, length: float) -> str:
        """Format the length text"""
        return self._document_window.grid_info.format_label(length, no_subs=True)
    
    @property
    def object_type(self) -> str:
        """Get object type"""
        return "line"
    
    @property
    def line_width(self) -> Optional[float]:
        """Get line width from model"""
        return self._line_object.line_width
    
    @line_width.setter
    def line_width(self, value: Optional[float]):
        """Set line width in model"""
        if self._line_object.line_width != value:
            self._line_object.line_width = value
            self.object_modified.emit()
    
    @property
    def start_point(self) -> QPointF:
        """Get start point from model"""
        return self._line_object.start_point.to_qpointf()
    
    @start_point.setter
    def start_point(self, value: QPointF):
        """Set start point in model and emit signal"""
        if self._line_object.start_point.x != value.x() or self._line_object.start_point.y != value.y():
            self._line_object.start_point = Point2D(value)
            self.start_point_changed.emit(value)
            self.object_modified.emit()
            # Note: update_controls will be called by the scene when needed
    
    @property
    def end_point(self) -> QPointF:
        """Get end point from model"""
        return self._line_object.end_point.to_qpointf()
    
    @end_point.setter
    def end_point(self, value: QPointF):
        """Set end point in model and emit signal"""
        if self._line_object.end_point.x != value.x() or self._line_object.end_point.y != value.y():
            self._line_object.end_point = Point2D(value.x(), value.y())
            self.end_point_changed.emit(value)
            self.object_modified.emit()
            # Note: update_controls will be called by the scene when needed
    
    @property
    def mid_point(self) -> QPointF:
        """Calculate mid point"""
        start = self.start_point
        end = self.end_point
        mid = (start + end) * 0.5
        return mid
    
    @mid_point.setter
    def mid_point(self, value: QPointF):
        """Set mid point"""
        start = self.start_point
        delta = value - start
        self.end_point = start + delta * 2
    
    @property
    def length(self) -> float:
        """Calculate length"""
        start = self.start_point
        end = self.end_point
        delta = end - start
        length = math.sqrt(delta.x()**2 + delta.y()**2)
        return length
    
    @length.setter
    def length(self, value: float):
        """Set length by adjusting end point"""
        if value <= 0:
            return
        start = self.start_point
        end = self.end_point
        current_length = self.length
        vec = (end - start) * (value / current_length)
        self.end_point = start + vec
    
    @property
    def angle_radians(self) -> float:
        """Calculate angle in radians"""
        start = self.start_point
        end = self.end_point
        return math.atan2(end.y() - start.y(), end.x() - start.x())
    
    @angle_radians.setter
    def angle_radians(self, value: float):
        """Set angle by rotating end point around start point"""
        start = self.start_point
        current_length = self.length
        delta = Point2D(current_length, angle=math.degrees(value)).to_qpointf()
        self.end_point = start + delta
    
    @property
    def angle_degrees(self) -> float:
        """Calculate angle in degrees"""
        return math.degrees(self.angle_radians)
    
    @angle_degrees.setter
    def angle_degrees(self, value: float):
        """Set angle in degrees"""
        self.angle_radians = math.radians(value)

    def translate(self, dx: float, dy: float):
        """Move the line by the given offset"""
        start = self.start_point
        end = self.end_point
        delta = QPointF(dx, dy)
        self.start_point = start + delta
        self.end_point = end + delta
        self.object_moved.emit(delta)
    
    def scale(self, scale_factor: float, center: QPointF):
        """Scale the line around the given center"""
        start = self.start_point
        end = self.end_point
        T = QTransform()
        T.translate(-center.x(), -center.y())
        T.scale(scale_factor, scale_factor)
        T.translate(center.x(), center.y())
        self.start_point = T.map(start)
        self.end_point = T.map(end)
        
    def rotate(self, angle: float, center: QPointF):
        """Rotate the line around the given center"""
        start = self.start_point
        end = self.end_point
        T = QTransform()
        T.translate(-center.x(), -center.y())
        T.rotate(angle)
        T.translate(center.x(), center.y())
        self.start_point = T.map(start)
        self.end_point = T.map(end)
        self.object_moved.emit(QPointF(0, 0))
        
    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get bounding box of the line"""
        start = self.start_point
        end = self.end_point
        return (
            min(start.x(), end.x()),
            min(start.y(), end.y()),
            max(start.x(), end.x()),
            max(start.y(), end.y())
        )
    
    def contains_point(self, point: QPointF, tolerance: float = 5.0) -> bool:
        """Check if point is near the line"""
        return self._line_object.contains_point(Point2D(point), tolerance)
    
    def _get_perpendicular_vector(self) -> QPointF:
        """Get the perpendicular vector to the line segment"""
        pvec = self._line_object.line.unit_vector.perpendicular_vector
        return pvec.to_qpointf()
    
    def _set_start_point(self, new_position):
        """Set the start point from control point movement"""
        self.start_point = new_position
        self.update_all()
    
    def _set_end_point(self, new_position):
        """Set the end point from control point movement"""
        self.end_point = new_position
        self.update_all()
    
    def _set_mid_point(self, new_position):
        """Set the mid point from control point movement"""
        self.mid_point = new_position
        self.update_all()
    
    def _set_length(self, value):
        """Set length from control datum"""
        self.length = value
        self.update_all()
    
    def _set_angle(self, value):
        """Set angle from control datum (value in degrees)"""
        self.angle_degrees = value
        self.update_all()
    