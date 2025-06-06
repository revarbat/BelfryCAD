"""
Line Drawing Tool Implementation

This module implements a line drawing tool based on the TCL
tool implementation.
"""

from typing import Optional, List
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPen, QColor
from PySide6.QtWidgets import QGraphicsLineItem

from BelfryCAD.core.cad_objects import CADObject, ObjectType, Point
from BelfryCAD.tools.base import Tool, ToolState, ToolCategory, ToolDefinition


class LineObject(CADObject):
    """Line object - requires exactly 2 points"""

    def __init__(self, object_id: int, start: Point, end: Point, **kwargs):
        super().__init__(
            object_id, ObjectType.LINE, coords=[start, end], **kwargs)

    @property
    def start(self) -> Point:
        return self.coords[0]

    @property
    def end(self) -> Point:
        return self.coords[1]

    def length(self) -> float:
        return self.start.distance_to(self.end)


class LineTool(Tool):
    """Tool for drawing straight lines"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="LINE",
            name="Line Tool",
            category=ToolCategory.LINES,
            icon="tool-line",
            cursor="crosshair",
            is_creator=True,
            secondary_key="L",
            node_info=["Start Point", "End Point"]
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
        # Convert Qt event coordinates to scene coordinates
        if hasattr(event, 'scenePos'):
            scene_pos = event.scenePos()
        else:
            scene_pos = QPointF(event.x, event.y)
        
        # Get the snapped point based on current snap settings
        point = self.get_snap_point(scene_pos.x(), scene_pos.y())

        if self.state == ToolState.ACTIVE:
            # First point - start drawing
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING:
            # Second point - complete the line
            self.points.append(point)
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING and len(self.points) == 1:
            # Draw preview line
            if hasattr(event, 'scenePos'):
                scene_pos = event.scenePos()
            else:
                scene_pos = QPointF(event.x, event.y)
            self.draw_preview(scene_pos.x(), scene_pos.y())

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the line being created"""
        # Clear previous preview
        self.clear_temp_objects()

        if len(self.points) == 1:
            # Get the snapped point based on current snap settings
            point = self.get_snap_point(current_x, current_y)

            # Draw temporary line
            start_point = self.points[0]
            pen = QPen(QColor("blue"))
            pen.setDashPattern([4, 4])  # Dashed line for preview
            
            preview_line = self.scene.addLine(
                start_point.x, start_point.y,
                point.x, point.y,
                pen
            )
            self.temp_objects.append(preview_line)

    def create_object(self) -> Optional[CADObject]:
        """Create a line object from the collected points"""
        if len(self.points) != 2:
            return None

        # Create a line object
        obj = CADObject(
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.LINE,
            layer=self.document.objects.current_layer,
            coords=self.points.copy(),
            attributes={
                'color': 'black',  # Default color
                'linewidth': 1     # Default line width
            }
        )
        return obj
