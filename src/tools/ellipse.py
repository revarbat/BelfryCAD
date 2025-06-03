"""
Ellipse Drawing Tool Implementation

This module implements various ellipse drawing tools based on the original TCL
tools_ellipses.tcl implementation.
"""

from typing import Optional, List

from src.core.cad_objects import CADObject, ObjectType, Point
from src.tools.base import Tool, ToolState, ToolCategory, ToolDefinition


class EllipseCenterTool(Tool):
    """Tool for drawing ellipses by center point and corner point"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="ELLIPSECTR",
            name="Ellipse by Center",
            category=ToolCategory.ELLIPSES,
            icon="tool-ellipsectr",
            cursor="crosshair",
            is_creator=True,
            node_info=["Center Point", "Corner Point"]
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
            # First point - center of ellipse
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING and len(self.points) == 1:
            # Second point - corner point defining x and y radii
            self.points.append(point)
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            # Draw preview ellipse
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the ellipse being created"""
        # Clear previous preview
        self.clear_temp_objects()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(current_x, current_y)

        if len(self.points) == 1:
            # Drawing from center to corner point
            center = self.points[0]

            # Calculate radii
            rad_x = abs(point.x - center.x)
            rad_y = abs(point.y - center.y)

            # Draw temporary ellipse using QGraphicsEllipseItem
            from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem
            from PySide6.QtCore import QRectF, Qt
            from PySide6.QtGui import QPen
            
            ellipse_item = QGraphicsEllipseItem(
                QRectF(center.x - rad_x, center.y - rad_y,
                       2 * rad_x, 2 * rad_y)
            )
            pen = QPen()
            pen.setColor("blue")
            pen.setStyle(Qt.DashLine)
            ellipse_item.setPen(pen)
            self.scene.addItem(ellipse_item)
            self.temp_objects.append(ellipse_item)

            # Draw major and minor axis lines
            line_h_item = QGraphicsLineItem(
                center.x - rad_x, center.y,
                center.x + rad_x, center.y
            )
            pen_line = QPen()
            pen_line.setColor("blue")
            pen_line.setStyle(Qt.DashLine)
            line_h_item.setPen(pen_line)
            self.scene.addItem(line_h_item)
            self.temp_objects.append(line_h_item)
            
            line_v_item = QGraphicsLineItem(
                center.x, center.y - rad_y,
                center.x, center.y + rad_y
            )
            line_v_item.setPen(pen_line)
            self.scene.addItem(line_v_item)
            self.temp_objects.append(line_v_item)

            # Add dimensions text
            if rad_x > 5 and rad_y > 5:  # Only show if large enough
                dim_x_item = QGraphicsTextItem(f"Width: {rad_x*2:.1f}")
                dim_x_item.setPos(center.x, center.y + rad_y + 15)
                dim_x_item.setDefaultTextColor("blue")
                self.scene.addItem(dim_x_item)
                self.temp_objects.append(dim_x_item)
                
                dim_y_item = QGraphicsTextItem(f"Height: {rad_y*2:.1f}")
                dim_y_item.setPos(center.x + rad_x + 15, center.y)
                dim_y_item.setDefaultTextColor("blue")
                self.scene.addItem(dim_y_item)
                self.temp_objects.append(dim_y_item)

    def create_object(self) -> Optional[CADObject]:
        """Create an ellipse object from the collected points"""
        if len(self.points) != 2:
            return None

        center = self.points[0]
        corner = self.points[1]

        # Calculate radii
        rad_x = abs(corner.x - center.x)
        rad_y = abs(corner.y - center.y)

        # Create an ellipse object
        obj = CADObject(
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.ELLIPSE,
            layer=self.document.objects.current_layer,
            coords=[center, corner],
            attributes={
                'color': 'black',      # Default color
                'linewidth': 1,        # Default line width
                'rad_x': rad_x,        # Store X radius
                'rad_y': rad_y         # Store Y radius
            }
        )
        return obj


class EllipseDiagonalTool(Tool):
    "Tool for drawing ellipses by diagonal opposite corners of bounding box"

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="ELLIPSEDIAG",
            name="Ellipse by Diagonal",
            category=ToolCategory.ELLIPSES,
            icon="tool-ellipsediag",
            cursor="crosshair",
            is_creator=True,
            node_info=["First Corner", "Opposite Corner"]
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
            # First point - first corner of ellipse bounding box
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING and len(self.points) == 1:
            # Second point - opposite corner defining the bounding box
            self.points.append(point)
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            # Draw preview ellipse
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the ellipse being created"""
        # Clear previous preview
        self.clear_temp_objects()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(current_x, current_y)

        if len(self.points) == 1:
            # Drawing from first corner to opposite corner
            p1 = self.points[0]
            p2 = point

            # Calculate bounding box coordinates
            x1, y1 = min(p1.x, p2.x), min(p1.y, p2.y)
            x2, y2 = max(p1.x, p2.x), max(p1.y, p2.y)

            # Calculate center and radii
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            rad_x = (x2 - x1) / 2
            rad_y = (y2 - y1) / 2

            # Draw temporary ellipse using QGraphicsEllipseItem
            from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem, QGraphicsRectItem
            from PySide6.QtCore import QRectF, Qt
            from PySide6.QtGui import QPen, QBrush
            
            ellipse_item = QGraphicsEllipseItem(QRectF(x1, y1, x2 - x1, y2 - y1))
            pen = QPen()
            pen.setColor("blue")
            pen.setStyle(Qt.DashLine)
            ellipse_item.setPen(pen)
            self.scene.addItem(ellipse_item)
            self.temp_objects.append(ellipse_item)

            # Draw bounding box
            box_item = QGraphicsRectItem(QRectF(x1, y1, x2 - x1, y2 - y1))
            pen_gray = QPen()
            pen_gray.setColor("gray")
            pen_gray.setStyle(Qt.DashLine)
            box_item.setPen(pen_gray)
            self.scene.addItem(box_item)
            self.temp_objects.append(box_item)

            # Draw center point
            center_item = QGraphicsEllipseItem(QRectF(center_x - 3, center_y - 3, 6, 6))
            center_item.setPen(QPen("gray"))
            center_item.setBrush(QBrush("gray"))
            self.scene.addItem(center_item)
            self.temp_objects.append(center_item)

            # Draw major and minor axis lines
            line_h_item = QGraphicsLineItem(
                center_x - rad_x, center_y,
                center_x + rad_x, center_y
            )
            line_h_item.setPen(QPen("blue"))
            self.scene.addItem(line_h_item)
            self.temp_objects.append(line_h_item)
            
            line_v_item = QGraphicsLineItem(
                center_x, center_y - rad_y,
                center_x, center_y + rad_y
            )
            line_v_item.setPen(QPen("blue"))
            self.scene.addItem(line_v_item)
            self.temp_objects.append(line_v_item)

            # Add dimensions text
            if rad_x > 5 and rad_y > 5:  # Only show if large enough
                dim_x_item = QGraphicsTextItem(f"Width: {rad_x*2:.1f}")
                dim_x_item.setPos(center_x, center_y + rad_y + 15)
                dim_x_item.setDefaultTextColor("blue")
                self.scene.addItem(dim_x_item)
                self.temp_objects.append(dim_x_item)
                
                dim_y_item = QGraphicsTextItem(f"Height: {rad_y*2:.1f}")
                dim_y_item.setPos(center_x + rad_x + 15, center_y)
                dim_y_item.setDefaultTextColor("blue")
                self.scene.addItem(dim_y_item)
                self.temp_objects.append(dim_y_item)

    def create_object(self) -> Optional[CADObject]:
        """Create an ellipse object from the collected points"""
        if len(self.points) != 2:
            return None

        p1 = self.points[0]
        p2 = self.points[1]

        # Calculate bounding box coordinates
        x1, y1 = min(p1.x, p2.x), min(p1.y, p2.y)
        x2, y2 = max(p1.x, p2.x), max(p1.y, p2.y)

        # Calculate center and radii
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        rad_x = (x2 - x1) / 2
        rad_y = (y2 - y1) / 2

        center = Point(center_x, center_y)

        # Create an ellipse object
        obj = CADObject(
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.ELLIPSE,
            layer=self.document.objects.current_layer,
            coords=[center, Point(center_x + rad_x, center_y + rad_y)],
            attributes={
                'color': 'black',      # Default color
                'linewidth': 1,        # Default line width
                'rad_x': rad_x,        # Store X radius
                'rad_y': rad_y,        # Store Y radius
                'bounds': [x1, y1, x2, y2]  # Store bounding box
            }
        )
        return obj
