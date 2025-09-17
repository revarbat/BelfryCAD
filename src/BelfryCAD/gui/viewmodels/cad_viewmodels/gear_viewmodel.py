"""
Gear ViewModel for BelfryCAD.

This ViewModel handles presentation logic for gear CAD objects and emits signals
for UI updates when gear properties change.
"""

import math
from typing import List, Tuple, Optional, TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, Signal
from PySide6.QtGui import QColor, QTransform, QPen, QBrush, QPolygonF
from PySide6.QtWidgets import QGraphicsScene

from .cad_viewmodel import CadViewModel
from ...graphics_items.control_points import (
    ControlPoint,
    ControlPointShape,
    ControlDatum
)
from ...graphics_items.cad_polygon_graphics_item import CadPolygonGraphicsItem
from ....models.cad_objects.gear_cad_object import GearCadObject
from ....cad_geometry import Point2D

if TYPE_CHECKING:
    from ....gui.document_window import DocumentWindow


class GearViewModel(CadViewModel):
    """Presentation logic for gear CAD objects with signals"""
    
    # Gear-specific signals
    center_changed = Signal(QPointF)  # new center position
    pitch_diameter_changed = Signal(float)  # new pitch diameter
    num_teeth_changed = Signal(int)  # new tooth count
    pressure_angle_changed = Signal(float)  # new pressure angle
    gear_path_changed = Signal()  # gear geometry updated
    
    def __init__(self, document_window: 'DocumentWindow', gear_object: GearCadObject):
        super().__init__(document_window, gear_object)
        self._gear_object = gear_object  # Keep reference for type-specific access
        
    def update_view(self, scene: QGraphicsScene):
        """
        Creates and/or updates the view items for this gear.
        This is called when the gear is added to the scene, and when the gear is modified.
        """
        self._clear_view_items(scene)

        color = QColor(self._gear_object.color)
        line_width = self._gear_object.line_width
        
        # Get gear path points from the model
        gear_points = self._gear_object.get_gear_path_points()
        
        if gear_points:
            # Convert to QPointF for Qt
            qpoints = [QPointF(point.x, point.y) for point in gear_points]
            
            # Create polygon item with no fill (gears are typically outlines)
            if line_width is not None:
                pen = QPen(color, line_width)
            else:
                pen = QPen(color, 1.0)
                pen.setCosmetic(True)
            brush = QBrush()  # No fill
            view_item = CadPolygonGraphicsItem(qpoints, pen=pen, brush=brush)
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
        
        # Get pitch circle points from the model
        pitch_points = self._gear_object.get_pitch_circle_points()
        if pitch_points:
            qpoints = [QPointF(point.x, point.y) for point in pitch_points]
            
            # Create pitch circle decoration with no fill
            pen = QPen(QColor(0x7f, 0x7f, 0x7f), 1.0)  # Gray
            brush = QBrush()  # No fill
            decoration_item = CadPolygonGraphicsItem(qpoints, pen=pen, brush=brush)
            self._decorations.append(decoration_item)
        
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

        # Center control point
        center_cp = ControlPoint(
            model_view=self,
            setter=self._set_center,
            tool_tip="Gear Center",
            cp_shape=ControlPointShape.SQUARE
        )
        self._controls.append(center_cp)
        
        # Pitch radius control point
        radius_cp = ControlPoint(
            model_view=self,
            setter=self._set_pitch_radius_point,
            tool_tip="Pitch Radius",
            cp_shape=ControlPointShape.ROUND
        )
        self._controls.append(radius_cp)

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
        pitch_radius = self.pitch_radius
        
        # Update control points
        self._controls[0].setPos(center)  # Center point
        radius_pos = QPointF(center.x() + pitch_radius, center.y())
        self._controls[1].setPos(radius_pos)  # Radius point
        
        self.control_points_updated.emit()

    def get_properties(self) -> List[str]:
        """Get properties of the gear"""
        return [
            "Pitch Diameter",
            "Tooth Count",
            "Pressure Angle",
            "Module",
            "Diametral Pitch"
        ]
    
    def get_property_value(self, name: str) -> float:
        """Get a gear property"""
        if name == "Pitch Diameter":
            return self.pitch_diameter
        elif name == "Tooth Count":
            return self.num_teeth
        elif name == "Pressure Angle":
            return self.pressure_angle
        elif name == "Module":
            return self.module
        elif name == "Diametral Pitch":
            return self.diametral_pitch
        else:
            raise ValueError(f"Invalid property name: {name}")
        
    def set_property_value(self, name: str, value: float):
        """Set a gear property"""
        if name == "Pitch Diameter":
            self.pitch_diameter = value
        elif name == "Tooth Count":
            self.num_teeth = int(value)
        elif name == "Pressure Angle":
            self.pressure_angle = value
        elif name == "Module":
            self.module = value
        elif name == "Diametral Pitch":
            self.diametral_pitch = value
        else:
            raise ValueError(f"Invalid property name: {name}")
    
    @property
    def object_type(self) -> str:
        """Get object type"""
        return "gear"
    
    @property
    def line_width(self) -> Optional[float]:
        """Get line width from model"""
        return self._gear_object.line_width
    
    @line_width.setter
    def line_width(self, value: Optional[float]):
        """Set line width in model"""
        if self._gear_object.line_width != value:
            self._gear_object.line_width = value
            self.object_modified.emit()
    
    # Gear-specific properties
    @property
    def center_point(self) -> QPointF:
        """Get center point"""
        center = self._gear_object.center_point
        return QPointF(center.x, center.y)
    
    @center_point.setter
    def center_point(self, value: QPointF):
        """Set center point"""
        new_center = Point2D(value.x(), value.y())
        if self._gear_object.center_point != new_center:
            self._gear_object.center_point = new_center
            self.center_changed.emit(value)
            self.object_modified.emit()
    
    @property
    def pitch_diameter(self) -> float:
        """Get pitch diameter"""
        return self._gear_object.pitch_diameter
    
    @pitch_diameter.setter
    def pitch_diameter(self, value: float):
        """Set pitch diameter"""
        if self._gear_object.pitch_diameter != value:
            self._gear_object.pitch_diameter = value
            self.pitch_diameter_changed.emit(value)
            self.object_modified.emit()
    
    @property
    def num_teeth(self) -> int:
        """Get number of teeth"""
        return self._gear_object.num_teeth
    
    @num_teeth.setter
    def num_teeth(self, value: int):
        """Set number of teeth"""
        if self._gear_object.num_teeth != value:
            self._gear_object.num_teeth = value
            self.num_teeth_changed.emit(value)
            self.object_modified.emit()
    
    @property
    def pressure_angle(self) -> float:
        """Get pressure angle in degrees"""
        return self._gear_object.pressure_angle
    
    @pressure_angle.setter
    def pressure_angle(self, value: float):
        """Set pressure angle in degrees"""
        if self._gear_object.pressure_angle != value:
            self._gear_object.pressure_angle = value
            self.pressure_angle_changed.emit(value)
            self.object_modified.emit()
    
    @property
    def pitch_radius(self) -> float:
        """Get pitch radius"""
        return self._gear_object.pitch_radius
    
    @pitch_radius.setter
    def pitch_radius(self, value: float):
        """Set pitch radius"""
        self.pitch_diameter = value * 2
    
    @property
    def module(self) -> float:
        """Get module (pitch diameter / teeth)"""
        return self._gear_object.module
    
    @module.setter
    def module(self, value: float):
        """Set module"""
        self.pitch_diameter = value * self.num_teeth
    
    @property
    def diametral_pitch(self) -> float:
        """Get diametral pitch"""
        return self._gear_object.diametral_pitch
    
    @diametral_pitch.setter
    def diametral_pitch(self, value: float):
        """Set diametral pitch"""
        self.pitch_diameter = self.num_teeth / value
    
    @property
    def circular_pitch(self) -> float:
        """Get circular pitch"""
        return self._gear_object.circular_pitch
    
    @circular_pitch.setter
    def circular_pitch(self, value: float):
        """Set circular pitch"""
        self.pitch_diameter = value * self.num_teeth / (2 * 3.14159)

    def translate(self, dx: float, dy: float):
        """Move gear by the given offset"""
        if dx != 0 or dy != 0:
            self._gear_object.translate(dx, dy)
            new_pos = self.center_point
            self.object_moved.emit(new_pos)
    
    def scale(self, scale_factor: float, center: QPointF):
        """Scale the gear around the given center"""
        center_point = Point2D(center.x(), center.y())
        self._gear_object.scale(scale_factor, center_point)
        
    def rotate(self, angle: float, center: QPointF):
        """Rotate the gear around the given center"""
        center_point = Point2D(center.x(), center.y())
        self._gear_object.rotate(angle, center_point)
        self.object_moved.emit(QPointF(0, 0))
        
    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get bounding box of the gear"""
        return self._gear_object.get_bounds()
    
    def contains_point(self, point: QPointF, tolerance: float = 5.0) -> bool:
        """Check if point is near the gear"""
        return self._gear_object.contains_point(Point2D(point), tolerance)
    
    def get_gear_path_points(self) -> List[QPointF]:
        """Get gear path points for rendering"""
        gear_points = self._gear_object.get_gear_path_points()
        return [QPointF(point.x, point.y) for point in gear_points]
    
    def get_pitch_circle_points(self) -> List[QPointF]:
        """Get pitch circle points for construction display"""
        pitch_points = self._gear_object.get_pitch_circle_points()
        return [QPointF(point.x, point.y) for point in pitch_points]
    
    # Control point setters
    def _set_center(self, new_position: QPointF):
        """Set center point from control point movement"""
        self.center_point = new_position
    
    def _set_pitch_radius_point(self, new_position: QPointF):
        """Set pitch radius from control point movement"""
        center = self.center_point
        dx = new_position.x() - center.x()
        dy = new_position.y() - center.y()
        new_radius = (dx * dx + dy * dy) ** 0.5
        self.pitch_radius = new_radius
    
    def _set_tooth_count(self, value):
        """Set tooth count from datum"""
        try:
            value = int(round(float(value)))
            if value < 3:
                value = 3
        except Exception:
            value = 12
        self.num_teeth = value
    
    def _set_pitch_diameter(self, value):
        """Set pitch diameter from datum"""
        try:
            value = float(value)
            if value <= 0:
                value = 1.0
        except Exception:
            value = 1.0
        self.pitch_diameter = value
    
    def _set_pressure_angle(self, value):
        """Set pressure angle from datum"""
        self.pressure_angle = value
    
    def _set_module(self, value):
        """Set module from datum"""
        self.module = value
    
    def _set_diametral_pitch(self, value):
        """Set diametral pitch from datum"""
        self.diametral_pitch = value
    
    def _is_metric(self) -> bool:
        """Check if using metric units"""
        # This should be determined by the application's unit system
        # For now, return True as default
        return True 