"""
Node Selection Tool Implementation

This module implements a node selection tool that allows users to select
individual control points (nodes) of CAD objects, based on the original
TCL NODESEL tool implementation.
"""

from typing import Optional, List, Tuple, Dict, Set
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QBrush
from PySide6.QtWidgets import QGraphicsEllipseItem

from src.core.cad_objects import CADObject, Point
from src.tools.base import Tool, ToolState, ToolCategory, ToolDefinition


class NodeSelectTool(Tool):
    """Tool for selecting individual nodes/control points of CAD objects"""

    def __init__(self, scene, document, preferences):
        super().__init__(scene, document, preferences)
        self.selected_nodes: Dict[str, Set[int]] = {}  # objid -> node indices
        self.selected_objects: List[CADObject] = []
        self.start_x = 0
        self.start_y = 0
        self.click_has_moved = False
        self.node_visual_items = []  # Visual indicators for selected nodes

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="NODESEL",
            name="Select Nodes",
            category=ToolCategory.NODES,
            icon="tool-nodesel",
            cursor="top_left_arrow",
            is_creator=False,
            secondary_key="S",
            show_controls=True
        )]

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        pass

    def activate(self):
        """Activate the tool"""
        super().activate()
        self.state = ToolState.ACTIVE

    def deactivate(self):
        """Deactivate the tool and clean up"""
        self.clear_all_selections()
        super().deactivate()

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.clear_all_selections()
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        if hasattr(event, 'scenePos'):
            scene_pos = event.scenePos()
        else:
            scene_pos = QPointF(event.x, event.y)

        self.start_x = scene_pos.x()
        self.start_y = scene_pos.y()
        self.click_has_moved = False

        # Find control point near the click
        node_info = self._find_node_near_point(self.start_x, self.start_y)

        if node_info:
            # Clicked on a control point
            obj_id, node_num = node_info
            self.state = "NODES_MOUSEDOWN"

            # Handle node selection
            shift_pressed = (hasattr(event, 'modifiers') and
                             event.modifiers() & 0x02000000)

            if not self._is_node_selected(obj_id, node_num):
                if not shift_pressed:
                    self.clear_all_selections()
                self._select_node(obj_id, node_num)
            else:
                if shift_pressed:
                    self._deselect_node(obj_id, node_num)
        else:
            # Clicked on empty space or object
            hit_object = self._find_object_near_point(self.start_x,
                                                      self.start_y)
            if not hit_object:
                # Clicked on empty space - clear selection
                self.clear_all_selections()
            else:
                # Clicked on object - select the entire object if not shift
                shift_pressed = (hasattr(event, 'modifiers') and
                                 event.modifiers() & 0x02000000)
                if not shift_pressed:
                    self.clear_all_selections()
                self._select_object(hit_object)

    def handle_mouse_up(self, event):
        """Handle mouse button release event"""
        if self.state == "NODES_MOUSEDOWN":
            self.state = ToolState.ACTIVE

    def handle_drag(self, event):
        """Handle mouse drag event"""
        if hasattr(event, 'scenePos'):
            scene_pos = event.scenePos()
        else:
            scene_pos = QPointF(event.x, event.y)

        current_x, current_y = scene_pos.x(), scene_pos.y()

        # Check if mouse has moved significantly
        dx = current_x - self.start_x
        dy = current_y - self.start_y
        if abs(dx) > 3 or abs(dy) > 3:
            self.click_has_moved = True

        # TODO: Implement node dragging/moving when nodes are selected
        # For now, just update the moved flag

    def handle_double_click(self, event):
        """Handle double-click to edit object"""
        if hasattr(event, 'scenePos'):
            scene_pos = event.scenePos()
        else:
            scene_pos = QPointF(event.x, event.y)

        # Find object to edit
        hit_object = self._find_object_near_point(scene_pos.x(),
                                                  scene_pos.y())
        if hit_object:
            # TODO: Implement object editing
            pass

    def delete_selected(self):
        """Delete selected nodes or objects"""
        if self.selected_nodes:
            # Delete selected nodes
            for obj_id, node_indices in self.selected_nodes.items():
                obj = self._find_object_by_id(obj_id)
                if obj:
                    self._delete_nodes_from_object(obj, list(node_indices))
        elif self.selected_objects:
            # Delete selected objects if no nodes are selected
            for obj in self.selected_objects:
                self.document.objects.remove_object(obj.id)

        self.clear_all_selections()
        self.document.mark_modified()

    def select_all_nodes(self):
        """Select all nodes of all visible objects"""
        self.clear_all_selections()

        for obj in self.document.objects.get_all_objects():
            if hasattr(obj, 'get_control_points'):
                control_points = obj.get_control_points()
                for i, _ in enumerate(control_points):
                    # Nodes are 1-indexed
                    self._select_node(obj.id, i + 1)
            else:
                # For objects without explicit control points, select object
                self._select_object(obj)

    def _find_node_near_point(self, x: float, y: float,
                             tolerance: float = 8.0) -> Optional[
                                 Tuple[str, int]]:
        """Find a control point near the given coordinates"""
        closest_distance = float('inf')
        closest_node = None

        for obj in self.document.objects.get_all_objects():
            if hasattr(obj, 'get_control_points'):
                control_points = obj.get_control_points()
                for i, point in enumerate(control_points):
                    distance = ((point.x - x) ** 2 + (point.y - y) ** 2) ** 0.5
                    if distance <= tolerance and distance < closest_distance:
                        closest_distance = distance
                        closest_node = (obj.id, i + 1)  # Nodes are 1-indexed

        return closest_node

    def _find_object_near_point(self, x: float, y: float) -> Optional[
            CADObject]:
        """Find an object near the given point"""
        tolerance = 8.0
        for obj in self.document.objects.get_all_objects():
            try:
                bounds = obj.get_bounds()
                if bounds:
                    x1, y1, x2, y2 = bounds
                    # Expand bounds by tolerance
                    if (x1 - tolerance <= x <= x2 + tolerance and
                            y1 - tolerance <= y <= y2 + tolerance):
                        return obj
            except (AttributeError, TypeError):
                continue
        return None

    def _find_object_by_id(self, obj_id: str) -> Optional[CADObject]:
        """Find an object by its ID"""
        for obj in self.document.objects.get_all_objects():
            if obj.id == obj_id:
                return obj
        return None

    def _is_node_selected(self, obj_id: str, node_num: int) -> bool:
        """Check if a specific node is selected"""
        return (obj_id in self.selected_nodes and
                node_num in self.selected_nodes[obj_id])

    def _select_node(self, obj_id: str, node_num: int):
        """Select a specific node"""
        if obj_id not in self.selected_nodes:
            self.selected_nodes[obj_id] = set()
        self.selected_nodes[obj_id].add(node_num)
        self._update_node_visuals()

    def _deselect_node(self, obj_id: str, node_num: int):
        """Deselect a specific node"""
        if obj_id in self.selected_nodes:
            self.selected_nodes[obj_id].discard(node_num)
            if not self.selected_nodes[obj_id]:
                del self.selected_nodes[obj_id]
        self._update_node_visuals()

    def _select_object(self, obj: CADObject):
        """Select an entire object"""
        if obj not in self.selected_objects:
            self.selected_objects.append(obj)
            obj.selected = True

    def _deselect_object(self, obj: CADObject):
        """Deselect an entire object"""
        if obj in self.selected_objects:
            self.selected_objects.remove(obj)
            obj.selected = False

    def clear_all_selections(self):
        """Clear all node and object selections"""
        # Clear node selections
        self.selected_nodes.clear()

        # Clear object selections
        for obj in self.selected_objects:
            obj.selected = False
        self.selected_objects.clear()

        # Clear visual indicators
        self._clear_node_visuals()

    def _update_node_visuals(self):
        """Update visual indicators for selected nodes"""
        self._clear_node_visuals()

        # Add visual indicators for selected nodes
        for obj_id, node_indices in self.selected_nodes.items():
            obj = self._find_object_by_id(obj_id)
            if obj and hasattr(obj, 'get_control_points'):
                control_points = obj.get_control_points()
                for node_num in node_indices:
                    if 1 <= node_num <= len(control_points):
                        # Convert to 0-indexed
                        point = control_points[node_num - 1]
                        self._add_node_visual(point.x, point.y)

    def _add_node_visual(self, x: float, y: float):
        """Add a visual indicator for a selected node"""
        # Create a small circle to highlight the selected node
        radius = 4
        circle = QGraphicsEllipseItem(x - radius, y - radius,
                                      radius * 2, radius * 2)
        circle.setPen(QPen(QColor("red"), 2))
        circle.setBrush(QBrush(QColor("yellow")))
        self.scene.addItem(circle)
        self.node_visual_items.append(circle)

    def _clear_node_visuals(self):
        """Clear all node visual indicators"""
        for item in self.node_visual_items:
            self.scene.removeItem(item)
        self.node_visual_items.clear()

    def _delete_nodes_from_object(self, obj: CADObject, node_indices: List[
            int]):
        """Delete specified nodes from an object"""
        # TODO: Implement node deletion based on object type
        # This would need to be implemented for each object type that
        # supports node deletion. For now, just mark the document as modified
        self.document.mark_modified()

    def get_selected_node_count(self) -> int:
        """Get the total number of selected nodes"""
        return sum(len(nodes) for nodes in self.selected_nodes.values())

    def get_selected_object_count(self) -> int:
        """Get the number of selected objects"""
        return len(self.selected_objects)

    def has_selection(self) -> bool:
        """Check if anything is selected"""
        return bool(self.selected_nodes or self.selected_objects)
