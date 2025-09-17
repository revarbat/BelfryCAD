"""
Polygon Drawing CadTool Implementation

This module implements various polygon drawing tools based on the original TCL
tools_polygons.tcl implementation, including rectangles and regular polygons.
"""

from typing import Optional

from ..models.cad_object import CadObject
from ..models.cad_objects.rectangle_cad_object import RectangleCadObject
from .base import CadTool, ToolState, ToolCategory, ToolDefinition

from PySide6.QtCore import QRectF, QPointF
from PySide6.QtGui import QPen, QColor


class RectangleTool(CadTool):
    """CadTool for drawing rectangles by two diagonal corners"""

    # Class-level tool definition
    tool_definitions = [
        ToolDefinition(
            token="RECTANGLE",
            name="Rectangle",
            category=ToolCategory.POLYGONS,
            icon="tool-rectangle",
            cursor="crosshair",
            is_creator=True,
            secondary_key="R",
            node_info=["First Corner", "Opposite Corner"]
        )
    ]

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        # Convert Qt event coordinates to scene coordinates
        if hasattr(event, 'scenePos'):
            scene_pos = event.scenePos()
        else:
            scene_pos = QPointF(event.x, event.y)

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(scene_pos.x(), scene_pos.y())

        if self.state == ToolState.ACTIVE:
            # First point - start drawing rectangle
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING:
            # Second point - complete the rectangle
            self.points.append(point)
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING and len(self.points) == 1:
            # Draw preview rectangle
            if hasattr(event, 'scenePos'):
                scene_pos = event.scenePos()
            else:
                scene_pos = QPointF(event.x, event.y)

            # Get the snapped point based on current snap settings
            point = self.get_snap_point(scene_pos.x(), scene_pos.y())

            self.draw_preview(point.x, point.y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the rectangle being created"""
        # Clear previous preview
        self.clear_temp_objects()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(current_x, current_y)

        pen = QPen(QColor("black"), 3.0)
        pen.setCosmetic(True)
        pen.setDashPattern([2, 2])

        if len(self.points) == 1:
            # Drawing from first corner to opposite corner
            p1 = self.points[0]
            p2 = point

            # Calculate bounding box coordinates
            x1, y1 = min(p1.x, p2.x), min(p1.y, p2.y)
            x2, y2 = max(p1.x, p2.x), max(p1.y, p2.y)

            # Draw temporary rectangle using QGraphicsRectItem
            rect_item = self.scene.addRect(
                QRectF(x1, y1, x2 - x1, y2 - y1),
                pen=pen
            )
            self.temp_objects.append(rect_item)
        self.draw_points()


    def create_object(self) -> Optional[CadObject]:
        """Create a rectangle object from the collected points"""
        if len(self.points) != 2:
            return None

        corner1 = self.points[0]
        corner2 = self.points[1]

        # Create rectangle object using the two diagonal corners
        rectangle = RectangleCadObject(
            document=self.document,
            corner1=corner1,
            corner2=corner2,
            color=self.preferences.get("default_color", "black"),
            line_width=self.preferences.get("default_line_width", 0.05)
        )
        return rectangle
