"""
Arc Dimension Tool Implementation

This module implements the arc dimension tool based on the original TCL
DIMARC tool implementation.
"""

import math
from typing import Optional, List

from PySide6.QtWidgets import (QGraphicsLineItem, QGraphicsTextItem)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QColor

from src.core.cad_objects import CADObject, ObjectType, Point
from src.tools.base import Tool, ToolState, ToolCategory, ToolDefinition


class ArcDimensionObject(CADObject):
    """Arc dimension object - angle measurement between two points from center"""

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
