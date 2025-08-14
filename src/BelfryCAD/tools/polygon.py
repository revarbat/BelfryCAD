"""
Polygon Drawing Tool Implementation

This module implements various polygon drawing tools based on the original TCL
tools_polygons.tcl implementation, including rectangles and regular polygons.
"""

import math
from typing import Optional, List

from ..models.cad_object import CadObject, ObjectType
from ..cad_geometry import Point2D
from .base import Tool, ToolState, ToolCategory, ToolDefinition


class PolygonObject(CadObject):
    """Polygon object - list of vertices"""

    def __init__(self, object_id: int, vertices: List[Point2D], **kwargs):
        super().__init__(
            object_id, ObjectType.POLYGON, coords=vertices, **kwargs)

    def is_closed(self) -> bool:
        """Check if polygon is closed (first and last points are same)"""
        if len(self.coords) < 3:
            return False
        return (abs(self.coords[0].x - self.coords[-1].x) < 1e-6 and
                abs(self.coords[0].y - self.coords[-1].y) < 1e-6)

    def close(self):
        """Close the polygon by adding first point at end if not closed"""
        if not self.is_closed() and len(self.coords) >= 3:
            self.coords.append(Point2D(self.coords[0].x, self.coords[0].y))


class RectangleTool(Tool):
    """Tool for drawing rectangles by two diagonal corners"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="RECTANGLE",
            name="Rectangle",
            category=ToolCategory.POLYGONS,
            icon="tool-rectangle",
            cursor="crosshair",
            is_creator=True,
            secondary_key="R",
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
            # First point - first corner of rectangle
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING and len(self.points) == 1:
            # Second point - opposite corner of rectangle
            self.points.append(point)
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            # Draw preview rectangle
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the rectangle being created"""
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

            # Draw temporary rectangle using QGraphicsRectItem
            from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
            from PySide6.QtCore import QRectF, Qt
            from PySide6.QtGui import QPen

            rect_item = QGraphicsRectItem(QRectF(x1, y1, x2 - x1, y2 - y1))
            pen = QPen()
            pen.setColor("blue")
            pen.setStyle(Qt.DashLine)
            rect_item.setPen(pen)
            self.scene.addItem(rect_item)
            self.temp_objects.append(rect_item)

            # Add dimensions text
            width = x2 - x1
            height = y2 - y1

            if width > 10 and height > 10:  # Only show if large enough
                dim_x_item = QGraphicsTextItem(f"Width: {width:.1f}")
                dim_x_item.setPos((x1 + x2) / 2, y2 + 15)
                dim_x_item.setDefaultTextColor("blue")
                self.scene.addItem(dim_x_item)
                self.temp_objects.append(dim_x_item)

                dim_y_item = QGraphicsTextItem(f"Height: {height:.1f}")
                dim_y_item.setPos(x2 + 15, (y1 + y2) / 2)
                dim_y_item.setDefaultTextColor("blue")
                self.scene.addItem(dim_y_item)
                self.temp_objects.append(dim_y_item)

    def create_object(self) -> Optional[CadObject]:
        """Create a rectangle object from the collected points"""
        if len(self.points) != 2:
            return None

        p1 = self.points[0]
        p2 = self.points[1]

        # Calculate the four corners in counterclockwise order
        x1, y1 = min(p1.x, p2.x), min(p1.y, p2.y)
        x2, y2 = max(p1.x, p2.x), max(p1.y, p2.y)

        # Create points for all four corners
        corners = [
            Point2D(x1, y1),  # Bottom-left
            Point2D(x2, y1),  # Bottom-right
            Point2D(x2, y2),  # Top-right
            Point2D(x1, y2)   # Top-left
        ]

        # Create a rectangle object (as a polygon)
        obj = CadObject(
            mainwin=self.document_window,
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.POLYGON,
            coords=corners,
            attributes={
                'color': 'black',      # Default color
                'linewidth': 1,        # Default line width
                'closed': True,        # Closed polygon
                'is_rectangle': True,  # Mark as rectangle for special handling
                'width': x2 - x1,      # Store width
                'height': y2 - y1      # Store height
            }
        )
        return obj


class RoundedRectangleTool(Tool):
    """Tool for drawing rounded rectangles with adjustable corner radius"""

    def __init__(self, canvas, document, preferences):
        """Initialize the tool with the canvas, document and preferences"""
        super().__init__(canvas, document, preferences)

        # Default corner radius
        self.corner_radius = 10.0

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="RRECTANGLE",
            name="Rounded Rectangle",
            category=ToolCategory.POLYGONS,
            icon="tool-rrectangle",
            cursor="crosshair",
            is_creator=True,
            node_info=["First Corner", "Opposite Corner", "Corner Radius"]
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
            # First point - first corner of rectangle
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING and len(self.points) == 1:
            # Second point - opposite corner of rectangle
            self.points.append(point)
            self.state = ToolState.SIZING
        elif self.state == ToolState.SIZING and len(self.points) == 2:
            # Third point - determines corner radius
            self._set_radius_from_point(point)
            self.complete()

    def _set_radius_from_point(self, point: Point2D):
        """Set corner radius based on distance from rectangle edge"""
        if len(self.points) < 2:
            return

        p1, p2 = self.points[0], self.points[1]

        # Calculate rectangle bounds
        x1, y1 = min(p1.x, p2.x), min(p1.y, p2.y)
        x2, y2 = max(p1.x, p2.x), max(p1.y, p2.y)

        # Calculate distance from point to nearest edge
        dx_left = abs(point.x - x1)
        dx_right = abs(point.x - x2)
        dy_bottom = abs(point.y - y1)
        dy_top = abs(point.y - y2)

        # Use the minimum distance to any edge as radius
        self.corner_radius = min(dx_left, dx_right, dy_bottom, dy_top)

        # Limit radius to half the minimum dimension
        max_radius = min(x2 - x1, y2 - y1) / 2
        self.corner_radius = min(self.corner_radius, max_radius)

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            # Draw preview rectangle
            self.draw_preview(event.x, event.y)
        elif self.state == ToolState.SIZING:
            # Draw preview with radius sizing
            self.draw_radius_preview(event.x, event.y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the rectangle being created"""
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

            # Draw temporary rectangle outline
            self._draw_temp_rectangle(x1, y1, x2, y2, 0)

            # Add dimensions text
            width = x2 - x1
            height = y2 - y1

            if width > 10 and height > 10:  # Only show if large enough
                from PySide6.QtWidgets import QGraphicsTextItem

                dim_x_item = QGraphicsTextItem(f"Width: {width:.1f}")
                dim_x_item.setPos((x1 + x2) / 2, y2 + 15)
                dim_x_item.setDefaultTextColor("blue")
                self.scene.addItem(dim_x_item)
                self.temp_objects.append(dim_x_item)

                dim_y_item = QGraphicsTextItem(f"Height: {height:.1f}")
                dim_y_item.setPos(x2 + 15, (y1 + y2) / 2)
                dim_y_item.setDefaultTextColor("blue")
                self.scene.addItem(dim_y_item)
                self.temp_objects.append(dim_y_item)

    def draw_radius_preview(self, current_x, current_y):
        """Draw a preview with adjustable corner radius"""
        # Clear previous preview
        self.clear_temp_objects()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(current_x, current_y)

        if len(self.points) == 2:
            p1, p2 = self.points[0], self.points[1]

            # Calculate rectangle bounds
            x1, y1 = min(p1.x, p2.x), min(p1.y, p2.y)
            x2, y2 = max(p1.x, p2.x), max(p1.y, p2.y)

            # Calculate temporary radius from current point
            temp_radius = self._calc_radius_from_point(point, x1, y1, x2, y2)

            # Draw rounded rectangle with current radius
            self._draw_temp_rounded_rectangle(x1, y1, x2, y2, temp_radius)

            # Add radius text
            from PySide6.QtWidgets import QGraphicsTextItem
            radius_text = QGraphicsTextItem(f"Radius: {temp_radius:.1f}")
            radius_text.setPos(point.x + 10, point.y + 10)
            radius_text.setDefaultTextColor("blue")
            self.scene.addItem(radius_text)
            self.temp_objects.append(radius_text)

    def _calc_radius_from_point(self, point: Point2D, x1: float, y1: float,
                                x2: float, y2: float) -> float:
        """Calculate corner radius based on distance from rectangle edge"""
        # Calculate distance from point to nearest edge
        dx_left = abs(point.x - x1)
        dx_right = abs(point.x - x2)
        dy_bottom = abs(point.y - y1)
        dy_top = abs(point.y - y2)

        # Use the minimum distance to any edge as radius
        radius = min(dx_left, dx_right, dy_bottom, dy_top)

        # Limit radius to half the minimum dimension
        max_radius = min(x2 - x1, y2 - y1) / 2
        return min(radius, max_radius)

    def _draw_temp_rectangle(self, x1: float, y1: float, x2: float,
                             y2: float, radius: float):
        """Draw a temporary rectangle (rounded if radius > 0)"""
        if radius <= 0:
            # Regular rectangle
            from PySide6.QtWidgets import QGraphicsRectItem
            from PySide6.QtCore import QRectF, Qt
            from PySide6.QtGui import QPen

            rect_item = QGraphicsRectItem(QRectF(x1, y1, x2 - x1, y2 - y1))
            pen = QPen()
            pen.setColor("blue")
            pen.setStyle(Qt.DashLine)
            rect_item.setPen(pen)
            self.scene.addItem(rect_item)
            self.temp_objects.append(rect_item)
        else:
            # Rounded rectangle
            self._draw_temp_rounded_rectangle(x1, y1, x2, y2, radius)

    def _draw_temp_rounded_rectangle(self, x1: float, y1: float, x2: float,
                                     y2: float, radius: float):
        """Draw a temporary rounded rectangle using bezier curves"""
        # Generate vertices for rounded rectangle
        vertices = self._gen_rounded_rect_vertices(x1, y1, x2, y2, radius)

        if vertices:
            from PySide6.QtWidgets import QGraphicsPathItem
            from PySide6.QtGui import QPainterPath, QPen
            from PySide6.QtCore import Qt

            # Create a path for the rounded rectangle
            path = QPainterPath()
            if vertices:
                path.moveTo(vertices[0].x, vertices[0].y)
                for vertex in vertices[1:]:
                    path.lineTo(vertex.x, vertex.y)
                path.closeSubpath()

            path_item = QGraphicsPathItem(path)
            pen = QPen()
            pen.setColor("blue")
            pen.setStyle(Qt.DashLine)
            path_item.setPen(pen)
            self.scene.addItem(path_item)
            self.temp_objects.append(path_item)

    def _gen_rounded_rect_vertices(self, x1: float, y1: float, x2: float,
                                   y2: float, radius: float) -> List[Point2D]:
        """Generate vertices for a rounded rectangle using bezier curves"""
        if radius <= 0:
            # Regular rectangle
            return [Point2D(x1, y1), Point2D(x2, y1), Point2D(x2, y2), Point2D(x1, y2)]

        # Limit radius to half the minimum dimension
        max_radius = min(x2 - x1, y2 - y1) / 2
        radius = min(radius, max_radius)

        # Import bezier utilities
        from ..utils.bezutils import bezutil_append_bezier_arc

        # Build coordinate list using bezier arcs for corners
        coords = []

        # Start at bottom-left + radius, move clockwise
        # Bottom edge (left to right)
        coords.extend([x1 + radius, y1, x2 - radius, y1])

        # Bottom-right corner (90 degree arc from bottom to right)
        bezutil_append_bezier_arc(coords, x2 - radius, y1 + radius,
                                  radius, radius, -90, 90)

        # Right edge (bottom to top)
        coords.extend([x2, y1 + radius, x2, y2 - radius])

        # Top-right corner (90 degree arc from right to top)
        bezutil_append_bezier_arc(coords, x2 - radius, y2 - radius,
                                  radius, radius, 0, 90)

        # Top edge (right to left)
        coords.extend([x2 - radius, y2, x1 + radius, y2])

        # Top-left corner (90 degree arc from top to left)
        bezutil_append_bezier_arc(coords, x1 + radius, y2 - radius,
                                  radius, radius, 90, 90)

        # Left edge (top to bottom)
        coords.extend([x1, y2 - radius, x1, y1 + radius])

        # Bottom-left corner (90 degree arc from left to bottom)
        bezutil_append_bezier_arc(coords, x1 + radius, y1 + radius,
                                  radius, radius, 180, 90)

        # Convert coordinate list to Point2D objects
        vertices = []
        for i in range(0, len(coords), 2):
            if i + 1 < len(coords):
                vertices.append(Point2D(coords[i], coords[i + 1]))

        return vertices

    def create_object(self) -> Optional[CadObject]:
        """Create a rounded rectangle object from the collected points"""
        if len(self.points) < 2:
            return None

        p1 = self.points[0]
        p2 = self.points[1]

        # Calculate the rectangle bounds
        x1, y1 = min(p1.x, p2.x), min(p1.y, p2.y)
        x2, y2 = max(p1.x, p2.x), max(p1.y, p2.y)

        # If we have a third point, calculate radius from it
        if len(self.points) == 3:
            self._set_radius_from_point(self.points[2])

        # Generate vertices for the rounded rectangle
        vertices = self._gen_rounded_rect_vertices(x1, y1, x2, y2,
                                                   self.corner_radius)

        if not vertices:
            return None

        # Create a rounded rectangle object
        obj = CadObject(
            mainwin=self.document_window,
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.POLYGON,
            coords=vertices,
            attributes={
                'color': 'black',                    # Default color
                'linewidth': 1,                      # Default line width
                'closed': True,                      # Closed polygon
                'is_rounded_rectangle': True,         # Mark as rounded rect
                'width': x2 - x1,                   # Store width
                'height': y2 - y1,                  # Store height
                'corner_radius': self.corner_radius,  # Store corner radius
                'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2  # Store bounds
            }
        )
        return obj


class RegularPolygonTool(Tool):
    """Tool for drawing regular polygons by center and radius"""

    def __init__(self, canvas, document, preferences):
        """Initialize the tool with the canvas, document and preferences"""
        super().__init__(canvas, document, preferences)

        # Default to 6 sides for a regular polygon
        self.num_sides = 6

    def _update_sides(self):
        """Update the number of sides when the control changes"""
        try:
            self.num_sides = int(self.side_var.get())
            self.num_sides = max(3, min(32, self.num_sides))  # Clamp 3-32

            # Update the preview if we're in drawing mode
            if self.state == ToolState.DRAWING and len(self.points) == 1:
                # Force a preview update by simulating mouse movement
                self.handle_mouse_move(None)
        except ValueError:
            pass  # Ignore non-integer values

    def activate(self):
        """Activate the tool and show any custom controls"""
        super().activate()
        # TODO: Implement Qt-based side control panel
        # if hasattr(self, 'side_control'):
        #     self.side_control.pack(side=tk.LEFT, padx=5)

    def deactivate(self):
        """Deactivate the tool and hide any custom controls"""
        super().deactivate()
        # TODO: Implement Qt-based side control panel
        # if hasattr(self, 'side_control'):
        #     self.side_control.pack_forget()

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="REGPOLYGON",
            name="Regular Polygon",
            category=ToolCategory.POLYGONS,
            icon="tool-regpolygon",
            cursor="crosshair",
            is_creator=True,
            secondary_key="G",
            node_info=["Center Point2D", "Radius Point2D"]
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
            # First point - center of polygon
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING and len(self.points) == 1:
            # Second point - defines radius
            self.points.append(point)
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            # Draw preview polygon
            if event:
                self.draw_preview(event.x, event.y)
            else:
                # Called from side count update, use last known mouse position
                last_x, last_y = self.canvas.winfo_pointerxy()
                root_x = self.canvas.winfo_rootx()
                root_y = self.canvas.winfo_rooty()
                canvas_x = last_x - root_x
                canvas_y = last_y - root_y
                self.draw_preview(canvas_x, canvas_y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the polygon being created"""
        # Clear previous preview
        self.clear_temp_objects()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(current_x, current_y)

        if len(self.points) == 1:
            # Drawing from center to radius point
            center = self.points[0]

            # Calculate radius
            dx = point.x - center.x
            dy = point.y - center.y
            radius = math.sqrt(dx * dx + dy * dy)

            # Generate the polygon vertices
            vertices = self._calculate_polygon_vertices(
                center, radius, self.num_sides)

            # Draw temporary polygon using QGraphicsPolygonItem
            if vertices:
                from PySide6.QtWidgets import QGraphicsPolygonItem, QGraphicsLineItem, QGraphicsTextItem
                from PySide6.QtGui import QPolygonF, QPointF, QPen
                from PySide6.QtCore import Qt

                # Create Qt polygon from vertices
                qt_polygon = QPolygonF()
                for p in vertices:
                    qt_polygon.append(QPointF(p.x, p.y))

                poly_item = QGraphicsPolygonItem(qt_polygon)
                pen = QPen()
                pen.setColor("blue")
                pen.setStyle(Qt.DashLine)
                poly_item.setPen(pen)
                self.scene.addItem(poly_item)
                self.temp_objects.append(poly_item)

                # Draw radius line
                radius_line_item = QGraphicsLineItem(
                    center.x, center.y, point.x, point.y
                )
                radius_line_item.setPen(QPen("blue"))
                self.scene.addItem(radius_line_item)
                self.temp_objects.append(radius_line_item)

                # Add side count and radius text
                radius_text_item = QGraphicsTextItem(f"R={radius:.1f}")
                radius_text_item.setPos(
                    (center.x + point.x) / 2, (center.y + point.y) / 2)
                radius_text_item.setDefaultTextColor("blue")
                self.scene.addItem(radius_text_item)
                self.temp_objects.append(radius_text_item)

                sides_text_item = QGraphicsTextItem(f"Sides: {self.num_sides}")
                sides_text_item.setPos(center.x, center.y - radius - 15)
                sides_text_item.setDefaultTextColor("blue")
                self.scene.addItem(sides_text_item)
                self.temp_objects.append(sides_text_item)

    def _calculate_polygon_vertices(self, center: Point2D, radius: float,
                                    num_sides: int) -> List[Point2D]:
        """Calculate the vertices of a regular polygon"""
        if radius <= 0 or num_sides < 3:
            return []

        vertices = []
        for i in range(num_sides):
            # Start from top (subtract pi/2)
            angle = 2 * math.pi * i / num_sides - math.pi / 2
            x = center.x + radius * math.cos(angle)
            y = center.y + radius * math.sin(angle)
            vertices.append(Point2D(x, y))

        return vertices

    def create_object(self) -> Optional[CadObject]:
        """Create a regular polygon object from the collected points"""
        if len(self.points) != 2:
            return None

        center = self.points[0]
        radius_point = self.points[1]

        # Calculate radius
        dx = radius_point.x - center.x
        dy = radius_point.y - center.y
        radius = math.sqrt(dx * dx + dy * dy)

        # Generate the polygon vertices
        vertices = self._calculate_polygon_vertices(
            center, radius, self.num_sides)

        if not vertices:
            return None

        # Create a regular polygon object
        obj = CadObject(
            mainwin=self.document_window,
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.POLYGON,
            coords=vertices,
            attributes={
                'color': 'black',      # Default color
                'linewidth': 1,        # Default line width
                'closed': True,        # Closed polygon
                'is_regular': True,    # Mark as regular polygon
                'num_sides': self.num_sides,  # Store number of sides
                'radius': radius,      # Store radius
                'center': center       # Store center point
            }
        )
        return obj
