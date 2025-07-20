"""
Point Tool Implementation

This module implements the point drawing tool based on the original TCL
tools_points.tcl implementation.
"""

from typing import Optional, List

from ..core.cad_objects import CADObject, ObjectType
from .base import Tool, ToolState, ToolCategory, ToolDefinition


class PointTool(Tool):
    """Tool for drawing individual points"""

    # Class-level tool definition
    tool_definitions = [
        ToolDefinition(
            token="POINT",
            name="Point",
            category=ToolCategory.MISC,
            icon="tool-point",
            cursor="crosshair",
            is_creator=True,
            secondary_key="P",
            node_info=["Point Location"]
        )
    ]

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
            # Add the point
            self.points.append(point)

            # Complete immediately since we only need one point
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.ACTIVE:
            # Draw preview point
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the point being created"""
        # Clear previous preview
        self.clear_temp_objects()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(current_x, current_y)

        # Draw temporary point marker (cross) using Qt graphics items
        x, y = point.x, point.y
        size = 3  # Size of the cross

        from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsEllipseItem, QGraphicsTextItem
        from PySide6.QtCore import QRectF, Qt
        from PySide6.QtGui import QPen

        # Draw horizontal line
        h_line_item = QGraphicsLineItem(x - size, y, x + size, y)
        pen = QPen()
        pen.setColor("blue")
        pen.setStyle(Qt.PenStyle.DashLine)
        h_line_item.setPen(pen)
        self.scene.addItem(h_line_item)

        # Draw vertical line
        v_line_item = QGraphicsLineItem(x, y - size, x, y + size)
        v_line_item.setPen(pen)
        self.scene.addItem(v_line_item)

        # Draw small circle around the point
        circle_item = QGraphicsEllipseItem(
            QRectF(x - size, y - size, 2 * size, 2 * size))
        circle_item.setPen(pen)
        self.scene.addItem(circle_item)

        self.temp_objects.extend([h_line_item, v_line_item, circle_item])

        # Add coordinates text
        text_item = QGraphicsTextItem(f"({x:.1f}, {y:.1f})")
        text_item.setPos(x, y + 15)
        text_item.setDefaultTextColor("blue")
        self.scene.addItem(text_item)
        self.temp_objects.append(text_item)

    def create_object(self) -> Optional[CADObject]:
        """Create a point object from the collected point"""
        if len(self.points) != 1:
            return None

        point = self.points[0]

        # Create a point object
        obj = CADObject(
            mainwin=self.main_window,
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.POINT,
            layer=self.document.objects.current_layer,
            coords=[point],
            attributes={
                'color': 'black',      # Default color
                'linewidth': 1         # Default line width
            }
        )
        return obj
