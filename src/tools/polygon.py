"""
Polygon Drawing Tool Implementation

This module implements various polygon drawing tools based on the original TCL
tools_polygons.tcl implementation, including rectangles and regular polygons.
"""

import tkinter as tk
import math
from typing import Optional, List

from src.core.cad_objects import CADObject, ObjectType, Point
from src.tools.base import Tool, ToolState, ToolCategory, ToolDefinition


class RectangleTool(Tool):
    """Tool for drawing rectangles by two diagonal corners"""

    def _get_definition(self) -> ToolDefinition:
        """Return the tool definition"""
        return ToolDefinition(
            token="RECTANGLE",
            name="Rectangle",
            category=ToolCategory.POLYGONS,
            icon="tool-rectangle",
            cursor="crosshair",
            is_creator=True,
            node_info=["First Corner", "Opposite Corner"]
        )

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        self.canvas.bind("<Button-1>", self.handle_mouse_down)
        self.canvas.bind("<Motion>", self.handle_mouse_move)
        self.canvas.bind("<Escape>", self.handle_escape)

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

            # Draw temporary rectangle
            rect_id = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline="blue", dash=(4, 4)
            )
            self.temp_objects.append(rect_id)

            # Add dimensions text
            width = x2 - x1
            height = y2 - y1

            if width > 10 and height > 10:  # Only show if large enough
                dim_x_id = self.canvas.create_text(
                    (x1 + x2) / 2, y2 + 15,
                    text=f"Width: {width:.1f}", fill="blue"
                )
                dim_y_id = self.canvas.create_text(
                    x2 + 15, (y1 + y2) / 2,
                    text=f"Height: {height:.1f}", fill="blue"
                )
                self.temp_objects.extend([dim_x_id, dim_y_id])

    def create_object(self) -> Optional[CADObject]:
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
            Point(x1, y1),  # Bottom-left
            Point(x2, y1),  # Bottom-right
            Point(x2, y2),  # Top-right
            Point(x1, y2)   # Top-left
        ]

        # Create a rectangle object (as a polygon)
        obj = CADObject(
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.POLYGON,
            layer=self.document.objects.current_layer,
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
        if hasattr(self, 'side_control'):
            self.side_control.pack(side=tk.LEFT, padx=5)

    def deactivate(self):
        """Deactivate the tool and hide any custom controls"""
        super().deactivate()
        if hasattr(self, 'side_control'):
            self.side_control.pack_forget()

    def _get_definition(self) -> ToolDefinition:
        """Return the tool definition"""
        return ToolDefinition(
            token="REGPOLYGON",
            name="Regular Polygon",
            category=ToolCategory.POLYGONS,
            icon="tool-regpolygon",
            cursor="crosshair",
            is_creator=True,
            node_info=["Center Point", "Radius Point"]
        )

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        self.canvas.bind("<Button-1>", self.handle_mouse_down)
        self.canvas.bind("<Motion>", self.handle_mouse_move)
        self.canvas.bind("<Escape>", self.handle_escape)

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

            # Draw temporary polygon
            if vertices:
                # Flatten the list of points for the create_polygon method
                flat_points = []
                for p in vertices:
                    flat_points.extend([p.x, p.y])

                poly_id = self.canvas.create_polygon(
                    *flat_points, outline="blue", fill="", dash=(4, 4)
                )
                self.temp_objects.append(poly_id)

                # Draw radius line
                radius_line_id = self.canvas.create_line(
                    center.x, center.y, point.x, point.y,
                    fill="blue", dash=(2, 2)
                )
                self.temp_objects.append(radius_line_id)

                # Add side count and radius text
                radius_text_id = self.canvas.create_text(
                    (center.x + point.x) / 2, (center.y + point.y) / 2,
                    text=f"R={radius:.1f}", fill="blue"
                )
                sides_text_id = self.canvas.create_text(
                    center.x, center.y - radius - 15,
                    text=f"Sides: {self.num_sides}", fill="blue"
                )
                self.temp_objects.extend([radius_text_id, sides_text_id])

    def _calculate_polygon_vertices(self, center: Point, radius: float,
                                    num_sides: int) -> List[Point]:
        """Calculate the vertices of a regular polygon"""
        if radius <= 0 or num_sides < 3:
            return []

        vertices = []
        for i in range(num_sides):
            # Start from top (subtract pi/2)
            angle = 2 * math.pi * i / num_sides - math.pi / 2
            x = center.x + radius * math.cos(angle)
            y = center.y + radius * math.sin(angle)
            vertices.append(Point(x, y))

        return vertices

    def create_object(self) -> Optional[CADObject]:
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
        obj = CADObject(
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.POLYGON,
            layer=self.document.objects.current_layer,
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
