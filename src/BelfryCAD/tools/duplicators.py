"""
Duplicator tools for BelfryCad - Grid, Linear, Radial, and Offset copy.
Translated from the original BelfryCad TCL codebase.
"""

import copy
import math
from typing import List
from PySide6.QtCore import Qt

from .base import Tool, ToolCategory, ToolDefinition
from ..core.cad_objects import CADObject, Point


def distance_between_points(p1: Point, p2: Point) -> float:
    """Calculate distance between two points"""
    return math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2)


def angle_between_points(p1: Point, p2: Point) -> float:
    """Calculate angle between two points in radians"""
    return math.atan2(p2.y - p1.y, p2.x - p1.x)


class GridCopyTool(Tool):
    """Grid copy tool - duplicates selected objects in a 2D grid pattern"""

    def __init__(self, scene, document, preferences):
        super().__init__(scene, document, preferences)
        self.x_count = 3
        self.y_count = 3
        self.x_spacing = 20.0
        self.y_spacing = 20.0
        self.selected_objects = []
        self.preview_items = []
        self.base_point = None

    def _get_definition(self) -> List[ToolDefinition]:
        return [ToolDefinition(
            token="GRIDCOPY",
            name="Grid Copy",
            category=ToolCategory.DUPLICATORS,
            icon="tool-gridcopy",
            cursor="crosshair",
            is_creator=False,
            secondary_key="G",
            show_controls=True
        )]

    def activate(self):
        """Activate the grid copy tool"""
        super().activate()
        objects = self.document.objects.get_selected_objects()
        self.selected_objects = objects
        if not self.selected_objects:
            self.document.show_message("Select objects to copy first")
            return False
        self.document.show_message("Click base point for grid copy")
        return True

    def deactivate(self):
        """Deactivate the grid copy tool"""
        self._clear_preview()
        super().deactivate()

    def _clear_preview(self):
        """Clear preview items from scene"""
        for item in self.preview_items:
            if item.scene():
                self.scene.removeItem(item)
        self.preview_items = []

    def _duplicate_object(self, obj: CADObject, offset_x: float,
                          offset_y: float) -> CADObject:
        """Create a duplicate of an object with offset"""
        new_obj = copy.deepcopy(obj)
        new_obj.translate(offset_x, offset_y)
        return new_obj

    def _execute_grid_copy(self):
        """Execute the grid copy operation"""
        if not self.base_point or not self.selected_objects:
            return

        new_objects = []
        for x in range(self.x_count):
            for y in range(self.y_count):
                if x == 0 and y == 0:
                    continue  # Skip original position
                offset_x = x * self.x_spacing
                offset_y = y * self.y_spacing
                for obj in self.selected_objects:
                    new_obj = self._duplicate_object(obj, offset_x, offset_y)
                    new_objects.append(new_obj)

        # Add new objects to document
        for obj in new_objects:
            self.document.objects.add_object(obj)

        self.document.mark_modified()
        msg = f"Grid copied {len(new_objects)} objects"
        self.document.show_message(msg)

    def handle_mouse_down(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.LeftButton:
            point = Point(event.scenePos().x(), event.scenePos().y())
            self.base_point = point
            self._execute_grid_copy()
            self.deactivate()

    def handle_key_press(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Escape:
            self.deactivate()


class LinearCopyTool(Tool):
    """Linear copy tool - duplicates objects along a line"""

    def __init__(self, scene, document, preferences):
        super().__init__(scene, document, preferences)
        self.selected_objects = []
        self.start_point = None
        self.end_point = None
        self.count = 3
        self.state = "start"
        self.preview_items = []

    def _get_definition(self) -> List[ToolDefinition]:
        return [ToolDefinition(
            token="LINEARCOPY",
            name="Linear Copy",
            category=ToolCategory.DUPLICATORS,
            icon="tool-linearcopy",
            cursor="crosshair",
            is_creator=False,
            secondary_key="L",
            show_controls=True
        )]

    def activate(self):
        """Activate the linear copy tool"""
        super().activate()
        objects = self.document.objects.get_selected_objects()
        self.selected_objects = objects
        if not self.selected_objects:
            self.document.show_message("Select objects to copy first")
            return False
        self.document.show_message("Click start point for linear copy")
        return True

    def deactivate(self):
        """Deactivate the linear copy tool"""
        self._clear_preview()
        super().deactivate()

    def _clear_preview(self):
        """Clear preview items from scene"""
        for item in self.preview_items:
            if item.scene():
                self.scene.removeItem(item)
        self.preview_items = []

    def _duplicate_object(self, obj: CADObject, offset_x: float,
                          offset_y: float) -> CADObject:
        """Create a duplicate of an object with offset"""
        new_obj = copy.deepcopy(obj)
        new_obj.translate(offset_x, offset_y)
        return new_obj

    def _execute_linear_copy(self):
        """Execute the linear copy operation"""
        if not self.start_point or not self.end_point or not self.count:
            return

        new_objects = []
        dx = self.end_point.x - self.start_point.x
        dy = self.end_point.y - self.start_point.y

        for i in range(1, self.count):
            t = i / (self.count - 1)
            offset_x = dx * t
            offset_y = dy * t

            for obj in self.selected_objects:
                new_obj = self._duplicate_object(obj, offset_x, offset_y)
                new_objects.append(new_obj)

        # Add new objects to document
        for obj in new_objects:
            self.document.objects.add_object(obj)

        self.document.mark_modified()
        msg = f"Linear copied {len(new_objects)} objects"
        self.document.show_message(msg)

    def handle_mouse_down(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.LeftButton:
            point = Point(event.scenePos().x(), event.scenePos().y())

            if self.state == "start":
                self.start_point = point
                self.state = "end"
                self.document.show_message("Click end point")
            elif self.state == "end":
                self.end_point = point
                self._execute_linear_copy()
                self.start_point = None
                self.end_point = None
                self.state = "start"
                self.deactivate()

    def handle_key_press(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Escape:
            if self.state == "end":
                self.state = "start"
                self.start_point = None
                self.document.show_message("Click start point")
            else:
                self.deactivate()


class RadialCopyTool(Tool):
    """Radial copy tool - duplicates objects in a circular pattern"""

    def __init__(self, scene, document, preferences):
        super().__init__(scene, document, preferences)
        self.selected_objects = []
        self.center_point = None
        self.radius_point = None
        self.count = 4
        self.state = "center"
        self.preview_items = []

    def _get_definition(self) -> List[ToolDefinition]:
        return [ToolDefinition(
            token="RADIALCOPY",
            name="Radial Copy",
            category=ToolCategory.DUPLICATORS,
            icon="tool-radialcopy",
            cursor="crosshair",
            is_creator=False,
            secondary_key="R",
            show_controls=True
        )]

    def activate(self):
        """Activate the radial copy tool"""
        super().activate()
        objects = self.document.objects.get_selected_objects()
        self.selected_objects = objects
        if not self.selected_objects:
            self.document.show_message("Select objects to copy first")
            return False
        self.document.show_message("Click center point for radial copy")
        return True

    def deactivate(self):
        """Deactivate the radial copy tool"""
        self._clear_preview()
        super().deactivate()

    def _clear_preview(self):
        """Clear preview items from scene"""
        for item in self.preview_items:
            if item.scene():
                self.scene.removeItem(item)
        self.preview_items = []

    def _rotate_object_around_center(self, obj: CADObject, center: Point,
                                     angle: float) -> CADObject:
        """Create a copy of object rotated around center"""
        new_obj = copy.deepcopy(obj)
        new_obj.rotate(center.x, center.y, angle)
        return new_obj

    def _execute_radial_copy(self):
        """Execute the radial copy operation"""
        if (not self.center_point or not self.radius_point or
                not self.count > 1):
            return

        new_objects = []
        angle_step = 2 * math.pi / self.count

        for i in range(1, self.count):
            angle = i * angle_step
            for obj in self.selected_objects:
                new_obj = self._rotate_object_around_center(
                    obj, self.center_point, angle
                )
                new_objects.append(new_obj)

        # Add new objects to document
        for obj in new_objects:
            self.document.objects.add_object(obj)

        self.document.mark_modified()
        msg = f"Radial copied {len(new_objects)} objects"
        self.document.show_message(msg)

    def handle_mouse_down(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.LeftButton:
            point = Point(event.scenePos().x(), event.scenePos().y())

            if self.state == "center":
                self.center_point = point
                self.state = "radius"
                self.document.show_message("Click radius point")
            elif self.state == "radius":
                self.radius_point = point
                self._execute_radial_copy()
                self.center_point = None
                self.radius_point = None
                self.state = "center"
                self.deactivate()

    def handle_key_press(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Escape:
            if self.state == "radius":
                self.state = "center"
                self.center_point = None
                self.document.show_message("Click center point")
            else:
                self.deactivate()


class OffsetCopyTool(Tool):
    """Offset copy tool - creates offset copies of selected objects"""

    def __init__(self, scene, document, preferences):
        super().__init__(scene, document, preferences)
        self.selected_objects = []
        self.start_point = None
        self.end_point = None
        self.distance = 10.0
        self.inward = False
        self.preview_items = []

    def _get_definition(self) -> List[ToolDefinition]:
        return [ToolDefinition(
            token="OFFSETCOPY",
            name="Offset Copy",
            category=ToolCategory.DUPLICATORS,
            icon="tool-offsetcopy",
            cursor="crosshair",
            is_creator=False,
            secondary_key="O",
            show_controls=True
        )]

    def activate(self):
        """Activate the offset copy tool"""
        super().activate()
        objects = self.document.objects.get_selected_objects()
        self.selected_objects = objects
        if not self.selected_objects:
            self.document.show_message("Select objects to copy first")
            return False
        msg = "Click first point for offset direction"
        self.document.show_message(msg)
        return True

    def deactivate(self):
        """Deactivate the offset copy tool"""
        self._clear_preview()
        super().deactivate()

    def _clear_preview(self):
        """Clear preview items from scene"""
        for item in self.preview_items:
            if item.scene():
                self.scene.removeItem(item)
        self.preview_items = []

    def _duplicate_object(self, obj: CADObject, offset_x: float,
                          offset_y: float) -> CADObject:
        """Create a duplicate of an object with offset"""
        new_obj = copy.deepcopy(obj)
        new_obj.translate(offset_x, offset_y)
        return new_obj

    def _calculate_offset(self, direction_x: float,
                          direction_y: float) -> tuple:
        """Calculate offset based on direction and distance"""
        length = math.sqrt(direction_x**2 + direction_y**2)
        if length == 0:
            return 0, 0

        unit_x = direction_x / length
        unit_y = direction_y / length

        offset_x = unit_x * self.distance
        offset_y = unit_y * self.distance

        if self.inward:
            offset_x = -offset_x
            offset_y = -offset_y

        return offset_x, offset_y

    def _execute_offset_copy(self):
        """Execute the offset copy operation"""
        if not self.start_point or not self.end_point:
            return

        direction_x = self.end_point.x - self.start_point.x
        direction_y = self.end_point.y - self.start_point.y
        offset_x, offset_y = self._calculate_offset(direction_x, direction_y)

        new_objects = []
        for obj in self.selected_objects:
            new_obj = self._duplicate_object(obj, offset_x, offset_y)
            new_objects.append(new_obj)

        # Add new objects to document
        for obj in new_objects:
            self.document.objects.add_object(obj)

        self.document.mark_modified()
        msg = f"Offset copied {len(new_objects)} objects"
        self.document.show_message(msg)

    def handle_mouse_down(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.LeftButton:
            point = Point(event.scenePos().x(), event.scenePos().y())
            if not self.start_point:
                self.start_point = point
                self.document.show_message("Click second point")
            else:
                self.end_point = point
                self._execute_offset_copy()
                self.start_point = None
                self.end_point = None
                self.deactivate()

    def handle_key_press(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Escape:
            if self.start_point:
                self.start_point = None
                self.document.show_message("Click first point")
            else:
                self.deactivate()


# Export list for tool registration
DUPLICATOR_TOOLS = [
    LinearCopyTool,
    RadialCopyTool,
    GridCopyTool,
    OffsetCopyTool
]
