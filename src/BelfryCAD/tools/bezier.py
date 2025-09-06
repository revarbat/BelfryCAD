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

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the cubic bezier curve being created"""
        self.clear_temp_objects()

        pen = QPen(QColor("black"), 3.0)
        pen.setCosmetic(True)
        pen.setStyle(Qt.PenStyle.DashLine)

        pen_gray = QPen(QColor("gray"), 3.0)
        pen_gray.setCosmetic(True)
        pen_gray.setStyle(Qt.PenStyle.DashLine)

        pointpath = self.points.copy()
        pointpath.append(Point2D(current_x, current_y))
        remainder = (len(pointpath) - 1) % 3
        ll = len(pointpath)

        # Draw temporary cubic bezier curve
        path = QPainterPath()
        path.moveTo(pointpath[0].to_qpointf())
        for i in range(1, len(pointpath)-remainder-1, 3):
            path.cubicTo(
                pointpath[i].to_qpointf(),
                pointpath[i+1].to_qpointf(),
                pointpath[i+2].to_qpointf()
            )
        if remainder == 1:
            i = ll - remainder
            path.lineTo(pointpath[i].to_qpointf())
        elif remainder == 2:
            i = ll - remainder
            path.cubicTo(
                pointpath[i].to_qpointf(),
                pointpath[i+1].to_qpointf(),
                pointpath[i+1].to_qpointf()
            )
        path_item = self.scene.addPath(path, pen=pen)
        self.temp_objects.append(path_item)

        for i in range(0, len(pointpath), 3):
            if i > 0:
                # Draw control line (before the curve)
                line_item = self.scene.addLine(
                    QLineF(
                        pointpath[i-1].to_qpointf(),
                        pointpath[i].to_qpointf()
                    ),
                    pen=pen_gray
                )
                self.temp_objects.append(line_item)

            if i < len(pointpath) - 1:
                # Draw control line (after the curve)
                line_item = self.scene.addLine(
                    QLineF(
                        pointpath[i].to_qpointf(),
                        pointpath[i+1].to_qpointf()
                    ),
                    pen=pen_gray
                )
                self.temp_objects.append(line_item)

        self.draw_points()

    def create_object(self) -> Optional[CadObject]:
        """Create a cubic bezier curve object from the collected points"""
        if len(self.points) < 4:
            return None

        obj = CubicBezierCadObject(
            document=self.document,
            points=self.points.copy(),
            color="black",
            line_width=1,
        )
        return obj

