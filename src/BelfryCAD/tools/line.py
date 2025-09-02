"""
Line Drawing Tool Implementation

This module implements a line drawing tool based on the TCL
tool implementation.
"""

from typing import Optional, List
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPen, QColor
from PySide6.QtWidgets import QGraphicsLineItem

from ..models.cad_object import CadObject, ObjectType, Point2D
from ..models.cad_objects.line_cad_object import LineCadObject
from .base import Tool, ToolState, ToolCategory, ToolDefinition


class LineTool(Tool):
    """Tool for drawing straight lines"""

    # Class-level tool definition
    tool_definitions = [
        ToolDefinition(
            token="LINE",
            name="Line Tool",
            category=ToolCategory.LINES,
            icon="tool-line",
            cursor="crosshair",
            is_creator=True,
            secondary_key="L",
            node_info=["Start Point2D", "End Point2D"]
        )
    ]

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
        # Convert Qt event coordinates to scene coordinates
        if hasattr(event, 'scenePos'):
            scene_pos = event.scenePos()
        else:
            scene_pos = QPointF(event.x, event.y)

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(scene_pos.x(), scene_pos.y())

        if self.state == ToolState.ACTIVE:
            # First point - start drawing
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING:
            # Second point - complete the line
            self.points.append(point)
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING and len(self.points) == 1:
            # Draw preview line
            if hasattr(event, 'scenePos'):
                scene_pos = event.scenePos()
            else:
                scene_pos = QPointF(event.x, event.y)
            self.draw_preview(scene_pos.x(), scene_pos.y())

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the line being created"""
        # Clear previous preview
        self.clear_temp_objects()

        if len(self.points) == 1:
            # Get the snapped point based on current snap settings
            point = self.get_snap_point(current_x, current_y)

            # Draw temporary line
            start_point = self.points[0]
            pen = QPen(QColor("black"), 3.0)
            pen.setCosmetic(True)
            pen.setDashPattern([2, 2])  # Dashed line for preview

            preview_line = self.scene.addLine(
                start_point.x, start_point.y,
                point.x, point.y,
                pen
            )
            self.temp_objects.append(preview_line)
        self.draw_points()

    def create_object(self) -> Optional[CadObject]:
        """Create a line object from the collected points"""
        if len(self.points) != 2:
            return None

        # Create line object
        line = LineCadObject(
            document=self.document,
            start_point=self.points[0],
            end_point=self.points[1],
            color=self.preferences.get("default_color", "black"),
            line_width=self.preferences.get("default_line_width", 0.05)
        )
        return line
