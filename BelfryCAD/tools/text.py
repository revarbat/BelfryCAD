"""
Text Tool Implementation

This module implements text drawing tools based on the original TCL
tools_text.tcl implementation.
"""

import math
from typing import Optional, List

from BelfryCAD.core.cad_objects import CADObject, ObjectType, Point
from BelfryCAD.tools.base import Tool, ToolState, ToolCategory, ToolDefinition


class TextObject(CADObject):
    """Text object - position and text content"""

    def __init__(self, object_id: int, position: Point, text: str, **kwargs):
        super().__init__(
            object_id, ObjectType.TEXT, coords=[position], **kwargs)
        self.attributes.update({
            'text': text,
            'font_size': kwargs.get('font_size', 12),
            'font_family': kwargs.get('font_family', 'Arial'),
            'angle': kwargs.get('angle', 0)
        })

    @property
    def position(self) -> Point:
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
            category=ToolCategory.TEXT,
            icon="tool-text",
            cursor="text",
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

    def _draw_text_preview(self, position: Point):
        """Draw a preview of the text"""
        # Calculate text properties
        angle_rad = math.radians(self.text_angle)
        font_spec = (self.font_family, self.font_size)

        # Draw the text using QGraphicsTextItem
        from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsRectItem, QGraphicsLineItem
        from PySide6.QtCore import QRectF, Qt
        from PySide6.QtGui import QPen, QBrush, QFont

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

    def create_object(self) -> Optional[CADObject]:
        """Create a text object"""
        if len(self.points) != 1 or not self.text:
            return None

        position = self.points[0]

        # Create a text object
        obj = CADObject(
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.TEXT,
            layer=self.document.objects.current_layer,
            coords=[position],
            attributes={
                'color': 'black',                 # Default color
                'text': self.text,                # The text string
                'font_family': self.font_family,  # Font family
                'font_size': self.font_size,      # Font size
                'angle': self.text_angle,         # Rotation angle in degrees
                'anchor': 'sw'                    # Text anchor (southwest)
            }
        )
        return obj
