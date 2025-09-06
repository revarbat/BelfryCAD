"""
Arc Drawing CadTool Implementation

This module implements various arc drawing tools based on the original TCL
tools_arcs.tcl implementation.
"""

import math
from typing import Optional, Tuple, List

from PySide6.QtWidgets import (QGraphicsLineItem, QGraphicsTextItem,
                               QGraphicsPathItem, QGraphicsEllipseItem)
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QColor, QPainterPath, QBrush

from ..models.cad_objects.arc_cad_object import ArcCadObject
from ..cad_geometry import Point2D, Circle

from .base import CadTool, ToolState, ToolCategory, ToolDefinition
from ..models.cad_object import CadObject, ObjectType


class ArcCenterTool(CadTool):
    """CadTool for drawing arcs by center point, start point, and end point."""

    # Class-level tool definition
    tool_definitions = [
        ToolDefinition(
            token="ARCCTR",
            name="Arc by Center",
            category=ToolCategory.ARCS,
            icon="tool-arcctr",
            cursor="crosshair",
            is_creator=True,
            secondary_key="C",
            node_info=["Center Point", "Start Point", "End Point"]
        )
    ]

    def handle_escape(self, event):
        """Handle escape key to cancel the operation."""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event."""
        # Convert Qt event coordinates to scene coordinates
        if hasattr(event, 'scenePos'):
            scene_pos = event.scenePos()
        else:
            scene_pos = QPointF(event.x, event.y)

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(scene_pos.x(), scene_pos.y())

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
            if hasattr(event, 'scenePos'):
                scene_pos = event.scenePos()
            else:
                scene_pos = QPointF(event.x, event.y)
            self.draw_preview(scene_pos.x(), scene_pos.y())

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the arc being created."""
        # Clear previous preview
        self.clear_temp_objects()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(current_x, current_y)

        pen = QPen(QColor("black"), 3.0)
        pen.setCosmetic(True)
        pen.setStyle(Qt.PenStyle.DashLine)

        pen_gray = QPen(QColor("gray"), 3.0)
        pen_gray.setCosmetic(True)
        pen_gray.setStyle(Qt.PenStyle.DashLine)

        if len(self.points) == 1:
            # Drawing from center to start point
            center = self.points[0]

            # Draw temporary line from center to current point
            line_item = self.scene.addLine(
                center.x, center.y, point.x, point.y,
                pen
            )
            self.temp_objects.append(line_item)

        elif len(self.points) == 2:
            # Drawing from center to end point
            center = self.points[0]
            start = self.points[1]

            # Calculate start angle and radius
            radius = math.sqrt(
                (start.x - center.x)**2 + (start.y - center.y)**2
            )
            start_degrees = math.degrees(math.atan2(start.y - center.y, start.x - center.x))
            end_degrees = math.degrees(math.atan2(point.y - center.y, point.x - center.x))
            span_degrees = end_degrees - start_degrees
            if span_degrees < 0:
                span_degrees += 360.0

            # Draw temporary arc
            arc_item = self.scene.addArc(
                center.to_qpointf(), radius,
                start_degrees, span_degrees, pen=pen)
            self.temp_objects.append(arc_item)

            # Draw control lines
            line1_item = self.scene.addLine(
                center.x, center.y, start.x, start.y,
                pen_gray
            )
            end_angle = math.degrees(math.atan2(point.y - center.y, point.x - center.x))
            end_point = center +Point2D(radius, angle=end_angle)
            line2_item = self.scene.addLine(
                center.x, center.y, end_point.x, end_point.y,
                pen_gray
            )

            self.temp_objects.extend([line1_item, line2_item])

        self.draw_points()

    def create_object(self) -> Optional[CadObject]:
        """Create an arc object from the collected points."""
        if len(self.points) != 3:
            return None

        center = self.points[0]
        start = self.points[1]
        end = self.points[2]

        if start == end or center == start or center == end:
            return None

        # Calculate radius and angles
        radius = center.distance_to(start)
        start_degrees = (start - center).angle_degrees
        end_degrees = (end - center).angle_degrees
        span_degrees = end_degrees - start_degrees
        
        # Normalize span angle to handle wraparound cases
        if span_degrees < 0.0:
            span_degrees += 360.0

        # Create an arc object
        obj = ArcCadObject(
            document=self.document,
            center_point=center,
            radius=radius,
            start_degrees=start_degrees,
            span_degrees=span_degrees,
        )
        return obj


class Arc3PointTool(CadTool):
    """CadTool for drawing arcs through 3 points (start, end, middle)."""

    # Class-level tool definition
    tool_definitions = [
        ToolDefinition(
            token="ARC3PT",
            name="Arc by 3 Points",
            category=ToolCategory.ARCS,
            icon="tool-arc3pt-123",
            cursor="crosshair",
            is_creator=True,
            secondary_key="3",
            node_info=["Start Point", "Middle Point", "End Point"]
        ),
        ToolDefinition(
            token="ARC3PTLAST",
            name="Arc by 3 Points, Middle Last",
            category=ToolCategory.ARCS,
            icon="tool-arc3pt-132",
            cursor="crosshair",
            is_creator=True,
            secondary_key="M",
            node_info=["Start Point", "End Point", "Middle Point"]
        )
    ]

    def handle_escape(self, event):
        """Handle escape key to cancel the operation."""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event."""
        # Convert Qt event coordinates to scene coordinates
        if hasattr(event, 'scenePos'):
            scene_pos = event.scenePos()
        else:
            scene_pos = QPointF(event.x, event.y)

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(scene_pos.x(), scene_pos.y())

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
            if hasattr(event, 'scenePos'):
                scene_pos = event.scenePos()
            else:
                scene_pos = QPointF(event.x, event.y)
            self.draw_preview(scene_pos.x(), scene_pos.y())

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the arc being created."""
        # Clear previous preview
        self.clear_temp_objects()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(current_x, current_y)

        pen = QPen(QColor("black"), 3.0)
        pen.setCosmetic(True)
        pen.setStyle(Qt.PenStyle.DashLine)

        pen_gray = QPen(QColor("#cccccc"), 3.0)
        pen_gray.setCosmetic(True)
        pen_gray.setStyle(Qt.PenStyle.DashLine)

        if len(self.points) == 1:
            # Only have start point, draw line to current point
            start = self.points[0]
            line_item = self.scene.addLine(
                start.x, start.y, point.x, point.y,
                pen
            )
            self.temp_objects.append(line_item)

        elif len(self.points) == 2:
            # Have start and middle points, draw arc through these and current
            p1 = self.points[0]  # Start
            p2 = self.points[1]  # Middle
            p3 = point          # End (current mouse position)

            # Calculate center and radius from 3 points
            circle = Circle.from_3_points([p1, p2, p3])
            if circle is not None:
                center = circle.center
                radius = circle.radius

                # Calculate start and end angles
                start_degrees = (p1 - center).angle_degrees
                p2_degrees = (p2 - center).angle_degrees
                p3_degrees = (p3 - center).angle_degrees
                if p2_degrees < start_degrees:
                    p2_degrees += 360.0
                if p3_degrees < start_degrees:
                    p3_degrees += 360.0
                if p3_degrees > p2_degrees:
                    end_degrees = p3_degrees
                    end_point = p3
                else:
                    end_degrees = p2_degrees
                    end_point = p2

                span_degrees = end_degrees - start_degrees

                # Draw the preview arc
                arc_item = self.scene.addArc(
                    center.to_qpointf(), radius,
                    start_degrees, span_degrees,
                    pen=pen
                )
                self.temp_objects.append(arc_item)

                line1_item = self.scene.addLine(
                    center.x, center.y, p1.x, p1.y,
                    pen=pen_gray
                )
                self.temp_objects.append(line1_item)

                line2_item = self.scene.addLine(
                    center.x, center.y, end_point.x, end_point.y,
                    pen=pen_gray
                )
                self.temp_objects.append(line2_item)

        self.draw_points()

    def create_object(self) -> Optional[CadObject]:
        """Create an arc object from the collected points."""
        if len(self.points) != 3:
            return None

        p1 = self.points[0]  # Start
        p2 = self.points[1]  # Middle
        p3 = self.points[2]  # End

        # Calculate center and radius
        circle = Circle.from_3_points([p1, p2, p3])
        if circle is None:
            return None

        center = circle.center
        radius = circle.radius
        start_degrees = (p1 - center).angle_degrees
        p2_degrees = (p2 - center).angle_degrees
        p3_degrees = (p3 - center).angle_degrees

        # Normalize angles
        while p2_degrees < start_degrees:
            p2_degrees += 360.0
        while p3_degrees < start_degrees:
            p3_degrees += 360.0
        end_degrees = p2_degrees if p2_degrees > p3_degrees else p3_degrees
        span_degrees = end_degrees - start_degrees

        # Create an arc object
        obj = ArcCadObject(
            document=self.document,
            center_point=center,
            radius=radius,
            start_degrees=start_degrees,
            span_degrees=span_degrees,
        )
        return obj


class ArcTangentTool(CadTool):
    """CadTool for drawing arcs by tangent to a line."""

    # Class-level tool definition
    tool_definitions = [
        ToolDefinition(
            token="ARCTAN",
            name="Arc by Tangent",
            category=ToolCategory.ARCS,
            icon="tool-arctan",
            cursor="crosshair",
            is_creator=True,
            secondary_key="T",
            node_info=["Starting Point", "Tangent Line Point", "Ending Point"]
        )
    ]

    def handle_escape(self, event):
        """Handle escape key to cancel the operation."""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event."""
        # Convert Qt event coordinates to scene coordinates
        if hasattr(event, 'scenePos'):
            scene_pos = event.scenePos()
        else:
            scene_pos = QPointF(event.x, event.y)

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(scene_pos.x(), scene_pos.y())

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
            if hasattr(event, 'scenePos'):
                scene_pos = event.scenePos()
            else:
                scene_pos = QPointF(event.x, event.y)
            self.draw_preview(scene_pos.x(), scene_pos.y())

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the arc being created."""
        # Clear previous preview
        self.clear_temp_objects()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(current_x, current_y)

        pen = QPen(QColor("black"), 3.0)
        pen.setCosmetic(True)
        pen.setStyle(Qt.PenStyle.DashLine)

        pen_gray = QPen(QColor("gray"), 3.0)
        pen_gray.setCosmetic(True)
        pen_gray.setStyle(Qt.PenStyle.DashLine)

        if len(self.points) == 1:
            # Only have start point, draw line to current point
            start = self.points[0]

            line_item = self.scene.addLine(
                start.x, start.y, point.x, point.y,
                pen
            )
            self.temp_objects.append(line_item)

        elif len(self.points) == 2:
            # Have start and tangent points, draw tangent line and arc preview
            start_point = self.points[0]
            tangent_point = self.points[1]
            end_point = point

            # Draw tangent line through tangent point
            tangent_line_item = self.scene.addLine(
                tangent_point.x - 50, tangent_point.y - 50,
                tangent_point.x + 50, tangent_point.y + 50,
                pen_gray
            )
            self.temp_objects.append(tangent_line_item)

            # Calculate and draw arc that's tangent to the line
            arc_params = self._calculate_tangent_arc(
                start_point, tangent_point, end_point
            )
            if arc_params is not None:
                center, radius, start_degrees, end_degrees = arc_params

                arc_item = self.scene.addArc(
                    center.to_qpointf(), radius,
                    start_degrees, end_degrees, pen=pen)
                self.temp_objects.append(arc_item)

                line1_item = self.scene.addLine(
                    center.x, center.y, start_point.x, start_point.y,
                    pen_gray
                )
                self.temp_objects.append(line1_item)

                line2_item = self.scene.addLine(
                    center.x, center.y, end_point.x, end_point.y,
                    pen_gray
                )
                self.temp_objects.append(line2_item)

        self.draw_points()

    def _calculate_tangent_arc(self, start_point: Point2D, tangent_point: Point2D,
                               end_point: Point2D) -> Optional[
                                   Tuple[Point2D, float, float, float]
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
        center = Point2D(center_x, center_y)

        # Calculate start and end angles
        start_degrees = (start_point - center).angle_degrees
        end_degrees = (end_point - center).angle_degrees

        return center, radius, start_degrees, end_degrees

    def create_object(self) -> Optional[CadObject]:
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

        center, _, _, _ = arc_params

        # Calculate radius and angles
        radius = center.distance_to(start_point)
        start_degrees = (start_point - center).angle_degrees
        end_degrees = (end_point - center).angle_degrees
        span_degrees = end_degrees - start_degrees
        
        # Normalize span angle to handle wraparound cases
        if span_degrees > 180.0:
            span_degrees -= 360.0
        elif span_degrees < -180.0:
            span_degrees += 360.0

        # Create an arc object
        obj = ArcCadObject(
            document=self.document,
            center_point=center,
            radius=radius,
            start_degrees=start_degrees,
            span_degrees=span_degrees,
        )
        return obj
