"""
Bezier Curve Drawing Tool Implementation

This module implements a bezier curve drawing tool based on the TCL
tools_beziers.tcl implementation.
"""

import math
from typing import Optional, List

from src.core.cad_objects import CADObject, ObjectType, Point
from src.tools.base import Tool, ToolState, ToolCategory, ToolDefinition


class BezierObject(CADObject):
    """Bezier curve object - control points"""

    def __init__(self, object_id: int, control_points: List[Point], **kwargs):
        super().__init__(
            object_id, ObjectType.BEZIER, coords=control_points, **kwargs)

    def evaluate_at(self, t: float) -> Point:
        """Evaluate Bezier curve at parameter t (0 to 1)"""
        n = len(self.coords) - 1
        result = Point(0, 0)

        for i, point in enumerate(self.coords):
            # Binomial coefficient
            coeff = math.comb(n, i) * ((1 - t) ** (n - i)) * (t ** i)
            result.x += coeff * point.x
            result.y += coeff * point.y

        return result


class BezierTool(Tool):
    """Tool for drawing bezier curves"""

    def __init__(self, scene, document, preferences):
        super().__init__(scene, document, preferences)
        self.is_quadratic = True  # If True, draw quadratic, else cubic beziers
        self.segment_points = []  # List of points for current segment
        self.preview_curve = None

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="BEZIER",
            name="Bezier Curve",
            category=ToolCategory.BEZIERS,
            icon="tool-bezier",
            cursor="crosshair",
            is_creator=True,
            node_info=["Endpoint", "Control Point", "Endpoint"]
        )]

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        # In Qt, event handling is done differently - these will be connected
        # in the main window or graphics view
        pass
        """Set up mouse and keyboard event bindings"""

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_double_click(self, event):
        """Handle double-click to complete the bezier curve"""
        if self.state == ToolState.DRAWING and len(self.points) >= 3:
            self.complete()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        # Get the snapped point based on current snap settings
        point = self.get_snap_point(event.x, event.y)

        if self.state == ToolState.ACTIVE:
            # First point - start drawing
            self.points.append(point)
            self.segment_points = [point]
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING:
            # Add point to the bezier
            self.segment_points.append(point)

            # If we have enough points for a segment, create it
            if len(self.segment_points) == 3 and self.is_quadratic:
                # We have enough points for a quadratic bezier segment
                self.points.extend(self.segment_points[1:])
                # Start a new segment from the last point
                self.segment_points = [self.segment_points[-1]]
            elif len(self.segment_points) == 4 and not self.is_quadratic:
                # We have enough points for a cubic bezier segment
                self.points.extend(self.segment_points[1:])
                # Start a new segment from the last point
                self.segment_points = [self.segment_points[-1]]

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            # Draw preview bezier
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the bezier curve being created"""
        # Clear previous preview
        self.clear_temp_objects()

        if len(self.segment_points) > 0:
            # Get the snapped point based on current snap settings
            point = self.get_snap_point(current_x, current_y)

            # Create temp preview points
            preview_points = self.segment_points.copy()
            preview_points.append(point)

            # Draw control lines using QGraphicsLineItem
            from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsRectItem, QGraphicsEllipseItem
            from PySide6.QtCore import QRectF, Qt
            from PySide6.QtGui import QPen, QBrush
            
            for i in range(len(preview_points) - 1):
                line_item = QGraphicsLineItem(
                    preview_points[i].x, preview_points[i].y,
                    preview_points[i+1].x, preview_points[i+1].y
                )
                pen = QPen()
                pen.setColor("gray")
                pen.setStyle(Qt.DashLine)
                line_item.setPen(pen)
                self.scene.addItem(line_item)
                self.temp_objects.append(line_item)

            # Draw temporary bezier curve using QGraphicsPathItem
            if self.is_quadratic and len(preview_points) >= 3:
                # For quadratic bezier, we need at least 3 points
                curve_points = self._get_quadratic_bezier_points(
                    preview_points[0], preview_points[1], preview_points[2])

                if curve_points:
                    from PySide6.QtWidgets import QGraphicsPathItem
                    from PySide6.QtGui import QPainterPath
                    
                    path = QPainterPath()
                    if curve_points:
                        path.moveTo(curve_points[0].x, curve_points[0].y)
                        for p in curve_points[1:]:
                            path.lineTo(p.x, p.y)
                    
                    path_item = QGraphicsPathItem(path)
                    path_item.setPen(QPen("blue"))
                    self.scene.addItem(path_item)
                    self.preview_curve = path_item
                    self.temp_objects.append(path_item)

            elif not self.is_quadratic and len(preview_points) >= 4:
                # For cubic bezier, we need at least 4 points
                curve_points = self._get_cubic_bezier_points(
                    preview_points[0], preview_points[1],
                    preview_points[2], preview_points[3])

                if curve_points:
                    from PySide6.QtWidgets import QGraphicsPathItem
                    from PySide6.QtGui import QPainterPath
                    
                    path = QPainterPath()
                    if curve_points:
                        path.moveTo(curve_points[0].x, curve_points[0].y)
                        for p in curve_points[1:]:
                            path.lineTo(p.x, p.y)
                    
                    path_item = QGraphicsPathItem(path)
                    path_item.setPen(QPen("blue"))
                    self.scene.addItem(path_item)
                    self.preview_curve = path_item
                    self.temp_objects.append(path_item)

            # Draw control points using Qt graphics items
            for i, p in enumerate(preview_points):
                if i == 0 or i == len(preview_points) - 1:
                    # Endpoint - use rectangle
                    marker_item = QGraphicsRectItem(QRectF(p.x - 3, p.y - 3, 6, 6))
                    marker_item.setPen(QPen("blue"))
                    marker_item.setBrush(QBrush("white"))
                    self.scene.addItem(marker_item)
                    self.temp_objects.append(marker_item)
                else:
                    # Control point - use circle
                    marker_item = QGraphicsEllipseItem(QRectF(p.x - 3, p.y - 3, 6, 6))
                    marker_item.setPen(QPen("blue"))
                    marker_item.setBrush(QBrush("white"))
                    self.scene.addItem(marker_item)
                    self.temp_objects.append(marker_item)

    def _get_quadratic_bezier_points(
            self, p0: Point, p1: Point, p2: Point) -> List[Point]:
        """Get points along a quadratic bezier curve"""
        points = []
        # Number of points to generate (more = smoother curve)
        steps = 20

        for i in range(steps + 1):
            t = i / steps
            # Quadratic bezier formula: B(t) = (1-t)^2*P0 + 2(1-t)t*P1 + t^2*P2
            x = ((1-t)**2 * p0.x + 2*(1-t)*t * p1.x + t**2 * p2.x)
            y = ((1-t)**2 * p0.y + 2*(1-t)*t * p1.y + t**2 * p2.y)
            points.append(Point(x, y))

        return points

    def _get_cubic_bezier_points(
            self, p0: Point, p1: Point, p2: Point, p3: Point) -> List[Point]:
        """Get points along a cubic bezier curve"""
        points = []
        # Number of points to generate (more = smoother curve)
        steps = 20

        for i in range(steps + 1):
            t = i / steps
            # Cubic bezier formula:
            # B(t) = (1-t)^3*P0 + 3(1-t)^2*t*P1 + 3(1-t)*t^2*P2 + t^3*P3
            x = ((1-t)**3 * p0.x + 3*(1-t)**2*t * p1.x +
                 3*(1-t)*t**2 * p2.x + t**3 * p3.x)
            y = ((1-t)**3 * p0.y + 3*(1-t)**2*t * p1.y +
                 3*(1-t)*t**2 * p2.y + t**3 * p3.y)
            points.append(Point(x, y))

        return points

    def create_object(self) -> Optional[CADObject]:
        """Create a bezier curve object from the collected points"""
        if len(self.points) < 3:
            return None

        # Create a bezier object
        obj = CADObject(
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.BEZIER,
            layer=self.document.objects.current_layer,
            coords=self.points.copy(),
            attributes={
                'color': 'black',      # Default color
                'linewidth': 1,        # Default line width
                'is_quadratic': self.is_quadratic  # Whether it's quadratic
            }
        )
        return obj
