"""
Image Tool Implementation

This module implements the image import and manipulation tool based on the original TCL
tools_images.tcl implementation.
"""

import os
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from PySide6.QtWidgets import (QGraphicsPixmapItem, QFileDialog,
                              QGraphicsRectItem)
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QPixmap, QImage, QBrush

from ..core.cad_objects import CADObject, ObjectType, Point
from .base import Tool, ToolState, ToolCategory, ToolDefinition

if TYPE_CHECKING:
    from ..gui.main_window import MainWindow


class ImageObject(CADObject):
    """Image object - position, size, and image data"""

    def __init__(self, mainwin: 'MainWindow', object_id: int, position: Point, width: float, height: float,
                 image_path: str, **kwargs):
        super().__init__(
            mainwin, object_id, ObjectType.IMAGE, coords=[position], **kwargs)
        self.attributes.update({
            'width': width,
            'height': height,
            'image_path': image_path,
            'rotation': kwargs.get('rotation', 0.0),
            'scale_x': kwargs.get('scale_x', 1.0),
            'scale_y': kwargs.get('scale_y', 1.0),
            'opacity': kwargs.get('opacity', 1.0),
            'brightness': kwargs.get('brightness', 0.0),
            'contrast': kwargs.get('contrast', 0.0)
        })

    @property
    def position(self) -> Point:
        return self.coords[0]

    @property
    def width(self) -> float:
        return self.attributes['width']

    @property
    def height(self) -> float:
        return self.attributes['height']

    @property
    def image_path(self) -> str:
        return self.attributes['image_path']

    @property
    def rotation(self) -> float:
        return self.attributes['rotation']

    @property
    def scale_x(self) -> float:
        return self.attributes['scale_x']

    @property
    def scale_y(self) -> float:
        return self.attributes['scale_y']

    @property
    def opacity(self) -> float:
        return self.attributes['opacity']

    @property
    def brightness(self) -> float:
        return self.attributes['brightness']

    @property
    def contrast(self) -> float:
        return self.attributes['contrast']


class ImageTool(Tool):
    """Tool for importing and manipulating images"""

    def __init__(self, main_window, document, preferences):
        super().__init__(main_window, document, preferences)
        self.preview_items = []
        self.image_path = ""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="IMAGE",
            name="Image",
            category=ToolCategory.MISC,
            icon="tool-image",
            cursor="crosshair",
            is_creator=True,
            secondary_key="I",
            node_info=["Position", "Size Point"]
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

        if self.state == ToolState.INIT:
            # First show file dialog to select image
            file_path, _ = QFileDialog.getOpenFileName(
                self.main_window,
                "Select Image",
                "",
                "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
            )
            if not file_path:
                self.cancel()
                return

            # Load image to get dimensions
            image = QImage(file_path)
            if image.isNull():
                self.cancel()
                return

            # Store image path and initial position
            self.image_path = file_path
            self.points.append(point)
            self.state = ToolState.DRAWING

        elif self.state == ToolState.DRAWING:
            # Second point determines size
            self.points.append(point)
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            # Draw preview of image placement
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x: float, current_y: float):
        """Draw preview of the image placement"""
        if len(self.points) < 1:
            return

        # Clear previous preview
        self.clear_preview()

        # Calculate size from points
        start = self.points[0]
        width = abs(current_x - start.x)
        height = abs(current_y - start.y)

        # Create preview rectangle
        rect = QGraphicsRectItem(
            min(start.x, current_x),
            min(start.y, current_y),
            width,
            height
        )
        pen = QPen(QColor(0, 0, 255), 1)
        pen.setStyle(Qt.PenStyle.DashLine)
        rect.setPen(pen)
        rect.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.preview_items.append(rect)

        # Add to scene
        self.scene.addItem(rect)

    def clear_preview(self):
        """Clear preview items"""
        for item in self.preview_items:
            self.scene.removeItem(item)
        self.preview_items.clear()

    def reset(self):
        """Reset tool state"""
        self.state = ToolState.INIT
        self.points.clear()
        self.image_path = ""
        self.clear_preview()

    def complete(self):
        """Complete the image placement"""
        if len(self.points) != 2:
            return

        # Calculate size from points
        start = self.points[0]
        end = self.points[1]
        width = abs(end.x - start.x)
        height = abs(end.y - start.y)

        # Create image object
        image = ImageObject(
            self.main_window,
            self.document.objects.get_next_id(),
            start,
            width,
            height,
            self.image_path
        )

        # Add to document
        self.document.objects.objects[image.object_id] = image

        # Emit signal
        self.object_created.emit(image)

        # Reset tool state
        self.reset()