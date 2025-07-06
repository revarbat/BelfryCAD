"""
Screw Hole Tool Implementation

This module implements the screw hole drawing tool based on the original TCL
tools_screwholes.tcl implementation.
"""

import math
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from PySide6.QtWidgets import (QGraphicsEllipseItem, QGraphicsPathItem,
                              QGraphicsLineItem)
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QColor, QPainterPath, QBrush

from ..core.cad_objects import CADObject, ObjectType, Point
from .base import Tool, ToolState, ToolCategory, ToolDefinition

if TYPE_CHECKING:
    from ..gui.main_window import MainWindow


class ScrewHoleObject(CADObject):
    """Screw hole object - position, size, and thread parameters"""

    def __init__(self, mainwin: 'MainWindow', object_id: int, position: Point, diameter: float, **kwargs):
        super().__init__(
            mainwin, object_id, ObjectType.SCREW_HOLE, coords=[position], **kwargs)
        self.attributes.update({
            'diameter': diameter,
            'thread_size': kwargs.get('thread_size', 'M3'),
            'thread_pitch': kwargs.get('thread_pitch', 0.5),
            'thread_depth': kwargs.get('thread_depth', 0.0),
            'counter_sink': kwargs.get('counter_sink', False),
            'counter_sink_angle': kwargs.get('counter_sink_angle', 90.0),
            'counter_sink_depth': kwargs.get('counter_sink_depth', 0.0),
            'counter_bore': kwargs.get('counter_bore', False),
            'counter_bore_diameter': kwargs.get('counter_bore_diameter', 0.0),
            'counter_bore_depth': kwargs.get('counter_bore_depth', 0.0)
        })

    @property
    def position(self) -> Point:
        return self.coords[0]

    @property
    def diameter(self) -> float:
        return self.attributes['diameter']

    @property
    def thread_size(self) -> str:
        return self.attributes['thread_size']

    @property
    def thread_pitch(self) -> float:
        return self.attributes['thread_pitch']

    @property
    def thread_depth(self) -> float:
        return self.attributes['thread_depth']

    @property
    def counter_sink(self) -> bool:
        return self.attributes['counter_sink']

    @property
    def counter_sink_angle(self) -> float:
        return self.attributes['counter_sink_angle']

    @property
    def counter_sink_depth(self) -> float:
        return self.attributes['counter_sink_depth']

    @property
    def counter_bore(self) -> bool:
        return self.attributes['counter_bore']

    @property
    def counter_bore_diameter(self) -> float:
        return self.attributes['counter_bore_diameter']

    @property
    def counter_bore_depth(self) -> float:
        return self.attributes['counter_bore_depth']


class ScrewHoleTool(Tool):
    """Tool for creating screw holes with various parameters"""

    def __init__(self, main_window, document, preferences):
        super().__init__(main_window, document, preferences)
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
            node_info=["Center Point", "Diameter Point"]
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
        screw_hole = ScrewHoleObject(
            self.main_window,
            self.document.objects.get_next_id(),
            center,
            diameter
        )

        # Add to document
        self.document.objects.objects[screw_hole.object_id] = screw_hole

        # Emit signal
        self.object_created.emit(screw_hole)

        # Reset tool state
        self.reset()