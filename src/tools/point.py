"""
Point Tool Implementation

This module implements the point drawing tool based on the original TCL
tools_points.tcl implementation.
"""

import tkinter as tk
import math
from typing import Optional, List, Tuple

from src.core.cad_objects import CADObject, ObjectType, Point
from src.tools.base import Tool, ToolState, ToolCategory, ToolDefinition


class PointTool(Tool):
    """Tool for drawing individual points"""

    def _get_definition(self) -> ToolDefinition:
        """Return the tool definition"""
        return ToolDefinition(
            token="POINT",
            name="Point",
            category=ToolCategory.POINTS,
            icon="tool-point",
            cursor="crosshair",
            is_creator=True,
            node_info=["Point Location"]
        )

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        self.canvas.bind("<Button-1>", self.handle_mouse_down)
        self.canvas.bind("<Motion>", self.handle_mouse_move)
        self.canvas.bind("<Escape>", self.handle_escape)

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        # Get the snapped point based on current snap settings
        point = self.get_snap_point(event.x, event.y)

        if self.state == ToolState.ACTIVE:
            # Add the point
            self.points.append(point)

            # Complete immediately since we only need one point
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.ACTIVE:
            # Draw preview point
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the point being created"""
        # Clear previous preview
        self.clear_temp_objects()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(current_x, current_y)

        # Draw temporary point marker (cross)
        x, y = point.x, point.y
        size = 3  # Size of the cross

        # Draw horizontal line
        h_line_id = self.canvas.create_line(
            x - size, y, x + size, y,
            fill="blue", dash=(2, 2)
        )

        # Draw vertical line
        v_line_id = self.canvas.create_line(
            x, y - size, x, y + size,
            fill="blue", dash=(2, 2)
        )

        # Draw small circle around the point
        circle_id = self.canvas.create_oval(
            x - size, y - size, x + size, y + size,
            outline="blue", dash=(2, 2)
        )

        self.temp_objects.extend([h_line_id, v_line_id, circle_id])

        # Add coordinates text
        text_id = self.canvas.create_text(
            x, y + 15,
            text=f"({x:.1f}, {y:.1f})",
            fill="blue"
        )
        self.temp_objects.append(text_id)

    def create_object(self) -> Optional[CADObject]:
        """Create a point object from the collected point"""
        if len(self.points) != 1:
            return None

        point = self.points[0]

        # Create a point object
        obj = CADObject(
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.POINT,
            layer=self.document.objects.current_layer,
            coords=[point],
            attributes={
                'color': 'black',      # Default color
                'linewidth': 1         # Default line width
            }
        )
        return obj
