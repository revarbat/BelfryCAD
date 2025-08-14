"""
CubicBezier ViewModel for BelfryCAD.

This ViewModel handles presentation logic for cubic Bezier CAD objects and emits signals
for UI updates when Bezier properties change.
"""

import math
from typing import List, Tuple, Optional, TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, Signal
from PySide6.QtGui import QColor, QPen, QPainterPath
from PySide6.QtWidgets import QGraphicsScene

from .cad_viewmodel import CadViewModel
from ...graphics_items.control_points import (
    ControlPoint,
    SquareControlPoint,
    ControlDatum
)
from ...graphics_items.cad_bezier_graphics_item import CadBezierGraphicsItem
from ....models.cad_objects.cubic_bezier_cad_object import CubicBezierCadObject
from ....cad_geometry import Point2D

if TYPE_CHECKING:
    from ....gui.document_window import DocumentWindow


class CubicBezierViewModel(CadViewModel):
    """Presentation logic for cubic Bezier CAD objects with signals"""
    
    # Bezier-specific signals
    points_changed = Signal(list)  # new points list
    start_point_changed = Signal(QPointF)  # new start point
    end_point_changed = Signal(QPointF)  # new end point
    is_closed_changed = Signal(bool)  # new closed state
    
    def __init__(self, document_window: 'DocumentWindow', bezier_object: CubicBezierCadObject):
        super().__init__(document_window, bezier_object)
        self._bezier_object = bezier_object  # Keep reference for type-specific access
        
    def update_view(self, scene: QGraphicsScene):
        """
        Creates and/or updates the view items for this Bezier curve.
        This is called when the Bezier curve is added to the scene, and when the Bezier curve is modified.
        """
        self._clear_view_items(scene)

        color = QColor(self._bezier_object.color)
        line_width = self._bezier_object.line_width
        points = self.points
        
        if len(points) >= 4:  # Need at least 4 points for a cubic Bezier
            # Create Bezier curve path
            path = QPainterPath()
            
            # Start at the first point
            path.moveTo(points[0])
            
            # Create cubic Bezier segments
            for i in range(0, len(points) - 3, 3):
                if i + 3 < len(points):
                    path.cubicTo(
                        points[i + 1],  # Control point 1
                        points[i + 2],  # Control point 2
                        points[i + 3]   # End point
                    )
            
            # If closed, connect back to start
            if self.is_closed and len(points) >= 6:
                # Use the last 3 points and first point to close the curve
                last_control1 = points[-2]
                last_control2 = points[-1]
                path.cubicTo(last_control1, last_control2, points[0])
            
            pen = QPen(color, line_width)
            view_item = CadBezierGraphicsItem(path, pen=pen)
            self._view_items.append(view_item)

        self._add_view_items_to_scene(scene)
        self.update_decorations(scene)
        self.update_controls(scene)
    
    def show_decorations(self, scene: QGraphicsScene):
        """
        Show the decorations.
        This is called when this object is selected.
        """
        self._clear_decorations(scene)
        # Bezier curve doesn't need special decorations for now
        self._add_decorations_to_scene(scene)
    
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

        points = self.points
        
        # Create control points for each point
        for i, point in enumerate(points):
            cp = SquareControlPoint(
                model_view=self,
                setter=lambda new_pos, idx=i: self._set_point(idx, new_pos),
                tool_tip=f"Bezier Control Point {i}"
            )
            self._controls.append(cp)

        # Get precision from main window or use default
        precision = self._document_window.preferences_viewmodel.get_precision()
        
        # Point count datum (read-only)
        point_count_datum = ControlDatum(
            model_view=self,
            label="Number of Control Points",
            setter=lambda value: None,  # Read-only
            format_string="{:.0f}",
            precision_override=0,
            min_value=0,
            is_length=False
        )
        self._controls.append(point_count_datum)
        
        # Closed state datum (read-only)
        closed_datum = ControlDatum(
            model_view=self,
            label="Path Closed",
            setter=lambda value: None,  # Read-only
            format_string="{:.0f}",
            precision_override=0,
            min_value=0,
            max_value=1,
            is_length=False
        )
        self._controls.append(closed_datum)

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

        points = self.points
        
        # Update control points
        for i, (cp, point) in enumerate(zip(self._controls[:-2], points)):
            cp.setPos(point)
        
        # Update datums
        if len(self._controls) >= 2 and points:
            center = points[len(points) // 2] if points else QPointF(0, 0)
            
            # Point count datum
            self._controls[-2].update_datum(
                len(points),
                center + QPointF(20, -20)
            )
            
            # Closed state datum
            self._controls[-1].update_datum(
                1 if self.is_closed else 0,
                center + QPointF(20, 20)
            )
    
        self.control_points_updated.emit()
    
    @property
    def object_type(self) -> str:
        """Get object type"""
        return "cubic_bezier"
    
    @property
    def line_width(self) -> Optional[float]:
        """Get line width from model"""
        return self._bezier_object.line_width
    
    @line_width.setter
    def line_width(self, value: Optional[float]):
        """Set line width in model"""
        if self._bezier_object.line_width != value:
            self._bezier_object.line_width = value
            self.object_modified.emit()
    
    @property
    def points(self) -> List[QPointF]:
        """Get all control points as QPointF list"""
        points = self._bezier_object.points
        return [QPointF(p.x, p.y) for p in points]
    
    @points.setter
    def points(self, value: List[QPointF]):
        """Set all control points and emit signal"""
        if self.points != value:
            point_list = [Point2D(p.x(), p.y()) for p in value]
            self._bezier_object.points = point_list
            self.points_changed.emit(value)
            self.object_modified.emit()
    
    @property
    def start_point(self) -> Optional[QPointF]:
        """Get start point as QPointF"""
        start = self._bezier_object.start_point
        if start:
            return QPointF(start.x, start.y)
        return None
    
    @property
    def end_point(self) -> Optional[QPointF]:
        """Get end point as QPointF"""
        end = self._bezier_object.end_point
        if end:
            return QPointF(end.x, end.y)
        return None
    
    @property
    def is_closed(self) -> bool:
        """Get closed state"""
        return self._bezier_object.is_closed
    
    def add_point(self, point: QPointF):
        """Add a new control point"""
        self._bezier_object.add_point(Point2D(point.x(), point.y()))
        self.object_modified.emit()
    
    def insert_point(self, index: int, point: QPointF):
        """Insert a control point at index"""
        self._bezier_object.insert_point(index, Point2D(point.x(), point.y()))
        self.object_modified.emit()
    
    def remove_point(self, index: int):
        """Remove a control point at index"""
        self._bezier_object.remove_point(index)
        self.object_modified.emit()
    
    def get_point(self, index: int) -> Optional[QPointF]:
        """Get control point at index"""
        point = self._bezier_object.get_point(index)
        if point:
            return QPointF(point.x, point.y)
        return None
    
    def set_point(self, index: int, point: QPointF):
        """Set control point at index"""
        self._bezier_object.set_point(index, Point2D(point.x(), point.y()))
        self.object_modified.emit()

    def translate(self, dx: float, dy: float):
        """Move Bezier curve by the given offset"""
        if dx != 0 or dy != 0:
            self._bezier_object.translate(dx, dy)
            new_points = self.points
            self.object_moved.emit(new_points[0] if new_points else QPointF(0, 0))
    
    def scale(self, scale_factor: float, center: QPointF):
        """Scale the Bezier curve around the given center"""
        center_point = Point2D(center.x(), center.y())
        self._bezier_object.scale(scale_factor, center_point)
        
    def rotate(self, angle: float, center: QPointF):
        """Rotate the Bezier curve around the given center"""
        center_point = Point2D(center.x(), center.y())
        self._bezier_object.rotate(angle, center_point)
        self.object_moved.emit(QPointF(0, 0))
        
    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get bounding box of the Bezier curve"""
        return self._bezier_object.get_bounds()
    
    def contains_point(self, point: QPointF, tolerance: float = 5.0) -> bool:
        """Check if point is near the Bezier curve"""
        return self._bezier_object.contains_point(Point2D(point), tolerance)
    
    def _set_point(self, index: int, new_position: QPointF):
        """Set a control point from control point movement"""
        self.set_point(index, new_position) 