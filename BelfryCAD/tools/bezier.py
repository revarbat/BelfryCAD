"""
Bezier Curve Drawing Tool Implementation

This module implements bezier curve drawing tools based on the TCL
tools_beziers.tcl implementation.
"""

import math
from typing import Optional, List

from BelfryCAD.core.cad_objects import CADObject, ObjectType, Point
from BelfryCAD.tools.base import Tool, ToolState, ToolCategory, ToolDefinition


class BezierTool(Tool):
    """Tool for drawing cubic bezier curves"""

    def __init__(self, scene, document, preferences):
        super().__init__(scene, document, preferences)
        self.is_quadratic = False  # Cubic beziers
        self.segment_points = []  # List of points for current segment
        self.preview_curve = None

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="BEZIER",
            name="Cubic Bezier Curve",
            category=ToolCategory.LINES,
            icon="tool-bezier",
            cursor="crosshair",
            is_creator=True,
            secondary_key="B",
            node_info=["First Point", "Next Point", "..."]
        )]

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        pass

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_double_click(self, event):
        """Handle double-click to complete the bezier curve"""
        if self.state == ToolState.DRAWING and len(self.points) >= 4:
            self.complete()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        point = self.get_snap_point(event.x, event.y)

        if self.state == ToolState.ACTIVE:
            self.points.append(point)
            self.segment_points = [point]
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING:
            self.segment_points.append(point)

            # For cubic bezier, we need 4 points per segment
            if len(self.segment_points) == 4:
                self.points.extend(self.segment_points[1:])
                self.segment_points = [self.segment_points[-1]]

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the cubic bezier curve being created"""
        self.clear_temp_objects()

        if len(self.segment_points) > 0:
            point = self.get_snap_point(current_x, current_y)
            preview_points = self.segment_points.copy()
            preview_points.append(point)

            # Draw control lines
            from PySide6.QtWidgets import QGraphicsLineItem
            from PySide6.QtCore import Qt
            from PySide6.QtGui import QPen
            
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

            # Draw temporary cubic bezier curve
            if len(preview_points) >= 4:
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
                    pen = QPen()
                    pen.setColor("blue")
                    pen.setWidth(2)
                    path_item.setPen(pen)
                    self.scene.addItem(path_item)
                    self.temp_objects.append(path_item)

    def _get_cubic_bezier_points(
            self, p0: Point, p1: Point, p2: Point, p3: Point) -> List[Point]:
        """Get points along a cubic bezier curve"""
        points = []
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
        """Create a cubic bezier curve object from the collected points"""
        if len(self.points) < 4:
            return None

        obj = CADObject(
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.BEZIER,
            layer=self.document.objects.current_layer,
            coords=self.points.copy(),
            attributes={
                'color': 'black',
                'linewidth': 1,
                'is_quadratic': False
            }
        )
        return obj


class BezierQuadTool(Tool):
    """Tool for drawing quadratic bezier curves"""

    def __init__(self, scene, document, preferences):
        super().__init__(scene, document, preferences)
        self.is_quadratic = True  # Quadratic beziers
        self.segment_points = []  # List of points for current segment
        self.preview_curve = None

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="BEZIERQUAD",
            name="Quadratic Bezier Curve",
            category=ToolCategory.LINES,
            icon="tool-bezierquad",
            cursor="crosshair",
            is_creator=True,
            secondary_key="Q",
            node_info=["First Point", "Control Point", "Next Point", "..."]
        )]

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        pass

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_double_click(self, event):
        """Handle double-click to complete the bezier curve"""
        if self.state == ToolState.DRAWING and len(self.points) >= 3:
            self.complete()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        point = self.get_snap_point(event.x, event.y)

        if self.state == ToolState.ACTIVE:
            self.points.append(point)
            self.segment_points = [point]
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING:
            self.segment_points.append(point)

            # For quadratic bezier, we need 3 points per segment
            if len(self.segment_points) == 3:
                self.points.extend(self.segment_points[1:])
                self.segment_points = [self.segment_points[-1]]

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the quadratic bezier curve being created"""
        self.clear_temp_objects()

        if len(self.segment_points) > 0:
            point = self.get_snap_point(current_x, current_y)
            preview_points = self.segment_points.copy()
            preview_points.append(point)

            # Draw control lines
            from PySide6.QtWidgets import QGraphicsLineItem
            from PySide6.QtCore import Qt
            from PySide6.QtGui import QPen
            
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

            # Draw temporary quadratic bezier curve
            if len(preview_points) >= 3:
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
                    pen = QPen()
                    pen.setColor("blue")
                    pen.setWidth(2)
                    path_item.setPen(pen)
                    self.scene.addItem(path_item)
                    self.temp_objects.append(path_item)

    def _get_quadratic_bezier_points(
            self, p0: Point, p1: Point, p2: Point) -> List[Point]:
        """Get points along a quadratic bezier curve"""
        points = []
        steps = 20

        for i in range(steps + 1):
            t = i / steps
            # Quadratic bezier formula: 
            # B(t) = (1-t)^2*P0 + 2(1-t)t*P1 + t^2*P2
            x = ((1-t)**2 * p0.x + 2*(1-t)*t * p1.x + t**2 * p2.x)
            y = ((1-t)**2 * p0.y + 2*(1-t)*t * p1.y + t**2 * p2.y)
            points.append(Point(x, y))

        return points

    def create_object(self) -> Optional[CADObject]:
        """Create a quadratic bezier curve object from the collected points"""
        if len(self.points) < 3:
            return None

        obj = CADObject(
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.BEZIERQUAD,
            layer=self.document.objects.current_layer,
            coords=self.points.copy(),
            attributes={
                'color': 'black',
                'linewidth': 1,
                'is_quadratic': True
            }
        )
        return obj
