"""
Enhanced CAD Object Selector Tool

This module provides an enhanced object selector tool with multi-selection,
rectangle selection, and clipboard operations based on cadselect.tcl patterns.
"""

from typing import List, Optional
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QPen, QColor, QBrush
from PySide6.QtWidgets import QGraphicsRectItem

from .base import Tool, ToolDefinition, ToolCategory
from ..models.cad_object import CadObject, ObjectType


class CadSelectorTool(Tool):
    """
    Enhanced CAD object selector tool with multi-selection capabilities.
    Based on design patterns from cadselect.tcl.
    """

    def __init__(self, scene, document, preferences):
        super().__init__(scene, document, preferences)

        # Selection state
        self.selected_objects: List[CadObject] = []
        self.selection_changed_callbacks: List = []

        # Rectangle selection state
        self._selection_start: Optional[QPointF] = None
        self._selection_rect: Optional[QGraphicsRectItem] = None
        self._is_rect_selecting = False

        # Selection colors
        self.selection_color = QColor(255, 0, 0)  # Red for selected objects
        self.selection_rect_color = QColor(0, 0, 255, 64)  # Blue rect

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="Object Selector",
            token="OBJSEL",
            category=ToolCategory.SELECTOR,
            icon="select",
            cursor="arrow"
        )

    def handle_mouse_down(self, event):
        """Handle mouse press for selection operations."""
        scene_pos = event.scenePos()

        # Check if clicking on existing object
        clicked_obj = self._find_object_at_point(scene_pos.x(), scene_pos.y())

        # Check for modifier keys (if available)
        ctrl_pressed = False
        if hasattr(event, 'modifiers'):
            ctrl_pressed = bool(event.modifiers() &
                              Qt.KeyboardModifier.ControlModifier)

        if clicked_obj:
            # Handle object selection
            if ctrl_pressed:
                # Ctrl+click: toggle selection
                self._toggle_object_selection(clicked_obj)
            else:
                # Normal click: select only this object
                self._select_single_object(clicked_obj)
        else:
            # Start rectangle selection
            if not ctrl_pressed:
                self._clear_selection()

            self._start_rectangle_selection(scene_pos)

    def handle_mouse_move(self, event):
        """Handle mouse move for rectangle selection."""
        if self._is_rect_selecting and self._selection_start:
            scene_pos = event.scenePos()
            self._update_rectangle_selection(scene_pos)

    def handle_mouse_up(self, event):
        """Handle mouse release to complete selection."""
        if self._is_rect_selecting:
            scene_pos = event.scenePos()
            self._complete_rectangle_selection(scene_pos)

    def _find_object_at_point(self, x: float, y: float) -> Optional[CadObject]:
        """Find CAD object at the given scene coordinates."""
        if not hasattr(self.document, 'objects'):
            return None

        # Check all objects to see if point is within their bounds
        for obj_id, obj in self.document.objects.objects.items():
            if self._point_in_object(x, y, obj):
                return obj
        return None

    def _point_in_object(self, x: float, y: float, obj: CadObject) -> bool:
        """Check if point is within object bounds."""
        if not obj.coords:
            return False

        # Simple distance-based selection for now
        tolerance = 5.0  # Selection tolerance in scene units

        for coord in obj.coords:
            distance = ((x - coord.x) ** 2 + (y - coord.y) ** 2) ** 0.5
            if distance <= tolerance:
                return True

        return False

    def _select_single_object(self, obj: CadObject):
        """Select a single object, clearing previous selection."""
        self._clear_selection()
        self.selected_objects.append(obj)
        obj.selected = True
        self._notify_selection_changed()

    def _toggle_object_selection(self, obj: CadObject):
        """Toggle selection state of an object."""
        if obj in self.selected_objects:
            self.selected_objects.remove(obj)
            obj.selected = False
        else:
            self.selected_objects.append(obj)
            obj.selected = True
        self._notify_selection_changed()

    def _clear_selection(self):
        """Clear all selected objects."""
        for obj in self.selected_objects:
            obj.selected = False
        self.selected_objects.clear()
        self._notify_selection_changed()

    def _start_rectangle_selection(self, start_pos: QPointF):
        """Start rectangle selection mode."""
        self._selection_start = start_pos
        self._is_rect_selecting = True

        # Create selection rectangle visual
        pen = QPen(self.selection_rect_color)
        brush = QBrush(self.selection_rect_color)
        self._selection_rect = self.scene.addRect(
            start_pos.x(), start_pos.y(), 0, 0, pen, brush)
        self._selection_rect.setZValue(1000)  # Draw on top

    def _update_rectangle_selection(self, current_pos: QPointF):
        """Update rectangle selection visual."""
        if not self._selection_rect or not self._selection_start:
            return

        # Calculate rectangle bounds
        x1, y1 = self._selection_start.x(), self._selection_start.y()
        x2, y2 = current_pos.x(), current_pos.y()

        rect = QRectF(
            min(x1, x2), min(y1, y2),
            abs(x2 - x1), abs(y2 - y1)
        )

        self._selection_rect.setRect(rect)

    def _complete_rectangle_selection(self, end_pos: QPointF):
        """Complete rectangle selection and select objects within."""
        if not self._selection_start:
            return

        # Calculate selection rectangle
        x1, y1 = self._selection_start.x(), self._selection_start.y()
        x2, y2 = end_pos.x(), end_pos.y()

        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)

        # Find objects within rectangle
        selected_in_rect = []
        if hasattr(self.document, 'objects'):
            for obj_id, obj in self.document.objects.objects.items():
                if self._object_in_rectangle(obj, min_x, min_y, max_x, max_y):
                    selected_in_rect.append(obj)

        # Add to selection
        for obj in selected_in_rect:
            if obj not in self.selected_objects:
                self.selected_objects.append(obj)
                obj.selected = True

        # Clean up selection rectangle
        if self._selection_rect:
            self.scene.removeItem(self._selection_rect)
            self._selection_rect = None

        self._selection_start = None
        self._is_rect_selecting = False
        self._notify_selection_changed()

    def _object_in_rectangle(self, obj: CadObject, min_x: float, min_y: float,
                           max_x: float, max_y: float) -> bool:
        """Check if object is within selection rectangle."""
        if not obj.coords:
            return False

        # Check if any coordinate is within rectangle
        for coord in obj.coords:
            if min_x <= coord.x <= max_x and min_y <= coord.y <= max_y:
                return True
        return False

    def _notify_selection_changed(self):
        """Notify listeners that selection has changed."""
        for callback in self.selection_changed_callbacks:
            callback(self.selected_objects)

    def add_selection_changed_callback(self, callback):
        """Add a callback for selection change events."""
        self.selection_changed_callbacks.append(callback)

    def get_selected_objects(self) -> List[CadObject]:
        """Get list of currently selected objects."""
        return self.selected_objects.copy()

    def select_objects(self, objects: List[CadObject]):
        """Programmatically select objects."""
        self._clear_selection()
        for obj in objects:
            self.selected_objects.append(obj)
            obj.selected = True
        self._notify_selection_changed()

    def deactivate(self):
        """Clean up when tool is deactivated."""
        # Clean up selection rectangle if active
        if self._selection_rect:
            self.scene.removeItem(self._selection_rect)
            self._selection_rect = None

        self._selection_start = None
        self._is_rect_selecting = False

        super().deactivate()


# Register the tool
available_tools = [CadSelectorTool]
