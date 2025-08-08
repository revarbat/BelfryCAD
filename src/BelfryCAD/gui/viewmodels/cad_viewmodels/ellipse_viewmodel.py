"""
Ellipse ViewModel for BelfryCAD.

This ViewModel handles presentation logic for ellipse CAD objects and emits signals
for UI updates when ellipse properties change.
"""

import math
from typing import Tuple, Optional, TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, Signal, QRectF
from PySide6.QtGui import QColor, QTransform, QPen
from PySide6.QtWidgets import QGraphicsScene, QGraphicsEllipseItem

from .cad_viewmodel import CadViewModel
from ...graphics_items.control_points import (
    ControlPoint,
    SquareControlPoint,
    ControlDatum
)
from ....models.cad_objects.ellipse_cad_object import EllipseCadObject
from ....cad_geometry import Point2D

if TYPE_CHECKING:
    from ....gui.main_window import MainWindow


class EllipseViewModel(CadViewModel):
    """Presentation logic for ellipse CAD objects with signals"""
    
    # Ellipse-specific signals
    center_changed = Signal(QPointF)  # new center position
    major_axis_point_changed = Signal(QPointF)  # new major axis point
    minor_axis_point_changed = Signal(QPointF)  # new minor axis point
    major_axis_changed = Signal(float)  # new major axis length
    minor_axis_changed = Signal(float)  # new minor axis length
    rotation_changed = Signal(float)  # new rotation angle
    focus1_changed = Signal(QPointF)  # new focus 1
    focus2_changed = Signal(QPointF)  # new focus 2
    
    def __init__(self, main_window: 'MainWindow', ellipse_object: EllipseCadObject):
        super().__init__(main_window, ellipse_object)
        self._ellipse_object = ellipse_object  # Keep reference for type-specific access
        
    def update_view(self, scene: QGraphicsScene):
        """
        Creates and/or updates the view items for this ellipse.
        This is called when the ellipse is added to the scene, and when the ellipse is modified.
        """
        self._clear_view_items(scene)

        color = QColor(self._ellipse_object.color)
        line_width = self._ellipse_object.line_width
        center = self.center_point
        major_axis = self.major_axis
        minor_axis = self.minor_axis
        rotation = self.rotation
        
        # Create ellipse graphics item
        # Note: QGraphicsEllipseItem uses a bounding rectangle, so we need to calculate it
        # based on the ellipse's center, axes, and rotation
        rect = QRectF(
            center.x() - major_axis,
            center.y() - minor_axis,
            major_axis * 2,
            minor_axis * 2
        )
        
        view_item = QGraphicsEllipseItem(rect)
        view_item.setPen(QPen(color, line_width))
        
        # Apply rotation if needed
        if rotation != 0:
            transform = QTransform()
            transform.translate(center.x(), center.y())
            transform.rotate(math.degrees(rotation))
            transform.translate(-center.x(), -center.y())
            view_item.setTransform(transform)
        
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
        # Ellipse doesn't need special decorations for now
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
            tool_tip="Ellipse Center"
        )
        self._controls.append(center_cp)

        major_cp = SquareControlPoint(
            model_view=self,
            setter=self._set_major_axis_point,
            tool_tip="Ellipse Major Axis"
        )
        self._controls.append(major_cp)

        minor_cp = SquareControlPoint(
            model_view=self,
            setter=self._set_minor_axis_point,
            tool_tip="Ellipse Minor Axis"
        )
        self._controls.append(minor_cp)

        # Get precision from main window or use default
        precision = self._main_window.preferences_viewmodel.get_precision()
        
        # Major axis datum
        major_datum = ControlDatum(
            model_view=self,
            label="Ellipse Major Axis",
            setter=self._set_major_axis,
            format_string=f"{{:.{precision}f}}",
            precision_override=precision,
            min_value=0,
            is_length=True
        )
        self._controls.append(major_datum)
        
        # Minor axis datum
        minor_datum = ControlDatum(
            model_view=self,
            label="Ellipse Minor Axis",
            setter=self._set_minor_axis,
            format_string=f"{{:.{precision}f}}",
            precision_override=precision,
            min_value=0,
            is_length=True
        )
        self._controls.append(minor_datum)
        
        # Rotation datum
        rotation_datum = ControlDatum(
            model_view=self,
            label="Ellipse Rotation",
            setter=self._set_rotation,
            format_string="{:.1f}",
            suffix="°",
            precision_override=1,
            min_value=-360,
            max_value=360,
            is_length=False
        )
        self._controls.append(rotation_datum)

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
        major = self.major_axis_point
        minor = self.minor_axis_point
        
        # Update control points
        self._controls[0].setPos(center)  # Center point
        self._controls[1].setPos(major)   # Major axis point
        self._controls[2].setPos(minor)   # Minor axis point
        
        # Update Major axis datum
        self._controls[3].update_datum(
            self.major_axis,
            center + QPointF(20, -20)
        )
        
        # Update Minor axis datum
        self._controls[4].update_datum(
            self.minor_axis,
            center + QPointF(20, 0)
        )
        
        # Update Rotation datum
        self._controls[5].update_datum(
            math.degrees(self.rotation),
            center + QPointF(20, 20)
        )
    
        self.control_points_updated.emit()
    
    @property
    def object_type(self) -> str:
        """Get object type"""
        return "ellipse"
    
    @property
    def line_width(self) -> Optional[float]:
        """Get line width from model"""
        return self._ellipse_object.line_width
    
    @line_width.setter
    def line_width(self, value: Optional[float]):
        """Set line width in model"""
        if self._ellipse_object.line_width != value:
            self._ellipse_object.line_width = value
            self.object_modified.emit()
    
    @property
    def center_point(self) -> QPointF:
        """Get center point as QPointF"""
        center = self._ellipse_object.center_point
        return QPointF(center.x, center.y)
    
    @center_point.setter
    def center_point(self, value: QPointF):
        """Set center point and emit signal"""
        if self.center_point != value:
            self._ellipse_object.center_point = Point2D(value.x(), value.y())
            self.center_changed.emit(value)
            self.object_modified.emit()
    
    @property
    def major_axis_point(self) -> QPointF:
        """Get major axis point as QPointF"""
        major = self._ellipse_object.major_axis_point
        return QPointF(major.x, major.y)
    
    @major_axis_point.setter
    def major_axis_point(self, value: QPointF):
        """Set major axis point and emit signal"""
        if self.major_axis_point != value:
            self._ellipse_object.major_axis_point = Point2D(value.x(), value.y())
            self.major_axis_point_changed.emit(value)
            self.object_modified.emit()
    
    @property
    def minor_axis_point(self) -> QPointF:
        """Get minor axis point as QPointF"""
        minor = self._ellipse_object.minor_axis_point
        return QPointF(minor.x, minor.y)
    
    @minor_axis_point.setter
    def minor_axis_point(self, value: QPointF):
        """Set minor axis point and emit signal"""
        if self.minor_axis_point != value:
            self._ellipse_object.minor_axis_point = Point2D(value.x(), value.y())
            self.minor_axis_point_changed.emit(value)
            self.object_modified.emit()
    
    @property
    def major_axis(self) -> float:
        """Get major axis length"""
        return self._ellipse_object.major_axis
    
    @major_axis.setter
    def major_axis(self, value: float):
        """Set major axis length and emit signal"""
        if self._ellipse_object.major_axis != value:
            self._ellipse_object.major_axis = value
            self.major_axis_changed.emit(value)
            self.object_modified.emit()
    
    @property
    def minor_axis(self) -> float:
        """Get minor axis length"""
        return self._ellipse_object.minor_axis
    
    @minor_axis.setter
    def minor_axis(self, value: float):
        """Set minor axis length and emit signal"""
        if self._ellipse_object.minor_axis != value:
            self._ellipse_object.minor_axis = value
            self.minor_axis_changed.emit(value)
            self.object_modified.emit()
    
    @property
    def rotation(self) -> float:
        """Get rotation angle in radians"""
        return self._ellipse_object.rotation
    
    @rotation.setter
    def rotation(self, value: float):
        """Set rotation angle and emit signal"""
        if self._ellipse_object.rotation != value:
            self._ellipse_object.rotation = value
            self.rotation_changed.emit(value)
            self.object_modified.emit()
    
    @property
    def focus1(self) -> QPointF:
        """Get focus 1 as QPointF"""
        focus = self._ellipse_object.focus1
        return QPointF(focus.x, focus.y)
    
    @focus1.setter
    def focus1(self, value: QPointF):
        """Set focus 1 and emit signal"""
        if self.focus1 != value:
            self._ellipse_object.focus1 = Point2D(value.x(), value.y())
            self.focus1_changed.emit(value)
            self.object_modified.emit()
    
    @property
    def focus2(self) -> QPointF:
        """Get focus 2 as QPointF"""
        focus = self._ellipse_object.focus2
        return QPointF(focus.x, focus.y)
    
    @focus2.setter
    def focus2(self, value: QPointF):
        """Set focus 2 and emit signal"""
        if self.focus2 != value:
            self._ellipse_object.focus2 = Point2D(value.x(), value.y())
            self.focus2_changed.emit(value)
            self.object_modified.emit()

    def translate(self, dx: float, dy: float):
        """Move ellipse by the given offset"""
        center = self.center_point
        delta = QPointF(dx, dy)
        self.center_point = center + delta
        self.object_moved.emit(delta)
    
    def scale(self, scale_factor: float, center: QPointF):
        """Scale the ellipse around the given center"""
        current_center = self.center_point
        current_major_axis = self.major_axis
        current_minor_axis = self.minor_axis
        
        # Scale the center point
        T = QTransform()
        T.translate(-center.x(), -center.y())
        T.scale(scale_factor, scale_factor)
        T.translate(center.x(), center.y())
        new_center = T.map(current_center)
        
        # Scale the axes
        new_major_axis = current_major_axis * scale_factor
        new_minor_axis = current_minor_axis * scale_factor
        
        self.center_point = new_center
        self.major_axis = new_major_axis
        self.minor_axis = new_minor_axis
        
    def rotate(self, angle: float, center: QPointF):
        """Rotate the ellipse around the given center"""
        current_center = self.center_point
        current_rotation = self.rotation
        
        # Rotate the center point
        T = QTransform()
        T.translate(-center.x(), -center.y())
        T.rotate(angle)
        T.translate(center.x(), center.y())
        new_center = T.map(current_center)
        
        # Add to the rotation
        new_rotation = current_rotation + math.radians(angle)
        
        self.center_point = new_center
        self.rotation = new_rotation
        self.object_moved.emit(QPointF(0, 0))
        
    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get bounding box of the ellipse"""
        return self._ellipse_object.get_bounds()
    
    def contains_point(self, point: QPointF, tolerance: float = 5.0) -> bool:
        """Check if point is near the ellipse"""
        return self._ellipse_object.contains_point(Point2D(point), tolerance)
    
    def _set_center_point(self, new_position):
        """Set the center point from control point movement"""
        self.center_point = new_position
    
    def _set_major_axis_point(self, new_position):
        """Set the major axis point from control point movement"""
        self.major_axis_point = new_position
    
    def _set_minor_axis_point(self, new_position):
        """Set the minor axis point from control point movement"""
        self.minor_axis_point = new_position
    
    def _set_major_axis(self, value):
        """Set major axis from control datum"""
        self.major_axis = value
    
    def _set_minor_axis(self, value):
        """Set minor axis from control datum"""
        self.minor_axis = value
    
    def _set_rotation(self, value):
        """Set rotation from control datum (value in degrees)"""
        rotation_radians = math.radians(value)
        self.rotation = rotation_radians 