"""
Screw hole tool for BelfryCAD.

This tool allows users to create and manipulate screw hole objects in the CAD document.
"""

import math
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from PySide6.QtWidgets import (QGraphicsEllipseItem, QGraphicsPathItem,
                              QGraphicsLineItem)
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QColor, QPainterPath, QBrush

from ..models.cad_object import CadObject, ObjectType
from ..cad_geometry import Point2D
from .base import Tool, ToolState, ToolCategory, ToolDefinition

if TYPE_CHECKING:
    from ..gui.document_window import DocumentWindow


class ScrewHoleCadObject(CadObject):
    """CAD object representing a screw hole."""
    
    def __init__(self, document_window: 'DocumentWindow', object_id: int, position: Point2D, diameter: float, **kwargs):
        super().__init__(
            document_window, object_id, ObjectType.SCREW_HOLE, coords=[position], **kwargs)
        self.position = position
        self.diameter = diameter
    
    def get_bounds(self):
        """Get the bounding box of the screw hole."""
        radius = self.diameter / 2
        return (
            self.position.x - radius,
            self.position.y - radius,
            self.position.x + radius,
            self.position.y + radius
        )
    
    def translate(self, dx: float, dy: float):
        """Translate the screw hole by the given offset."""
        self.position = Point2D(self.position.x + dx, self.position.y + dy)
    
    def scale(self, scale_factor: float, center: Point2D):
        """Scale the screw hole around the given center point."""
        # Scale the position relative to center
        dx = self.position.x - center.x
        dy = self.position.y - center.y
        self.position = Point2D(center.x + dx * scale_factor, center.y + dy * scale_factor)
        
        # Scale the diameter
        self.diameter *= scale_factor
    
    def rotate(self, angle: float, center: Point2D):
        """Rotate the screw hole around the given center point."""
        # TODO: Implement rotation
        pass


class ScrewHoleTool(Tool):
    """Tool for creating screw holes in the CAD document."""
    
    def __init__(self, document_window, document, preferences):
        super().__init__(document_window, document, preferences)
        self.preview_items = []
    
    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="SCREWHOLE",
            name="Screw Hole",
            category=ToolCategory.CAM,
            icon="tool-screwhole",
            cursor="crosshair",
            is_creator=True,
            secondary_key="H",
            node_info=["Center Point2D", "Diameter Point2D"]
        )]

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        # In Qt, event handling is done differently - these will be connected
        # in the main window or graphics view
        pass

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        # Get the snapped point based on current snap settings
        point = self.get_snap_point(event.x, event.y)

        if self.state == ToolState.ACTIVE:
            # First point - center of screw hole
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING:
            # Second point - determines diameter
            self.points.append(point)
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            # Draw preview of screw hole
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x: float, current_y: float):
        """Draw preview of the screw hole"""
        if len(self.points) < 1:
            return

        # Clear previous preview
        self.clear_preview()

        # Calculate diameter from center to current point
        center = self.points[0]
        radius = math.sqrt((current_x - center.x) ** 2 + (current_y - center.y) ** 2)

        # Create preview items
        # Main hole circle
        hole = QGraphicsEllipseItem(
            center.x - radius, center.y - radius,
            radius * 2, radius * 2
        )
        pen = QPen(QColor(0, 0, 255), 1)
        pen.setStyle(Qt.PenStyle.DashLine)
        hole.setPen(pen)
        hole.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.preview_items.append(hole)

        # Add to scene
        self.scene.addItem(hole)

    def clear_preview(self):
        """Clear preview items"""
        for item in self.preview_items:
            self.scene.removeItem(item)
        self.preview_items.clear()

    def reset(self):
        """Reset tool state"""
        self.state = ToolState.ACTIVE
        self.points.clear()
        self.clear_preview()

    def complete(self):
        """Complete the screw hole creation"""
        if len(self.points) != 2:
            return

        # Calculate diameter from points
        center = self.points[0]
        diameter_point = self.points[1]
        diameter = 2 * math.sqrt(
            (diameter_point.x - center.x) ** 2 +
            (diameter_point.y - center.y) ** 2
        )

        # Create screw hole object
        screw_hole = ScrewHoleCadObject(
            self.document_window,
            self.document.get_next_object_id(),
            center,
            diameter
        )

        # Add to document
        self.document.add_object(screw_hole)
        self.document.mark_modified()

        # Emit signal
        self.object_created.emit(screw_hole)

        # Reset tool state
        self.reset()