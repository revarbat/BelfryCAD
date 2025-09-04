# filepath: /Users/gminette/dev/git-repos/pyBelfryCad/src/tools/ellipse.py
"""
Ellipse Drawing CadTool Implementation

This module implements various ellipse drawing tools.
"""

import math
from typing import Optional, List

from ..models.cad_object import CadObject
from ..models.cad_objects.ellipse_cad_object import EllipseCadObject
from ..cad_geometry import Point2D, Ellipse
from .base import CadTool, ToolState, ToolCategory, ToolDefinition
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsTextItem,
)
from PySide6.QtCore import QRectF, Qt, QPointF
from PySide6.QtGui import QPen, QBrush, QColor, QPolygonF


class EllipseCenterTool(CadTool):
    """CadTool for drawing ellipses by center point and corner point"""

    # Class-level tool definition
    tool_definitions = [
        ToolDefinition(
            token="ELLIPSECTR",
            name="Ellipse by Center",
            category=ToolCategory.ELLIPSES,
            icon="tool-ellipsectr",
            cursor="crosshair",
            is_creator=True,
            secondary_key="E",
            node_info=["Center Point2D", "Corner Point2D"]
        )
    ]

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        if hasattr(event, 'scenePos'):
            scene_pos = event.scenePos()
        else:
            scene_pos = QPointF(event.x, event.y)

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(scene_pos.x(), scene_pos.y())

        if self.state == ToolState.ACTIVE:
            # First point - center of ellipse
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING and len(self.points) == 1:
            # Second point - corner point defining x and y radii
            self.points.append(point)
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if hasattr(event, 'scenePos'):
            scene_pos = event.scenePos()
        else:
            scene_pos = QPointF(event.x, event.y)

        if self.state == ToolState.DRAWING:
            # Draw preview ellipse
            self.draw_preview(scene_pos.x(), scene_pos.y())

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the ellipse being created"""
        # Clear previous preview
        self.clear_temp_objects()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(current_x, current_y)

        if len(self.points) == 1:
            # Drawing from center to corner point
            center = self.points[0]

            # Calculate radii
            rad_x = abs(point.x - center.x)
            rad_y = abs(point.y - center.y)

            # Draw bounding box
            pen_gray = QPen(QColor("gray"), 3.0)
            pen_gray.setCosmetic(True)
            pen_gray.setDashPattern([2, 2])  # Dashed line for preview
            box_item = self.scene.addRect(
                QRectF(center.x - rad_x, center.y - rad_y,
                       2 * rad_x, 2 * rad_y),
                pen_gray
            )
            self.temp_objects.append(box_item)

            # Draw temporary ellipse using QGraphicsEllipseItem
            pen = QPen(QColor("black"), 3.0)
            pen.setCosmetic(True)
            pen.setDashPattern([2, 2])  # Dashed line for preview
            ellipse_item = self.scene.addEllipse(
                QRectF(center.x - rad_x, center.y - rad_y,
                       2 * rad_x, 2 * rad_y),
                pen
            )
            self.temp_objects.append(ellipse_item)

        self.draw_points()

    def create_object(self) -> Optional[CadObject]:
        """Create an ellipse object from the collected points"""
        if len(self.points) != 2:
            return None

        center = self.points[0]
        corner = self.points[1]

        # Calculate radii
        rad_x = abs(corner.x - center.x)
        rad_y = abs(corner.y - center.y)

        # Create an ellipse object
        obj = EllipseCadObject(
            document=self.document,
            center_point=center,
            radius1=rad_x,
            radius2=rad_y,
            color=self.preferences.get("default_color", "black"),
            line_width=self.preferences.get("default_line_width", 0.05)
        )
        return obj


class EllipseDiagonalTool(CadTool):
    "CadTool for drawing ellipses by diagonal opposite corners of bounding box"

    # Class-level tool definition
    tool_definitions = [
        ToolDefinition(
            token="ELLIPSEDIAG",
            name="Ellipse by Diagonal",
            category=ToolCategory.ELLIPSES,
            icon="tool-ellipsediag",
            cursor="crosshair",
            secondary_key="D",
            is_creator=True,
            node_info=["First Corner", "Opposite Corner"]
        )
    ]

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        if hasattr(event, 'scenePos'):
            scene_pos = event.scenePos()
        else:
            scene_pos = QPointF(event.x, event.y)

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(scene_pos.x(), scene_pos.y())

        if self.state == ToolState.ACTIVE:
            # First point - first corner of ellipse bounding box
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING and len(self.points) == 1:
            # Second point - opposite corner defining the bounding box
            self.points.append(point)
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if hasattr(event, 'scenePos'):
            scene_pos = event.scenePos()
        else:
            scene_pos = QPointF(event.x, event.y)

        if self.state == ToolState.DRAWING:
            # Draw preview ellipse
            self.draw_preview(scene_pos.x(), scene_pos.y())

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the ellipse being created"""
        # Clear previous preview
        self.clear_temp_objects()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(current_x, current_y)

        if len(self.points) == 1:
            # Drawing from first corner to opposite corner
            p1 = self.points[0]
            p2 = point

            # Calculate bounding box coordinates
            x1, y1 = min(p1.x, p2.x), min(p1.y, p2.y)
            x2, y2 = max(p1.x, p2.x), max(p1.y, p2.y)

            # Calculate center and radii
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            rad_x = (x2 - x1) / 2
            rad_y = (y2 - y1) / 2

            # Draw temporary ellipse using QGraphicsEllipseItem
            pen = QPen(QColor("black"), 3.0)
            pen.setCosmetic(True)
            pen.setDashPattern([2, 2])  # Dashed line for preview
            ellipse_item = self.scene.addEllipse(
                QRectF(x1, y1, x2 - x1, y2 - y1), pen
            )
            self.temp_objects.append(ellipse_item)

            # Draw bounding box
            pen_gray = QPen(QColor("gray"), 3.0)
            pen_gray.setCosmetic(True)
            pen_gray.setDashPattern([2, 2])  # Dashed line for preview
            box_item = self.scene.addRect(
                QRectF(x1, y1, x2 - x1, y2 - y1), pen_gray
            )
            self.temp_objects.append(box_item)

            # Draw center point
            center_h_item = self.scene.addLine(
                center_x - rad_x, center_y,
                center_x + rad_x, center_y,
                pen_gray
            )
            self.temp_objects.append(center_h_item)
            center_v_item = self.scene.addLine(
                center_x, center_y - rad_y,
                center_x, center_y + rad_y,
                pen_gray
            )
            self.temp_objects.append(center_v_item)

        self.draw_points()

    def create_object(self) -> Optional[CadObject]:
        """Create an ellipse object from the collected points"""
        if len(self.points) != 2:
            return None

        p1 = self.points[0]
        p2 = self.points[1]

        # Calculate bounding box coordinates
        x1, y1 = min(p1.x, p2.x), min(p1.y, p2.y)
        x2, y2 = max(p1.x, p2.x), max(p1.y, p2.y)

        # Calculate center and radii
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        rad_x = (x2 - x1) / 2
        rad_y = (y2 - y1) / 2

        center = Point2D(center_x, center_y)

        # Create an ellipse object
        obj = EllipseCadObject(
            document=self.document,
            center_point=center,
            radius1=rad_x,
            radius2=rad_y,
            color=self.preferences.get("default_color", "black"),
            line_width=self.preferences.get("default_line_width", 0.05)
        )
        return obj


class Ellipse3CornerTool(CadTool):
    """
    CadTool for drawing ellipses by three corner points of bounding rectangle
    """

    # Class-level tool definition
    tool_definitions = [
        ToolDefinition(
            token="ELLIPSE3CRN",
            name="Ellipse by 3 Corners",
            category=ToolCategory.ELLIPSES,
            icon="tool-ellipse3crn",
            cursor="crosshair",
            is_creator=True,
            secondary_key="R",
            node_info=["First Corner", "Second Corner", "Third Corner"]
        )
    ]

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        if hasattr(event, 'scenePos'):
            scene_pos = event.scenePos()
        else:
            scene_pos = QPointF(event.x, event.y)

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(scene_pos.x(), scene_pos.y())

        if self.state == ToolState.ACTIVE:
            # First point - first corner of bounding rectangle
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING:
            self.points.append(point)
            if len(self.points) == 3:
                # Third point completes the ellipse
                self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if hasattr(event, 'scenePos'):
            scene_pos = event.scenePos()
        else:
            scene_pos = QPointF(event.x, event.y)

        if self.state == ToolState.DRAWING:
            self.draw_preview(scene_pos.x(), scene_pos.y())

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the ellipse being created"""
        # Clear previous preview
        self.clear_temp_objects()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(current_x, current_y)

        pen = QPen(QColor("black"), 3.0)
        pen.setCosmetic(True)
        pen.setDashPattern([2, 2])  # Dashed line for preview

        pen_gray = QPen(QColor("gray"), 3.0)
        pen_gray.setCosmetic(True)
        pen_gray.setDashPattern([2, 2])  # Dashed line for preview

        if len(self.points) == 1:
            # Show line from first point to current
            line_item = self.scene.addLine(
                self.points[0].x, self.points[0].y,
                point.x, point.y,
                pen_gray
            )
            self.temp_objects.append(line_item)

        elif len(self.points) == 2:
            # Drawing from first two corners - show rectangle preview
            p1, p2 = self.points[0], self.points[1]
            p3 = point
            p4 = p1 - p2 + p3

            # Show partial parallelogram outline
            rect_item = self.scene.addPolygon(
                QPolygonF([
                    p1.to_qpointf(),
                    p2.to_qpointf(),
                    p3.to_qpointf(),
                    p4.to_qpointf()
                ]),
                pen_gray
            )
            self.temp_objects.append(rect_item)

            # Calculate ellipse from three corners
            ellipse = Ellipse.from_parallelogram_corners(p1, p2, p3)
            if ellipse and ellipse.radius1 > 0 and ellipse.radius2 > 0:
                # Draw preview ellipse
                ellipse_item = self.scene.addEllipse(
                    QRectF(
                        ellipse.center.x - ellipse.radius1,
                        ellipse.center.y - ellipse.radius2,
                        2 * ellipse.radius1, 2 * ellipse.radius2
                    ),
                    pen
                )
                ellipse_item.setTransformOriginPoint(ellipse.center.x, ellipse.center.y)
                ellipse_item.setRotation(ellipse.rotation_degrees)
                self.temp_objects.append(ellipse_item)

        self.draw_points()

    def create_object(self) -> Optional[CadObject]:
        """Create an ellipse object from the collected points"""
        if len(self.points) != 3:
            return None

        p1, p2, p3 = self.points
        ellipse = Ellipse.from_parallelogram_corners(p1, p2, p3)
        if not ellipse:
            return None

        # Create an ellipse object
        obj = EllipseCadObject(
            document=self.document,
            center_point=ellipse.center,
            radius1=ellipse.radius1,
            radius2=ellipse.radius2,
            rotation_degrees=ellipse.rotation_degrees,
            color=self.preferences.get("default_color", "black"),
            line_width=self.preferences.get("default_line_width", 0.05)
        )
        return obj


class EllipseCenterTangentTool(CadTool):
    """CadTool for drawing ellipses by center point and tangent constraints"""

    # Class-level tool definition
    tool_definitions = [
        ToolDefinition(
            token="ELLIPSECTRTAN",
            name="Ellipse Center-Tangent",
            category=ToolCategory.ELLIPSES,
            icon="tool-ellipsectrtan",
            cursor="crosshair",
            is_creator=True,
            secondary_key="T",
            node_info=["Center Point2D", "Tangent Point2D 1", "Tangent Point2D 2"]
        )
    ]

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        if hasattr(event, 'scenePos'):
            scene_pos = event.scenePos()
        else:
            scene_pos = QPointF(event.x, event.y)

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(scene_pos.x(), scene_pos.y())

        if self.state == ToolState.ACTIVE:
            # First point - center of ellipse
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING:
            self.points.append(point)
            if len(self.points) == 3:
                # Third point completes the ellipse
                self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if hasattr(event, 'scenePos'):
            scene_pos = event.scenePos()
        else:
            scene_pos = QPointF(event.x, event.y)

        if self.state == ToolState.DRAWING:
            # Draw preview ellipse
            self.draw_preview(scene_pos.x(), scene_pos.y())

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the ellipse being created"""
        # Clear previous preview
        self.clear_temp_objects()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(current_x, current_y)

        if len(self.points) == 1:
            # Show line from center to current point (first tangent)
            center = self.points[0]
            line_item = QGraphicsLineItem(
                center.x, center.y, point.x, point.y
            )
            pen = QPen(QColor("gray"), 3.0)
            pen.setCosmetic(True)
            pen.setDashPattern([2, 2])  # Dashed line for preview
            line_item.setPen(pen)
            self.scene.addItem(line_item)
            self.temp_objects.append(line_item)

            # Show radius distance
            distance = math.sqrt((point.x - center.x)**2 +
                                 (point.y - center.y)**2)
            text_item = QGraphicsTextItem(f"R1: {distance:.1f}")
            text_item.setPos(center.x + 10, center.y + 10)
            text_item.setDefaultTextColor("gray")
            self.scene.addItem(text_item)
            self.temp_objects.append(text_item)

        elif len(self.points) == 2:
            # Show lines from center to both tangent points
            center, t1 = self.points[0], self.points[1]

            # Line to first tangent point
            line1_item = QGraphicsLineItem(center.x, center.y, t1.x, t1.y)
            pen_gray = QPen(QColor("gray"), 3.0)
            pen_gray.setCosmetic(True)
            pen_gray.setDashPattern([2, 2])  # Dashed line for preview
            line1_item.setPen(pen_gray)
            self.scene.addItem(line1_item)
            self.temp_objects.append(line1_item)

            # Line to current point (second tangent)
            line2_item = QGraphicsLineItem(center.x, center.y,
                                           point.x, point.y)
            line2_item.setPen(pen_gray)
            self.scene.addItem(line2_item)
            self.temp_objects.append(line2_item)

            # Calculate ellipse from center and two tangent points
            center_x, center_y, rad_x, rad_y, angle = (
                self._calculate_ellipse_from_center_tangents(center, t1, point)
            )

            if rad_x > 0 and rad_y > 0:
                # Draw preview ellipse (approximation)
                ellipse_item = QGraphicsEllipseItem(
                    QRectF(center_x - rad_x, center_y - rad_y,
                           2 * rad_x, 2 * rad_y)
                )
                pen = QPen(QColor("black"), 3.0)
                pen.setCosmetic(True)
                pen.setDashPattern([2, 2])  # Dashed line for preview
                ellipse_item.setPen(pen)
                self.scene.addItem(ellipse_item)
                self.temp_objects.append(ellipse_item)

                # Show radii values
                text1_item = QGraphicsTextItem(f"Rx: {rad_x:.1f}")
                text1_item.setPos(center_x + rad_x + 5, center_y)
                text1_item.setDefaultTextColor("black")
                self.scene.addItem(text1_item)
                self.temp_objects.append(text1_item)

                text2_item = QGraphicsTextItem(f"Ry: {rad_y:.1f}")
                text2_item.setPos(center_x, center_y + rad_y + 5)
                text2_item.setDefaultTextColor("black")
                self.scene.addItem(text2_item)
                self.temp_objects.append(text2_item)
        self.draw_points()

    def _calculate_ellipse_from_center_tangents(self, center: Point2D,
                                                t1: Point2D, t2: Point2D):
        """Calculate ellipse parameters from center and two tangent points
        """
        # Calculate distances from center to tangent points
        d1 = math.sqrt((t1.x - center.x)**2 + (t1.y - center.y)**2)
        d2 = math.sqrt((t2.x - center.x)**2 + (t2.y - center.y)**2)

        # Calculate angles
        angle1 = math.atan2(t1.y - center.y, t1.x - center.x)
        angle2 = math.atan2(t2.y - center.y, t2.x - center.x)

        # For simplicity, use the distances as the semi-major and
        # semi-minor axes. In a more sophisticated implementation,
        # this would involve solving the tangent conditions for an ellipse
        rad_x = max(d1, d2)
        rad_y = min(d1, d2)

        # Calculate rotation angle (average of the two tangent angles)
        angle = (angle1 + angle2) / 2

        return center.x, center.y, rad_x, rad_y, angle

    def create_object(self) -> Optional[CadObject]:
        """Create an ellipse object from the collected points"""
        if len(self.points) != 3:
            return None

        center, t1, t2 = self.points
        center_x, center_y, rad_x, rad_y, angle = (
            self._calculate_ellipse_from_center_tangents(center, t1, t2)
        )

        # Create an ellipse object
        obj = EllipseCadObject(
            document=self.document,
            center_point=center,
            radius1=rad_x,
            radius2=rad_y,
            rotation_degrees=angle,
            color=self.preferences.get("default_color", "black"),
            line_width=self.preferences.get("default_line_width", 0.05)
        )
        return obj


class EllipseOppositeTangentTool(CadTool):
    """CadTool for drawing ellipses using opposite tangent constraints"""

    # Class-level tool definition
    tool_definitions = [
        ToolDefinition(
            token="ELLIPSEOPPTAN",
            name="Ellipse Opposite Tangents",
            category=ToolCategory.ELLIPSES,
            icon="tool-ellipseopptan",
            cursor="crosshair",
            is_creator=True,
            secondary_key="O",
            node_info=["First Tangent", "Opposite Tangent", "Size Point2D"]
        )
    ]

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        if hasattr(event, 'scenePos'):
            scene_pos = event.scenePos()
        else:
            scene_pos = QPointF(event.x, event.y)

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(scene_pos.x(), scene_pos.y())

        if self.state == ToolState.ACTIVE:
            # First point - first tangent line point
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING:
            self.points.append(point)
            if len(self.points) == 3:
                # Third point completes the ellipse
                self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if hasattr(event, 'scenePos'):
            scene_pos = event.scenePos()
        else:
            scene_pos = QPointF(event.x, event.y)

        if self.state == ToolState.DRAWING:
            # Draw preview ellipse
            self.draw_preview(scene_pos.x(), scene_pos.y())

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the ellipse being created"""
        # Clear previous preview
        self.clear_temp_objects()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(current_x, current_y)

        if len(self.points) == 1:
            # Show line representing first tangent
            t1 = self.points[0]
            line_item = QGraphicsLineItem(
                t1.x - 50, t1.y, t1.x + 50, t1.y  # Horizontal tangent line
            )
            pen = QPen(QColor("gray"), 3.0)
            pen.setCosmetic(True)
            pen.setDashPattern([2, 2])  # Dashed line for preview
            line_item.setPen(pen)
            self.scene.addItem(line_item)
            self.temp_objects.append(line_item)

            # Show line to current point
            line2_item = QGraphicsLineItem(t1.x, t1.y, point.x, point.y)
            line2_item.setPen(pen)
            self.scene.addItem(line2_item)
            self.temp_objects.append(line2_item)

        elif len(self.points) == 2:
            # Show both tangent lines
            t1, t2 = self.points[0], self.points[1]

            # First tangent line
            line1_item = QGraphicsLineItem(
                t1.x - 50, t1.y, t1.x + 50, t1.y
            )
            pen_gray = QPen(QColor("gray"), 3.0)
            pen_gray.setCosmetic(True)
            pen_gray.setDashPattern([2, 2])  # Dashed line for preview
            line1_item.setPen(pen_gray)
            self.scene.addItem(line1_item)
            self.temp_objects.append(line1_item)

            # Second tangent line (opposite)
            line2_item = QGraphicsLineItem(
                t2.x - 50, t2.y, t2.x + 50, t2.y
            )
            line2_item.setPen(pen_gray)
            self.scene.addItem(line2_item)
            self.temp_objects.append(line2_item)

            # Line to size point
            line3_item = QGraphicsLineItem(
                (t1.x + t2.x) / 2, (t1.y + t2.y) / 2, point.x, point.y
            )
            line3_item.setPen(pen_gray)
            self.scene.addItem(line3_item)
            self.temp_objects.append(line3_item)

            # Calculate ellipse from opposite tangents and size point
            center_x, center_y, rad_x, rad_y = (
                self._calculate_ellipse_from_opposite_tangents(t1, t2, point)
            )

            if rad_x > 0 and rad_y > 0:
                # Draw preview ellipse
                ellipse_item = QGraphicsEllipseItem(
                    QRectF(center_x - rad_x, center_y - rad_y,
                           2 * rad_x, 2 * rad_y)
                )
                pen = QPen(QColor("black"), 3.0)
                pen.setCosmetic(True)
                pen.setDashPattern([2, 2])  # Dashed line for preview
                ellipse_item.setPen(pen)
                self.scene.addItem(ellipse_item)
                self.temp_objects.append(ellipse_item)
        self.draw_points()

    def _calculate_ellipse_from_opposite_tangents(self, t1: Point2D, t2: Point2D,
                                                  size_point: Point2D):
        """Calculate ellipse parameters from opposite tangent points and a
        size point"""
        # Calculate center as midpoint between tangents
        center_x = (t1.x + t2.x) / 2
        center_y = (t1.y + t2.y) / 2

        # Calculate distance between tangents (this will be one diameter)
        distance_between_tangents = math.sqrt((t2.x - t1.x)**2 +
                                              (t2.y - t1.y)**2)

        # Distance from center to size point determines the other radius
        distance_to_size = math.sqrt((size_point.x - center_x)**2 +
                                     (size_point.y - center_y)**2)

        # Determine which is the major and minor axis
        rad_x = distance_between_tangents / 2
        rad_y = distance_to_size

        # Ensure rad_x >= rad_y (major axis convention)
        if rad_y > rad_x:
            rad_x, rad_y = rad_y, rad_x

        return center_x, center_y, rad_x, rad_y

    def create_object(self) -> Optional[CadObject]:
        """Create an ellipse object from the collected points"""
        if len(self.points) != 3:
            return None

        t1, t2, size_point = self.points
        center_x, center_y, rad_x, rad_y = (
            self._calculate_ellipse_from_opposite_tangents(t1, t2, size_point)
        )

        center = Point2D(center_x, center_y)

        # Create an ellipse object
        obj = EllipseCadObject(
            document=self.document,
            center_point=center,
            radius1=rad_x,
            radius2=rad_y,
            color=self.preferences.get("default_color", "black"),
            line_width=self.preferences.get("default_line_width", 0.05)
        )
        return obj
