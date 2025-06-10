"""
Line Midpoint Tool Implementation

This module implements the LINEMP tool based on the original TCL
tools_lines.tcl implementation. The tool creates a line from a midpoint
and endpoint by extending the line mathematically.
"""

from typing import Optional, List
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPen, QColor
from PySide6.QtWidgets import QGraphicsLineItem

from BelfryCAD.core.cad_objects import CADObject, ObjectType, Point
from BelfryCAD.tools.base import Tool, ToolState, ToolCategory, ToolDefinition


class LineMPObject(CADObject):
    """Line Midpoint object - stores midpoint and endpoint, renders as full line"""

    def __init__(self, object_id: int, midpoint: Point, endpoint: Point, **kwargs):
        # Calculate the extended endpoint: extended_point = midpoint + 2*(endpoint - midpoint)
        extended_x = (endpoint.x - midpoint.x) * 2.0 + midpoint.x
        extended_y = (endpoint.y - midpoint.y) * 2.0 + midpoint.y
        extended_point = Point(extended_x, extended_y)

        # Store the full line (midpoint to extended endpoint)
        super().__init__(
            object_id, ObjectType.LINE, coords=[midpoint, extended_point], **kwargs)

        # Store the original control points for editing
        self.midpoint = midpoint
        self.endpoint = endpoint

    @property
    def start(self) -> Point:
        """Start point of the full line"""
        return self.coords[0]

    @property
    def end(self) -> Point:
        """End point of the full line"""
        return self.coords[1]

    def length(self) -> float:
        """Length of the full line"""
        return self.start.distance_to(self.end) * 2.0

    def get_field(self, field_name: str) -> Optional[float]:
        """Get field values for LENGTH and ANGLE (matching TCL implementation)"""
        if field_name == "LENGTH":
            # Length is distance * 2.0 (from midpoint to endpoint)
            return self.midpoint.distance_to(self.endpoint) * 2.0
        elif field_name == "ANGLE":
            # Angle from midpoint to endpoint
            import math
            dx = self.endpoint.x - self.midpoint.x
            dy = self.endpoint.y - self.midpoint.y
            return math.degrees(math.atan2(dy, dx))
        return None

    def set_field(self, field_name: str, value: float):
        """Set field values for LENGTH and ANGLE (matching TCL implementation)"""
        if field_name == "LENGTH":
            # Calculate new endpoint based on length
            import math
            current_angle = self.get_field("ANGLE")
            if current_angle is not None:
                # Half the length since we measure from midpoint to endpoint
                radius = value / 2.0
                angle_rad = math.radians(current_angle)
                new_endpoint_x = self.midpoint.x + radius * math.cos(angle_rad)
                new_endpoint_y = self.midpoint.y + radius * math.sin(angle_rad)
                self.endpoint = Point(new_endpoint_x, new_endpoint_y)
                self._update_coords()
        elif field_name == "ANGLE":
            # Calculate new endpoint based on angle
            import math
            current_length = self.get_field("LENGTH")
            if current_length is not None:
                radius = current_length / 2.0
                angle_rad = math.radians(value)
                new_endpoint_x = self.midpoint.x + radius * math.cos(angle_rad)
                new_endpoint_y = self.midpoint.y + radius * math.sin(angle_rad)
                self.endpoint = Point(new_endpoint_x, new_endpoint_y)
                self._update_coords()

    def _update_coords(self):
        """Update the full line coordinates after field changes"""
        extended_x = (self.endpoint.x - self.midpoint.x) * \
            2.0 + self.midpoint.x
        extended_y = (self.endpoint.y - self.midpoint.y) * \
            2.0 + self.midpoint.y
        extended_point = Point(extended_x, extended_y)
        self.coords = [self.midpoint, extended_point]

    def get_points_of_interest(self) -> List[Point]:
        """Get control points and midpoint (matching TCL implementation)"""
        return [self.midpoint, self.endpoint, self.midpoint]  # Midpoint listed twice as in TCL


class LineMPTool(Tool):
    """Tool for creating lines from midpoint and endpoint"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [
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
            if hasattr(self, 'definition') and self.definition.token == "LINEMP21":
                # End First variant: first point is endpoint, second is midpoint
                endpoint = first_point
                midpoint = second_point
            else:
                # Standard variant: first point is midpoint, second is endpoint
                midpoint = first_point
                endpoint = second_point

            # Calculate the extended endpoint to show the full line
            extended_x = (endpoint.x - midpoint.x) * 2.0 + midpoint.x
            extended_y = (endpoint.y - midpoint.y) * 2.0 + midpoint.y

            # Draw temporary full line
            pen = QPen(QColor("blue"))
            pen.setDashPattern([4, 4])  # Dashed line for preview

            preview_line = self.scene.addLine(
                midpoint.x, midpoint.y,
                extended_x, extended_y,
                pen
            )
            self.temp_objects.append(preview_line)

            # Draw control points for clarity
            control_pen = QPen(QColor("red"))
            control_pen.setWidth(2)

            # Midpoint marker (circle)
            midpoint_marker = self.scene.addEllipse(
                midpoint.x - 2, midpoint.y - 2, 4, 4,
                control_pen
            )
            self.temp_objects.append(midpoint_marker)

            # Endpoint marker (square)
            endpoint_marker = self.scene.addRect(
                endpoint.x - 2, endpoint.y - 2, 4, 4,
                control_pen
            )
            self.temp_objects.append(endpoint_marker)

    def create_object(self) -> Optional[CADObject]:
        """Create a line midpoint object from the collected points"""
        if len(self.points) != 2:
            return None

        # Determine which point is midpoint and which is endpoint based on tool variant
        first_point = self.points[0]
        second_point = self.points[1]

        # Check which tool variant was used based on the current definition
        if hasattr(self, 'definition') and self.definition.token == "LINEMP21":
            # End First variant: first point is endpoint, second is midpoint
            endpoint = first_point
            midpoint = second_point
        else:
            # Standard variant: first point is midpoint, second is endpoint
            midpoint = first_point
            endpoint = second_point

        # Create a line midpoint object
        obj = LineMPObject(
            object_id=self.document.objects.get_next_id(),
            midpoint=midpoint,
            endpoint=endpoint,
            layer=self.document.objects.current_layer,
            attributes={
                'color': 'black',  # Default color
                'linewidth': 1     # Default line width
            }
        )
        return obj
