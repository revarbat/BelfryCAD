"""
Object Selection Tool Implementation

This module implements an object selection tool based on the TCL selector tool.
"""

from typing import Optional, List
from PySide6.QtCore import QRectF, QPointF
from PySide6.QtGui import QPen, QColor

from ..core.cad_objects import CADObject
from .base import Tool, ToolState, ToolCategory, ToolDefinition


class SelectorTool(Tool):
    """Tool for selecting CAD objects"""

    def __init__(self, scene, document, preferences):
        super().__init__(scene, document, preferences)
        self.start_x = 0
        self.start_y = 0
        self.selection_rect = None
        self.selected_objects = []

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="OBJSEL",
            name="Select Objects",
            category=ToolCategory.SELECTOR,
            icon="tool-objsel",
            cursor="arrow",
            is_creator=False,
            show_controls=True
        )]

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        # In Qt, event handling is done differently - these will be connected
        # in the main window or graphics view
        pass

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.clear_selection()
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        # Convert Qt event coordinates to scene coordinates
        if hasattr(event, 'scenePos'):
            scene_pos = event.scenePos()
        else:
            scene_pos = QPointF(event.x, event.y)

        self.start_x = scene_pos.x()
        self.start_y = scene_pos.y()

        # Check if clicking on an object directly
        hit_object = self.hit_test(self.start_x, self.start_y)

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

    def handle_mouse_up(self, event):
        """Handle mouse button release event"""
        if self.state == ToolState.SELECTING:
            # Finish selection rectangle
            if self.selection_rect:
                if hasattr(event, 'scenePos'):
                    scene_pos = event.scenePos()
                else:
                    scene_pos = QPointF(event.x, event.y)

                # Get bounds of selection rectangle
                x1 = min(self.start_x, scene_pos.x())
                y1 = min(self.start_y, scene_pos.y())
                x2 = max(self.start_x, scene_pos.x())
                y2 = max(self.start_y, scene_pos.y())

                # Select objects in the rectangle
                self.select_objects_in_rect(x1, y1, x2, y2)

                # Remove selection rectangle
                self.scene.removeItem(self.selection_rect)
                if self.selection_rect in self.temp_objects:
                    self.temp_objects.remove(self.selection_rect)
                self.selection_rect = None

        # Reset state
        self.state = ToolState.ACTIVE

    def handle_drag(self, event):
        """Handle mouse drag event"""
        if hasattr(event, 'scenePos'):
            scene_pos = event.scenePos()
        else:
            scene_pos = QPointF(event.x, event.y)

        current_x, current_y = scene_pos.x(), scene_pos.y()

        if self.state == ToolState.SELECTING:
            # Drawing selection rectangle
            if self.selection_rect:
                self.scene.removeItem(self.selection_rect)
                if self.selection_rect in self.temp_objects:
                    self.temp_objects.remove(self.selection_rect)

            # Create selection rectangle
            rect = QRectF(
                min(self.start_x, current_x),
                min(self.start_y, current_y),
                abs(current_x - self.start_x),
                abs(current_y - self.start_y)
            )
            pen = QPen(QColor("blue"))
            pen.setDashPattern([2, 2])  # Dash pattern
            self.selection_rect = self.scene.addRect(rect, pen)
            self.temp_objects.append(self.selection_rect)

        elif self.state == ToolState.EDITING:
            # Moving selected objects
            dx = current_x - self.start_x
            dy = current_y - self.start_y

            if abs(dx) > 5 or abs(dy) > 5:  # Threshold to start moving
                # Move selected objects
                for obj in self.selected_objects:
                    obj.move(dx, dy)

                # Update display
                self.document.mark_modified()
                # TODO: Trigger main window redraw

                # Update start position for next move
                self.start_x = current_x
                self.start_y = current_y

    def hit_test(self, x, y) -> Optional[CADObject]:
        """Test if a point hits any object"""
        for obj in self.document.objects.get_all_objects():
            if self._point_in_object(x, y, obj):
                return obj
        return None

    def _point_in_object(self, x, y, obj) -> bool:
        """Test if a point is within or close to an object"""
        # Get object bounds with some padding for easier selection
        padding = 5
        try:
            bounds = obj.get_bounds()
            x1, y1, x2, y2 = bounds
            x1 -= padding
            y1 -= padding
            x2 += padding
            y2 += padding
            return x >= x1 and x <= x2 and y >= y1 and y <= y2
        except (AttributeError, TypeError):
            return False

    def select_object(self, obj):
        """Select a single object"""
        obj.selected = True
        self.selected_objects.append(obj)

    def select_objects_in_rect(self, x1, y1, x2, y2):
        """Select all objects that intersect with the given rectangle"""
        for obj in self.document.objects.get_all_objects():
            try:
                ox1, oy1, ox2, oy2 = obj.get_bounds()
                if not (ox2 < x1 or ox1 > x2 or oy2 < y1 or oy1 > y2):
                    self.select_object(obj)
            except (AttributeError, TypeError):
                continue

    def clear_selection(self):
        """Clear the current selection"""
        for obj in self.selected_objects:
            obj.selected = False
        self.selected_objects = []
