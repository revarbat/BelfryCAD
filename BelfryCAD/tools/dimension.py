"""
Dimension Tools Implementation

This module implements various dimension tools based on the original TCL
tools_dimensions.tcl implementation.
"""

import math
from typing import Optional, List

from PySide6.QtWidgets import (QGraphicsLineItem, QGraphicsTextItem)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QColor, QTransform

from BelfryCAD.core.cad_objects import CADObject, ObjectType, Point
from BelfryCAD.tools.base import Tool, ToolState, ToolCategory, ToolDefinition


class DimensionObject(CADObject):
    """Dimension object - measurement between two points"""

    def __init__(self, object_id: int, start: Point, end: Point,
                 text_position: Point, **kwargs):
        super().__init__(object_id, ObjectType.DIMENSION,
                         coords=[start, end, text_position], **kwargs)
        self.attributes.update({
            'precision': kwargs.get('precision', 2),
            'units': kwargs.get('units', 'mm')
        })

    @property
    def start(self) -> Point:
        return self.coords[0]

    @property
    def end(self) -> Point:
        return self.coords[1]

    @property
    def text_position(self) -> Point:
        return self.coords[2]

    def measured_distance(self) -> float:
        return self.start.distance_to(self.end)


class HorizontalDimensionTool(Tool):
    """Tool for creating horizontal dimension lines"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="DIMLINEH",
            name="Horizontal Dimension",
            category=ToolCategory.DIMENSIONS,
            icon="tool-dimlineh",
            cursor="crosshair",
            is_creator=True,
            secondary_key="H",
            node_info=["Start Point", "End Point", "Line Offset"]
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
            # First point - start of dimension line
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING and len(self.points) == 1:
            # Second point - end of dimension line
            # For horizontal dimension, we need to adjust the Y to match
            # the first point
            adjusted_point = Point(point.x, self.points[0].y)
            self.points.append(adjusted_point)
        elif self.state == ToolState.DRAWING and len(self.points) == 2:
            # Third point - offset distance for dimension line
            # For horizontal dimension, we only care about the Y coordinate
            adjusted_point = Point(point.x, point.y)
            self.points.append(adjusted_point)
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            # Draw preview dimension
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the dimension being created"""
        # Clear previous preview
        self.clear_temp_objects()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(current_x, current_y)

        if len(self.points) == 1:
            # Drawing from start to end point
            start = self.points[0]

            # For horizontal dimension, adjust the Y to match
            end = Point(point.x, start.y)

            # Draw temporary line
            line_item = QGraphicsLineItem(start.x, start.y, end.x, end.y)
            pen = QPen(QColor("blue"))
            pen.setStyle(Qt.DashLine)
            line_item.setPen(pen)
            self.scene.addItem(line_item)
            self.temp_objects.append(line_item)

            # Draw dimension text
            length = abs(end.x - start.x)
            text_item = QGraphicsTextItem(f"{length:.2f}")
            text_item.setDefaultTextColor(QColor("blue"))
            text_item.setPos((start.x + end.x) / 2 - 20, start.y - 30)
            self.scene.addItem(text_item)
            self.temp_objects.append(text_item)

        elif len(self.points) == 2:
            # Drawing offset position
            start = self.points[0]
            end = self.points[1]

            # Draw dimension line at the current offset position
            offset_y = point.y

            # Extension lines
            ext1_item = QGraphicsLineItem(start.x, start.y, start.x, offset_y)
            pen1 = QPen(QColor("blue"))
            pen1.setStyle(Qt.DashLine)
            ext1_item.setPen(pen1)
            self.scene.addItem(ext1_item)

            ext2_item = QGraphicsLineItem(end.x, end.y, end.x, offset_y)
            pen2 = QPen(QColor("blue"))
            pen2.setStyle(Qt.DashLine)
            ext2_item.setPen(pen2)
            self.scene.addItem(ext2_item)

            # Dimension line
            dim_item = QGraphicsLineItem(start.x, offset_y, end.x, offset_y)
            pen3 = QPen(QColor("blue"))
            pen3.setStyle(Qt.DashLine)
            dim_item.setPen(pen3)
            self.scene.addItem(dim_item)

            # Arrow heads
            arrow_size = 10

            # Left arrow
            left_arrow1_item = QGraphicsLineItem(
                start.x, offset_y, start.x + arrow_size,
                offset_y - arrow_size/2
            )
            left_arrow1_item.setPen(QPen(QColor("blue")))
            self.scene.addItem(left_arrow1_item)

            left_arrow2_item = QGraphicsLineItem(
                start.x, offset_y, start.x + arrow_size,
                offset_y + arrow_size/2
            )
            left_arrow2_item.setPen(QPen(QColor("blue")))
            self.scene.addItem(left_arrow2_item)

            # Right arrow
            right_arrow1_item = QGraphicsLineItem(
                end.x, offset_y, end.x - arrow_size,
                offset_y - arrow_size/2
            )
            right_arrow1_item.setPen(QPen(QColor("blue")))
            self.scene.addItem(right_arrow1_item)

            right_arrow2_item = QGraphicsLineItem(
                end.x, offset_y, end.x - arrow_size,
                offset_y + arrow_size/2
            )
            right_arrow2_item.setPen(QPen(QColor("blue")))
            self.scene.addItem(right_arrow2_item)

            # Dimension text
            length = abs(end.x - start.x)
            text_item = QGraphicsTextItem(f"{length:.2f}")
            text_item.setDefaultTextColor(QColor("blue"))
            text_item.setPos((start.x + end.x) / 2 - 20, offset_y - 30)
            self.scene.addItem(text_item)

            self.temp_objects.extend([
                ext1_item, ext2_item, dim_item,
                left_arrow1_item, left_arrow2_item,
                right_arrow1_item, right_arrow2_item,
                text_item
            ])

    def create_object(self) -> Optional[CADObject]:
        """Create a dimension object from the collected points"""
        if len(self.points) != 3:
            return None

        start = self.points[0]
        end = self.points[1]
        offset = self.points[2]

        # Calculate dimension value
        length = abs(end.x - start.x)

        # Create a dimension object
        obj = CADObject(
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.DIMENSION,
            layer=self.document.objects.current_layer,
            coords=[start, end, offset],
            attributes={
                'color': 'black',      # Default color
                'linewidth': 1,        # Default line width
                'dimension_type': 'horizontal',
                'dimension_value': length,
                'text': f"{length:.2f}"
            }
        )
        return obj


class VerticalDimensionTool(Tool):
    """Tool for creating vertical dimension lines"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="DIMLINEV",
            name="Vertical Dimension",
            category=ToolCategory.DIMENSIONS,
            icon="tool-dimlinev",
            cursor="crosshair",
            is_creator=True,
            secondary_key="V",
            node_info=["Start Point", "End Point", "Line Offset"]
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
            # First point - start of dimension line
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING and len(self.points) == 1:
            # Second point - end of dimension line
            # For vertical dimension, we need to adjust the X to match
            # the first point
            adjusted_point = Point(self.points[0].x, point.y)
            self.points.append(adjusted_point)
        elif self.state == ToolState.DRAWING and len(self.points) == 2:
            # Third point - offset distance for dimension line
            # For vertical dimension, we only care about the X coordinate
            adjusted_point = Point(point.x, point.y)
            self.points.append(adjusted_point)
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            # Draw preview dimension
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the dimension being created"""
        # Clear previous preview
        self.clear_temp_objects()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(current_x, current_y)

        if len(self.points) == 1:
            # Drawing from start to end point
            start = self.points[0]

            # For vertical dimension, adjust the X to match
            end = Point(start.x, point.y)

            # Draw temporary line
            line_item = QGraphicsLineItem(start.x, start.y, end.x, end.y)
            pen = QPen(QColor("blue"))
            pen.setStyle(Qt.DashLine)
            line_item.setPen(pen)
            self.scene.addItem(line_item)
            self.temp_objects.append(line_item)

            # Draw dimension text
            length = abs(end.y - start.y)
            text_item = QGraphicsTextItem(f"{length:.2f}")
            text_item.setDefaultTextColor(QColor("blue"))
            # Create rotation transform for vertical text
            transform = QTransform()
            transform.rotate(90)
            text_item.setTransform(transform)
            text_item.setPos(start.x - 45, (start.y + end.y) / 2 - 10)
            self.scene.addItem(text_item)
            self.temp_objects.append(text_item)

        elif len(self.points) == 2:
            # Drawing offset position
            start = self.points[0]
            end = self.points[1]

            # Draw dimension line at the current offset position
            offset_x = point.x

            # Extension lines
            ext1_item = QGraphicsLineItem(start.x, start.y, offset_x, start.y)
            pen1 = QPen(QColor("blue"))
            pen1.setStyle(Qt.DashLine)
            ext1_item.setPen(pen1)
            self.scene.addItem(ext1_item)

            ext2_item = QGraphicsLineItem(end.x, end.y, offset_x, end.y)
            pen2 = QPen(QColor("blue"))
            pen2.setStyle(Qt.DashLine)
            ext2_item.setPen(pen2)
            self.scene.addItem(ext2_item)

            # Dimension line
            dim_item = QGraphicsLineItem(offset_x, start.y, offset_x, end.y)
            pen3 = QPen(QColor("blue"))
            pen3.setStyle(Qt.DashLine)
            dim_item.setPen(pen3)
            self.scene.addItem(dim_item)

            # Arrow heads
            arrow_size = 10

            # Top arrow
            top_arrow1_item = QGraphicsLineItem(
                offset_x, start.y, offset_x - arrow_size/2,
                start.y + arrow_size
            )
            top_arrow1_item.setPen(QPen(QColor("blue")))
            self.scene.addItem(top_arrow1_item)

            top_arrow2_item = QGraphicsLineItem(
                offset_x, start.y, offset_x + arrow_size/2,
                start.y + arrow_size
            )
            top_arrow2_item.setPen(QPen(QColor("blue")))
            self.scene.addItem(top_arrow2_item)

            # Bottom arrow
            bottom_arrow1_item = QGraphicsLineItem(
                offset_x, end.y, offset_x - arrow_size/2,
                end.y - arrow_size
            )
            bottom_arrow1_item.setPen(QPen(QColor("blue")))
            self.scene.addItem(bottom_arrow1_item)

            bottom_arrow2_item = QGraphicsLineItem(
                offset_x, end.y, offset_x + arrow_size/2,
                end.y - arrow_size
            )
            bottom_arrow2_item.setPen(QPen(QColor("blue")))
            self.scene.addItem(bottom_arrow2_item)

            # Dimension text
            length = abs(end.y - start.y)
            text_item = QGraphicsTextItem(f"{length:.2f}")
            text_item.setDefaultTextColor(QColor("blue"))
            # Create rotation transform for vertical text
            transform = QTransform()
            transform.rotate(90)
            text_item.setTransform(transform)
            text_item.setPos(offset_x - 45, (start.y + end.y) / 2 - 10)
            self.scene.addItem(text_item)

            self.temp_objects.extend([
                ext1_item, ext2_item, dim_item,
                top_arrow1_item, top_arrow2_item,
                bottom_arrow1_item, bottom_arrow2_item,
                text_item
            ])

    def create_object(self) -> Optional[CADObject]:
        """Create a dimension object from the collected points"""
        if len(self.points) != 3:
            return None

        start = self.points[0]
        end = self.points[1]
        offset = self.points[2]

        # Calculate dimension value
        length = abs(end.y - start.y)

        # Create a dimension object
        obj = CADObject(
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.DIMENSION,
            layer=self.document.objects.current_layer,
            coords=[start, end, offset],
            attributes={
                'color': 'black',      # Default color
                'linewidth': 1,        # Default line width
                'dimension_type': 'vertical',
                'dimension_value': length,
                'text': f"{length:.2f}"
            }
        )
        return obj


class LinearDimensionTool(Tool):
    """Tool for creating linear dimension lines at any angle"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="DIMLINE",
            name="Linear Dimension",
            category=ToolCategory.DIMENSIONS,
            icon="tool-dimline",
            cursor="crosshair",
            is_creator=True,
            secondary_key="L",
            node_info=["Start Point", "End Point", "Line Offset"]
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
            # First point - start of dimension line
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING and len(self.points) == 1:
            # Second point - end of dimension line
            self.points.append(point)
        elif self.state == ToolState.DRAWING and len(self.points) == 2:
            # Third point - offset distance for dimension line
            self.points.append(point)
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            # Draw preview dimension
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the dimension being created"""
        # Clear previous preview
        self.clear_temp_objects()

        # Get the snapped point based on current snap settings
        point = self.get_snap_point(current_x, current_y)

        if len(self.points) == 1:
            # Drawing from start to end point
            start = self.points[0]
            end = point

            # Draw temporary line
            line_item = QGraphicsLineItem(start.x, start.y, end.x, end.y)
            pen = QPen(QColor("blue"))
            pen.setStyle(Qt.DashLine)
            line_item.setPen(pen)
            self.scene.addItem(line_item)
            self.temp_objects.append(line_item)

            # Draw dimension text
            length = math.sqrt((end.x - start.x)**2 + (end.y - start.y)**2)

            # Calculate angle for text
            angle = math.degrees(math.atan2(end.y - start.y, end.x - start.x))
            if angle < 0:
                angle += 360

            text_item = QGraphicsTextItem(f"{length:.2f}")
            text_item.setDefaultTextColor(QColor("blue"))
            text_item.setPos(
                (start.x + end.x) / 2 - 20, (start.y + end.y) / 2 - 30
            )
            self.scene.addItem(text_item)
            self.temp_objects.append(text_item)

        elif len(self.points) == 2:
            # Drawing offset position
            start = self.points[0]
            end = self.points[1]
            offset = point

            # Calculate the line direction and perpendicular direction
            dx = end.x - start.x
            dy = end.y - start.y
            length = math.sqrt(dx**2 + dy**2)

            if length < 0.001:  # Avoid division by zero
                return

            # Normalize direction vector
            dx /= length
            dy /= length

            # Perpendicular direction vector
            perp_dx = -dy
            perp_dy = dx

            # Calculate the perpendicular distance from the offset
            # point to the line.  Project the vector (offset - start) onto
            # the perpendicular direction
            offset_vec_x = offset.x - start.x
            offset_vec_y = offset.y - start.y
            perp_dist = offset_vec_x * perp_dx + offset_vec_y * perp_dy

            # Calculate the points for dimension line
            dim_start_x = start.x + perp_dx * perp_dist
            dim_start_y = start.y + perp_dy * perp_dist
            dim_end_x = end.x + perp_dx * perp_dist
            dim_end_y = end.y + perp_dy * perp_dist

            # Extension lines
            ext1_item = QGraphicsLineItem(
                start.x, start.y, dim_start_x, dim_start_y
            )
            pen1 = QPen(QColor("blue"))
            pen1.setStyle(Qt.DashLine)
            ext1_item.setPen(pen1)
            self.scene.addItem(ext1_item)

            ext2_item = QGraphicsLineItem(
                end.x, end.y, dim_end_x, dim_end_y
            )
            pen2 = QPen(QColor("blue"))
            pen2.setStyle(Qt.DashLine)
            ext2_item.setPen(pen2)
            self.scene.addItem(ext2_item)

            # Dimension line
            dim_item = QGraphicsLineItem(
                dim_start_x, dim_start_y, dim_end_x, dim_end_y
            )
            pen3 = QPen(QColor("blue"))
            pen3.setStyle(Qt.DashLine)
            dim_item.setPen(pen3)
            self.scene.addItem(dim_item)

            # Arrow heads - calculate the arrow points
            arrow_size = 10
            arrow_angle = math.radians(15)  # 15 degree arrow

            # For start arrow
            angle1 = math.atan2(dim_end_y - dim_start_y,
                                dim_end_x - dim_start_x)
            arrow1_x1 = dim_start_x + arrow_size * \
                math.cos(angle1 + math.pi - arrow_angle)
            arrow1_y1 = dim_start_y + arrow_size * \
                math.sin(angle1 + math.pi - arrow_angle)
            arrow1_x2 = dim_start_x + arrow_size * \
                math.cos(angle1 + math.pi + arrow_angle)
            arrow1_y2 = dim_start_y + arrow_size * \
                math.sin(angle1 + math.pi + arrow_angle)

            # For end arrow
            angle2 = math.atan2(dim_start_y - dim_end_y,
                                dim_start_x - dim_end_x)
            arrow2_x1 = dim_end_x + arrow_size * \
                math.cos(angle2 + math.pi - arrow_angle)
            arrow2_y1 = dim_end_y + arrow_size * \
                math.sin(angle2 + math.pi - arrow_angle)
            arrow2_x2 = dim_end_x + arrow_size * \
                math.cos(angle2 + math.pi + arrow_angle)
            arrow2_y2 = dim_end_y + arrow_size * \
                math.sin(angle2 + math.pi + arrow_angle)

            # Draw arrows
            start_arrow1_item = QGraphicsLineItem(
                dim_start_x, dim_start_y, arrow1_x1, arrow1_y1
            )
            start_arrow1_item.setPen(QPen(QColor("blue")))
            self.scene.addItem(start_arrow1_item)

            start_arrow2_item = QGraphicsLineItem(
                dim_start_x, dim_start_y, arrow1_x2, arrow1_y2
            )
            start_arrow2_item.setPen(QPen(QColor("blue")))
            self.scene.addItem(start_arrow2_item)

            end_arrow1_item = QGraphicsLineItem(
                dim_end_x, dim_end_y, arrow2_x1, arrow2_y1
            )
            end_arrow1_item.setPen(QPen(QColor("blue")))
            self.scene.addItem(end_arrow1_item)

            end_arrow2_item = QGraphicsLineItem(
                dim_end_x, dim_end_y, arrow2_x2, arrow2_y2
            )
            end_arrow2_item.setPen(QPen(QColor("blue")))
            self.scene.addItem(end_arrow2_item)

            # Dimension text
            text_x = (dim_start_x + dim_end_x) / 2
            text_y = (dim_start_y + dim_end_y) / 2

            # Calculate the offset for the text to place it above the
            # dimension line
            text_offset = 15
            text_offset_x = text_offset * perp_dx
            text_offset_y = text_offset * perp_dy

            # Draw the text with proper rotation
            text_angle = math.degrees(math.atan2(dy, dx))
            if text_angle < -90 or text_angle > 90:
                text_angle += 180  # Flip text if it would be upside-down

            text_item = QGraphicsTextItem(f"{length:.2f}")
            text_item.setDefaultTextColor(QColor("blue"))
            # Create rotation transform for angled text
            transform = QTransform()
            transform.rotate(text_angle)
            text_item.setTransform(transform)
            text_item.setPos(
                text_x - text_offset_x - 20, text_y - text_offset_y - 15
            )
            self.scene.addItem(text_item)

            self.temp_objects.extend([
                ext1_item, ext2_item, dim_item,
                start_arrow1_item, start_arrow2_item,
                end_arrow1_item, end_arrow2_item,
                text_item
            ])

    def create_object(self) -> Optional[CADObject]:
        """Create a dimension object from the collected points"""
        if len(self.points) != 3:
            return None

        start = self.points[0]
        end = self.points[1]
        offset = self.points[2]

        # Calculate dimension value
        length = math.sqrt((end.x - start.x)**2 + (end.y - start.y)**2)

        # Calculate angle for the dimension
        angle = math.degrees(math.atan2(end.y - start.y, end.x - start.x))

        # Create a dimension object
        obj = CADObject(
            object_id=self.document.objects.get_next_id(),
            object_type=ObjectType.DIMENSION,
            layer=self.document.objects.current_layer,
            coords=[start, end, offset],
            attributes={
                'color': 'black',      # Default color
                'linewidth': 1,        # Default line width
                'dimension_type': 'linear',
                'dimension_value': length,
                'angle': angle,
                'text': f"{length:.2f}"
            }
        )
        return obj


class ArcDimensionObject(CADObject):
    """Arc dimension object - angle measurement between two points"""

    def __init__(self, object_id: int, center: Point, start_angle: Point,
                 end_angle: Point, arc_offset: Point, **kwargs):
        super().__init__(object_id, ObjectType.DIMENSION,
                         coords=[center, start_angle, end_angle, arc_offset],
                         **kwargs)
        self.attributes.update({
            'precision': kwargs.get('precision', 2),
            'units': kwargs.get('units', '°'),
            'dimension_type': 'arc'
        })

    @property
    def center(self) -> Point:
        return self.coords[0]

    @property
    def start_angle_point(self) -> Point:
        return self.coords[1]

    @property
    def end_angle_point(self) -> Point:
        return self.coords[2]

    @property
    def arc_offset_point(self) -> Point:
        return self.coords[3]

    def measured_angle(self) -> float:
        """Calculate angle between two points from center in degrees"""
        # Calculate angles from center to each point
        angle1 = math.degrees(math.atan2(
            self.start_angle_point.y - self.center.y,
            self.start_angle_point.x - self.center.x
        ))
        angle2 = math.degrees(math.atan2(
            self.end_angle_point.y - self.center.y,
            self.end_angle_point.x - self.center.x
        ))

        # Calculate angle difference
        diff = angle2 - angle1

        # Normalize to [-180, 180]
        while diff < -180:
            diff += 360
        while diff > 180:
            diff -= 360

        return abs(diff)


class ArcDimensionTool(Tool):
    """Tool for creating arc dimension lines (angle measurements)"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="DIMARC",
            name="Arc Dimension",
            category=ToolCategory.DIMENSIONS,
            icon="tool-dimarc",
            cursor="crosshair",
            is_creator=True,
            secondary_key="A",
            node_info=["Center Point", "Start Point", "End Point",
                       "Arc Offset"]
        )]

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        pass

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        point = self.get_snap_point(event.x, event.y)

        if self.state == ToolState.ACTIVE:
            # First point - center of arc
            self.points.append(point)
            self.state = ToolState.DRAWING
        elif self.state == ToolState.DRAWING and len(self.points) == 1:
            # Second point - start angle point
            self.points.append(point)
        elif self.state == ToolState.DRAWING and len(self.points) == 2:
            # Third point - end angle point
            self.points.append(point)
        elif self.state == ToolState.DRAWING and len(self.points) == 3:
            # Fourth point - arc offset position
            self.points.append(point)
            self.complete()

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        if self.state == ToolState.DRAWING:
            self.draw_preview(event.x, event.y)

    def draw_preview(self, current_x, current_y):
        """Draw a preview of the arc dimension being created"""
        self.clear_temp_objects()

        point = self.get_snap_point(current_x, current_y)

        if len(self.points) == 1:
            # Preview line from center to current position
            center = self.points[0]
            line_item = QGraphicsLineItem(center.x, center.y,
                                          point.x, point.y)
            pen = QPen(QColor("blue"))
            pen.setStyle(Qt.DashLine)
            line_item.setPen(pen)
            self.scene.addItem(line_item)
            self.temp_objects.append(line_item)

        elif len(self.points) == 2:
            # Preview lines from center to both points
            center = self.points[0]
            start_point = self.points[1]

            # Line to start angle point
            line1_item = QGraphicsLineItem(center.x, center.y,
                                           start_point.x, start_point.y)
            pen1 = QPen(QColor("blue"))
            pen1.setStyle(Qt.DashLine)
            line1_item.setPen(pen1)
            self.scene.addItem(line1_item)

            # Line to current end angle point
            line2_item = QGraphicsLineItem(center.x, center.y,
                                           point.x, point.y)
            pen2 = QPen(QColor("blue"))
            pen2.setStyle(Qt.DashLine)
            line2_item.setPen(pen2)
            self.scene.addItem(line2_item)

            self.temp_objects.extend([line1_item, line2_item])

        elif len(self.points) == 3:
            # Preview complete arc dimension
            center = self.points[0]
            start_point = self.points[1]
            end_point = self.points[2]

            self._draw_arc_dimension_preview(center, start_point,
                                             end_point, point)

    def _draw_arc_dimension_preview(self, center: Point, start_point: Point,
                                    end_point: Point, offset_point: Point):
        """Draw a complete arc dimension preview"""
        # Calculate angles
        start_angle = math.atan2(start_point.y - center.y,
                                 start_point.x - center.x)
        end_angle = math.atan2(end_point.y - center.y,
                               end_point.x - center.x)
        offset_angle = math.atan2(offset_point.y - center.y,
                                  offset_point.x - center.x)

        # Calculate arc radius based on offset point distance
        arc_radius = math.sqrt((offset_point.x - center.x)**2 +
                               (offset_point.y - center.y)**2)

        # Calculate angle difference
        angle_diff = end_angle - start_angle

        # Normalize angle difference
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi

        # Determine which way to draw the arc based on offset position
        mid_angle = (start_angle + end_angle) / 2
        if abs(offset_angle - mid_angle) > math.pi / 2:
            # Use the long way around
            if angle_diff > 0:
                angle_diff -= 2 * math.pi
            else:
                angle_diff += 2 * math.pi

        # Draw extension lines
        start_radius = math.sqrt((start_point.x - center.x)**2 +
                                 (start_point.y - center.y)**2)
        end_radius = math.sqrt((end_point.x - center.x)**2 +
                               (end_point.y - center.y)**2)

        # Extension line from start point to arc
        ext_start_x = center.x + arc_radius * math.cos(start_angle)
        ext_start_y = center.y + arc_radius * math.sin(start_angle)
        if start_radius < arc_radius:
            ext1_item = QGraphicsLineItem(start_point.x, start_point.y,
                                          ext_start_x, ext_start_y)
            pen1 = QPen(QColor("blue"))
            pen1.setStyle(Qt.DashLine)
            ext1_item.setPen(pen1)
            self.scene.addItem(ext1_item)
            self.temp_objects.append(ext1_item)

        # Extension line from end point to arc
        ext_end_x = center.x + arc_radius * math.cos(end_angle)
        ext_end_y = center.y + arc_radius * math.sin(end_angle)
        if end_radius < arc_radius:
            ext2_item = QGraphicsLineItem(end_point.x, end_point.y,
                                          ext_end_x, ext_end_y)
            pen2 = QPen(QColor("blue"))
            pen2.setStyle(Qt.DashLine)
            ext2_item.setPen(pen2)
            self.scene.addItem(ext2_item)
            self.temp_objects.append(ext2_item)

        # Draw arc segments (simplified version)
        num_segments = max(8, int(abs(angle_diff) * 180 / math.pi / 10))
        angle_step = angle_diff / num_segments

        for i in range(num_segments):
            angle1 = start_angle + i * angle_step
            angle2 = start_angle + (i + 1) * angle_step

            x1 = center.x + arc_radius * math.cos(angle1)
            y1 = center.y + arc_radius * math.sin(angle1)
            x2 = center.x + arc_radius * math.cos(angle2)
            y2 = center.y + arc_radius * math.sin(angle2)

            line_item = QGraphicsLineItem(x1, y1, x2, y2)
            pen = QPen(QColor("blue"))
            line_item.setPen(pen)
            self.scene.addItem(line_item)
            self.temp_objects.append(line_item)

        # Draw arrows at arc ends
        arrow_size = 0.1 * arc_radius
        arrow_angle = math.pi / 6  # 30 degrees

        # Start arrow
        arrow1_x1 = ext_start_x + arrow_size * math.cos(
            start_angle + math.pi - arrow_angle)
        arrow1_y1 = ext_start_y + arrow_size * math.sin(
            start_angle + math.pi - arrow_angle)
        arrow1_x2 = ext_start_x + arrow_size * math.cos(
            start_angle + math.pi + arrow_angle)
        arrow1_y2 = ext_start_y + arrow_size * math.sin(
            start_angle + math.pi + arrow_angle)

        start_arrow1_item = QGraphicsLineItem(ext_start_x, ext_start_y,
                                              arrow1_x1, arrow1_y1)
        start_arrow1_item.setPen(QPen(QColor("blue")))
        self.scene.addItem(start_arrow1_item)

        start_arrow2_item = QGraphicsLineItem(ext_start_x, ext_start_y,
                                              arrow1_x2, arrow1_y2)
        start_arrow2_item.setPen(QPen(QColor("blue")))
        self.scene.addItem(start_arrow2_item)

        # End arrow
        arrow2_x1 = ext_end_x + arrow_size * math.cos(
            end_angle - arrow_angle)
        arrow2_y1 = ext_end_y + arrow_size * math.sin(
            end_angle - arrow_angle)
        arrow2_x2 = ext_end_x + arrow_size * math.cos(
            end_angle + arrow_angle)
        arrow2_y2 = ext_end_y + arrow_size * math.sin(
            end_angle + arrow_angle)

        end_arrow1_item = QGraphicsLineItem(ext_end_x, ext_end_y,
                                            arrow2_x1, arrow2_y1)
        end_arrow1_item.setPen(QPen(QColor("blue")))
        self.scene.addItem(end_arrow1_item)

        end_arrow2_item = QGraphicsLineItem(ext_end_x, ext_end_y,
                                            arrow2_x2, arrow2_y2)
        end_arrow2_item.setPen(QPen(QColor("blue")))
        self.scene.addItem(end_arrow2_item)

        # Draw angle text
        angle_degrees = abs(math.degrees(angle_diff))
        text = f"{angle_degrees:.1f}°"

        # Position text at middle of arc
        text_angle = (start_angle + end_angle) / 2
        if abs(angle_diff) > math.pi:
            text_angle += math.pi  # Flip for reflex angles

        text_radius = arc_radius * 0.7  # Position text inside arc
        text_x = center.x + text_radius * math.cos(text_angle)
        text_y = center.y + text_radius * math.sin(text_angle)

        text_item = QGraphicsTextItem(text)
        text_item.setDefaultTextColor(QColor("blue"))
        text_item.setPos(text_x - 20, text_y - 10)
        self.scene.addItem(text_item)

        self.temp_objects.extend([
            start_arrow1_item, start_arrow2_item,
            end_arrow1_item, end_arrow2_item,
            text_item
        ])

    def create_object(self) -> Optional[CADObject]:
        """Create an arc dimension object from the collected points"""
        if len(self.points) != 4:
            return None

        center = self.points[0]
        start_point = self.points[1]
        end_point = self.points[2]
        offset_point = self.points[3]

        # Calculate angle value
        start_angle = math.degrees(math.atan2(start_point.y - center.y,
                                              start_point.x - center.x))
        end_angle = math.degrees(math.atan2(end_point.y - center.y,
                                            end_point.x - center.x))

        angle_diff = end_angle - start_angle
        while angle_diff < -180:
            angle_diff += 360
        while angle_diff > 180:
            angle_diff -= 360

        angle_value = abs(angle_diff)

        # Create arc dimension object
        obj = ArcDimensionObject(
            object_id=self.document.objects.get_next_id(),
            center=center,
            start_angle=start_point,
            end_angle=end_point,
            arc_offset=offset_point,
            layer=self.document.objects.current_layer,
            attributes={
                'color': 'black',
                'linewidth': 1,
                'dimension_type': 'arc',
                'dimension_value': angle_value,
                'text': f"{angle_value:.1f}°"
            }
        )
        return obj
