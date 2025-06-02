"""
Line Drawing Tool Implementation

This module implements a line drawing tool based on the TCL
tool implementation.
"""

from typing import Optional, List

from src.core.cad_objects import CADObject, ObjectType
from src.tools.base import Tool, ToolState, ToolCategory, ToolDefinition


class LineTool(Tool):
    """Tool for drawing straight lines"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="LINE",
            name="Line Tool",
            category=ToolCategory.LINES,
            icon="tool-line",
            cursor="crosshair",
            is_creator=True,
            node_info=["Start Point", "End Point"]
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
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the line being created"""
        # Clear previous preview
        self.clear_temp_objects()

        if len(self.points) == 1:
            # Get the snapped point based on current snap settings
            point = self.get_snap_point(current_x, current_y)

            # Draw temporary line
            start_point = self.points[0]
            preview_id = self.canvas.create_line(
                start_point.x, start_point.y,
                point.x, point.y,
                fill="blue", dash=(4, 4)  # Dashed line for preview
            )
            self.temp_objects.append(preview_id)

    def create_object(self) -> Optional[CADObject]:
        """Create a line object from the collected points"""
        if len(self.points) != 2:
            return None

        # Create a line object
        obj = CADObject(
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.LINE,
            layer=self.document.objects.current_layer,
            coords=self.points.copy(),
            attributes={
                'color': 'black',  # Default color
                'linewidth': 1     # Default line width
            }
        )
        return obj
