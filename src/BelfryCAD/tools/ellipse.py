# filepath: /Users/gminette/dev/git-repos/pyBelfryCad/src/tools/ellipse.py
"""
Ellipse Drawing Tool Implementation

This module implements various ellipse drawing tools.
"""

import math
from typing import Optional, List

from ..models.cad_object import CadObject, ObjectType
from ..cad_geometry import Point2D
from .base import Tool, ToolState, ToolCategory, ToolDefinition


class EllipseCenterTool(Tool):
    """Tool for drawing ellipses by center point and corner point"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="ELLIPSECTR",
            name="Ellipse by Center",
            category=ToolCategory.ELLIPSES,
            icon="tool-ellipsectr",
            cursor="crosshair",
            is_creator=True,
            secondary_key="E",
            node_info=["Center Point2D", "Corner Point2D"]
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

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        # Get the snapped point based on current snap settings
        point = self.get_snap_point(event.x, event.y)

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
        if self.state == ToolState.DRAWING:
            # Draw preview ellipse
            self.draw_preview(event.x, event.y)

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

            # Draw temporary ellipse using QGraphicsEllipseItem
            from PySide6.QtWidgets import QGraphicsEllipseItem
            from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsTextItem
            from PySide6.QtCore import QRectF, Qt
            from PySide6.QtGui import QPen

            ellipse_item = QGraphicsEllipseItem(
                QRectF(center.x - rad_x, center.y - rad_y,
                       2 * rad_x, 2 * rad_y)
            )
            pen = QPen()
            pen.setColor("blue")
            pen.setStyle(Qt.DashLine)
            ellipse_item.setPen(pen)
            self.scene.addItem(ellipse_item)
            self.temp_objects.append(ellipse_item)

            # Draw major and minor axis lines
            line_h_item = QGraphicsLineItem(
                center.x - rad_x, center.y,
                center.x + rad_x, center.y
            )
            pen_line = QPen()
            pen_line.setColor("blue")
            pen_line.setStyle(Qt.DashLine)
            line_h_item.setPen(pen_line)
            self.scene.addItem(line_h_item)
            self.temp_objects.append(line_h_item)

            line_v_item = QGraphicsLineItem(
                center.x, center.y - rad_y,
                center.x, center.y + rad_y
            )
            line_v_item.setPen(pen_line)
            self.scene.addItem(line_v_item)
            self.temp_objects.append(line_v_item)

            # Add dimensions text
            if rad_x > 5 and rad_y > 5:  # Only show if large enough
                dim_x_item = QGraphicsTextItem(f"Width: {rad_x*2:.1f}")
                dim_x_item.setPos(center.x, center.y + rad_y + 15)
                dim_x_item.setDefaultTextColor("blue")
                self.scene.addItem(dim_x_item)
                self.temp_objects.append(dim_x_item)

                dim_y_item = QGraphicsTextItem(f"Height: {rad_y*2:.1f}")
                dim_y_item.setPos(center.x + rad_x + 15, center.y)
                dim_y_item.setDefaultTextColor("blue")
                self.scene.addItem(dim_y_item)
                self.temp_objects.append(dim_y_item)

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
        obj = CadObject(
            mainwin=self.main_window,
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.ELLIPSE,
            coords=[center, corner],
            attributes={
                'color': 'black',      # Default color
                'linewidth': 1,        # Default line width
                'rad_x': rad_x,        # Store X radius
                'rad_y': rad_y         # Store Y radius
            }
        )
        return obj


class EllipseDiagonalTool(Tool):
    "Tool for drawing ellipses by diagonal opposite corners of bounding box"

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="ELLIPSEDIAG",
            name="Ellipse by Diagonal",
            category=ToolCategory.ELLIPSES,
            icon="tool-ellipsediag",
            cursor="crosshair",
            secondary_key="D",
            is_creator=True,
            node_info=["First Corner", "Opposite Corner"]
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

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        # Get the snapped point based on current snap settings
        point = self.get_snap_point(event.x, event.y)

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
        if self.state == ToolState.DRAWING:
            # Draw preview ellipse
            self.draw_preview(event.x, event.y)

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
            from PySide6.QtWidgets import QGraphicsEllipseItem
            from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsTextItem
            from PySide6.QtWidgets import QGraphicsRectItem
            from PySide6.QtCore import QRectF, Qt
            from PySide6.QtGui import QPen, QBrush

            ellipse_item = QGraphicsEllipseItem(
                QRectF(x1, y1, x2 - x1, y2 - y1)
            )
            pen = QPen()
            pen.setColor("blue")
            pen.setStyle(Qt.DashLine)
            ellipse_item.setPen(pen)
            self.scene.addItem(ellipse_item)
            self.temp_objects.append(ellipse_item)

            # Draw bounding box
            box_item = QGraphicsRectItem(QRectF(x1, y1, x2 - x1, y2 - y1))
            pen_gray = QPen()
            pen_gray.setColor("gray")
            pen_gray.setStyle(Qt.DashLine)
            box_item.setPen(pen_gray)
            self.scene.addItem(box_item)
            self.temp_objects.append(box_item)

            # Draw center point
            center_item = QGraphicsEllipseItem(
                QRectF(center_x - 3, center_y - 3, 6, 6)
            )
            center_item.setPen(QPen("gray"))
            center_item.setBrush(QBrush("gray"))
            self.scene.addItem(center_item)
            self.temp_objects.append(center_item)

            # Draw major and minor axis lines
            line_h_item = QGraphicsLineItem(
                center_x - rad_x, center_y,
                center_x + rad_x, center_y
            )
            line_h_item.setPen(QPen("blue"))
            self.scene.addItem(line_h_item)
            self.temp_objects.append(line_h_item)

            line_v_item = QGraphicsLineItem(
                center_x, center_y - rad_y,
                center_x, center_y + rad_y
            )
            line_v_item.setPen(QPen("blue"))
            self.scene.addItem(line_v_item)
            self.temp_objects.append(line_v_item)

            # Add dimensions text
            if rad_x > 5 and rad_y > 5:  # Only show if large enough
                dim_x_item = QGraphicsTextItem(f"Width: {rad_x*2:.1f}")
                dim_x_item.setPos(center_x, center_y + rad_y + 15)
                dim_x_item.setDefaultTextColor("blue")
                self.scene.addItem(dim_x_item)
                self.temp_objects.append(dim_x_item)

                dim_y_item = QGraphicsTextItem(f"Height: {rad_y*2:.1f}")
                dim_y_item.setPos(center_x + rad_x + 15, center_y)
                dim_y_item.setDefaultTextColor("blue")
                self.scene.addItem(dim_y_item)
                self.temp_objects.append(dim_y_item)

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
        obj = CadObject(
            mainwin=self.main_window,
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.ELLIPSE,
            coords=[center, Point2D(center_x + rad_x, center_y + rad_y)],
            attributes={
                'color': 'black',      # Default color
                'linewidth': 1,        # Default line width
                'rad_x': rad_x,        # Store X radius
                'rad_y': rad_y,        # Store Y radius
                'bounds': [x1, y1, x2, y2]  # Store bounding box
            }
        )
        return obj


class Ellipse3CornerTool(Tool):
    """Tool for drawing ellipses by three corner points of bounding rectangle
    """

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="ELLIPSE3CRN",
            name="Ellipse by 3 Corners",
            category=ToolCategory.ELLIPSES,
            icon="tool-ellipse3crn",
            cursor="crosshair",
            is_creator=True,
            secondary_key="R",
            node_info=["First Corner", "Second Corner", "Third Corner"]
        )]

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        pass

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        # Get the snapped point based on current snap settings
        point = self.get_snap_point(event.x, event.y)

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
        if self.state == ToolState.DRAWING:
            # Draw preview ellipse
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the ellipse being created"""
        # Clear previous preview
        self.clear_temp_objects()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(current_x, current_y)

        from PySide6.QtWidgets import (QGraphicsEllipseItem,
                                       QGraphicsLineItem,
                                       QGraphicsRectItem)
        from PySide6.QtCore import QRectF, Qt
        from PySide6.QtGui import QPen

        if len(self.points) == 1:
            # Show line from first point to current
            line_item = QGraphicsLineItem(
                self.points[0].x, self.points[0].y,
                point.x, point.y
            )
            pen = QPen()
            pen.setColor("gray")
            pen.setStyle(Qt.DashLine)
            line_item.setPen(pen)
            self.scene.addItem(line_item)
            self.temp_objects.append(line_item)

        elif len(self.points) == 2:
            # Drawing from first two corners - show rectangle preview
            p1, p2 = self.points[0], self.points[1]

            # Show partial rectangle outline
            rect_item = QGraphicsRectItem(
                QRectF(min(p1.x, p2.x), min(p1.y, p2.y),
                       abs(p2.x - p1.x), abs(p2.y - p1.y))
            )
            pen_gray = QPen()
            pen_gray.setColor("gray")
            pen_gray.setStyle(Qt.DashLine)
            rect_item.setPen(pen_gray)
            self.scene.addItem(rect_item)
            self.temp_objects.append(rect_item)

            # Show line to current point
            line_item = QGraphicsLineItem(p2.x, p2.y, point.x, point.y)
            line_item.setPen(pen_gray)
            self.scene.addItem(line_item)
            self.temp_objects.append(line_item)

            # Calculate ellipse from three corners
            center_x, center_y, rad_x, rad_y = (
                self._calculate_ellipse_from_corners(p1, p2, point)
            )

            if rad_x > 0 and rad_y > 0:
                # Draw preview ellipse
                ellipse_item = QGraphicsEllipseItem(
                    QRectF(center_x - rad_x, center_y - rad_y,
                           2 * rad_x, 2 * rad_y)
                )
                pen = QPen()
                pen.setColor("blue")
                pen.setStyle(Qt.DashLine)
                ellipse_item.setPen(pen)
                self.scene.addItem(ellipse_item)
                self.temp_objects.append(ellipse_item)

                # Draw bounding rectangle
                full_rect_item = QGraphicsRectItem(
                    QRectF(center_x - rad_x, center_y - rad_y,
                           2 * rad_x, 2 * rad_y)
                )
                full_rect_item.setPen(pen_gray)
                self.scene.addItem(full_rect_item)
                self.temp_objects.append(full_rect_item)

    def _calculate_ellipse_from_corners(self, p1: Point2D, p2: Point2D,
                                        p3: Point2D):
        """Calculate ellipse parameters from three corner points"""
        # The three points define corners of a rectangle
        # We need to determine which corner the third point represents

        # Calculate potential rectangle bounds
        x_coords = [p1.x, p2.x, p3.x]
        y_coords = [p1.y, p2.y, p3.y]

        # Find the bounds that would make a complete rectangle
        min_x = min(x_coords)
        max_x = max(x_coords)
        min_y = min(y_coords)
        max_y = max(y_coords)

        # Center and radii
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        rad_x = (max_x - min_x) / 2
        rad_y = (max_y - min_y) / 2

        return center_x, center_y, rad_x, rad_y

    def create_object(self) -> Optional[CadObject]:
        """Create an ellipse object from the collected points"""
        if len(self.points) != 3:
            return None

        p1, p2, p3 = self.points
        center_x, center_y, rad_x, rad_y = (
            self._calculate_ellipse_from_corners(p1, p2, p3)
        )

        center = Point2D(center_x, center_y)

        # Create an ellipse object
        obj = CadObject(
            mainwin=self.main_window,
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.ELLIPSE,
            coords=[center, Point2D(center_x + rad_x, center_y + rad_y)],
            attributes={
                'color': 'black',
                'linewidth': 1,
                'rad_x': rad_x,
                'rad_y': rad_y,
                'bounds': [center_x - rad_x, center_y - rad_y,
                           center_x + rad_x, center_y + rad_y],
                'corner_points': [p1, p2, p3]  # Store original corners
            }
        )
        return obj


class EllipseCenterTangentTool(Tool):
    """Tool for drawing ellipses by center point and tangent constraints"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="ELLIPSECTRTAN",
            name="Ellipse Center-Tangent",
            category=ToolCategory.ELLIPSES,
            icon="tool-ellipsectrtan",
            cursor="crosshair",
            is_creator=True,
            secondary_key="T",
            node_info=["Center Point2D", "Tangent Point2D 1", "Tangent Point2D 2"]
        )]

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        pass

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        # Get the snapped point based on current snap settings
        point = self.get_snap_point(event.x, event.y)

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
        if self.state == ToolState.DRAWING:
            # Draw preview ellipse
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the ellipse being created"""
        # Clear previous preview
        self.clear_temp_objects()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(current_x, current_y)

        from PySide6.QtWidgets import (QGraphicsEllipseItem,
                                       QGraphicsLineItem,
                                       QGraphicsTextItem)
        from PySide6.QtCore import QRectF, Qt
        from PySide6.QtGui import QPen

        if len(self.points) == 1:
            # Show line from center to current point (first tangent)
            center = self.points[0]
            line_item = QGraphicsLineItem(
                center.x, center.y, point.x, point.y
            )
            pen = QPen()
            pen.setColor("gray")
            pen.setStyle(Qt.DashLine)
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
            pen_gray = QPen()
            pen_gray.setColor("gray")
            pen_gray.setStyle(Qt.DashLine)
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
                pen = QPen()
                pen.setColor("blue")
                pen.setStyle(Qt.DashLine)
                ellipse_item.setPen(pen)
                self.scene.addItem(ellipse_item)
                self.temp_objects.append(ellipse_item)

                # Show radii values
                text1_item = QGraphicsTextItem(f"Rx: {rad_x:.1f}")
                text1_item.setPos(center_x + rad_x + 5, center_y)
                text1_item.setDefaultTextColor("blue")
                self.scene.addItem(text1_item)
                self.temp_objects.append(text1_item)

                text2_item = QGraphicsTextItem(f"Ry: {rad_y:.1f}")
                text2_item.setPos(center_x, center_y + rad_y + 5)
                text2_item.setDefaultTextColor("blue")
                self.scene.addItem(text2_item)
                self.temp_objects.append(text2_item)

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
        obj = CadObject(
            mainwin=self.main_window,
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.ELLIPSE,
            coords=[center, Point2D(center_x + rad_x, center_y + rad_y)],
            attributes={
                'color': 'black',
                'linewidth': 1,
                'rad_x': rad_x,
                'rad_y': rad_y,
                'rotation': angle,
                'tangent_points': [t1, t2]  # Store the tangent points
            }
        )
        return obj


class EllipseOppositeTangentTool(Tool):
    """Tool for drawing ellipses using opposite tangent constraints"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="ELLIPSEOPPTAN",
            name="Ellipse Opposite Tangents",
            category=ToolCategory.ELLIPSES,
            icon="tool-ellipseopptan",
            cursor="crosshair",
            is_creator=True,
            secondary_key="O",
            node_info=["First Tangent", "Opposite Tangent", "Size Point2D"]
        )]

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        pass

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        # Get the snapped point based on current snap settings
        point = self.get_snap_point(event.x, event.y)

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
        if self.state == ToolState.DRAWING:
            # Draw preview ellipse
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the ellipse being created"""
        # Clear previous preview
        self.clear_temp_objects()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(current_x, current_y)

        from PySide6.QtWidgets import (QGraphicsEllipseItem,
                                       QGraphicsLineItem)
        from PySide6.QtCore import QRectF, Qt
        from PySide6.QtGui import QPen

        if len(self.points) == 1:
            # Show line representing first tangent
            t1 = self.points[0]
            line_item = QGraphicsLineItem(
                t1.x - 50, t1.y, t1.x + 50, t1.y  # Horizontal tangent line
            )
            pen = QPen()
            pen.setColor("gray")
            pen.setStyle(Qt.DashLine)
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
            pen_gray = QPen()
            pen_gray.setColor("gray")
            pen_gray.setStyle(Qt.DashLine)
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
                pen = QPen()
                pen.setColor("blue")
                pen.setStyle(Qt.DashLine)
                ellipse_item.setPen(pen)
                self.scene.addItem(ellipse_item)
                self.temp_objects.append(ellipse_item)

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
        obj = CadObject(
            mainwin=self.main_window,
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.ELLIPSE,
            coords=[center, Point2D(center_x + rad_x, center_y + rad_y)],
            attributes={
                'color': 'black',
                'linewidth': 1,
                'rad_x': rad_x,
                'rad_y': rad_y,
                'tangent_points': [t1, t2],  # Store the tangent points
                'size_point': size_point     # Store the size reference point
            }
        )
        return obj
