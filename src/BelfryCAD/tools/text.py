"""
Text Tool Implementation

This module implements text drawing tools based on the original TCL
tools_text.tcl implementation.
"""

import math
from typing import Optional, List

from ..models.cad_object import CadObject, ObjectType
from ..tools.base import Tool, ToolState, ToolCategory, ToolDefinition
from ..cad_geometry import Point2D, Region
from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsRectItem, QGraphicsLineItem
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPen, QBrush, QFont


class TextObject(CadObject):
    """Text object - position and text content"""

    def __init__(self, object_id: int, position: Point2D, text: str, **kwargs):
        super().__init__(
            object_id, ObjectType.TEXT, coords=[position], **kwargs)
        self.attributes.update({
            'text': text,
            'font_size': kwargs.get('font_size', 12),
            'font_family': kwargs.get('font_family', 'Arial'),
            'angle': kwargs.get('angle', 0)
        })

    @property
    def position(self) -> Point2D:
        return self.coords[0]

    @property
    def text(self) -> str:
        return self.attributes['text']


class TextTool(Tool):
    """Tool for creating text elements"""

    def __init__(self, scene, document, preferences):
        """Initialize the tool with the scene, document and preferences"""
        super().__init__(scene, document, preferences)

        # Default text properties
        self.text = "Text"
        self.font_family = "Arial"
        self.font_size = 12
        self.text_angle = 0.0

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="TEXT",
            name="Text",
            category=ToolCategory.MISC,
            icon="tool-text",
            cursor="text",
            secondary_key="T",
            is_creator=True,
            node_info=["Position"]
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
            # First click - set position and complete
            self.points.append(point)
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.ACTIVE:
            # Show preview at cursor position
            point = self.get_snap_point(event.x, event.y)
            self.clear_temp_objects()
            self._draw_text_preview(point)

    def _draw_text_preview(self, position: Point2D):
        """Draw a preview of the text"""
        # Calculate text properties
        angle_rad = math.radians(self.text_angle)
        font_spec = (self.font_family, self.font_size)

        # Draw the text using QGraphicsTextItem
        text_item = QGraphicsTextItem(self.text)
        font = QFont(self.font_family, self.font_size)
        text_item.setFont(font)
        text_item.setPos(position.x, position.y)
        text_item.setDefaultTextColor("gray")

        # Apply rotation if needed
        if abs(self.text_angle) > 0.01:
            text_item.setRotation(self.text_angle)

        self.scene.addItem(text_item)
        self.temp_objects.append(text_item)

        # Add a small marker at the position point
        marker_item = QGraphicsRectItem(
            QRectF(position.x - 3, position.y - 3, 6, 6))
        marker_item.setPen(QPen("red"))
        marker_item.setBrush(QBrush("red"))
        self.scene.addItem(marker_item)
        self.temp_objects.append(marker_item)

        # Draw text baseline guide
        line_length = 50
        x2 = position.x + line_length * math.cos(angle_rad)
        y2 = position.y + line_length * math.sin(angle_rad)
        line_item = QGraphicsLineItem(position.x, position.y, x2, y2)
        pen = QPen()
        pen.setColor("gray")
        pen.setStyle(Qt.DashLine)
        line_item.setPen(pen)
        self.scene.addItem(line_item)
        self.temp_objects.append(line_item)

    def create_object(self) -> Optional[CadObject]:
        """Create a text object"""
        if len(self.points) != 1 or not self.text:
            return None

        position = self.points[0]

        # Create text object
        text = TextCadObject(
            mainwin=self.document_window,
            object_id=self.document.get_next_object_id(),
            position=text_pos,
            text=text_content,
            color=self.preferences.get("default_color", "black"),
            line_width=self.preferences.get("default_line_width", 0.5)
        )
        return obj
