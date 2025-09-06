"""
Bezier Curve Drawing CadTool Implementation

This module implements bezier curve drawing tools based on the TCL
tools_beziers.tcl implementation.
"""

import math
from typing import Optional, List

from ..models.cad_object import CadObject, ObjectType
from ..models.cad_objects.cubic_bezier_cad_object import CubicBezierCadObject
from ..cad_geometry import Point2D
from .base import CadTool, ToolState, ToolCategory, ToolDefinition

from PySide6.QtCore import QPointF, QLineF
from PySide6.QtGui import QPen, QPainterPath, QColor, Qt
from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsPathItem


class BezierTool(CadTool):
    """CadTool for drawing cubic bezier curves"""

    def __init__(self, scene, document, preferences):
        super().__init__(scene, document, preferences)
        self.points = []

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
            node_info=["First point", "Next point", "..."]
        )]

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_double_click(self, event):
        """Handle double-click to complete the bezier curve"""
        if self.state == ToolState.DRAWING and len(self.points) >= 4:
            self.complete()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        # Convert Qt event coordinates to scene coordinates
        if hasattr(event, 'scenePos'):
            scene_pos = event.scenePos()
        else:
            scene_pos = QPointF(event.x, event.y)

        # Get the snap point
        point = self.get_snap_point(scene_pos.x(), scene_pos.y())

        if self.state == ToolState.ACTIVE:
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING:
            self.draw_preview(point.x, point.y)
            self.points.append(point)

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        # Convert Qt event coordinates to scene coordinates
        if hasattr(event, 'scenePos'):
            scene_pos = event.scenePos()
        else:
            scene_pos = QPointF(event.x, event.y)
        point = self.get_snap_point(scene_pos.x(), scene_pos.y())

        if self.state == ToolState.DRAWING:
            self.draw_preview(point.x, point.y)

    def _get_tangent_points(self, p1, p2, p3, ratio):
        dist1 = p2.distance_to(p1)
        dist2 = p2.distance_to(p3)
        vector = (p3 - p1).unit_vector
        p1 = p2 - vector * dist1 * ratio
        p3 = p2 + vector * dist2 * ratio
        return p1, p3

    def _calculate_control_points(self, points):
        ratio = 0.4
        
        points = [
            points[i] for i in range(len(points)) if i == 0 or points[i-1] != points[i]
        ]

        if len(points) <= 1:
            return []

        if len(points) == 2:
            vector = (points[1] - points[0]).unit_vector
            dist = points[0].distance_to(points[1])
            return [
                points[0],
                points[0] + vector * dist * 0.4,
                points[1] - vector * dist * 0.4,
                points[1],
            ]

        control_points = [points[0]]

        if points[0] != points[-1]:  # open path
            p1, p2 = self._get_tangent_points(points[0], points[1], points[2], 0.5)
            control_points.append((points[0] + p1) / 2)
        else:  # closed loop
            p1, p2 = self._get_tangent_points(points[-2], points[0], points[1], ratio)
            control_points.append(p2)
        
        for i in range(1, len(points)-1):
            p1, p2 = self._get_tangent_points(points[i-1], points[i], points[i+1], ratio)
            control_points.append(p1)
            control_points.append(points[i])
            control_points.append(p2)
        
        if points[0] != points[-1]:  # open path
            p1, p2 = self._get_tangent_points(points[-3], points[-2], points[-1], 0.5)
            control_points.append((points[-1] + p2) / 2)
        else:  # closed loop
            p1, p2 = self._get_tangent_points(points[-2], points[0], points[1], ratio)
            control_points.append(p1)

        control_points.append(points[-1])

        return control_points

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the cubic bezier curve being created"""
        self.clear_temp_objects()

        pen = QPen(QColor("black"), 3.0)
        pen.setCosmetic(True)
        pen.setStyle(Qt.PenStyle.DashLine)

        pen_gray = QPen(QColor("gray"), 3.0)
        pen_gray.setCosmetic(True)
        pen_gray.setStyle(Qt.PenStyle.SolidLine)

        # Draw temporary cubic bezier curve
        points = self.points.copy()
        points.append(Point2D(current_x, current_y))

        control_points = self._calculate_control_points(points)
        if len(control_points) <= 1:
            return
        if len(control_points) == 2 and control_points[0] == control_points[1]:
            return

        path = QPainterPath()
        path.moveTo(control_points[0].to_qpointf())
        for i in range(1, len(control_points)-1, 3):
            path.cubicTo(
                control_points[i].to_qpointf(),
                control_points[i+1].to_qpointf(),
                control_points[i+2].to_qpointf()
            )
        path_item = self.scene.addPath(path, pen=pen)
        self.temp_objects.append(path_item)

        for i in range(0, len(control_points)-2, 3):
            # Draw first control handle line
            line_item = self.scene.addLine(
                QLineF(
                    control_points[i].to_qpointf(),
                    control_points[i+1].to_qpointf()
                ),
                pen=pen_gray
            )
            self.temp_objects.append(line_item)

            # Draw second control handle line
            line_item = self.scene.addLine(
                QLineF(
                    control_points[i+2].to_qpointf(),
                    control_points[i+3].to_qpointf()
                ),
                pen=pen_gray
            )
            self.temp_objects.append(line_item)

        self.draw_points(control_points.copy())

    def create_object(self) -> Optional[CadObject]:
        """Create a cubic bezier curve object from the collected points"""
        if len(self.points) < 4:
            return None

        points = self._calculate_control_points(self.points.copy())
        obj = CubicBezierCadObject(
            document=self.document,
            points=points,
            color="black",
            line_width=0.05,
        )
        return obj

