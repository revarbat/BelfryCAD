"""
Arc ViewModel for BelfryCAD.

This ViewModel handles presentation logic for arc CAD objects and emits signals
for UI updates when arc properties change.
"""

import math
from typing import Tuple, Optional, TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, Signal, QRectF
from PySide6.QtGui import QColor, QTransform, QPen
from PySide6.QtWidgets import QGraphicsScene

from .cad_viewmodel import CadViewModel
from ...graphics_items.control_points import (
    ControlPoint,
    SquareControlPoint,
    ControlDatum
)
from ...graphics_items.cad_arc_graphics_item import (
    CadArcGraphicsItem,
    CadArcArrowheadEndcaps
)
from ....models.cad_objects.arc_cad_object import ArcCadObject
from ....cad_geometry import Point2D

if TYPE_CHECKING:
    from ....gui.main_window import MainWindow


class ArcViewModel(CadViewModel):
    """Presentation logic for arc CAD objects with signals"""
    
    # Arc-specific signals
    center_changed = Signal(QPointF)  # new center position
    start_point_changed = Signal(QPointF)  # new start point
    end_point_changed = Signal(QPointF)  # new end point
    radius_changed = Signal(float)  # new radius
    start_angle_changed = Signal(float)  # new start angle
    end_angle_changed = Signal(float)  # new end angle
    span_angle_changed = Signal(float)  # new span angle
    
    def __init__(self, main_window: 'MainWindow', arc_object: ArcCadObject):
        super().__init__(main_window, arc_object)
        self._arc_object = arc_object  # Keep reference for type-specific access
        
    def update_view(self, scene: QGraphicsScene):
        """
        Creates and/or updates the view items for this arc.
        This is called when the arc is added to the scene, and when the arc is modified.
        """
        self._clear_view_items(scene)

        color = QColor(self._arc_object.color)
        line_width = self._arc_object.line_width
        center = self.center_point
        radius = self.radius
        start_angle = math.degrees(self.start_angle)  # Convert to degrees for CadArcGraphicsItem
        span_angle = math.degrees(self.span_angle)    # Convert to degrees for CadArcGraphicsItem
        
        # Create main arc using CadArcGraphicsItem
        if line_width is None:
            arc_pen = QPen(color, 1.0)
            arc_pen.setCosmetic(True)
        else:
            arc_pen = QPen(color, line_width)
        arc_item = CadArcGraphicsItem(
            center_point=center,
            radius=radius,
            start_angle=start_angle,
            span_angle=span_angle,
            arrowheads=CadArcArrowheadEndcaps.NONE,  # No arrowheads for regular arcs
            pen=arc_pen
        )
        self._view_items.append(arc_item)

        self._add_view_items_to_scene(scene)
        self.update_decorations(scene)
        self.update_controls(scene)
    
    def show_decorations(self, scene: QGraphicsScene):
        """
        Show the decorations.
        This is called when this object is selected.
        """
        self._clear_decorations(scene)
        
        # Create decoration arc that completes the circle (from end to start)
        line_width = self._arc_object.line_width
        center = self.center_point
        radius = self.radius
        start_angle = math.degrees(self.start_angle)
        span_angle = math.degrees(self.span_angle)
        
        const_color = QColor(0x7f, 0x7f, 0x7f)
        decoration_pen = QPen(const_color, 1.0)
        decoration_pen.setCosmetic(True)
        decoration_pen.setStyle(Qt.PenStyle.DashLine)
        decoration_pen.setDashPattern([5.0, 5.0])
        
        # Calculate the completion arc (from end to start)
        end_angle = start_angle + span_angle
        completion_span = 360 - span_angle  # Complete the circle
        
        decoration_arc = CadArcGraphicsItem(
            center_point=center,
            radius=radius,
            start_angle=end_angle,
            span_angle=completion_span,
            arrowheads=CadArcArrowheadEndcaps.NONE,
            pen=decoration_pen
        )
        self._decorations.append(decoration_arc)
        
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

        # Create control points with direct setters
        center_cp = SquareControlPoint(
            model_view=self,
            setter=self._set_center_point,
            tool_tip="Arc Center"
        )
        self._controls.append(center_cp)

        start_cp = SquareControlPoint(
            model_view=self,
            setter=self._set_start_point,
            tool_tip="Arc Start"
        )
        self._controls.append(start_cp)

        end_cp = SquareControlPoint(
            model_view=self,
            setter=self._set_end_point,
            tool_tip="Arc End"
        )
        self._controls.append(end_cp)

        # Get precision from main window or use default
        precision = self._main_window.preferences_viewmodel.get_precision()
        
        # Radius datum
        radius_datum = ControlDatum(
            model_view=self,
            label="Arc Radius",
            setter=self._set_radius,
            format_string=f"{{:.{precision}f}}",
            precision_override=precision,
            min_value=0,
            is_length=True
        )
        self._controls.append(radius_datum)
        
        # Span angle datum
        span_datum = ControlDatum(
            model_view=self,
            label="Arc Span Angle",
            setter=self._set_span_angle,
            format_string="{:.1f}",
            suffix="°",
            precision_override=1,
            min_value=-360,
            max_value=360,
            is_length=False
        )
        self._controls.append(span_datum)

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

        center = self.center_point
        start = self.start_point
        end = self.end_point
        
        # Update control points
        self._controls[0].setPos(center)  # Center point
        self._controls[1].setPos(start)   # Start point
        self._controls[2].setPos(end)     # End point
        
        # Update Radius datum
        self._controls[3].update_datum(
            self.radius,
            center + QPointF(20, -20)
        )
        
        # Update Span Angle datum
        self._controls[4].update_datum(
            math.degrees(self.span_angle),
            center + QPointF(20, 20)
        )
    
        self.control_points_updated.emit()
    
    @property
    def object_type(self) -> str:
        """Get object type"""
        return "arc"
    
    @property
    def line_width(self) -> Optional[float]:
        """Get line width from model"""
        return self._arc_object.line_width
    
    @line_width.setter
    def line_width(self, value: Optional[float]):
        """Set line width in model"""
        if self._arc_object.line_width != value:
            self._arc_object.line_width = value
            self.object_modified.emit()
    
    @property
    def center_point(self) -> QPointF:
        """Get center point as QPointF"""
        center = self._arc_object.center_point
        return QPointF(center.x, center.y)
    
    @center_point.setter
    def center_point(self, value: QPointF):
        """Set center point and emit signal"""
        if self.center_point != value:
            self._arc_object.center_point = Point2D(value.x(), value.y())
            self.center_changed.emit(value)
            self.object_modified.emit()
    
    @property
    def start_point(self) -> QPointF:
        """Get start point as QPointF"""
        start = self._arc_object.start_point
        return QPointF(start.x, start.y)
    
    @start_point.setter
    def start_point(self, value: QPointF):
        """Set start point and emit signal"""
        if self.start_point != value:
            self._arc_object.start_point = Point2D(value.x(), value.y())
            self.start_point_changed.emit(value)
            self.object_modified.emit()
    
    @property
    def end_point(self) -> QPointF:
        """Get end point as QPointF"""
        end = self._arc_object.end_point
        return QPointF(end.x, end.y)
    
    @end_point.setter
    def end_point(self, value: QPointF):
        """Set end point and emit signal"""
        if self.end_point != value:
            self._arc_object.end_point = Point2D(value.x(), value.y())
            self.end_point_changed.emit(value)
            self.object_modified.emit()
    
    @property
    def radius(self) -> float:
        """Get arc radius"""
        return self._arc_object.radius
    
    @radius.setter
    def radius(self, value: float):
        """Set radius and emit signal"""
        if self._arc_object.radius != value:
            self._arc_object.radius = value
            self.radius_changed.emit(value)
            self.object_modified.emit()
    
    @property
    def start_angle(self) -> float:
        """Get start angle in radians"""
        return self._arc_object.start_angle
    
    @start_angle.setter
    def start_angle(self, value: float):
        """Set start angle and emit signal"""
        if self._arc_object.start_angle != value:
            self._arc_object.start_angle = value
            self.start_angle_changed.emit(value)
            self.object_modified.emit()
    
    @property
    def end_angle(self) -> float:
        """Get end angle in radians"""
        return self._arc_object.end_angle
    
    @end_angle.setter
    def end_angle(self, value: float):
        """Set end angle and emit signal"""
        if self._arc_object.end_angle != value:
            self._arc_object.end_angle = value
            self.end_angle_changed.emit(value)
            self.object_modified.emit()
    
    @property
    def span_angle(self) -> float:
        """Get span angle in radians"""
        return self._arc_object.span_angle
    
    @span_angle.setter
    def span_angle(self, value: float):
        """Set span angle and emit signal"""
        if self._arc_object.span_angle != value:
            self._arc_object.span_angle = value
            self.span_angle_changed.emit(value)
            self.object_modified.emit()

    def translate(self, dx: float, dy: float):
        """Move arc by the given offset"""
        center = self.center_point
        delta = QPointF(dx, dy)
        self.center_point = center + delta
        self.object_moved.emit(delta)
    
    def scale(self, scale_factor: float, center: QPointF):
        """Scale the arc around the given center"""
        current_center = self.center_point
        current_radius = self.radius
        
        # Scale the center point
        T = QTransform()
        T.translate(-center.x(), -center.y())
        T.scale(scale_factor, scale_factor)
        T.translate(center.x(), center.y())
        new_center = T.map(current_center)
        
        # Scale the radius
        new_radius = current_radius * scale_factor
        
        self.center_point = new_center
        self.radius = new_radius
        
    def rotate(self, angle: float, center: QPointF):
        """Rotate the arc around the given center"""
        current_center = self.center_point
        current_start_angle = self.start_angle
        
        # Rotate the center point
        T = QTransform()
        T.translate(-center.x(), -center.y())
        T.rotate(angle)
        T.translate(center.x(), center.y())
        new_center = T.map(current_center)
        
        # Rotate the start angle
        new_start_angle = current_start_angle + math.radians(angle)
        
        self.center_point = new_center
        self.start_angle = new_start_angle
        self.object_moved.emit(QPointF(0, 0))
        
    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get bounding box of the arc"""
        return self._arc_object.get_bounds()
    
    def contains_point(self, point: QPointF, tolerance: float = 5.0) -> bool:
        """Check if point is near the arc"""
        return self._arc_object.contains_point(Point2D(point), tolerance)
    
    def _set_center_point(self, new_position):
        """Set the center point from control point movement"""
        self.center_point = new_position
    
    def _set_start_point(self, new_position):
        """Set the start point from control point movement"""
        self.start_point = new_position
    
    def _set_end_point(self, new_position):
        """Set the end point from control point movement"""
        self.end_point = new_position
    
    def _set_radius(self, value):
        """Set radius from control datum"""
        self.radius = value
    
    def _set_span_angle(self, value):
        """Set span angle from control datum (value in degrees)"""
        span_radians = math.radians(value)
        self.span_angle = span_radians 