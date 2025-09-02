"""
Circle Drawing Tool Implementation

This module implements a circle drawing tool based on the TCL tool
implementation.
"""

import math
from typing import Optional, List

from ..models.cad_object import CadObject, ObjectType
from ..models.cad_objects.circle_cad_object import CircleCadObject
from ..cad_geometry import Point2D
from .base import Tool, ToolState, ToolCategory, ToolDefinition
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPen, QColor, QBrush
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem



class CircleTool(Tool):
    """Tool for drawing circles"""

    # Class-level tool definition
    tool_definitions = [
        ToolDefinition(
            token="CIRCLE",
            name="Circle Tool",
            category=ToolCategory.ELLIPSES,
            icon="tool-circlectr",
            cursor="crosshair",
            is_creator=True,
            secondary_key="C",
            node_info=["Center Point2D", "Radius Point2D"]
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
            # First point - center of circle
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING:
            # Second point - radius point
            self.points.append(point)
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING and len(self.points) == 1:
            # Draw preview circle
            if hasattr(event, 'scenePos'):
                scene_pos = event.scenePos()
            else:
                scene_pos = QPointF(event.x, event.y)
            self.draw_preview(scene_pos.x(), scene_pos.y())

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the circle being created"""
        # Clear previous preview
        self.clear_temp_objects()

        if len(self.points) == 1:
            # Get the snapped point based on current snap settings
            point = self.get_snap_point(current_x, current_y)

            # Calculate radius
            center_point = self.points[0]
            delta = point - center_point
            radius = math.hypot(delta.x, delta.y)

            # Create temporary ellipse using CadScene's addEllipse method
            pen = QPen(QColor("black"), 3.0)
            pen.setCosmetic(True)
            pen.setDashPattern([2, 2])  # Dashed line for preview
            ellipse_item = self.scene.addEllipse(
                center_point.x - radius, center_point.y - radius,
                2 * radius, 2 * radius,
                pen=pen
            )
            self.temp_objects.append(ellipse_item)
        self.draw_points()

    def create_object(self) -> Optional[CadObject]:
        """Create a circle object from the collected points"""
        if len(self.points) != 2:
            return None

        # Calculate radius
        center_point = self.points[0]
        radius_point = self.points[1]
        delta = radius_point - center_point
        radius = math.hypot(delta.x, delta.y)

        # Create circle object
        circle = CircleCadObject(
            document=self.document,
            center_point=center_point,
            radius=radius,
            color=self.preferences.get("default_color", "black"),
            line_width=self.preferences.get("default_line_width", 0.05)
        )
        return circle


class Circle2PTTool(Tool):
    """Tool for drawing circles by 2 points (diameter endpoints)"""

    # Class-level tool definition
    tool_definitions = [
        ToolDefinition(
            token="CIRCLE2PT",
            name="Circle by 2 Points",
            category=ToolCategory.ELLIPSES,
            icon="tool-circle2pt",
            cursor="crosshair",
            is_creator=True,
            secondary_key="2",
            node_info=["First Point2D", "Second Point2D"]
        )
    ]

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        pass

    def handle_mouse_down(self, event):
        """Handle mouse down events"""
        print(f"Handle mouse down events: {self.state} ({len(self.points)})")
        scene_pos = event.scenePos()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(scene_pos.x(), scene_pos.y())

        if self.state == ToolState.ACTIVE:
            self.points = [point]
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING:
            self.points.append(point)
            # Create the circle object
            obj = self.create_object()
            if obj:
                self.document.add_object(obj)
                self.object_created.emit(obj)
            self.cancel()

    def handle_mouse_move(self, event):
        """Handle mouse move events for preview"""
        if self.state == ToolState.DRAWING and len(self.points) >= 1:
            scene_pos = event.scenePos()
            self.draw_preview(scene_pos.x(), scene_pos.y())

    def draw_preview(self, current_x, current_y):
        """Draw preview of the circle"""
        self.clear_temp_objects()

        if len(self.points) >= 1:
            # Calculate circle center and radius
            p1 = self.points[0]
            p2 = self.get_snap_point(current_x, current_y)
            center = (p1 + p2) / 2
            radius = p2.distance_to(center)

            pen = QPen(QColor("black"), 3.0)
            pen.setCosmetic(True)
            pen.setDashPattern([2, 2])  # Dashed line for preview
            ellipse_item = self.scene.addEllipse(
                center.x - radius, center.y - radius,
                2 * radius, 2 * radius,
                pen=pen
            )
            self.temp_objects.append(ellipse_item)
        self.draw_points()

    def create_object(self) -> Optional[CadObject]:
        """Create a circle object from the collected points"""
        if len(self.points) != 2:
            return None

        p1 = self.points[0]
        p2 = self.points[1]
        center = (p1 + p2) / 2
        radius = p1.distance_to(center)

        obj = CircleCadObject(
            document=self.document,
            center_point=center,
            radius=radius,
            color=self.preferences.get("default_color", "black"),
            line_width=self.preferences.get("default_line_width", 0.05)
        )
        return obj


class Circle3PTTool(Tool):
    """Tool for drawing circles by 3 points on circumference"""

    # Class-level tool definition
    tool_definitions = [
        ToolDefinition(
            token="CIRCLE3PT",
            name="Circle by 3 Points",
            category=ToolCategory.ELLIPSES,
            icon="tool-circle3pt",
            cursor="crosshair",
            is_creator=True,
            secondary_key="3",
            node_info=["First Point2D", "Second Point2D", "Third Point2D"]
        )
    ]

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        pass

    def handle_mouse_down(self, event):
        """Handle mouse down events"""
        scene_pos = event.scenePos()
        point = Point2D(scene_pos.x(), scene_pos.y())

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(scene_pos.x(), scene_pos.y())

        if self.state == ToolState.ACTIVE:
            self.points = [point]
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING:
            self.points.append(point)
            if len(self.points) == 3:
                # Create the circle object
                obj = self.create_object()
                if obj:
                    self.document.add_object(obj)
                    self.object_created.emit(obj)
                self.cancel()

    def handle_mouse_move(self, event):
        """Handle mouse move events for preview"""
        print(f"Handle mouse move events for preview: {self.state} ({len(self.points)})")
        if self.state == ToolState.DRAWING and len(self.points) >= 1:
            scene_pos = event.scenePos()
            current_point = self.get_snap_point(scene_pos.x(), scene_pos.y())
            self.draw_preview(current_point.x, current_point.y)

    def _calculate_circle_from_3_points(self, p1, p2, p3):
        """Calculate circle from 3 points"""
        # Check if collinear
        col = p1.x * (p2.y - p3.y) + p2.x * \
            (p3.y - p1.y) + p3.x * (p1.y - p2.y)
        if abs(col) < 1e-6:
            return None

        mx1 = (p1.x + p3.x) / 2.0
        my1 = (p1.y + p3.y) / 2.0
        mx2 = (p2.x + p3.x) / 2.0
        my2 = (p2.y + p3.y) / 2.0

        if abs(p3.y - p1.y) < 1e-6:
            m2 = -(p2.x - p3.x) / (p2.y - p3.y)
            c2 = my2 - m2 * mx2
            cx = mx1
            cy = m2 * cx + c2

        elif abs(p3.y - p2.y) < 1e-6:
            m1 = -(p3.x - p1.x) / (p3.y - p1.y)
            c1 = my1 - m1 * mx1
            cx = mx2
            cy = m1 * cx + c1

        else:
            m1 = -(p3.x - p1.x) / (p3.y - p1.y)
            m2 = -(p2.x - p3.x) / (p2.y - p3.y)
            c1 = my1 - m1 * mx1
            c2 = my2 - m2 * mx2
            cx = (c2 - c1) / (m1 - m2)
            cy = m1 * cx + c1

        radius = math.sqrt((p1.y - cy)**2 + (p1.x - cx)**2)
        return Point2D(cx, cy), radius

    def draw_preview(self, current_x, current_y):
        """Draw preview of the circle"""
        # Clear previous preview
        self.clear_temp_objects()

        if len(self.points) >= 2:
            # Calculate circle from 3 points
            p1, p2 = self.points
            p3 = self.get_snap_point(current_x, current_y)
            circ_info = self._calculate_circle_from_3_points(p1, p2, p3)
            if circ_info is None:
                return
            center, radius = circ_info

            # Draw preview circle
            pen = QPen(QColor("black"), 3.0)
            pen.setCosmetic(True)
            pen.setDashPattern([2, 2])  # Dashed line for preview
            ellipse_item = self.scene.addEllipse(
                center.x - radius, center.y - radius,
                2 * radius, 2 * radius,
                pen=pen
            )
            self.temp_objects.append(ellipse_item)

        elif len(self.points) == 1:
            # Draw line preview between first two points
            p1 = self.points[0]
            p2 = self.get_snap_point(current_x, current_y)
            center = (p1 + p2) / 2
            radius = p1.distance_to(center)

            # Draw preview circle
            pen = QPen(QColor("black"), 3.0)
            pen.setCosmetic(True)
            pen.setDashPattern([2, 2])  # Dashed line for preview
            ellipse_item = self.scene.addEllipse(
                center.x - radius, center.y - radius,
                2 * radius, 2 * radius,
                pen=pen
            )
            self.temp_objects.append(ellipse_item)

        self.draw_points()

    def create_object(self) -> Optional[CadObject]:
        """Create a circle object from the collected points"""
        if len(self.points) != 3:
            return None

        p1, p2, p3 = self.points
        circ_info = self._calculate_circle_from_3_points(p1, p2, p3)
        if circ_info is None:
            return None
        center, radius = circ_info

        obj = CircleCadObject(
            document=self.document,
            center_point=center,
            radius=radius,
            color=self.preferences.get("default_color", "black"),
            line_width=self.preferences.get("default_line_width", 0.05)
        )
        return obj
