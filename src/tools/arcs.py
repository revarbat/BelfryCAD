"""
Arc Drawing Tool Implementation

This module implements various arc drawing tools based on the original TCL
tools_arcs.tcl implementation.
"""

import math
from typing import Optional, Tuple, List

from PySide6.QtWidgets import (QGraphicsLineItem, QGraphicsTextItem,
                               QGraphicsPathItem, QGraphicsEllipseItem)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QColor, QPainterPath, QBrush

from src.core.cad_objects import CADObject, ObjectType, Point
from src.tools.base import Tool, ToolState, ToolCategory, ToolDefinition


class ArcObject(CADObject):
    """Arc object - center, start angle, end angle, radius"""

    def __init__(self, object_id: int, center: Point, radius: float,
                 start_angle: float, end_angle: float, **kwargs):
        super().__init__(object_id, ObjectType.ARC, coords=[center], **kwargs)
        self.attributes.update({
            'radius': radius,
            'start_angle': start_angle,
            'end_angle': end_angle
        })

    @property
    def center(self) -> Point:
        return self.coords[0]

    @property
    def radius(self) -> float:
        return self.attributes['radius']

    @property
    def start_angle(self) -> float:
        return self.attributes['start_angle']

    @property
    def end_angle(self) -> float:
        return self.attributes['end_angle']


class ArcCenterTool(Tool):
    """Tool for drawing arcs by center point, start point, and end point."""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition."""
        return [ToolDefinition(
            token="ARCCTR",
            name="Arc by Center",
            category=ToolCategory.ARCS,
            icon="tool-arcctr",
            cursor="crosshair",
            is_creator=True,
            node_info=["Center Point", "Start Point", "End Point"]
        )]

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        # In Qt, event handling is done differently - these will be connected
        # in the main window or graphics view
        pass
        """Set up mouse and keyboard event bindings."""

    def handle_escape(self, event):
        """Handle escape key to cancel the operation."""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event."""
        # Get the snapped point based on current snap settings
        point = self.get_snap_point(event.x, event.y)
        if self.state == ToolState.ACTIVE:
            # First point - center of arc
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING and len(self.points) == 1:
            # Second point - start point of arc
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
            # Drawing from center to start point
            center = self.points[0]

            # Draw temporary line from center to current point
            line_item = QGraphicsLineItem(center.x, center.y, point.x, point.y)
            pen = QPen(QColor("blue"))
            pen.setStyle(Qt.DashLine)
            line_item.setPen(pen)
            self.scene.addItem(line_item)
            self.temp_objects.append(line_item)

            # Draw radius indicator
            radius = math.sqrt(
                (point.x - center.x)**2 + (point.y - center.y)**2
            )
            text_item = QGraphicsTextItem(f"R={radius:.1f}")
            text_item.setDefaultTextColor(QColor("blue"))
            text_item.setPos((center.x + point.x) / 2,
                             (center.y + point.y) / 2)
            self.scene.addItem(text_item)
            self.temp_objects.append(text_item)

        elif len(self.points) == 2:
            # Drawing from center to end point
            center = self.points[0]
            start = self.points[1]

            # Calculate start angle and radius
            radius = math.sqrt(
                (start.x - center.x)**2 + (start.y - center.y)**2
            )
            start_angle = math.atan2(start.y - center.y, start.x - center.x)
            end_angle = math.atan2(point.y - center.y, point.x - center.x)

            # Draw temporary arc
            self._draw_arc_preview(center, radius, start_angle, end_angle)

            # Draw control lines
            line1_item = QGraphicsLineItem(center.x, center.y, start.x, start.y)
            pen1 = QPen(QColor("blue"))
            pen1.setStyle(Qt.DashLine)
            line1_item.setPen(pen1)
            self.scene.addItem(line1_item)

            line2_item = QGraphicsLineItem(center.x, center.y, point.x, point.y)
            pen2 = QPen(QColor("blue"))
            pen2.setStyle(Qt.DashLine)
            line2_item.setPen(pen2)
            self.scene.addItem(line2_item)

            self.temp_objects.extend([line1_item, line2_item])

    def _draw_arc_preview(self, center: Point, radius: float,
                          start_angle: float, end_angle: float):
        """Draw an arc preview with the given parameters."""
        # Ensure proper arc direction
        if end_angle < start_angle:
            end_angle += 2 * math.pi

        # Create points along the arc
        arc_points = []
        steps = 36  # Number of segments for the arc
        angle_step = (end_angle - start_angle) / steps

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

        center = self.points[0]
        start = self.points[1]
        end = self.points[2]

        # Calculate radius
        radius = math.sqrt(
            (start.x - center.x)**2 + (start.y - center.y)**2
        )

        # Calculate start and end angles
        start_angle = math.atan2(start.y - center.y, start.x - center.x)
        end_angle = math.atan2(end.y - center.y, end.x - center.x)

        # Ensure proper arc direction
        if end_angle < start_angle:
            end_angle += 2 * math.pi

        # Create an arc object
        obj = CADObject(
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.ARC,
            layer=self.document.objects.current_layer,
            coords=[center, start, end],
            attributes={
                'color': 'black',      # Default color
                'linewidth': 1,        # Default line width
                'radius': radius,      # Store the radius
                'start_angle': start_angle,  # Start angle in radians
                'end_angle': end_angle      # End angle in radians
            }
        )
        return obj


class Arc3PointTool(Tool):
    """Tool for drawing arcs through 3 points (start, end, middle)."""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition."""
        return [
            ToolDefinition(
                token="ARC3PT",
                name="Arc by 3 Points",
                category=ToolCategory.ARCS,
                icon="tool-arc3pt-123",
                cursor="crosshair",
                is_creator=True,
                node_info=["Start Point", "Middle Point", "End Point"]
            ),
            ToolDefinition(
                token="ARC3PT",
                name="Arc by 3 Points, Middle Last",
                category=ToolCategory.ARCS,
                icon="tool-arc3pt-132",
                cursor="crosshair",
                is_creator=True,
                node_info=["Start Point", "End Point", "Middle Point"]
            )
        ]

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        # In Qt, event handling is done differently - these will be connected
        # in the main window or graphics view
        pass
        """Set up mouse and keyboard event bindings."""

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
            # Second point - middle point of arc
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

            from PySide6.QtWidgets import QGraphicsLineItem
            from PySide6.QtCore import Qt
            from PySide6.QtGui import QPen, QColor

            line_item = QGraphicsLineItem(start.x, start.y, point.x, point.y)
            pen = QPen(QColor("blue"))
            pen.setStyle(Qt.DashLine)
            line_item.setPen(pen)
            self.scene.addItem(line_item)
            self.temp_objects.append(line_item)

        elif len(self.points) == 2:
            # Have start and middle points, draw arc through these and current
            p1 = self.points[0]  # Start
            p2 = self.points[1]  # Middle
            p3 = point          # End (current mouse position)

            # Calculate center and radius from 3 points
            center, radius = self._calculate_arc_center_radius(p1, p2, p3)

            if center is not None:
                # Calculate start and end angles
                start_angle = math.atan2(p1.y - center.y, p1.x - center.x)
                end_angle = math.atan2(p3.y - center.y, p3.x - center.x)

                # Determine arc direction using middle point
                if not self._is_point_on_arc(p1, p3, p2, center,
                                             start_angle, end_angle):
                    if end_angle < start_angle:
                        end_angle += 2 * math.pi
                    else:
                        end_angle -= 2 * math.pi

                # Draw the preview arc
                self._draw_arc_preview(center, radius, start_angle, end_angle)

                # Draw center point and radius lines for reference
                center_item = QGraphicsEllipseItem(
                    center.x - 3, center.y - 3, 6, 6
                )
                center_item.setPen(QPen(QColor("gray")))
                center_item.setBrush(QBrush(QColor("gray")))
                self.scene.addItem(center_item)

                line1_item = QGraphicsLineItem(center.x, center.y, p1.x, p1.y)
                pen1 = QPen(QColor("gray"))
                pen1.setStyle(Qt.DashLine)
                line1_item.setPen(pen1)
                self.scene.addItem(line1_item)

                line2_item = QGraphicsLineItem(center.x, center.y, p3.x, p3.y)
                pen2 = QPen(QColor("gray"))
                pen2.setStyle(Qt.DashLine)
                line2_item.setPen(pen2)
                self.scene.addItem(line2_item)

                self.temp_objects.extend([center_item, line1_item, line2_item])

    def _calculate_arc_center_radius(
            self, p1: Point, p2: Point, p3: Point
    ) -> Tuple[Optional[Point], float]:
        "Calculate center point and radius of arc passing through 3 points."
        # Check if points are in a straight line (or nearly so)
        epsilon = 1e-10

        # Create line segments
        ax, ay = p2.x - p1.x, p2.y - p1.y
        bx, by = p3.x - p2.x, p3.y - p2.y

        # Check if the points are collinear using cross product
        cross_product = ax * by - ay * bx
        if abs(cross_product) < epsilon:
            # Points are collinear, can't form an arc
            return None, 0.0

        # Use perpendicular bisector method to find center
        # First bisector
        mid1x, mid1y = (p1.x + p2.x) / 2, (p1.y + p2.y) / 2
        slope1 = (-1 / ((p2.y - p1.y) / (p2.x - p1.x))
                  if p2.x != p1.x else 0)

        # Second bisector
        mid2x, mid2y = (p2.x + p3.x) / 2, (p2.y + p3.y) / 2
        slope2 = (-1 / ((p3.y - p2.y) / (p3.x - p2.x))
                  if p3.x != p2.x else 0)

        # Find intersection of bisectors
        if abs(slope1 - slope2) < epsilon:
            return None, 0.0

        # Calculate intersection (center of the circle)
        cx = ((mid2y - mid1y + slope1 * mid1x - slope2 * mid2x) /
              (slope1 - slope2))
        cy = mid1y + slope1 * (cx - mid1x)

        # Calculate radius
        radius = math.sqrt((cx - p1.x)**2 + (cy - p1.y)**2)

        return Point(cx, cy), radius

    def _is_point_on_arc(self, p1: Point, p2: Point, p3: Point,
                         center: Point, start_angle: float,
                         end_angle: float) -> bool:
        """Check if p3 is on the arc defined by p1, p2, and center."""
        angle = math.atan2(p3.y - center.y, p3.x - center.x)

        # Normalize angles
        while start_angle < 0:
            start_angle += 2 * math.pi
        while end_angle < 0:
            end_angle += 2 * math.pi
        while angle < 0:
            angle += 2 * math.pi

        # Check if angle is between start and end
        if start_angle <= end_angle:
            return start_angle <= angle <= end_angle
        else:
            return angle >= start_angle or angle <= end_angle

    def _draw_arc_preview(self, center: Point, radius: float,
                          start_angle: float, end_angle: float):
        """Draw an arc preview with the given parameters."""
        # Create points along the arc
        arc_points = []

        # Determine arc direction and step
        if end_angle < start_angle:
            start_angle, end_angle = end_angle, start_angle

        steps = 36  # Number of segments for the arc
        angle_diff = end_angle - start_angle
        if angle_diff < 0:
            angle_diff += 2 * math.pi
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

        p1 = self.points[0]  # Start
        p2 = self.points[1]  # Middle
        p3 = self.points[2]  # End

        # Calculate center and radius
        center, radius = self._calculate_arc_center_radius(p1, p2, p3)

        if center is None:
            return None

        # Calculate start and end angles
        start_angle = math.atan2(p1.y - center.y, p1.x - center.x)
        end_angle = math.atan2(p3.y - center.y, p3.x - center.x)

        # Determine arc direction using middle point
        if not self._is_point_on_arc(p1, p3, p2, center,
                                     start_angle, end_angle):
            if end_angle < start_angle:
                end_angle += 2 * math.pi
            else:
                end_angle -= 2 * math.pi

        # Create an arc object
        obj = CADObject(
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.ARC,
            layer=self.document.objects.current_layer,
            coords=[center, p1, p3],  # Center, start, end
            attributes={
                'color': 'black',      # Default color
                'linewidth': 1,        # Default line width
                'radius': radius,      # Store the radius
                'start_angle': start_angle,  # Start angle in radians
                'end_angle': end_angle,      # End angle in radians
                'middle_point': p2      # Store middle point for reference
            }
        )
        return obj
