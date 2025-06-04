"""
Arc Tangent Tool Implementation

This module implements the ARCTAN tool for drawing arcs tangent to a line.
"""

import math
from typing import Optional, Tuple, List

from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsEllipseItem
from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QColor, QPainterPath, QBrush

from src.core.cad_objects import CADObject, ObjectType, Point
from src.tools.base import Tool, ToolState, ToolCategory, ToolDefinition


class ArcTangentTool(Tool):
    """Tool for drawing arcs by tangent to a line."""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition."""
        return [ToolDefinition(
            token="ARCTAN",
            name="Arc by Tangent",
            category=ToolCategory.ARCS,
            icon="tool-arctan",
            cursor="crosshair",
            is_creator=True,
            node_info=["Starting Point", "Tangent Line Point", "Ending Point"]
        )]

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        pass

    def handle_escape(self, event):
        """Handle escape key to cancel the operation."""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event."""
        # Get the snapped point based on current snap settings
        point = self.get_snap_point(event.x, event.y)

        if self.state == ToolState.ACTIVE:
            # First point - start of arc
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING and len(self.points) == 1:
            # Second point - tangent line point
            self.points.append(point)
        elif self.state == ToolState.DRAWING and len(self.points) == 2:
            # Third point - end point of arc
            self.points.append(point)
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event."""
        if self.state == ToolState.DRAWING:
            # Draw preview arc
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the arc being created."""
        # Clear previous preview
        self.clear_temp_objects()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(current_x, current_y)

        if len(self.points) == 1:
            # Only have start point, draw line to current point
            start = self.points[0]

            line_item = QGraphicsLineItem(start.x, start.y, point.x, point.y)
            pen = QPen(QColor("blue"))
            pen.setStyle(Qt.DashLine)
            line_item.setPen(pen)
            self.scene.addItem(line_item)
            self.temp_objects.append(line_item)

        elif len(self.points) == 2:
            # Have start and tangent points, draw tangent line and arc preview
            start_point = self.points[0]
            tangent_point = self.points[1]
            end_point = point

            # Draw tangent line through tangent point
            tangent_line_item = QGraphicsLineItem(
                tangent_point.x - 50, tangent_point.y - 50,
                tangent_point.x + 50, tangent_point.y + 50
            )
            pen_tangent = QPen(QColor("gray"))
            pen_tangent.setStyle(Qt.DashLine)
            tangent_line_item.setPen(pen_tangent)
            self.scene.addItem(tangent_line_item)
            self.temp_objects.append(tangent_line_item)

            # Calculate and draw arc that's tangent to the line
            arc_params = self._calculate_tangent_arc(
                start_point, tangent_point, end_point
            )
            if arc_params is not None:
                center, radius, start_angle, end_angle = arc_params
                self._draw_arc_preview(center, radius, start_angle, end_angle)

                # Draw center and radius lines for reference
                center_item = QGraphicsEllipseItem(
                    center.x - 3, center.y - 3, 6, 6
                )
                center_item.setPen(QPen(QColor("gray")))
                center_item.setBrush(QBrush(QColor("gray")))
                self.scene.addItem(center_item)

                line1_item = QGraphicsLineItem(
                    center.x, center.y, start_point.x, start_point.y
                )
                line2_item = QGraphicsLineItem(
                    center.x, center.y, end_point.x, end_point.y
                )
                pen_gray = QPen(QColor("gray"))
                pen_gray.setStyle(Qt.DashLine)
                line1_item.setPen(pen_gray)
                line2_item.setPen(pen_gray)
                self.scene.addItem(line1_item)
                self.scene.addItem(line2_item)

                self.temp_objects.extend([center_item, line1_item, line2_item])

    def _calculate_tangent_arc(self, start_point: Point, tangent_point: Point,
                               end_point: Point) -> Optional[
                                   Tuple[Point, float, float, float]
                               ]:
        """Calculate arc params for arc tangent to line through tangent_pt."""

        # For simplicity, assume tangent line passes through tangent point
        # In full implementation, this would handle arbitrary tangent lines.

        # Calculate midpoint between start and end
        mid_x = (start_point.x + end_point.x) / 2
        mid_y = (start_point.y + end_point.y) / 2

        # Distance from start to end
        chord_length = math.sqrt(
            (end_point.x - start_point.x)**2 +
            (end_point.y - start_point.y)**2
        )

        if chord_length < 1e-6:
            return None

        # For simple tangent arc, create circular arc where tangent point
        # influences the arc's curvature

        # Distance from chord midpoint to tangent point influences height
        tangent_dist = math.sqrt(
            (tangent_point.x - mid_x)**2 +
            (tangent_point.y - mid_y)**2
        )

        # Use tangent distance to determine arc height (simplified approach)
        arc_height = min(tangent_dist, chord_length / 2)

        # Calculate radius using relationship between chord length and height
        if arc_height < 1e-6:
            arc_height = chord_length / 8  # Default shallow arc

        radius = (chord_length**2 + 4 * arc_height**2) / (8 * arc_height)

        # Calculate center position
        # The center lies on the perpendicular bisector of the chord
        chord_angle = math.atan2(
            end_point.y - start_point.y, end_point.x - start_point.x
        )
        perp_angle = chord_angle + math.pi / 2

        # Determine which side of chord center should be on
        center_dist = radius - arc_height

        # Check which side of the chord the tangent point is on
        cross_product = (
            (end_point.x - start_point.x) * (tangent_point.y - start_point.y) -
            (end_point.y - start_point.y) * (tangent_point.x - start_point.x)
        )

        if cross_product < 0:
            center_dist = -center_dist

        center_x = mid_x + center_dist * math.cos(perp_angle)
        center_y = mid_y + center_dist * math.sin(perp_angle)
        center = Point(center_x, center_y)

        # Calculate start and end angles
        start_angle = math.atan2(
            start_point.y - center_y, start_point.x - center_x
        )
        end_angle = math.atan2(end_point.y - center_y, end_point.x - center_x)

        return center, radius, start_angle, end_angle

    def _draw_arc_preview(self, center: Point, radius: float,
                          start_angle: float, end_angle: float):
        """Draw an arc preview with the given parameters."""
        # Ensure proper arc direction
        angle_diff = end_angle - start_angle
        if angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        elif angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        # Create points along the arc
        arc_points = []
        steps = 36  # Number of segments for the arc
        angle_step = angle_diff / steps

        for i in range(steps + 1):
            angle = start_angle + i * angle_step
            x = center.x + radius * math.cos(angle)
            y = center.y + radius * math.sin(angle)
            arc_points.extend([x, y])

        if len(arc_points) >= 4:  # Need at least 2 points (4 coordinates)
            # Create a path for the arc
            path = QPainterPath()
            path.moveTo(arc_points[0], arc_points[1])
            for i in range(2, len(arc_points), 2):
                path.lineTo(arc_points[i], arc_points[i + 1])

            path_item = QGraphicsPathItem(path)
            pen = QPen(QColor("blue"))
            pen.setStyle(Qt.DashLine)
            path_item.setPen(pen)
            self.scene.addItem(path_item)
            self.temp_objects.append(path_item)

    def create_object(self) -> Optional[CADObject]:
        """Create an arc object from the collected points."""
        if len(self.points) != 3:
            return None

        start_point = self.points[0]
        tangent_point = self.points[1]
        end_point = self.points[2]

        # Calculate arc parameters
        arc_params = self._calculate_tangent_arc(
            start_point, tangent_point, end_point
        )
        if arc_params is None:
            return None

        center, radius, start_angle, end_angle = arc_params

        # Create an arc object
        obj = CADObject(
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.ARC,
            layer=self.document.objects.current_layer,
            coords=[center, start_point, end_point],  # Center, start, end
            attributes={
                'color': 'black',      # Default color
                'linewidth': 1,        # Default line width
                'radius': radius,      # Store the radius
                'start_angle': start_angle,  # Start angle in radians
                'end_angle': end_angle,      # End angle in radians
                'tangent_point': tangent_point  # Store tangent point
            }
        )
        return obj
