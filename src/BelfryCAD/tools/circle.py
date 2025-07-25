"""
Circle Drawing Tool Implementation

This module implements a circle drawing tool based on the TCL tool
implementation.
"""

import math
from typing import Optional, List

from ..core.cad_objects import CADObject, ObjectType, Point
from .base import Tool, ToolState, ToolCategory, ToolDefinition
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPen
from PySide6.QtWidgets import QGraphicsEllipseItem



class CircleObject(CADObject):
    """Circle object - center and radius"""

    def __init__(
            self,
            mainwin: 'MainWindow',
            object_id: int,
            **kwargs
    ):
        super().__init__(mainwin, object_id, **kwargs)


    def draw_object(self):
        scene = self.mainwin.get_scene().scene
        center = self.coords[0]
        delta = self.coords[1] - center
        radius = math.sqrt(delta.x**2 + delta.y**2)
        obj = scene.addEllipse(
            center.x - radius,
            center.y - radius,
            2 * radius,
            2 * radius
        )
        scene.tagAsObject(obj)

    def draw_controls(self):
        scene = self.mainwin.get_scene().scene
        center = self.coords[0]
        radpt = self.coords[1]
        cp1 = scene.addControlPoint(self.object_id, center.x, center.y, 0)
        cp2 = scene.addControlPoint(self.object_id, radpt.x, radpt.y, 1)
        scene.tagAsControlPoint(cp1)
        scene.tagAsControlPoint(cp2)

    @property
    def center(self) -> Point:
        return self.coords[0]

    @center.setter
    def center(self, value: Point):
        self.coords[0] = value
        self.draw_object()
        self.draw_controls()

    @property
    def radius(self) -> float:
        delta = self.coords[1] - self.coords[0]
        return math.sqrt(delta.x**2 + delta.y**2)

    @radius.setter
    def radius(self, value: float):
        delta = self.coords[1] - self.coords[0]
        dist = math.sqrt(delta.x**2 + delta.y**2)
        delta = delta / dist * value
        self.coords[1] = self.coords[0] + delta
        self.draw_object()
        self.draw_controls()

    @property
    def diameter(self) -> float:
        return 2 * self.radius

    @diameter.setter
    def diameter(self, value: float):
        self.radius = value / 2



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
            node_info=["Center Point", "Radius Point"]
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
        # Get the snapped point based on current snap settings
        point = self.get_snap_point(event.x, event.y)

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
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the circle being created"""
        # Clear previous preview
        self.clear_temp_objects()

        if len(self.points) == 1:
            # Get the snapped point based on current snap settings
            point = self.get_snap_point(current_x, current_y)

            # Calculate radius
            center_point = self.points[0]
            radius = math.sqrt((point.x - center_point.x)**2 +
                               (point.y - center_point.y)**2)

            # Create temporary ellipse using CadScene's addEllipse method
            pen = QPen()
            pen.setColor("blue")
            pen.setWidthF(0.1)
            pen.setStyle(Qt.PenStyle.DashLine)
            ellipse_item = self.scene.addEllipse(
                center_point.x - radius, center_point.y - radius,
                2 * radius, 2 * radius,
                pen=pen
            )
            self.scene.tagAsConstruction(ellipse_item)

    def create_object(self) -> Optional[CADObject]:
        """Create a circle object from the collected points"""
        if len(self.points) != 2:
            return None

        # Calculate radius
        center_point = self.points[0]
        radius_point = self.points[1]
        radius = math.sqrt(
            (radius_point.x - center_point.x)**2 +
            (radius_point.y - center_point.y)**2
        )

        # Create a circle object
        obj = CircleObject(
            mainwin=self.main_window,
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.CIRCLE,
            layer=self.document.objects.current_layer,
            coords=[center_point, radius_point],  # Only need center point
            attributes={
                'color': 'black',  # Default color
                'linewidth': 1    # Default line width
            }
        )
        return obj


class Circle2PTObject(CADObject):
    """Circle object defined by 2 points (diameter endpoints)"""

    def __init__(self, mainwin: 'MainWindow', object_id: int, point1: Point, point2: Point, **kwargs):
        super().__init__(
            mainwin, object_id, ObjectType.CIRCLE, coords=[point1, point2], **kwargs)

    @property
    def point1(self) -> Point:
        return self.coords[0]

    @property
    def point2(self) -> Point:
        return self.coords[1]

    @property
    def center(self) -> Point:
        """Calculate center point between the two points"""
        p1, p2 = self.point1, self.point2
        return Point((p1.x + p2.x) / 2.0, (p1.y + p2.y) / 2.0)

    @property
    def radius(self) -> float:
        """Calculate radius as half the distance between points"""
        p1, p2 = self.point1, self.point2
        return math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2) / 2.0


class Circle3PTObject(CADObject):
    """Circle object defined by 3 points on the circumference"""

    def __init__(
            self,
            mainwin: 'MainWindow',
            object_id: int,
            point1: Point,
            point2: Point,
            point3: Point,
            **kwargs
    ):
        super().__init__(
            mainwin, object_id, ObjectType.CIRCLE,
            coords=[point1, point2, point3],
            **kwargs)
        self._calculate_circle()

    @property
    def point1(self) -> Point:
        return self.coords[0]

    @property
    def point2(self) -> Point:
        return self.coords[1]

    @property
    def point3(self) -> Point:
        return self.coords[2]

    def _calculate_circle(self):
        """Calculate center and radius from three points"""
        p1, p2, p3 = self.point1, self.point2, self.point3

        # Check if points are collinear
        col = p1.x * (p2.y - p3.y) + p2.x * \
            (p3.y - p1.y) + p3.x * (p1.y - p2.y)

        if abs(col) < 1e-6:
            # Points are collinear - this becomes a line
            self.attributes['is_line'] = True
            self.attributes['center'] = Point(0, 0)
            self.attributes['radius'] = 0
            return

        self.attributes['is_line'] = False

        # Calculate center using perpendicular bisector method
        mx1 = (p1.x + p3.x) / 2.0
        my1 = (p1.y + p3.y) / 2.0
        mx2 = (p2.x + p3.x) / 2.0
        my2 = (p2.y + p3.y) / 2.0

        if abs(p3.y - p1.y) < 1e-6:
            # Segment1 is horizontal
            m2 = -(p2.x - p3.x) / (p2.y - p3.y)
            c2 = my2 - m2 * mx2
            cx = mx1
            cy = m2 * cx + c2
        elif abs(p3.y - p2.y) < 1e-6:
            # Segment2 is horizontal
            m1 = -(p3.x - p1.x) / (p3.y - p1.y)
            c1 = my1 - m1 * mx1
            cx = mx2
            cy = m1 * cx + c1
        else:
            # General case
            m1 = -(p3.x - p1.x) / (p3.y - p1.y)
            m2 = -(p2.x - p3.x) / (p2.y - p3.y)
            c1 = my1 - m1 * mx1
            c2 = my2 - m2 * mx2
            cx = (c2 - c1) / (m1 - m2)
            cy = m1 * cx + c1

        center = Point(cx, cy)
        radius = math.sqrt((p1.y - cy)**2 + (p1.x - cx)**2)

        self.attributes['center'] = center
        self.attributes['radius'] = radius

    @property
    def center(self) -> Point:
        """Get the calculated center point"""
        return self.attributes.get('center', Point(0, 0))

    @property
    def radius(self) -> float:
        """Get the calculated radius"""
        return self.attributes.get('radius', 0.0)

    @property
    def is_line(self) -> bool:
        """Check if the three points are collinear (making this a line)"""
        return self.attributes.get('is_line', False)


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
            node_info=["First Point", "Second Point"]
        )
    ]

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        pass

    def handle_mouse_down(self, event):
        """Handle mouse down events"""
        scene_pos = event.scenePos()
        point = Point(scene_pos.x(), scene_pos.y())

        if self.state == ToolState.INIT:
            self.points = [point]
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING:
            self.points.append(point)
            # Create the circle object
            obj = self.create_object()
            if obj:
                self.document.objects.add_object(obj)
                self.object_created.emit(obj)
            self.reset()

    def handle_mouse_move(self, event):
        """Handle mouse move events for preview"""
        if self.state == ToolState.DRAWING and len(self.points) == 1:
            scene_pos = event.scenePos()
            current_point = Point(scene_pos.x(), scene_pos.y())
            self.draw_preview(scene_pos.x(), scene_pos.y())

    def draw_preview(self, current_x, current_y):
        """Draw preview of the circle"""
        self.clear_temp_objects()

        if len(points) == 2:
            # Calculate circle center and radius
            p1 = self.points[0]
            p2 = [current_x, current_y]
            center_x = (p1.x + current_x) / 2.0
            center_y = (p1.y + current_y) / 2.0
            radius = math.sqrt(
                (current_x - p1.x)**2 + (current_y - p1.y)**2
            ) / 2.0

            ellipse_item = QGraphicsEllipseItem(
                QRectF(center_x - radius, center_y - radius,
                       2 * radius, 2 * radius)
            )
            pen = QPen()
            pen.setColor("blue")
            pen.setStyle(Qt.PenStyle.DashLine)
            ellipse_item.setPen(pen)

            self.scene.addItem(ellipse_item)
            self.scene.tagAsConstruction(ellipse_item)

    def create_object(self) -> Optional[CADObject]:
        """Create a circle object from the collected points"""
        if len(self.points) != 2:
            return None

        obj = Circle2PTObject(
            mainwin=self.main_window,
            object_id=self.document.objects.get_next_id(),
            point1=self.points[0],
            point2=self.points[1],
            layer=self.document.objects.current_layer,
            attributes={
                'color': 'black',
                'linewidth': 1
            }
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
            node_info=["First Point", "Second Point", "Third Point"]
        )
    ]

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        pass

    def handle_mouse_down(self, event):
        """Handle mouse down events"""
        scene_pos = event.scenePos()
        point = Point(scene_pos.x(), scene_pos.y())

        if self.state == ToolState.INIT:
            self.points = [point]
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING:
            self.points.append(point)
            if len(self.points) == 3:
                # Create the circle object
                obj = self.create_object()
                if obj:
                    self.document.objects.add_object(obj)
                    self.object_created.emit(obj)
                self.reset()

    def handle_mouse_move(self, event):
        """Handle mouse move events for preview"""
        if self.state == ToolState.DRAWING:
            scene_pos = event.scenePos()
            current_point = Point(scene_pos.x(), scene_pos.y())

            if len(self.points) == 1:
                self.draw_preview([self.points[0], current_point])
            elif len(self.points) == 2:
                self.draw_preview(
                    [self.points[0], self.points[1], current_point])

    def draw_preview(self, points):
        """Draw preview of the circle"""
        # Clear previous preview
        self.clear_temp_objects()

        if len(points) == 3:
            # Calculate circle from 3 points
            p1, p2, p3 = points

            # Check if collinear
            col = p1.x * (p2.y - p3.y) + p2.x * \
                (p3.y - p1.y) + p3.x * (p1.y - p2.y)
            if abs(col) < 1e-6:
                # Draw line preview for collinear points
                from PySide6.QtWidgets import QGraphicsLineItem
                from PySide6.QtGui import QPen, Qt

                line_item = QGraphicsLineItem(p1.x, p1.y, p3.x, p3.y)
                pen = QPen()
                pen.setColor("red")
                pen.setStyle(Qt.PenStyle.DashLine)
                line_item.setPen(pen)

                self.scene.addItem(line_item)
                return

            # Calculate center and radius
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

            # Draw preview circle
            from PySide6.QtWidgets import QGraphicsEllipseItem
            from PySide6.QtCore import QRectF
            from PySide6.QtGui import QPen, Qt

            ellipse_item = QGraphicsEllipseItem(
                QRectF(cx - radius, cy - radius, 2 * radius, 2 * radius)
            )
            pen = QPen()
            pen.setColor("blue")
            pen.setStyle(Qt.PenStyle.DashLine)
            ellipse_item.setPen(pen)

            self.scene.addItem(ellipse_item)

        elif len(points) == 2:
            # Draw line preview between first two points
            from PySide6.QtWidgets import QGraphicsLineItem
            from PySide6.QtGui import QPen, Qt

            p1, p2 = points
            line_item = QGraphicsLineItem(p1.x, p1.y, p2.x, p2.y)
            pen = QPen()
            pen.setColor("gray")
            pen.setStyle(Qt.PenStyle.DashLine)
            line_item.setPen(pen)

            self.scene.addItem(line_item)

    def create_object(self) -> Optional[CADObject]:
        """Create a circle object from the collected points"""
        if len(self.points) != 3:
            return None

        obj = Circle3PTObject(
            mainwin=self.main_window,
            object_id=self.document.objects.get_next_id(),
            point1=self.points[0],
            point2=self.points[1],
            point3=self.points[2],
            layer=self.document.objects.current_layer,
            attributes={
                'color': 'black',
                'linewidth': 1
            }
        )
        return obj
