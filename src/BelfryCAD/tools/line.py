"""
Line Drawing CadTool Implementation

This module implements a line drawing tool based on the TCL
tool implementation.
"""

from typing import Optional, List
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPen, QColor
from PySide6.QtWidgets import QGraphicsLineItem

from ..models.cad_object import CadObject, ObjectType, Point2D
from ..models.cad_objects.line_cad_object import LineCadObject
from .base import CadTool, ToolState, ToolCategory, ToolDefinition


class LineTool(CadTool):
    """CadTool for drawing straight lines"""

    # Class-level tool definition
    tool_definitions = [
        ToolDefinition(
            token="LINE",
            name="Lines",
            category=ToolCategory.LINES,
            icon="tool-lines",
            cursor="crosshair",
            is_creator=True,
            secondary_key="L",
            node_info=["Start Point2D", "End Point2D"]
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
            # First point - start drawing
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING:
            # Second point - complete the line
            self.points.append(point)
            self.complete()  # Complete this line segment
            self.points = [point]  # Start a new line segment from here
            self.state = ToolState.DRAWING

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


class LineMPTool(CadTool):
    """CadTool for creating lines from midpoint and endpoint"""

    # Class-level tool definition
    tool_definitions = [
        ToolDefinition(
            token="LINEMP",
            name="Midpoint Line",
            category=ToolCategory.LINES,
            icon="tool-linemp",
            cursor="crosshair",
            is_creator=True,
            secondary_key="M",
            node_info=["Midpoint", "Endpoint"]
        ),
        ToolDefinition(
            token="LINEMP21",
            name="Midpoint Line, End First",
            category=ToolCategory.LINES,
            icon="tool-linemp21",
            cursor="crosshair",
            is_creator=True,
            node_info=["Endpoint", "Midpoint"]
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
            # First point
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

            # Determine which point is midpoint and which is endpoint based on tool variant
            first_point = self.points[0]
            second_point = point

            # Check which tool variant is active based on the current definition
            # Default to standard variant (first point is midpoint)
            is_end_first = False
            if hasattr(self, 'definition') and self.definition and self.definition.token == "LINEMP21":
                is_end_first = True

            if is_end_first:
                # End First variant: first point is endpoint, second is midpoint
                endpoint = first_point
                midpoint = second_point
            else:
                # Standard variant: first point is midpoint, second is endpoint
                midpoint = first_point
                endpoint = second_point

            # Calculate the start point (extend from midpoint in opposite direction)
            # start_point = midpoint - (endpoint - midpoint) = 2*midpoint - endpoint
            start_x = 2 * midpoint.x - endpoint.x
            start_y = 2 * midpoint.y - endpoint.y
            start_point = Point2D(start_x, start_y)

            # Draw temporary full line from start to end
            pen = QPen(QColor("black"), 3.0)
            pen.setCosmetic(True)
            pen.setDashPattern([4, 4])  # Dashed line for preview

            preview_line = self.scene.addLine(
                start_point.x, start_point.y,
                endpoint.x, endpoint.y,
                pen
            )
            self.temp_objects.append(preview_line)

        self.draw_points()

    def create_object(self) -> Optional[CadObject]:
        """Create a line object from the collected points"""
        if len(self.points) != 2:
            return None

        # Determine which point is midpoint and which is endpoint based on tool variant
        midpt = self.points[0]
        startpt = self.points[1]
        endpt = midpt + (midpt - startpt)

        # Create a standard line object from start to end
        line = LineCadObject(
            document=self.document,
            start_point=startpt,
            end_point=endpt,
            color=self.preferences.get("default_color", "black"),
            line_width=self.preferences.get("default_line_width", 0.05)
        )
        return line
