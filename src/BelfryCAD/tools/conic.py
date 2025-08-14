"""
Conic Tools Implementation

This module implements conic section drawing tools based on the original TCL
tools_conics.tcl implementation.
"""

import math
from typing import Optional, List

from PySide6.QtWidgets import (QGraphicsLineItem, QGraphicsEllipseItem,
                               QGraphicsPathItem)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QColor, QPainterPath, QBrush

from ..models.cad_object import CadObject, ObjectType
from ..cad_geometry import Point2D
from .base import Tool, ToolState, ToolCategory, ToolDefinition


class Conic2PointTool(Tool):
    """Tool for drawing conic sections by 2 points"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="CONIC2PT",
            name="Conic Section by 2 Points",
            category=ToolCategory.ARCS,
            icon="tool-conic2pt",
            cursor="crosshair",
            is_creator=True,
            secondary_key="2",
            node_info=["Starting Point2D", "Ending Point2D"]
        )]

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
        # Get the snapped point based on current snap settings
        point = self.get_snap_point(event.x, event.y)

        if self.state == ToolState.ACTIVE:
            # First point - start of conic
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING and len(self.points) == 1:
            # Second point - end of conic
            self.points.append(point)
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            # Draw preview conic
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the conic being created"""
        # Clear previous preview
        self.clear_temp_objects()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(current_x, current_y)

        if len(self.points) == 1:
            # Drawing from start to end point
            start = self.points[0]
            end = point

            # Calculate conic parameters
            rad_x = abs(end.x - start.x)
            rad_y = abs(end.y - start.y)

            # Determine center and start/extent angles based on point positions
            if start.x > end.x:
                if start.y < end.y:
                    cx, cy = start.x, end.y
                    start_angle, extent_angle = -90.0, -90.0
                else:
                    cx, cy = start.x, end.y
                    start_angle, extent_angle = 90.0, 90.0
            else:
                if start.y < end.y:
                    cx, cy = start.x, end.y
                    start_angle, extent_angle = -90.0, 90.0
                else:
                    cx, cy = start.x, end.y
                    start_angle, extent_angle = 90.0, -90.0

            # Convert angles to radians for drawing
            start_rad = math.radians(start_angle)
            end_rad = math.radians(start_angle + extent_angle)

            # Draw conic preview
            self._draw_conic_preview(
                Point2D(cx, cy), rad_x, rad_y, start_rad, end_rad
            )

            # Draw control points and lines
            start_point_item = QGraphicsEllipseItem(
                start.x - 3, start.y - 3, 6, 6
            )
            start_point_item.setPen(QPen(QColor("blue")))
            start_point_item.setBrush(QBrush(QColor("blue")))
            self.scene.addItem(start_point_item)

            end_point_item = QGraphicsEllipseItem(
                end.x - 3, end.y - 3, 6, 6
            )
            end_point_item.setPen(QPen(QColor("blue")))
            end_point_item.setBrush(QBrush(QColor("blue")))
            self.scene.addItem(end_point_item)

            center_point_item = QGraphicsEllipseItem(
                cx - 3, cy - 3, 6, 6
            )
            center_point_item.setPen(QPen(QColor("gray")))
            center_point_item.setBrush(QBrush(QColor("gray")))
            self.scene.addItem(center_point_item)

            # Radius lines
            line1_item = QGraphicsLineItem(cx, cy, start.x, start.y)
            pen1 = QPen(QColor("gray"))
            pen1.setStyle(Qt.DashLine)
            line1_item.setPen(pen1)
            self.scene.addItem(line1_item)

            line2_item = QGraphicsLineItem(cx, cy, end.x, end.y)
            pen2 = QPen(QColor("gray"))
            pen2.setStyle(Qt.DashLine)
            line2_item.setPen(pen2)
            self.scene.addItem(line2_item)

            self.temp_objects.extend([
                start_point_item, end_point_item, center_point_item,
                line1_item, line2_item
            ])

    def _draw_conic_preview(
            self, center: Point2D, rad_x: float, rad_y: float,
            start_angle: float, end_angle: float):
        """Draw a conic section preview with the given parameters"""
        # Create points along the conic
        arc_points = []

        # Ensure proper direction
        if end_angle < start_angle:
            if end_angle - start_angle > -math.pi:
                # Swap angles for correct direction
                start_angle, end_angle = end_angle, start_angle
            else:
                # Add 2π to end angle to make it larger than start
                end_angle += 2 * math.pi

        # Number of segments for the conic
        steps = 36
        angle_diff = end_angle - start_angle
        angle_step = angle_diff / steps

        for i in range(steps + 1):
            angle = start_angle + i * angle_step
            x = center.x + rad_x * math.cos(angle)
            y = center.y + rad_y * math.sin(angle)
            arc_points.extend([x, y])

        if len(arc_points) >= 4:  # Need at least 2 points (4 coordinates)
            # Create path for smooth conic curve
            path = QPainterPath()
            path.moveTo(arc_points[0], arc_points[1])

            for i in range(2, len(arc_points), 2):
                path.lineTo(arc_points[i], arc_points[i+1])

            path_item = QGraphicsPathItem(path)
            pen = QPen(QColor("blue"))
            pen.setStyle(Qt.DashLine)
            path_item.setPen(pen)
            self.scene.addItem(path_item)
            self.temp_objects.append(path_item)

    def create_object(self) -> Optional[CadObject]:
        """Create a conic object from the collected points"""
        if len(self.points) != 2:
            return None

        start = self.points[0]
        end = self.points[1]

        # Calculate conic parameters
        rad_x = abs(end.x - start.x)
        rad_y = abs(end.y - start.y)

        # Determine center and start/extent angles based on point positions
        if start.x > end.x:
            if start.y < end.y:
                cx, cy = start.x, end.y
                start_angle, extent_angle = -90.0, -90.0
            else:
                cx, cy = start.x, end.y
                start_angle, extent_angle = 90.0, 90.0
        else:
            if start.y < end.y:
                cx, cy = start.x, end.y
                start_angle, extent_angle = -90.0, 90.0
            else:
                cx, cy = start.x, end.y
                start_angle, extent_angle = 90.0, -90.0

        center = Point2D(cx, cy)

        # Create a conic object
        obj = CadObject(
            mainwin=self.document_window,
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.CONIC,
            coords=[start, end],
            attributes={
                'color': 'black',           # Default color
                'linewidth': 1,             # Default line width
                'center': center,           # Center point
                'rad_x': rad_x,             # X radius
                'rad_y': rad_y,             # Y radius
                'start_angle': start_angle,  # Start angle in degrees
                'extent_angle': extent_angle  # Extent angle in degrees
            }
        )
        return obj


class Conic3PointTool(Tool):
    """Tool for drawing conic sections by 3 points"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="CONIC3PT",
            name="Conic Section by 3 Points",
            category=ToolCategory.ARCS,
            icon="tool-conic3pt",
            cursor="crosshair",
            is_creator=True,
            secondary_key="I",
            node_info=["Starting Point2D", "Ending Point2D", "Slope Control Point2D"]
        )]

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
        # Get the snapped point based on current snap settings
        point = self.get_snap_point(event.x, event.y)

        if self.state == ToolState.ACTIVE:
            # First point - start of conic
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING and len(self.points) == 1:
            # Second point - end of conic
            self.points.append(point)
        elif self.state == ToolState.DRAWING and len(self.points) == 2:
            # Third point - control point for the slope
            self.points.append(point)
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            # Draw preview conic
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the conic being created"""
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
            # Have start and end points, use current point as control
            start = self.points[0]
            end = self.points[1]
            control = point

            # Calculate bezier control points for the conic approximation
            # Using the scalar value from the TCL implementation
            scalar1 = 0.447707
            scalar2 = 1.0 - scalar1

            # Calculate internal control points
            ix1 = scalar2 * control.x + scalar1 * start.x
            iy1 = scalar2 * control.y + scalar1 * start.y
            ix2 = scalar2 * control.x + scalar1 * end.x
            iy2 = scalar2 * control.y + scalar1 * end.y

            # Draw the bezier curve approximation
            bezier_points = [
                start.x, start.y,
                ix1, iy1,
                ix2, iy2,
                end.x, end.y
            ]

            # We'll draw this as a series of small line segments
            curve_points = self._bezier_to_points(bezier_points)

            if len(curve_points) >= 4:  # Need at least 2 points
                # Create path for smooth bezier curve
                path = QPainterPath()
                path.moveTo(curve_points[0], curve_points[1])

                for i in range(2, len(curve_points), 2):
                    path.lineTo(curve_points[i], curve_points[i+1])

                path_item = QGraphicsPathItem(path)
                pen = QPen(QColor("blue"))
                pen.setStyle(Qt.DashLine)
                path_item.setPen(pen)
                self.scene.addItem(path_item)
                self.temp_objects.append(path_item)

            # Draw control points and control lines
            start_point_item = QGraphicsEllipseItem(
                start.x - 3, start.y - 3, 6, 6
            )
            start_point_item.setPen(QPen(QColor("blue")))
            start_point_item.setBrush(QBrush(QColor("blue")))
            self.scene.addItem(start_point_item)

            end_point_item = QGraphicsEllipseItem(
                end.x - 3, end.y - 3, 6, 6
            )
            end_point_item.setPen(QPen(QColor("blue")))
            end_point_item.setBrush(QBrush(QColor("blue")))
            self.scene.addItem(end_point_item)

            control_point_item = QGraphicsEllipseItem(
                control.x - 3, control.y - 3, 6, 6
            )
            control_point_item.setPen(QPen(QColor("gray")))
            control_point_item.setBrush(QBrush(QColor("gray")))
            self.scene.addItem(control_point_item)

            # Control lines
            line1_item = QGraphicsLineItem(
                start.x, start.y, control.x, control.y
            )
            pen1 = QPen(QColor("gray"))
            pen1.setStyle(Qt.DashLine)
            line1_item.setPen(pen1)
            self.scene.addItem(line1_item)

            line2_item = QGraphicsLineItem(
                end.x, end.y, control.x, control.y
            )
            pen2 = QPen(QColor("gray"))
            pen2.setStyle(Qt.DashLine)
            line2_item.setPen(pen2)
            self.scene.addItem(line2_item)

            self.temp_objects.extend([
                start_point_item, end_point_item, control_point_item,
                line1_item, line2_item
            ])

    def _bezier_to_points(self, bezier_points: List[float]) -> List[float]:
        """Convert a cubic bezier curve to a series of points"""
        # Unpack the bezier control points
        x0, y0, x1, y1, x2, y2, x3, y3 = bezier_points

        # Number of segments to use
        num_segments = 36

        # Generate points along the bezier curve
        points = []
        for i in range(num_segments + 1):
            t = i / num_segments
            # Cubic bezier formula
            omt = 1 - t
            omt2 = omt * omt
            omt3 = omt2 * omt
            t2 = t * t
            t3 = t2 * t

            x = omt3 * x0 + 3 * omt2 * t * x1 + 3 * omt * t2 * x2 + t3 * x3
            y = omt3 * y0 + 3 * omt2 * t * y1 + 3 * omt * t2 * y2 + t3 * y3

            points.extend([x, y])

        return points

    def create_object(self) -> Optional[CadObject]:
        """Create a conic object from the collected points"""
        if len(self.points) != 3:
            return None

        start = self.points[0]
        end = self.points[1]
        control = self.points[2]

        # Calculate bezier control points for the conic approximation
        # Using the scalar value from the TCL implementation
        scalar1 = 0.447707
        scalar2 = 1.0 - scalar1

        # Calculate internal control points
        ix1 = scalar2 * control.x + scalar1 * start.x
        iy1 = scalar2 * control.y + scalar1 * start.y
        ix2 = scalar2 * control.x + scalar1 * end.x
        iy2 = scalar2 * control.y + scalar1 * end.y

        # Store the bezier representation
        bezier_points = [
            start.x, start.y,
            ix1, iy1,
            ix2, iy2,
            end.x, end.y
        ]

        # Create a conic object
        obj = CadObject(
            mainwin=self.document_window,
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.CONIC,
            coords=[start, end, control],
            attributes={
                'color': 'black',           # Default color
                'linewidth': 1,             # Default line width
                'bezier_path': bezier_points,  # Bezier representation
                'conic_type': '3pt'         # Type of conic definition
            }
        )
        return obj
