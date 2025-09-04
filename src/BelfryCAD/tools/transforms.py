"""
Transform Tools Implementation

This module implements transformation tools based on the original TCL
tools_transforms.tcl implementation.

Transform tools include:
- Node Add/Delete/Reorient tools for manipulating object nodes
- Connect tool for connecting objects
- Translation tool for moving objects
- Rotation tool for rotating objects around a center point
- Scale tool for scaling objects
- Flip tool for reflecting objects across a line
- Shear tool for shearing objects
- Bend/Wrap/Unwrap tools for advanced transformations
"""

import math
from typing import Optional, List, Tuple, Dict, Any

from PySide6.QtWidgets import (QGraphicsLineItem, QGraphicsEllipseItem,
                               QGraphicsPathItem, QGraphicsRectItem)
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QPainterPath, QBrush, QTransform

from ..models.cad_object import CadObject, ObjectType
from ..cad_geometry import Point2D
from .base import CadTool, ToolState, ToolCategory, ToolDefinition


def _reflect_point_across_line(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> tuple[float, float]:
    """Reflect a point across a line defined by two points."""
    # Calculate line direction vector
    dx = x2 - x1
    dy = y2 - y1
    
    # Handle degenerate case (line is a point)
    if dx == 0 and dy == 0:
        return px, py
    
    # Normalize line direction
    length = math.sqrt(dx * dx + dy * dy)
    dx /= length
    dy /= length
    
    # Vector from line start to point
    wx = px - x1
    wy = py - y1
    
    # Project point onto line
    t = wx * dx + wy * dy
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    
    # Reflect point across line
    reflected_x = 2 * closest_x - px
    reflected_y = 2 * closest_y - py
    
    return reflected_x, reflected_y


def _transform_coords_reflection(coords: List[float], x1: float, y1: float, x2: float, y2: float) -> List[float]:
    """Transform coordinates using reflection across a line."""
    result = []
    for i in range(0, len(coords), 2):
        if i + 1 < len(coords):
            rx, ry = _reflect_point_across_line(coords[i], coords[i + 1], x1, y1, x2, y2)
            result.extend([rx, ry])
    return result


def _transform_coords_skew(coords: List[float], shear_x: float, shear_y: float, cx: float, cy: float) -> List[float]:
    """Transform coordinates using skew transformation."""
    result = []
    for i in range(0, len(coords), 2):
        if i + 1 < len(coords):
            x, y = coords[i], coords[i + 1]
            # Apply skew transformation relative to center
            new_x = x + shear_x * (y - cy)
            new_y = y + shear_y * (x - cx)
            result.extend([new_x, new_y])
    return result


class NodeAddTool(CadTool):
    """CadTool for adding nodes to objects"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="NODEADD",
            name="Add Node",
            category=ToolCategory.NODES,
            icon="tool-nodeadd",
            cursor="crosshair",
            is_creator=False,
            secondary_key="A",
            show_controls=True,
            node_info=["Node Add Position"]
        )]

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        point = self.get_snap_point(event.x, event.y)

        if self.state == ToolState.ACTIVE:
            # Find object near the click point
            obj = self._find_object_near_point(point.x, point.y)
            if obj:
                # Add node to the object
                self._add_node_to_object(obj, point.x, point.y)
            else:
                # No object found - make a sound or show error
                pass

    def _find_object_near_point(self, x: float, y: float) -> Optional[CadObject]:
        """Find an object near the given point"""
        close_enough = 5.0
        # TODO: Implement object search in scene
        # This would need access to the document's object list
        return None

    def _add_node_to_object(self, obj: CadObject, x: float, y: float):
        """Add a node to the given object at the specified coordinates"""
        # TODO: Implement node addition based on object type
        pass


class NodeDeleteTool(CadTool):
    """CadTool for deleting nodes from objects"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="NODEDEL",
            name="Delete Node",
            category=ToolCategory.NODES,
            icon="tool-nodedel",
            cursor="top_left_arrow",
            is_creator=False,
            secondary_key="D",
            show_controls=True,
            node_info=["Node to Delete"]
        )]

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        point = self.get_snap_point(event.x, event.y)

        if self.state == ToolState.ACTIVE:
            # Find control point or object near the click
            node_info = self._find_node_near_point(point.x, point.y)
            if node_info:
                obj_id, node_num = node_info
                self._delete_node_from_object(obj_id, node_num)
            else:
                # No node found - select object instead
                obj = self._find_object_near_point(point.x, point.y)
                if obj:
                    self._select_object(obj)

    def _find_node_near_point(self, x: float, y: float) -> Optional[Tuple[str, int]]:
        """Find a control point near the given coordinates"""
        # TODO: Implement control point detection
        return None

    def _delete_node_from_object(self, obj_id: str, node_num: int):
        """Delete a node from the specified object"""
        # TODO: Implement node deletion
        pass

    def _find_object_near_point(self, x: float, y: float) -> Optional[CadObject]:
        """Find an object near the given point"""
        # TODO: Implement object search
        return None

    def _select_object(self, obj: CadObject):
        """Select the given object"""
        # TODO: Implement object selection
        pass


class ReorientTool(CadTool):
    """CadTool for changing loop's start node"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="REORIENT",
            name="Change Loop's Start Node",
            category=ToolCategory.NODES,
            icon="tool-reorient",
            cursor="top_left_arrow",
            is_creator=False,
            secondary_key="R",
            show_controls=True,
            node_info=["Node to Reorient Endpoints To"]
        )]

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        point = self.get_snap_point(event.x, event.y)

        if self.state == ToolState.ACTIVE:
            # Find control point near the click
            node_info = self._find_node_near_point(point.x, point.y)
            if node_info:
                obj_id, node_num = node_info
                self._reorient_object_to_node(obj_id, node_num)

    def _find_node_near_point(self, x: float, y: float) -> Optional[Tuple[str, int]]:
        """Find a control point near the given coordinates"""
        # TODO: Implement control point detection
        return None

    def _reorient_object_to_node(self, obj_id: str, node_num: int):
        """Reorient object to start from the specified node"""
        # TODO: Implement object reorientation
        pass


class ConnectTool(CadTool):
    """CadTool for connecting two objects"""

    def __init__(self, scene, document, preferences):
        super().__init__(scene, document, preferences)
        self.first_object = None

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="CONNECT",
            name="Connect",
            category=ToolCategory.NODES,
            icon="tool-connect",
            cursor="crosshair",
            is_creator=True,
            secondary_key="C",
            node_info=["Start Point2D", "End Point2D"]
        )]

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.first_object = None
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        point = self.get_snap_point(event.x, event.y)

        if self.state == ToolState.ACTIVE:
            # First click - select first object
            self.points.append(point)
            obj = self._find_object_near_point(point.x, point.y)
            if obj:
                self.first_object = obj
                self.state = ToolState.DRAWING
            else:
                self.cancel()

        elif self.state == ToolState.DRAWING:
            # Second click - select second object and connect
            self.points.append(point)
            obj = self._find_object_near_point(point.x, point.y)
            if obj and obj != self.first_object:
                self._connect_objects(self.first_object, self.points[0],
                                      obj, self.points[1])
                self.complete()
            else:
                self.cancel()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x: float, current_y: float):
        """Draw a preview line from first point to current position"""
        if len(self.points) < 1:
            return

        self.clear_temp_objects()
        start_point = self.points[0]

        # Create a preview line
        line_item = QGraphicsLineItem(start_point.x, start_point.y,
                                      current_x, current_y)
        line_item.setPen(QPen(QColor(0, 0, 255)))  # Blue preview
        self.scene.addItem(line_item)
        self.temp_objects.append(line_item)

    def _find_object_near_point(self, x: float, y: float) -> Optional[CadObject]:
        """Find an object near the given point"""
        # TODO: Implement object search
        return None

    def _connect_objects(self, obj1: CadObject, point1: Point2D,
                         obj2: CadObject, point2: Point2D):
        """Connect two objects with a line"""
        # TODO: Implement object connection
        pass


class TranslateTool(CadTool):
    """CadTool for translating (moving) objects"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="TRANSLATE",
            name="Translate",
            category=ToolCategory.TRANSFORMS,
            icon="tool-translate",
            cursor="crosshair",
            is_creator=False,
            secondary_key="T",
            node_info=["Reference Point2D", "Move To"]
        )]

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        point = self.get_snap_point(event.x, event.y)

        if self.state == ToolState.ACTIVE:
            # First click - reference point
            self.points.append(point)
            self.state = ToolState.DRAWING

        elif self.state == ToolState.DRAWING:
            # Second click - destination point
            self.points.append(point)
            self._translate_selected_objects()
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x: float, current_y: float):
        """Draw a preview of the translation"""
        if len(self.points) < 1:
            return

        self.clear_temp_objects()
        ref_point = self.points[0]

        # Calculate translation vector
        dx = current_x - ref_point.x
        dy = current_y - ref_point.y

        # Check for constrained movement (SHIFT key)
        if self._is_shift_pressed():
            # Constrain to horizontal, vertical, or diagonal
            if abs(dx) > abs(dy):
                if abs(abs(dx) - abs(dy)) < min(abs(dx), abs(dy)):
                    # Diagonal
                    dy = abs(dx) * (1.0 if dy >= 0 else -1.0)
                else:
                    # Horizontal
                    dy = 0.0
            else:
                if abs(abs(dx) - abs(dy)) < min(abs(dx), abs(dy)):
                    # Diagonal
                    dx = abs(dy) * (1.0 if dx >= 0 else -1.0)
                else:
                    # Vertical
                    dx = 0.0

        # Draw preview of selected objects at new position
        selected_objects = self._get_selected_objects()
        if selected_objects:
            bbox = self._get_objects_bbox(selected_objects)
            if bbox:
                self._draw_translate_preview_box(bbox, dx, dy)

    def _translate_selected_objects(self):
        """Translate all selected objects"""
        if len(self.points) < 2:
            return

        ref_point = self.points[0]
        dest_point = self.points[1]

        dx = dest_point.x - ref_point.x
        dy = dest_point.y - ref_point.y

        # Check for constrained movement
        if self._is_shift_pressed():
            if abs(dx) > abs(dy):
                if abs(abs(dx) - abs(dy)) < min(abs(dx), abs(dy)):
                    dy = abs(dx) * (1.0 if dy >= 0 else -1.0)
                else:
                    dy = 0.0
            else:
                if abs(abs(dx) - abs(dy)) < min(abs(dx), abs(dy)):
                    dx = abs(dy) * (1.0 if dx >= 0 else -1.0)
                else:
                    dx = 0.0

        # Apply translation to selected objects
        selected_objects = self._get_selected_objects()
        for obj in selected_objects:
            self._translate_object(obj, dx, dy)

    def _draw_translate_preview_box(self, bbox: QRectF, dx: float, dy: float):
        """Draw a preview box showing the translated position"""
        # Draw lines representing the corners of the bounding box
        corners = [
            (bbox.left(), bbox.top()),
            (bbox.left(), bbox.bottom()),
            (bbox.right(), bbox.top()),
            (bbox.right(), bbox.bottom())
        ]

        # Draw lines connecting original corners to new positions
        for x, y in corners:
            line_item = QGraphicsLineItem(x + dx, y + dy, x + dx, y + dy)
            line_item.setPen(QPen(QColor(0, 0, 255)))  # Blue preview
            self.scene.addItem(line_item)
            self.temp_objects.append(line_item)

    def _get_selected_objects(self) -> List[CadObject]:
        """Get list of currently selected objects"""
        # TODO: Implement selection retrieval
        return []

    def _get_objects_bbox(self, objects: List[CadObject]) -> Optional[QRectF]:
        """Get bounding box of objects"""
        # TODO: Implement bounding box calculation
        return None

    def _translate_object(self, obj: CadObject, dx: float, dy: float):
        """Translate an object by the given offset"""
        # TODO: Implement object translation
        pass

    def _is_shift_pressed(self) -> bool:
        """Check if SHIFT key is currently pressed"""
        # TODO: Implement key state checking
        return False


class RotateTool(CadTool):
    """CadTool for rotating objects around a center point"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="ROTATE",
            name="Rotate",
            category=ToolCategory.TRANSFORMS,
            icon="tool-rotate",
            cursor="crosshair",
            is_creator=False,
            secondary_key="R",
            node_info=["Center of Rotation", "Reference Point2D", "Rotate To"]
        )]

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        point = self.get_snap_point(event.x, event.y)

        if self.state == ToolState.ACTIVE:
            # First click - center of rotation
            self.points.append(point)
            self.state = ToolState.DRAWING

        elif self.state == ToolState.DRAWING and len(self.points) == 1:
            # Second click - reference point
            self.points.append(point)

        elif self.state == ToolState.DRAWING and len(self.points) == 2:
            # Third click - rotation target
            self.points.append(point)
            self._rotate_selected_objects()
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x: float, current_y: float):
        """Draw a preview of the rotation"""
        if len(self.points) < 2:
            return

        self.clear_temp_objects()
        center = self.points[0]
        ref_point = self.points[1]

        # Calculate rotation angle
        angle1 = math.atan2(ref_point.y - center.y, ref_point.x - center.x)
        angle2 = math.atan2(current_y - center.y, current_x - center.x)
        rotation_angle = math.degrees(angle2 - angle1)

        # Normalize angle to -180 to 180
        while rotation_angle > 180:
            rotation_angle -= 360
        while rotation_angle < -180:
            rotation_angle += 360

        # Draw preview of rotated selection
        selected_objects = self._get_selected_objects()
        if selected_objects:
            bbox = self._get_objects_bbox(selected_objects)
            if bbox:
                self._draw_rotate_preview_box(bbox, center, rotation_angle)

    def _rotate_selected_objects(self):
        """Rotate all selected objects"""
        if len(self.points) < 3:
            return

        center = self.points[0]
        ref_point = self.points[1]
        target_point = self.points[2]

        # Calculate rotation angle
        angle1 = math.atan2(ref_point.y - center.y, ref_point.x - center.x)
        angle2 = math.atan2(target_point.y - center.y,
                            target_point.x - center.x)
        rotation_angle = math.degrees(angle2 - angle1)

        # Normalize angle
        while rotation_angle > 180:
            rotation_angle -= 360
        while rotation_angle < -180:
            rotation_angle += 360

        # Apply rotation to selected objects
        selected_objects = self._get_selected_objects()
        for obj in selected_objects:
            self._rotate_object(obj, rotation_angle, center.x, center.y)

    def _draw_rotate_preview_box(self, bbox: QRectF, center: Point2D, angle: float):
        """Draw a preview box showing the rotated position"""
        # Convert angle to radians
        angle_rad = math.radians(-angle)  # Negative for screen coordinates
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        # Get corners of bounding box
        corners = [
            (bbox.left(), bbox.top()),
            (bbox.left(), bbox.bottom()),
            (bbox.right(), bbox.bottom()),
            (bbox.right(), bbox.top())
        ]

        # Rotate corners around center
        rotated_corners = []
        for x, y in corners:
            # Translate to origin
            tx = x - center.x
            ty = y - center.y
            # Rotate
            rx = tx * cos_a - ty * sin_a
            ry = tx * sin_a + ty * cos_a
            # Translate back
            rx += center.x
            ry += center.y
            rotated_corners.append((rx, ry))

        # Draw rotated box outline
        for i in range(len(rotated_corners)):
            x1, y1 = rotated_corners[i]
            x2, y2 = rotated_corners[(i + 1) % len(rotated_corners)]
            line_item = QGraphicsLineItem(x1, y1, x2, y2)
            line_item.setPen(QPen(QColor(0, 0, 255)))  # Blue preview
            self.scene.addItem(line_item)
            self.temp_objects.append(line_item)

    def _get_selected_objects(self) -> List[CadObject]:
        """Get list of currently selected objects"""
        # TODO: Implement selection retrieval
        return []

    def _get_objects_bbox(self, objects: List[CadObject]) -> Optional[QRectF]:
        """Get bounding box of objects"""
        # TODO: Implement bounding box calculation
        return None

    def _rotate_object(self, obj: CadObject, angle: float, cx: float, cy: float):
        """Rotate an object around the given center point"""
        # TODO: Implement object rotation
        pass


class ScaleTool(CadTool):
    """CadTool for scaling objects"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="SCALE",
            name="Scale",
            category=ToolCategory.TRANSFORMS,
            icon="tool-scale",
            cursor="crosshair",
            is_creator=False,
            secondary_key="S",
            node_info=["Center of Scaling", "Reference Point2D", "Scale To"]
        )]

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        point = self.get_snap_point(event.x, event.y)

        if self.state == ToolState.ACTIVE:
            # First click - center of scaling
            self.points.append(point)
            self.state = ToolState.DRAWING

        elif self.state == ToolState.DRAWING and len(self.points) == 1:
            # Second click - reference point
            self.points.append(point)

        elif self.state == ToolState.DRAWING and len(self.points) == 2:
            # Third click - scale target
            self.points.append(point)
            self._scale_selected_objects()
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x: float, current_y: float):
        """Draw a preview of the scaling"""
        if len(self.points) < 2:
            return

        self.clear_temp_objects()
        center = self.points[0]
        ref_point = self.points[1]

        # Calculate scale factors
        ref_dx = ref_point.x - center.x
        ref_dy = ref_point.y - center.y

        if abs(ref_dx) > 1e-6:
            scale_x = (current_x - center.x) / ref_dx
        else:
            scale_x = 1.0

        if abs(ref_dy) > 1e-6:
            scale_y = (current_y - center.y) / ref_dy
        else:
            scale_y = 1.0

        # Check for uniform scaling (SHIFT key)
        if self._is_shift_pressed():
            if abs(scale_x) > abs(scale_y):
                scale_y = abs(scale_x) * (1.0 if scale_y >= 0 else -1.0)
            else:
                scale_x = abs(scale_y) * (1.0 if scale_x >= 0 else -1.0)

        # Draw preview of scaled selection
        selected_objects = self._get_selected_objects()
        if selected_objects:
            bbox = self._get_objects_bbox(selected_objects)
            if bbox:
                self._draw_scale_preview_box(bbox, center, scale_x, scale_y)

    def _scale_selected_objects(self):
        """Scale all selected objects"""
        if len(self.points) < 3:
            return

        center = self.points[0]
        ref_point = self.points[1]
        target_point = self.points[2]

        # Calculate scale factors
        ref_dx = ref_point.x - center.x
        ref_dy = ref_point.y - center.y

        if abs(ref_dx) > 1e-6:
            scale_x = (target_point.x - center.x) / ref_dx
        else:
            scale_x = 1.0

        if abs(ref_dy) > 1e-6:
            scale_y = (target_point.y - center.y) / ref_dy
        else:
            scale_y = 1.0

        # Check for uniform scaling
        if self._is_shift_pressed():
            if abs(scale_x) > abs(scale_y):
                scale_y = abs(scale_x) * (1.0 if scale_y >= 0 else -1.0)
            else:
                scale_x = abs(scale_y) * (1.0 if scale_x >= 0 else -1.0)

        # Apply scaling to selected objects
        selected_objects = self._get_selected_objects()
        for obj in selected_objects:
            self._scale_object(obj, scale_x, scale_y, center.x, center.y)

    def _draw_scale_preview_box(self, bbox: QRectF, center: Point2D,
                                scale_x: float, scale_y: float):
        """Draw a preview box showing the scaled position"""
        # Get corners of bounding box
        corners = [
            (bbox.left(), bbox.top()),
            (bbox.left(), bbox.bottom()),
            (bbox.right(), bbox.bottom()),
            (bbox.right(), bbox.top())
        ]

        # Scale corners around center
        scaled_corners = []
        for x, y in corners:
            # Scale around center
            sx = (x - center.x) * scale_x + center.x
            sy = (y - center.y) * scale_y + center.y
            scaled_corners.append((sx, sy))

        # Draw scaled box outline
        for i in range(len(scaled_corners)):
            x1, y1 = scaled_corners[i]
            x2, y2 = scaled_corners[(i + 1) % len(scaled_corners)]
            line_item = QGraphicsLineItem(x1, y1, x2, y2)
            line_item.setPen(QPen(QColor(0, 0, 255)))  # Blue preview
            self.scene.addItem(line_item)
            self.temp_objects.append(line_item)

    def _get_selected_objects(self) -> List[CadObject]:
        """Get list of currently selected objects"""
        # TODO: Implement selection retrieval
        return []

    def _get_objects_bbox(self, objects: List[CadObject]) -> Optional[QRectF]:
        """Get bounding box of objects"""
        # TODO: Implement bounding box calculation
        return None

    def _scale_object(self, obj: CadObject, scale_x: float, scale_y: float,
                      cx: float, cy: float):
        """Scale an object around the given center point"""
        # TODO: Implement object scaling
        pass

    def _is_shift_pressed(self) -> bool:
        """Check if SHIFT key is currently pressed"""
        # TODO: Implement key state checking
        return False


class FlipTool(CadTool):
    """CadTool for flipping (reflecting) objects across a line"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="FLIP",
            name="Flip",
            category=ToolCategory.TRANSFORMS,
            icon="tool-flip",
            cursor="crosshair",
            is_creator=False,
            secondary_key="F",
            node_info=["Start of Line to Flip Across",
                "End of Line to Flip Across"]
        )]
    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        point = self.get_snap_point(event.x, event.y)

        if self.state == ToolState.ACTIVE:
            # First click - start of flip line
            self.points.append(point)
            self.state = ToolState.DRAWING

        elif self.state == ToolState.DRAWING:
            # Second click - end of flip line
            self.points.append(point)
            self._flip_selected_objects()
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x: float, current_y: float):
        """Draw a preview of the flip operation"""
        if len(self.points) < 1:
            return

        self.clear_temp_objects()
        start_point = self.points[0]

        # Check for valid flip line
        line_length = math.sqrt((current_x - start_point.x)**2 +
                                (current_y - start_point.y)**2)
        if line_length < 1e-6:
            return

        # Draw preview of flipped selection
        selected_objects = self._get_selected_objects()
        if selected_objects:
            bbox = self._get_objects_bbox(selected_objects)
            if bbox:
                self._draw_flip_preview_box(bbox, start_point.x, start_point.y,
                                            current_x, current_y)

    def _flip_selected_objects(self):
        """Flip all selected objects across the defined line"""
        if len(self.points) < 2:
            return

        start_point = self.points[0]
        end_point = self.points[1]

        # Apply flip to selected objects
        selected_objects = self._get_selected_objects()
        for obj in selected_objects:
            self._flip_object(obj, start_point.x, start_point.y,
                              end_point.x, end_point.y)

    def _draw_flip_preview_box(self, bbox: QRectF, x1: float, y1: float,
                               x2: float, y2: float):
        """Draw a preview box showing the flipped position"""
        try:
            # Get corners of bounding box and center
            corners = [
                (bbox.left(), bbox.top()),
                (bbox.left(), bbox.bottom()),
                (bbox.right(), bbox.bottom()),
                (bbox.right(), bbox.top())
            ]

            center_x = bbox.center().x()
            center_y = bbox.center().y()
            quarter_x = (bbox.left() + bbox.right() * 3) / 4
            quarter_y = (bbox.top() + bbox.bottom() * 3) / 4

            # Add center and quarter point lines for reference
            preview_lines = corners + [
                (bbox.left(), center_y), (bbox.right(), center_y),
                (center_x, bbox.top()), (center_x, bbox.bottom()),
                (center_x, bbox.top()), (quarter_x, quarter_y)
            ]

            # Transform and draw original and reflected lines
            for i in range(0, len(preview_lines), 2):
                if i + 1 < len(preview_lines):
                    # Original line in light blue
                    x_orig1, y_orig1 = preview_lines[i]
                    x_orig2, y_orig2 = preview_lines[i + 1]
                    line_item = QGraphicsLineItem(
                        x_orig1, y_orig1, x_orig2, y_orig2)
                    line_item.setPen(QPen(QColor(127, 127, 255)))  # Light blue
                    self.scene.addItem(line_item)
                    self.temp_objects.append(line_item)

                    # Reflected line in blue
                    coords = [x_orig1, y_orig1, x_orig2, y_orig2]
                    # Use direct mathematical implementation for reflection
                    reflected_coords = _transform_coords_reflection(coords, x1, y1, x2, y2)
                    if len(reflected_coords) >= 4:
                        line_item = QGraphicsLineItem(reflected_coords[0], reflected_coords[1],
                                                      reflected_coords[2], reflected_coords[3])
                        line_item.setPen(QPen(QColor(0, 0, 255)))  # Blue
                        self.scene.addItem(line_item)
                        self.temp_objects.append(line_item)
        except:
            return

    def _get_selected_objects(self) -> List[CadObject]:
        """Get list of currently selected objects"""
        # TODO: Implement selection retrieval
        return []

    def _get_objects_bbox(self, objects: List[CadObject]) -> Optional[QRectF]:
        """Get bounding box of objects"""
        # TODO: Implement bounding box calculation
        return None

    def _flip_object(self, obj: CadObject, x1: float, y1: float,
                     x2: float, y2: float):
        """Flip an object across the given line"""
        # TODO: Implement object reflection
        pass


class ShearTool(CadTool):
    """CadTool for shearing objects"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="SHEAR",
            name="Shear",
            category=ToolCategory.TRANSFORMS,
            icon="tool-shear",
            cursor="crosshair",
            is_creator=False,
            secondary_key="H",
            node_info=["Center of Shear", "Reference Point2D", "Shear To"]
        )]
    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        point = self.get_snap_point(event.x, event.y)

        if self.state == ToolState.ACTIVE:
            # First click - center of shear
            self.points.append(point)
            self.state = ToolState.DRAWING

        elif self.state == ToolState.DRAWING and len(self.points) == 1:
            # Second click - reference point
            self.points.append(point)

        elif self.state == ToolState.DRAWING and len(self.points) == 2:
            # Third click - shear target
            self.points.append(point)
            self._shear_selected_objects()
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x: float, current_y: float):
        """Draw a preview of the shear operation"""
        if len(self.points) < 2:
            return

        self.clear_temp_objects()
        center = self.points[0]
        ref_point = self.points[1]

        # Calculate shear factors
        ref_dy = ref_point.y - center.y
        ref_dx = ref_point.x - center.x

        if abs(ref_dy) > 1e-6:
            shear_x = (current_x - ref_point.x) / ref_dy
        else:
            shear_x = 0.0

        if abs(ref_dx) > 1e-6:
            shear_y = (current_y - ref_point.y) / ref_dx
        else:
            shear_y = 0.0

        # Check for constrained shear (SHIFT key)
        if self._is_shift_pressed():
            if abs(shear_x) > abs(shear_y):
                shear_y = 0.0
            else:
                shear_x = 0.0

        # Draw preview of sheared selection
        selected_objects = self._get_selected_objects()
        if selected_objects:
            bbox = self._get_objects_bbox(selected_objects)
            if bbox:
                self._draw_shear_preview_box(bbox, center, shear_x, shear_y)

    def _shear_selected_objects(self):
        """Shear all selected objects"""
        if len(self.points) < 3:
            return

        center = self.points[0]
        ref_point = self.points[1]
        target_point = self.points[2]

        # Calculate shear factors
        ref_dy = ref_point.y - center.y
        ref_dx = ref_point.x - center.x

        if abs(ref_dy) > 1e-6:
            shear_x = (target_point.x - ref_point.x) / ref_dy
        else:
            shear_x = 0.0

        if abs(ref_dx) > 1e-6:
            shear_y = (target_point.y - ref_point.y) / ref_dx
        else:
            shear_y = 0.0

        # Check for constrained shear
        if self._is_shift_pressed():
            if abs(shear_x) > abs(shear_y):
                shear_y = 0.0
            else:
                shear_x = 0.0

        # Apply shear to selected objects
        selected_objects = self._get_selected_objects()
        for obj in selected_objects:
            self._shear_object(obj, shear_x, shear_y, center.x, center.y)

    def _draw_shear_preview_box(self, bbox: QRectF, center: Point2D,
                                shear_x: float, shear_y: float):
        """Draw a preview box showing the sheared position"""
        try:
            # Get corners of bounding box
            corners = [
                (bbox.left(), bbox.top()),
                (bbox.left(), bbox.bottom()),
                (bbox.right(), bbox.bottom()),
                (bbox.right(), bbox.top())
            ]

            # Transform corners and draw lines
            for i in range(len(corners)):
                x1, y1 = corners[i]
                x2, y2 = corners[(i + 1) % len(corners)]
                coords = [x1, y1, x2, y2]
                sheared_coords = _transform_coords_skew(coords, shear_x, shear_y, center.x, center.y)
                if len(sheared_coords) >= 4:
                    line_item = QGraphicsLineItem(sheared_coords[0], sheared_coords[1],
                                                  sheared_coords[2], sheared_coords[3])
                    line_item.setPen(QPen(QColor(0, 0, 255)))  # Blue preview
                    self.scene.addItem(line_item)
                    self.temp_objects.append(line_item)
        except:
            return

    def _get_selected_objects(self) -> List[CadObject]:
        """Get list of currently selected objects"""
        # TODO: Implement selection retrieval
        return []

    def _get_objects_bbox(self, objects: List[CadObject]) -> Optional[QRectF]:
        """Get bounding box of objects"""
        # TODO: Implement bounding box calculation
        return None

    def _shear_object(self, obj: CadObject, shear_x: float, shear_y: float,
                      cx: float, cy: float):
        """Shear an object around the given center point"""
        # TODO: Implement object shearing
        pass

    def _is_shift_pressed(self) -> bool:
        """Check if SHIFT key is currently pressed"""
        # TODO: Implement key state checking
        return False


class BendTool(CadTool):
    """CadTool for bending objects along a curve"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="BEND",
            name="Bend",
            category=ToolCategory.TRANSFORMS,
            icon="tool-bend",
            cursor="crosshair",
            is_creator=False,
            secondary_key="B",
            node_info=["First Endpoint", "Second Endpoint", "Control Point2D"]
        )]
    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        point = self.get_snap_point(event.x, event.y)

        if self.state == ToolState.ACTIVE:
            # First click - first endpoint
            self.points.append(point)
            self.state = ToolState.DRAWING

        elif self.state == ToolState.DRAWING and len(self.points) == 1:
            # Second click - second endpoint
            self.points.append(point)

        elif self.state == ToolState.DRAWING and len(self.points) == 2:
            # Third click - control point
            self.points.append(point)
            self._bend_selected_objects()
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x: float, current_y: float):
        """Draw a preview of the bend operation"""
        if len(self.points) < 2:
            return

        self.clear_temp_objects()

        # Show the current bend line/arc
        if len(self.points) == 1:
            # Show line from first point to cursor
            start_point = self.points[0]
            line_item = QGraphicsLineItem(start_point.x, start_point.y,
                                          current_x, current_y)
            line_item.setPen(QPen(QColor(127, 127, 255)))  # Light blue
            self.scene.addItem(line_item)
            self.temp_objects.append(line_item)
        elif len(self.points) == 2:
            # Show arc defined by three points
            self._draw_bend_preview_arc(self.points[0], self.points[1],
                                        Point2D(current_x, current_y))

    def _draw_bend_preview_arc(self, p1: Point2D, p2: Point2D, p3: Point2D):
        """Draw a preview arc through three points"""
        # Calculate arc center and radius
        arc_info = self._find_arc_from_points(
            p1.x, p1.y, p3.x, p3.y, p2.x, p2.y)
        if not arc_info:
            return

        cx, cy, radius, start_angle, end_angle = arc_info

        # Draw arc preview
        rect = QRectF(cx - radius, cy - radius, 2 * radius, 2 * radius)
        # Note: QGraphicsEllipseItem doesn't directly support arcs,
        # would need QPainterPath for proper arc drawing
        ellipse_item = QGraphicsEllipseItem(rect)
        ellipse_item.setPen(QPen(QColor(127, 127, 255)))  # Light blue
        ellipse_item.setBrush(QBrush(Qt.NoBrush))
        self.scene.addItem(ellipse_item)
        self.temp_objects.append(ellipse_item)

    def _find_arc_from_points(self, x1: float, y1: float, x2: float, y2: float,
                              x3: float, y3: float) -> Optional[Tuple[float, float, float, float, float]]:
        """Find arc center and angles from three points"""
        # TODO: Implement arc calculation from three points
        # This is a complex geometric calculation
        return None

    def _bend_selected_objects(self):
        """Bend all selected objects"""
        if len(self.points) < 3:
            return

        # Apply bend to selected objects
        selected_objects = self._get_selected_objects()
        for obj in selected_objects:
            self._bend_object(
                obj, self.points[0], self.points[1], self.points[2])

    def _get_selected_objects(self) -> List[CadObject]:
        """Get list of currently selected objects"""
        # TODO: Implement selection retrieval
        return []

    def _bend_object(self, obj: CadObject, p1: Point2D, p2: Point2D, p3: Point2D):
        """Bend an object along the defined curve"""
        # TODO: Implement object bending
        pass


class WrapTool(CadTool):
    """CadTool for wrapping objects around a center point"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="WRAP",
            name="Wrap around Center",
            category=ToolCategory.TRANSFORMS,
            icon="tool-wrap",
            cursor="crosshair",
            is_creator=False,
            secondary_key="W",
            node_info=["Center Point2D", "Reference Point2D", "Tangent Point2D"]
        )]
    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        point = self.get_snap_point(event.x, event.y)

        if self.state == ToolState.ACTIVE:
            # First click - center point
            self.points.append(point)
            self.state = ToolState.DRAWING

        elif self.state == ToolState.DRAWING and len(self.points) == 1:
            # Second click - reference point
            self.points.append(point)

        elif self.state == ToolState.DRAWING and len(self.points) == 2:
            # Third click - tangent point (or auto-calculate perpendicular)
            if len(self.points) < 3:
                # Auto-calculate perpendicular point
                center = self.points[0]
                ref_point = self.points[1]
                # Calculate perpendicular direction
                angle = math.atan2(ref_point.y - center.y,
                                   ref_point.x - center.x) - math.pi/2
                perp_x = ref_point.x + math.cos(angle)
                perp_y = ref_point.y + math.sin(angle)
                self.points.append(Point2D(perp_x, perp_y))
            else:
                self.points.append(point)
            self._wrap_selected_objects()
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x: float, current_y: float):
        """Draw a preview of the wrap operation"""
        if len(self.points) < 1:
            return

        self.clear_temp_objects()

        # Draw reference elements based on current state
        if len(self.points) == 1:
            # Show line from center to cursor
            center = self.points[0]
            line_item = QGraphicsLineItem(
                center.x, center.y, current_x, current_y)
            line_item.setPen(QPen(QColor(127, 127, 255)))  # Light blue
            self.scene.addItem(line_item)
            self.temp_objects.append(line_item)
        elif len(self.points) >= 2:
            # Show wrap preview
            self._draw_wrap_preview()

    def _draw_wrap_preview(self):
        """Draw a preview of the wrap transformation"""
        # TODO: Implement wrap preview drawing
        # This involves complex curve mathematics
        pass

    def _wrap_selected_objects(self):
        """Wrap all selected objects"""
        if len(self.points) < 3:
            return

        # Apply wrap to selected objects
        selected_objects = self._get_selected_objects()
        for obj in selected_objects:
            self._wrap_object(
                obj, self.points[0], self.points[1], self.points[2])

    def _get_selected_objects(self) -> List[CadObject]:
        """Get list of currently selected objects"""
        # TODO: Implement selection retrieval
        return []

    def _wrap_object(self, obj: CadObject, center: Point2D, ref_point: Point2D,
                     tangent_point: Point2D):
        """Wrap an object around the defined center"""
        # TODO: Implement object wrapping
        pass


class UnwrapTool(CadTool):
    """CadTool for unwrapping objects from a curved arrangement"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="UNWRAP",
            name="Un-wrap",
            category=ToolCategory.TRANSFORMS,
            icon="tool-unwrap",
            cursor="crosshair",
            secondary_key="U",
            is_creator=False,
            node_info=["Center Point2D", "Reference Point2D", "Tangent Point2D"]
        )]
    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        point = self.get_snap_point(event.x, event.y)

        if self.state == ToolState.ACTIVE:
            # First click - center point
            self.points.append(point)
            self.state = ToolState.DRAWING

        elif self.state == ToolState.DRAWING and len(self.points) == 1:
            # Second click - reference point
            self.points.append(point)

        elif self.state == ToolState.DRAWING and len(self.points) == 2:
            # Third click - tangent point (or auto-calculate)
            if len(self.points) < 3:
                # Auto-calculate perpendicular point
                center = self.points[0]
                ref_point = self.points[1]
                angle = math.atan2(ref_point.y - center.y,
                                   ref_point.x - center.x) - math.pi/2
                perp_x = ref_point.x + math.cos(angle)
                perp_y = ref_point.y + math.sin(angle)
                self.points.append(Point2D(perp_x, perp_y))
            else:
                self.points.append(point)
            self._unwrap_selected_objects()
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x: float, current_y: float):
        """Draw a preview of the unwrap operation"""
        if len(self.points) < 2:
            return

        self.clear_temp_objects()

        # Draw preview elements
        self._draw_unwrap_preview()

    def _draw_unwrap_preview(self):
        """Draw a preview of the unwrap transformation"""
        if len(self.points) < 2:
            return

        center = self.points[0]
        ref_point = self.points[1]

        # Calculate radius and draw reference circle/arc
        radius = math.sqrt((ref_point.x - center.x)**2 +
                           (ref_point.y - center.y)**2)

        # Draw reference arc
        rect = QRectF(center.x - radius, center.y -
                      radius, 2 * radius, 2 * radius)
        ellipse_item = QGraphicsEllipseItem(rect)
        ellipse_item.setPen(QPen(QColor(127, 127, 255)))  # Light blue
        ellipse_item.setBrush(QBrush(Qt.NoBrush))
        self.scene.addItem(ellipse_item)
        self.temp_objects.append(ellipse_item)

        # Draw reference line
        if len(self.points) >= 2:
            line_item = QGraphicsLineItem(self.points[0].x, self.points[0].y,
                                          self.points[1].x, self.points[1].y)
            line_item.setPen(QPen(QColor(127, 127, 255)))  # Light blue
            self.scene.addItem(line_item)
            self.temp_objects.append(line_item)

    def _unwrap_selected_objects(self):
        """Unwrap all selected objects"""
        if len(self.points) < 3:
            return

        # Apply unwrap to selected objects
        selected_objects = self._get_selected_objects()
        for obj in selected_objects:
            self._unwrap_object(
                obj, self.points[0], self.points[1], self.points[2])

    def _get_selected_objects(self) -> List[CadObject]:
        """Get list of currently selected objects"""
        # TODO: Implement selection retrieval
        return []

    def _unwrap_object(self, obj: CadObject, center: Point2D, ref_point: Point2D,
                       tangent_point: Point2D):
        """Unwrap an object from the defined center"""
        # TODO: Implement object unwrapping
        pass
