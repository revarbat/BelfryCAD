"""
Object Selection Tool Implementation

This module implements an object selection tool based on the TCL selector tool.
"""

import tkinter as tk
from typing import Optional, List

from src.core.cad_objects import CADObject
from src.tools.base import Tool, ToolState, ToolCategory, ToolDefinition


class SelectorTool(Tool):
    """Tool for selecting CAD objects"""

    def __init__(self, canvas, document, preferences):
        super().__init__(canvas, document, preferences)
        self.start_x = 0
        self.start_y = 0
        self.selection_rect = None
        self.selected_objects = []

    def _get_definition(self) -> ToolDefinition:
        """Return the tool definition"""
        return ToolDefinition(
            token="OBJSEL",
            name="Select Objects",
            category=ToolCategory.SELECTOR,
            icon="tool-objsel",
            cursor="arrow",
            is_creator=False,
            show_controls=True
        )

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        self.canvas.bind("<Button-1>", self.handle_mouse_down)
        self.canvas.bind("<B1-Motion>", self.handle_drag)
        self.canvas.bind("<ButtonRelease-1>", self.handle_mouse_up)
        self.canvas.bind("<Escape>", self.handle_escape)

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.clear_selection()
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        self.start_x = event.x
        self.start_y = event.y

        # Check if clicking on an object directly
        hit_object = self.hit_test(event.x, event.y)

        # Handle selection
        if not hit_object:
            # Clicked on empty space, clear selection and start selection rect
            self.clear_selection()
            self.state = ToolState.SELECTING
        else:
            # Clicked on an object
            if hit_object.selected:
                # Clicked on already selected object - prepare for move
                self.state = ToolState.EDITING
            else:
                # Clicked on unselected object - select it
                self.clear_selection()
                self.select_object(hit_object)
                self.state = ToolState.EDITING

    def handle_drag(self, event):
        """Handle mouse drag event"""
        if self.state == ToolState.SELECTING:
            # Drawing selection rectangle
            if self.selection_rect:
                self.canvas.delete(self.selection_rect)

            self.selection_rect = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline="blue", dash=(2, 2)
            )
        elif self.state == ToolState.EDITING:
            # Moving selected objects
            dx = event.x - self.start_x
            dy = event.y - self.start_y

            if abs(dx) > 5 or abs(dy) > 5:  # Threshold to start moving
                # Move selected objects
                for obj in self.selected_objects:
                    obj.move(dx, dy)

                # Update display
                self.document.mark_modified()
                self.canvas.delete("all")
                # TODO: This should call the main window's draw_objects method
                # but for now we'll just use a simple redraw
                for obj in self.document.objects.get_all_objects():
                    self._draw_object(obj)

                # Update start position for next move
                self.start_x = event.x
                self.start_y = event.y

    def handle_mouse_up(self, event):
        """Handle mouse button release event"""
        if self.state == ToolState.SELECTING:
            # Finish selection rectangle
            if self.selection_rect:
                # Get bounds of selection rectangle
                x1 = min(self.start_x, event.x)
                y1 = min(self.start_y, event.y)
                x2 = max(self.start_x, event.x)
                y2 = max(self.start_y, event.y)

                # Select objects in the rectangle
                self.select_objects_in_rect(x1, y1, x2, y2)

                # Remove selection rectangle
                self.canvas.delete(self.selection_rect)
                self.selection_rect = None

        # Reset state
        self.state = ToolState.ACTIVE

    def hit_test(self, x, y) -> Optional[CADObject]:
        """Test if a point hits any object"""
        # Simple hit testing - can be improved with more sophisticated algorithms
        for obj in self.document.objects.get_all_objects():
            if self._point_in_object(x, y, obj):
                return obj
        return None

    def _point_in_object(self, x, y, obj) -> bool:
        """Test if a point is within or close to an object"""
        # Get object bounds with some padding for easier selection
        padding = 5
        bounds = obj.get_bounds()

        # Expand bounds by padding
        x1, y1, x2, y2 = bounds
        x1 -= padding
        y1 -= padding
        x2 += padding
        y2 += padding

        # Check if point is within expanded bounds
        if x >= x1 and x <= x2 and y >= y1 and y <= y2:
            # For more complex objects, additional testing would be needed here
            return True

        return False

    def select_object(self, obj):
        """Select a single object"""
        obj.selected = True
        self.selected_objects.append(obj)
        self._draw_object(obj)  # Redraw to show selection

    def select_objects_in_rect(self, x1, y1, x2, y2):
        """Select all objects that intersect with the given rectangle"""
        for obj in self.document.objects.get_all_objects():
            # Get object bounds
            ox1, oy1, ox2, oy2 = obj.get_bounds()

            # Check for intersection with selection rectangle
            if not (ox2 < x1 or ox1 > x2 or oy2 < y1 or oy1 > y2):
                self.select_object(obj)

    def clear_selection(self):
        """Clear the current selection"""
        for obj in self.selected_objects:
            obj.selected = False
        self.selected_objects = []
        # Redraw to update display
        self.canvas.delete("all")
        for obj in self.document.objects.get_all_objects():
            self._draw_object(obj)

    def _draw_object(self, obj):
        """Draw a single object with selection highlighting if needed"""
        t = getattr(obj, 'object_type', None)
        if t is None:
            return

        tname = t.value if hasattr(t, 'value') else str(t)
        color = obj.attributes.get('color', 'black')

        # If selected, use a different color
        if obj.selected:
            color = "red"

        if tname == "line":
            pts = obj.coords
            if len(pts) == 2:
                self.canvas.create_line(
                    pts[0].x, pts[0].y, pts[1].x, pts[1].y,
                    fill=color,
                    width=obj.attributes.get('linewidth', 1)
                )
        elif tname == "circle":
            pts = obj.coords
            r = obj.attributes.get('radius', 0)
            if pts and r:
                x, y = pts[0].x, pts[0].y
                self.canvas.create_oval(
                    x - r, y - r, x + r, y + r,
                    outline=color,
                    width=obj.attributes.get('linewidth', 1)
                )
        elif tname == "point":
            pts = obj.coords
            if pts:
                x, y = pts[0].x, pts[0].y
                self.canvas.create_oval(
                    x-2, y-2, x+2, y+2,
                    fill=color
                )
