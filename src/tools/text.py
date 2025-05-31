"""
Text Tool Implementation

This module implements text drawing tools based on the original TCL
tools_text.tcl implementation.
"""

import tkinter as tk
import math
from typing import Optional

from src.core.cad_objects import CADObject, ObjectType, Point
from src.tools.base import Tool, ToolState, ToolCategory, ToolDefinition


class TextTool(Tool):
    """Tool for creating text elements"""

    def __init__(self, canvas, document, preferences):
        """Initialize the tool with the canvas, document and preferences"""
        super().__init__(canvas, document, preferences)

        # Default text properties
        self.text = "Text"
        self.font_family = "Arial"
        self.font_size = 12
        self.text_angle = 0.0

    def _get_definition(self) -> ToolDefinition:
        """Return the tool definition"""
        return ToolDefinition(
            token="TEXT",
            name="Text",
            category=ToolCategory.TEXT,
            icon="tool-text",
            cursor="text",
            is_creator=True,
            node_info=["Position"]
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
            # First click - set position and complete
            self.points.append(point)
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.ACTIVE:
            # Show preview at cursor position
            point = self.get_snap_point(event.x, event.y)
            self.clear_temp_objects()
            self._draw_text_preview(point)

    def _draw_text_preview(self, position: Point):
        """Draw a preview of the text"""
        # Calculate text properties
        angle_rad = math.radians(self.text_angle)
        font_spec = (self.font_family, self.font_size)

        # Draw the text
        text_id = self.canvas.create_text(
            position.x, position.y,
            text=self.text,
            font=font_spec,
            fill="gray",
            angle=self.text_angle,
            anchor=tk.SW  # Southwest anchor (bottom-left)
        )
        self.temp_objects.append(text_id)

        # Add a small marker at the position point
        marker_id = self.canvas.create_rectangle(
            position.x - 3, position.y - 3,
            position.x + 3, position.y + 3,
            fill="red", outline="red"
        )
        self.temp_objects.append(marker_id)

        # Draw text baseline guide
        line_length = 50
        x2 = position.x + line_length * math.cos(angle_rad)
        y2 = position.y + line_length * math.sin(angle_rad)
        line_id = self.canvas.create_line(
            position.x, position.y, x2, y2,
            fill="gray", dash=(2, 2)
        )
        self.temp_objects.append(line_id)

    def create_object(self) -> Optional[CADObject]:
        """Create a text object"""
        if len(self.points) != 1 or not self.text:
            return None

        position = self.points[0]

        # Create a text object
        obj = CADObject(
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.TEXT,
            layer=self.document.objects.current_layer,
            coords=[position],
            attributes={
                'color': 'black',                # Default color
                'text': self.text,               # The text string
                'font_family': self.font_family, # Font family
                'font_size': self.font_size,     # Font size
                'angle': self.text_angle,        # Rotation angle in degrees
                'anchor': 'sw'                   # Text anchor (southwest)
            }
        )
        return obj
