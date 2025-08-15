"""
Circle ViewModel for BelfryCAD.

This ViewModel handles presentation logic for circle CAD objects and emits signals
for UI updates when circle properties change.
"""

import math
from typing import Tuple, Optional, TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, Signal
from PySide6.QtGui import QColor, QTransform, QPen
from PySide6.QtWidgets import QGraphicsScene

from .cad_viewmodel import CadViewModel
from ...graphics_items.control_points import (
    ControlPoint,
    SquareControlPoint,
    ControlDatum
)
from ...graphics_items.dimension_line_composite import (
    DimensionLineComposite
)
from ...graphics_items.cad_circle_graphics_item import CadCircleGraphicsItem
from ...graphics_items.construction_cross_item import ConstructionCrossItem, DashPattern
from ....models.cad_objects.circle_cad_object import CircleCadObject
from ....cad_geometry import Point2D

if TYPE_CHECKING:
    from ....gui.document_window import DocumentWindow


class CircleViewModel(CadViewModel):
    """Presentation logic for circle CAD objects with signals"""
    
    # Circle-specific signals
    center_changed = Signal(QPointF)  # new center position
    radius_changed = Signal(float)  # new radius
    diameter_changed = Signal(float)  # new diameter
    perimeter_point_changed = Signal(QPointF)  # new perimeter point
    
    def __init__(self, document_window: 'DocumentWindow', circle_object: CircleCadObject):
        super().__init__(document_window, circle_object)
        self._circle_object = circle_object  # Keep reference for type-specific access
        
    def update_view(self, scene: QGraphicsScene):
        """
        Creates and/or updates the view items for this circle.
        This is called when the circle is added to the scene, and when the circle is modified.
        """
        self._clear_view_items(scene)

        color = QColor(self._circle_object.color)
        line_width = self._circle_object.line_width
        if line_width is None:
            line_width = 1.0  # Default line width
        center = self.center_point
        radius = self.radius
        pen = QPen(color, line_width)
        
        # Create circle graphics item
        view_item = CadCircleGraphicsItem(
            center_point=center,
            radius=radius,
            pen=pen
        )
        # Selection flags are now set by the base class

        self._view_items.append(view_item)

        self._add_view_items_to_scene(scene)
        self.update_decorations(scene)
        self.update_controls(scene)
    
    def show_decorations(self, scene: QGraphicsScene):
        """
        Show the decorations.
        This is called when this object is selected.
        """
        print("show_decorations circle")
        self._clear_decorations(scene)
        
        # Add center cross decoration
        center = self.center_point
        radius = self.radius
        
        # Calculate appropriate cross size based on circle radius
        cross_size = radius * 2.5
        
        center_cross = ConstructionCrossItem(
            center=center,
            size=cross_size,
            dash_pattern=DashPattern.CENTERLINE,
            line_width=None
        )
        
        self._decorations.append(center_cross)
        self._add_decorations_to_scene(scene)
    
    def hide_decorations(self, scene: QGraphicsScene):
        """
        Hide the decorations.
        This is called when this object is deselected.
        """
        print("hide_decorations circle")
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
            tool_tip="Circle Center"
        )
        self._controls.append(center_cp)

        perimeter_cp = SquareControlPoint(
            model_view=self,
            setter=self._set_perimeter_point,
            tool_tip="Circle Radius"
        )
        self._controls.append(perimeter_cp)

        # Get precision from document window or use default
        precision = self._document_window.preferences_viewmodel.get_precision()
        
        # Radius datum
        radius_datum = ControlDatum(
            model_view=self,
            label="Circle Radius",
            setter=self._set_radius,
            format_string=f"{{:.{precision}f}}",
            precision_override=precision,
            min_value=0,
            is_length=True
        )
        self._controls.append(radius_datum)
        
        # Diameter datum
        diameter_datum = ControlDatum(
            model_view=self,
            label="Circle Diameter",
            setter=self._set_diameter,
            format_string=f"{{:.{precision}f}}",
            precision_override=precision,
            min_value=0,
            is_length=True
        )
        self._controls.append(diameter_datum)

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
        perimeter = self.perimeter_point
        
        # Update control points
        self._controls[0].setPos(center)  # Center point
        self._controls[1].setPos(perimeter)  # Perimeter point
        
        # Update Radius datum
        self._controls[2].update_datum(
            self.radius,
            center + QPointF(20, -20)
        )
        
        # Update Diameter datum
        self._controls[3].update_datum(
            self.diameter,
            center + QPointF(20, 20)
        )
    
        self.control_points_updated.emit()
    
    @property
    def object_type(self) -> str:
        """Get object type"""
        return "circle"
    
    @property
    def line_width(self) -> Optional[float]:
        """Get line width from model"""
        return self._circle_object.line_width
    
    @line_width.setter
    def line_width(self, value: Optional[float]):
        """Set line width in model"""
        if self._circle_object.line_width != value:
            self._circle_object.line_width = value
            self.object_modified.emit()
    
    @property
    def center_point(self) -> QPointF:
        """Get center point as QPointF"""
        center = self._circle_object.center_point
        return QPointF(center.x, center.y)
    
    @center_point.setter
    def center_point(self, value: QPointF):
        """Set center point and emit signal"""
        if self.center_point != value:
            self._circle_object.center_point = Point2D(value.x(), value.y())
            self.center_changed.emit(value)
            self.object_modified.emit()
    
    @property
    def radius(self) -> float:
        """Get radius"""
        return self._circle_object.radius
    
    @radius.setter
    def radius(self, value: float):
        """Set radius and emit signal"""
        if self._circle_object.radius != value:
            self._circle_object.radius = value
            self.radius_changed.emit(value)
            self.object_modified.emit()
    
    @property
    def diameter(self) -> float:
        """Get diameter"""
        return self._circle_object.diameter
    
    @diameter.setter
    def diameter(self, value: float):
        """Set diameter and emit signal"""
        if self._circle_object.diameter != value:
            self._circle_object.diameter = value
            self.diameter_changed.emit(value)
            self.object_modified.emit()
    
    @property
    def perimeter_point(self) -> QPointF:
        """Get perimeter point as QPointF"""
        perimeter = self._circle_object.perimeter_point
        return QPointF(perimeter.x, perimeter.y)
    
    @perimeter_point.setter
    def perimeter_point(self, value: QPointF):
        """Set perimeter point and emit signal"""
        if self.perimeter_point != value:
            self._circle_object.perimeter_point = Point2D(value.x(), value.y())
            self.perimeter_point_changed.emit(value)
            self.object_modified.emit()

    def translate(self, dx: float, dy: float):
        """Move circle by the given offset"""
        center = self.center_point
        delta = QPointF(dx, dy)
        self.center_point = center + delta
        self.object_moved.emit(delta)
    
    def scale(self, scale_factor: float, center: QPointF):
        """Scale the circle around the given center"""
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
        """Rotate the circle around the given center"""
        current_center = self.center_point
        
        # Rotate the center point
        T = QTransform()
        T.translate(-center.x(), -center.y())
        T.rotate(angle)
        T.translate(center.x(), center.y())
        new_center = T.map(current_center)
        
        self.center_point = new_center
        self.object_moved.emit(QPointF(0, 0))
        
    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get bounding box of the circle"""
        center = self.center_point
        radius = self.radius
        return (
            center.x() - radius,
            center.y() - radius,
            center.x() + radius,
            center.y() + radius
        )
    
    def contains_point(self, point: QPointF, tolerance: float = 5.0) -> bool:
        """Check if point is near the circle"""
        return self._circle_object.contains_point(Point2D(point), tolerance)
    
    def _set_center_point(self, new_position):
        """Set the center point from control point movement"""
        self.center_point = new_position
    
    def _set_perimeter_point(self, new_position):
        """Set the perimeter point from control point movement"""
        self.perimeter_point = new_position
    
    def _set_radius(self, value):
        """Set radius from control datum"""
        self.radius = value
    
    def _set_diameter(self, value):
        """Set diameter from control datum"""
        self.diameter = value 