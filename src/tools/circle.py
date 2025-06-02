"""
Circle Drawing Tool Implementation

This module implements a circle drawing tool based on the TCL tool
implementation.
"""

import math
from typing import Optional, List

from src.core.cad_objects import CADObject, ObjectType
from src.tools.base import Tool, ToolState, ToolCategory, ToolDefinition


class CircleTool(Tool):
    """Tool for drawing circles"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="CIRCLE",
            name="Circle Tool",
            category=ToolCategory.CIRCLES,
            icon="tool-circlectr",
            cursor="crosshair",
            is_creator=True,
            node_info=["Center Point", "Radius Point"]
        )]

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
            # First point - center of circle
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING:
            # Second point - radius point
            self.points.append(point)
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING and len(self.points) == 1:
            # Draw preview circle
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the circle being created"""
        # Clear previous preview
        self.clear_temp_objects()

        if len(self.points) == 1:
            # Get the snapped point based on current snap settings
            point = self.get_snap_point(current_x, current_y)

            # Calculate radius
            center_point = self.points[0]
            radius = math.sqrt((point.x - center_point.x)**2 +
                               (point.y - center_point.y)**2)

            # Draw temporary circle
            preview_id = self.canvas.create_oval(
                center_point.x - radius, center_point.y - radius,
                center_point.x + radius, center_point.y + radius,
                outline="blue", dash=(4, 4)  # Dashed line for preview
            )
            self.temp_objects.append(preview_id)

    def create_object(self) -> Optional[CADObject]:
        """Create a circle object from the collected points"""
        if len(self.points) != 2:
            return None

        # Calculate radius
        center_point = self.points[0]
        radius_point = self.points[1]
        radius = math.sqrt(
            (radius_point.x - center_point.x)**2 +
            (radius_point.y - center_point.y)**2
        )

        # Create a circle object
        obj = CADObject(
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.CIRCLE,
            layer=self.document.objects.current_layer,
            coords=[center_point],  # Only need center point
            attributes={
                'color': 'black',  # Default color
                'linewidth': 1,    # Default line width
                'radius': radius   # Store the radius as an attribute
            }
        )
        return obj
