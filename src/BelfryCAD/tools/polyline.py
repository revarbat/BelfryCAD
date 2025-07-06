"""
Polyline Drawing Tool Implementation

This module implements a polyline drawing tool that allows creating connected
line segments by clicking multiple points. The polyline can be completed by
pressing escape or double-clicking.
"""

from typing import Optional, List
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPen, QColor
from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsEllipseItem

from ..core.cad_objects import CADObject, ObjectType, Point
from .base import Tool, ToolState, ToolCategory, ToolDefinition


class PolylineObject(CADObject):
    """Polyline object - list of connected line segments"""

    def __init__(self, object_id: int, vertices: List[Point], **kwargs):
        super().__init__(
            object_id, ObjectType.POLYGON, coords=vertices, **kwargs)

    def is_closed(self) -> bool:
        """Check if polyline is closed (first and last points are same)"""
        if len(self.coords) < 3:
            return False
        return (abs(self.coords[0].x - self.coords[-1].x) < 1e-6 and
                abs(self.coords[0].y - self.coords[-1].y) < 1e-6)


class PolylineTool(Tool):
    """Tool for drawing polylines (connected line segments)"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="POLYLINE",
            name="Polyline",
            category=ToolCategory.LINES,
            icon="tool-lines",
            cursor="crosshair",
            is_creator=True,
            secondary_key="P",
            node_info=[
                "Click points for polyline segments",
                "Escape to finish"
            ]
        )]

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        # In Qt, event handling is done differently - these will be connected
        # in the main window or graphics view
        pass

    def handle_escape(self, event):
        """Handle escape key to complete the polyline"""
        if self.state == ToolState.DRAWING and len(self.points) >= 2:
            # Complete the polyline with current points
            self.complete()
        else:
            # Cancel if not enough points
            self.cancel()

    def handle_double_click(self, event):
        """Handle double-click to complete the polyline"""
        if self.state == ToolState.DRAWING and len(self.points) >= 2:
            self.complete()

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
            # First point - start drawing polyline
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING:
            # Additional point - add to polyline
            self.points.append(point)
            # Continue drawing - don't complete automatically

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING and len(self.points) >= 1:
            # Draw preview of next segment
            if hasattr(event, 'scenePos'):
                scene_pos = event.scenePos()
            else:
                scene_pos = QPointF(event.x, event.y)
            self.draw_preview(scene_pos.x(), scene_pos.y())

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the polyline being created"""
        # Clear previous preview
        self.clear_temp_objects()

        if len(self.points) >= 1:
            # Get the snapped point based on current snap settings
            point = self.get_snap_point(current_x, current_y)

            # Draw all existing segments in the polyline
            for i in range(len(self.points) - 1):
                start_point = self.points[i]
                end_point = self.points[i + 1]

                # Draw segment line
                segment_line = QGraphicsLineItem(
                    start_point.x, start_point.y,
                    end_point.x, end_point.y
                )
                pen = QPen(QColor("green"))
                pen.setWidth(2)
                segment_line.setPen(pen)
                self.scene.addItem(segment_line)
                self.temp_objects.append(segment_line)

            # Draw preview line from last point to current mouse position
            last_point = self.points[-1]
            preview_line = QGraphicsLineItem(
                last_point.x, last_point.y,
                point.x, point.y
            )
            pen = QPen(QColor("blue"))
            pen.setDashPattern([4, 4])  # Dashed line for preview
            preview_line.setPen(pen)
            self.scene.addItem(preview_line)
            self.temp_objects.append(preview_line)

            # Draw vertex markers for existing points
            for i, vertex in enumerate(self.points):
                if i == 0:
                    # Start point - larger green circle
                    marker = QGraphicsEllipseItem(
                        vertex.x - 4, vertex.y - 4, 8, 8
                    )
                    pen = QPen(QColor("green"))
                    pen.setWidth(2)
                    marker.setPen(pen)
                else:
                    # Regular vertex - smaller blue circle
                    marker = QGraphicsEllipseItem(
                        vertex.x - 3, vertex.y - 3, 6, 6
                    )
                    pen = QPen(QColor("blue"))
                    pen.setWidth(2)
                    marker.setPen(pen)

                self.scene.addItem(marker)
                self.temp_objects.append(marker)

            # Draw current point marker (red)
            current_marker = QGraphicsEllipseItem(
                point.x - 2, point.y - 2, 4, 4
            )
            pen = QPen(QColor("red"))
            pen.setWidth(2)
            current_marker.setPen(pen)
            self.scene.addItem(current_marker)
            self.temp_objects.append(current_marker)

    def create_object(self) -> Optional[CADObject]:
        """Create a polyline object from the collected points"""
        if len(self.points) < 2:
            return None

        # Create a polyline object using POLYGON type with closed=False
        obj = CADObject(
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.POLYGON,
            layer=self.document.objects.current_layer,
            coords=self.points.copy(),
            attributes={
                'color': 'black',       # Default color
                'linewidth': 1,         # Default line width
                'closed': False,        # Open polyline (not closed polygon)
                'is_polyline': True,    # Mark as polyline for special handling
                'segment_count': len(self.points) - 1  # Number of segments
            }
        )
        return obj
