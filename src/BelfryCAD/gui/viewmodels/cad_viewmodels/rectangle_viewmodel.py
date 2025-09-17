"""
Rectangle ViewModel for BelfryCAD.

This ViewModel handles presentation logic for rectangle CAD objects and emits signals
for UI updates when rectangle properties change.
"""

from typing import Tuple, Optional, TYPE_CHECKING, List

from PySide6.QtCore import QPointF, Signal
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QGraphicsScene

from .cad_viewmodel import CadViewModel
from ...graphics_items.control_points import (
    ControlPoint,
    ControlPointShape,
    ControlDatum
)
from ...graphics_items.cad_polygon_graphics_item import CadPolygonGraphicsItem
from ...graphics_items.construction_cross_item import ConstructionCrossItem, DashPattern
from ....models.cad_objects.rectangle_cad_object import RectangleCadObject
from ....cad_geometry import Point2D

if TYPE_CHECKING:
    from ....gui.document_window import DocumentWindow


class RectangleViewModel(CadViewModel):
    """Presentation logic for rectangle CAD objects with signals"""
    
    # Rectangle-specific signals
    corner_changed = Signal(QPointF)  # new corner position
    width_changed = Signal(float)  # new width
    height_changed = Signal(float)  # new height
    center_changed = Signal(QPointF)  # new center position
    
    def __init__(self, document_window: 'DocumentWindow', rectangle_object: RectangleCadObject):
        super().__init__(document_window, rectangle_object)
        self._rectangle_object = rectangle_object  # Keep reference for type-specific access
        
    def update_view(self, scene: QGraphicsScene):
        """
        Creates and/or updates the view items for this rectangle.
        This is called when the rectangle is added to the scene, and when the rectangle is modified.
        """
        self._clear_view_items(scene)

        color = QColor(self._rectangle_object.color)
        line_width = self._rectangle_object.line_width
        if line_width is None:
            line_width = 1.0  # Default line width
        pen = QPen(color, line_width)
        
        # Get all four corner points in order (counter-clockwise)
        corner_points = [
            self.corner1,    # Bottom-left
            self.corner2,    # Top-left
            self.corner3,    # Top-right
            self.corner4     # Bottom-right  
        ]
        
        # Create polygon graphics item from rectangle corners
        view_item = CadPolygonGraphicsItem(
            points=corner_points,
            pen=pen
        )

        self._view_items.append(view_item)

        self._add_view_items_to_scene(scene)
        self.update_decorations(scene)
        self.update_controls(scene)
    
    def show_decorations(self, scene: QGraphicsScene):
        """
        Show the decorations for this rectangle.
        This is called when this object is being drawn or when it becomes visible.
        
        Args:
            scene: The graphics scene to add decoration items to
        """
        self._clear_decorations(scene)
        
        # Add center cross decoration
        center = self.center_point
        cross_item = ConstructionCrossItem(
            center=center,
            size=10.0
        )
        self._decorations.append(cross_item)
        
        self._add_decorations_to_scene(scene)
    
    def hide_decorations(self, scene: QGraphicsScene):
        """
        Hide the decorations for this rectangle.
        This is called when this object is no longer being drawn or when it becomes invisible.
        
        Args:
            scene: The graphics scene to remove decoration items from
        """
        self._clear_decorations(scene)

    def update_decorations(self, scene: QGraphicsScene):
        """
        Update the decorations for this rectangle.
        This is called when this object is modified.
        """
        if self._decorations:
            self.hide_decorations(scene)
            self.show_decorations(scene)
    
    def show_controls(self, scene: QGraphicsScene):
        """
        Show the controls for this rectangle.
        This is called when this object is selected.
        
        Args:
            scene: The graphics scene to add control items to
        """
        self._clear_controls(scene)
        
        # Corner control points for all four corners
        corner1_cp = ControlPoint(
            model_view=self,
            setter=self._set_corner1_point,
            tool_tip="Rectangle Corner 1"
        )
        self._controls.append(corner1_cp)
        
        corner2_cp = ControlPoint(
            model_view=self,
            setter=self._set_corner2_point,
            tool_tip="Rectangle Corner 2"
        )
        self._controls.append(corner2_cp)
        
        corner3_cp = ControlPoint(
            model_view=self,
            setter=self._set_corner3_point,
            tool_tip="Rectangle Corner 3"
        )
        self._controls.append(corner3_cp)
        
        corner4_cp = ControlPoint(
            model_view=self,
            setter=self._set_corner4_point,
            tool_tip="Rectangle Corner 4"
        )
        self._controls.append(corner4_cp)
        
        # Center control point
        center_cp = ControlPoint(
            model_view=self,
            setter=self._set_center_point,
            tool_tip="Rectangle Center",
            cp_shape=ControlPointShape.SQUARE
        )
        self._controls.append(center_cp)
        
        # Width and height control datums
        width_datum = ControlDatum(
            model_view=self,
            setter=self._set_width,
            prefix="W: ",
            is_length=True,
            min_value=0.0,
        )
        self._controls.append(width_datum)

        height_datum = ControlDatum(
            model_view=self,
            setter=self._set_height,
            prefix="H: ",
            is_length=True,
            min_value=0.0,
        )
        self._controls.append(height_datum)
        
        self._add_controls_to_scene(scene)
    
    def hide_controls(self, scene: QGraphicsScene):
        """
        Hide the controls for this rectangle.
        This is called when this object is deselected, or when an additional object becomes selected.
        
        Args:
            scene: The graphics scene to remove control items from
        """
        self._clear_controls(scene)
    
    def update_controls(self, scene: QGraphicsScene):
        """
        Update the controls for this rectangle.
        This is called when this object is modified.
        
        Args:
            scene: The graphics scene containing the control items
        """
        if not self._controls:
            return

        # Update control points
        self._controls[0].setPos(self.corner1)
        self._controls[1].setPos(self.corner2)
        self._controls[2].setPos(self.corner3)
        self._controls[3].setPos(self.corner4)
        self._controls[4].setPos(self.center_point)
        
        # Update Width and Height datums
        self._controls[5].update_datum(
            self.width,
            self.center_point + QPointF(0, self.height / 2)
        )
        
        self._controls[6].update_datum(
            self.height,
            self.center_point + QPointF(-self.width / 2, 0)
        )
        
        self.control_points_updated.emit()

    def get_properties(self) -> List[str]:
        """Get properties of the rectangle"""
        return [ "Width", "Height" ]
    
    def get_property_value(self, name: str) -> float:
        """Get a rectangle property"""
        if name == "Width":
            return self.width
        elif name == "Height":
            return self.height
        else:
            raise ValueError(f"Invalid property name: {name}")
        
    def set_property_value(self, name: str, value: float):
        """Set a rectangle property"""
        if name == "Width":
            self.width = value
        elif name == "Height":
            self.height = value
        else:
            raise ValueError(f"Invalid property name: {name}")
    
    def get_bounds(self) -> Tuple[float, float, float, float]:
        """
        Get the bounding box of this rectangle.
        
        Returns:
            Tuple of (min_x, min_y, max_x, max_y) coordinates
        """
        return self._rectangle_object.get_bounds()
    
    def contains_point(self, point: QPointF, tolerance: float = 5.0) -> bool:
        """
        Check if a point is near this rectangle.
        
        Args:
            point: The point to check
            tolerance: Distance tolerance for hit testing
            
        Returns:
            True if the point is within tolerance of this rectangle
        """
        cad_point = Point2D(point.x(), point.y())
        return self._rectangle_object.contains_point(cad_point, tolerance)
    
    # Properties for accessing rectangle geometry
    
    @property
    def object_type(self) -> str:
        """Get the object type."""
        return "rectangle"
    
    @property
    def corner1(self) -> QPointF:
        """Get the bottom-left corner point as QPointF."""
        return self._rectangle_object.corner1.to_qpointf()
    
    @corner1.setter
    def corner1(self, value: QPointF):
        """Set the bottom-left corner point from QPointF."""
        self._rectangle_object.corner1 = Point2D(value)
        self.corner_changed.emit(value)
        self.object_modified.emit()
    
    @property
    def corner2(self) -> QPointF:
        """Get the top-left corner point as QPointF."""
        return self._rectangle_object.corner2.to_qpointf()
    
    @corner2.setter
    def corner2(self, value: QPointF):
        """Set the top-left corner point from QPointF."""
        self._rectangle_object.corner2 = Point2D(value)
        self.corner_changed.emit(value)
        self.object_modified.emit()
    
    @property
    def corner3(self) -> QPointF:
        """Get the top-right corner point as QPointF."""
        return self._rectangle_object.corner3.to_qpointf()
    
    @corner3.setter
    def corner3(self, value: QPointF):
        """Set the top-right corner point from QPointF."""
        self._rectangle_object.corner3 = Point2D(value)
        self.corner_changed.emit(value)
        self.object_modified.emit()
    
    @property
    def corner4(self) -> QPointF:
        """Get the bottom-right corner point as QPointF."""
        return self._rectangle_object.corner4.to_qpointf()
    
    @corner4.setter
    def corner4(self, value: QPointF):
        """Set the bottom-right corner point from QPointF."""
        self._rectangle_object.corner4 = Point2D(value)
        self.corner_changed.emit(value)
        self.object_modified.emit()
    
    @property
    def width(self) -> float:
        """Get the width."""
        return self._rectangle_object.width
    
    @width.setter
    def width(self, value: float):
        """Set the width."""
        self._rectangle_object.width = value
        self.width_changed.emit(value)
        self.object_modified.emit()
    
    @property
    def height(self) -> float:
        """Get the height."""
        return self._rectangle_object.height
    
    @height.setter
    def height(self, value: float):
        """Set the height."""
        self._rectangle_object.height = value
        self.height_changed.emit(value)
        self.object_modified.emit()
    
    @property
    def center_point(self) -> QPointF:
        """Get the center point as QPointF."""
        center = self._rectangle_object.center_point
        return QPointF(center.x, center.y)
    
    @center_point.setter
    def center_point(self, value: QPointF):
        """Set the center point from QPointF."""
        self._rectangle_object.center_point = Point2D(value.x(), value.y())
        self.center_changed.emit(value)
        self.object_modified.emit()
    
    # Control point setter methods (required by control point system)
    
    def _set_corner1_point(self, new_position: QPointF):
        """Set corner1 from control point."""
        self.corner1 = new_position
        self.update_all()
    
    def _set_corner2_point(self, new_position: QPointF):
        """Set corner2 from control point."""
        self.corner2 = new_position
        self.update_all()
    
    def _set_corner3_point(self, new_position: QPointF):
        """Set corner3 from control point."""
        self.corner3 = new_position
        self.update_all()
    
    def _set_corner4_point(self, new_position: QPointF):
        """Set corner4 from control point."""
        self.corner4 = new_position
        self.update_all()
    
    def _set_center_point(self, new_position: QPointF):
        """Set center from control point."""
        self.center_point = new_position
        self.update_all()
    
    def _set_width(self, value: float):
        """Set the width."""
        self.width = value
        self.update_all()
    
    def _set_height(self, value: float):
        """Set the height."""
        self.height = value
        self.update_all()
    