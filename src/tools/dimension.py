"""
Dimension Tools Implementation

This module implements various dimension tools based on the original TCL
tools_dimensions.tcl implementation.
"""

import math
from typing import Optional, List

from src.core.cad_objects import CADObject, ObjectType, Point
from src.tools.base import Tool, ToolState, ToolCategory, ToolDefinition


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
            node_info=["Start Point", "End Point", "Line Offset"]
        )]

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        self.canvas.bind("<Button-1>", self.handle_mouse_down)
        self.canvas.bind("<Motion>", self.handle_mouse_move)
        self.canvas.bind("<Escape>", self.handle_escape)

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
            line_id = self.canvas.create_line(
                start.x, start.y, end.x, end.y,
                fill="blue", dash=(4, 4)
            )
            self.temp_objects.append(line_id)

            # Draw dimension text
            length = abs(end.x - start.x)
            text_id = self.canvas.create_text(
                (start.x + end.x) / 2, start.y - 15,
                text=f"{length:.2f}",
                fill="blue"
            )
            self.temp_objects.append(text_id)

        elif len(self.points) == 2:
            # Drawing offset position
            start = self.points[0]
            end = self.points[1]

            # Draw dimension line at the current offset position
            offset_y = point.y

            # Extension lines
            ext1_id = self.canvas.create_line(
                start.x, start.y, start.x, offset_y,
                fill="blue", dash=(2, 2)
            )
            ext2_id = self.canvas.create_line(
                end.x, end.y, end.x, offset_y,
                fill="blue", dash=(2, 2)
            )

            # Dimension line
            dim_id = self.canvas.create_line(
                start.x, offset_y, end.x, offset_y,
                fill="blue", dash=(4, 4)
            )

            # Arrow heads
            arrow_size = 10

            # Left arrow
            left_arrow1_id = self.canvas.create_line(
                start.x, offset_y, start.x + arrow_size,
                offset_y - arrow_size/2,
                fill="blue"
            )
            left_arrow2_id = self.canvas.create_line(
                start.x, offset_y, start.x + arrow_size,
                offset_y + arrow_size/2,
                fill="blue"
            )

            # Right arrow
            right_arrow1_id = self.canvas.create_line(
                end.x, offset_y, end.x - arrow_size,
                offset_y - arrow_size/2,
                fill="blue"
            )
            right_arrow2_id = self.canvas.create_line(
                end.x, offset_y, end.x - arrow_size,
                offset_y + arrow_size/2,
                fill="blue"
            )

            # Dimension text
            length = abs(end.x - start.x)
            text_id = self.canvas.create_text(
                (start.x + end.x) / 2, offset_y - 15,
                text=f"{length:.2f}",
                fill="blue"
            )

            self.temp_objects.extend([
                ext1_id, ext2_id, dim_id,
                left_arrow1_id, left_arrow2_id,
                right_arrow1_id, right_arrow2_id,
                text_id
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
            node_info=["Start Point", "End Point", "Line Offset"]
        )]

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        self.canvas.bind("<Button-1>", self.handle_mouse_down)
        self.canvas.bind("<Motion>", self.handle_mouse_move)
        self.canvas.bind("<Escape>", self.handle_escape)

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
            line_id = self.canvas.create_line(
                start.x, start.y, end.x, end.y,
                fill="blue", dash=(4, 4)
            )
            self.temp_objects.append(line_id)

            # Draw dimension text
            length = abs(end.y - start.y)
            text_id = self.canvas.create_text(
                start.x - 15, (start.y + end.y) / 2,
                text=f"{length:.2f}",
                fill="blue",
                angle=90
            )
            self.temp_objects.append(text_id)

        elif len(self.points) == 2:
            # Drawing offset position
            start = self.points[0]
            end = self.points[1]

            # Draw dimension line at the current offset position
            offset_x = point.x

            # Extension lines
            ext1_id = self.canvas.create_line(
                start.x, start.y, offset_x, start.y,
                fill="blue", dash=(2, 2)
            )
            ext2_id = self.canvas.create_line(
                end.x, end.y, offset_x, end.y,
                fill="blue", dash=(2, 2)
            )

            # Dimension line
            dim_id = self.canvas.create_line(
                offset_x, start.y, offset_x, end.y,
                fill="blue", dash=(4, 4)
            )

            # Arrow heads
            arrow_size = 10

            # Top arrow
            top_arrow1_id = self.canvas.create_line(
                offset_x, start.y, offset_x - arrow_size/2,
                start.y + arrow_size,
                fill="blue"
            )
            top_arrow2_id = self.canvas.create_line(
                offset_x, start.y, offset_x + arrow_size/2,
                start.y + arrow_size,
                fill="blue"
            )

            # Bottom arrow
            bottom_arrow1_id = self.canvas.create_line(
                offset_x, end.y, offset_x - arrow_size/2,
                end.y - arrow_size,
                fill="blue"
            )
            bottom_arrow2_id = self.canvas.create_line(
                offset_x, end.y, offset_x + arrow_size/2,
                end.y - arrow_size,
                fill="blue"
            )

            # Dimension text
            length = abs(end.y - start.y)
            text_id = self.canvas.create_text(
                offset_x - 15, (start.y + end.y) / 2,
                text=f"{length:.2f}",
                fill="blue",
                angle=90
            )

            self.temp_objects.extend([
                ext1_id, ext2_id, dim_id,
                top_arrow1_id, top_arrow2_id,
                bottom_arrow1_id, bottom_arrow2_id,
                text_id
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
            node_info=["Start Point", "End Point", "Line Offset"]
        )]

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        self.canvas.bind("<Button-1>", self.handle_mouse_down)
        self.canvas.bind("<Motion>", self.handle_mouse_move)
        self.canvas.bind("<Escape>", self.handle_escape)

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
            line_id = self.canvas.create_line(
                start.x, start.y, end.x, end.y,
                fill="blue", dash=(4, 4)
            )
            self.temp_objects.append(line_id)

            # Draw dimension text
            length = math.sqrt((end.x - start.x)**2 + (end.y - start.y)**2)

            # Calculate angle for text
            angle = math.degrees(math.atan2(end.y - start.y, end.x - start.x))
            if angle < 0:
                angle += 360

            text_id = self.canvas.create_text(
                (start.x + end.x) / 2, (start.y + end.y) / 2 - 15,
                text=f"{length:.2f}",
                fill="blue"
            )
            self.temp_objects.append(text_id)

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
            ext1_id = self.canvas.create_line(
                start.x, start.y, dim_start_x, dim_start_y,
                fill="blue", dash=(2, 2)
            )
            ext2_id = self.canvas.create_line(
                end.x, end.y, dim_end_x, dim_end_y,
                fill="blue", dash=(2, 2)
            )

            # Dimension line
            dim_id = self.canvas.create_line(
                dim_start_x, dim_start_y, dim_end_x, dim_end_y,
                fill="blue", dash=(4, 4)
            )

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
            start_arrow1_id = self.canvas.create_line(
                dim_start_x, dim_start_y, arrow1_x1, arrow1_y1,
                fill="blue"
            )
            start_arrow2_id = self.canvas.create_line(
                dim_start_x, dim_start_y, arrow1_x2, arrow1_y2,
                fill="blue"
            )

            end_arrow1_id = self.canvas.create_line(
                dim_end_x, dim_end_y, arrow2_x1, arrow2_y1,
                fill="blue"
            )
            end_arrow2_id = self.canvas.create_line(
                dim_end_x, dim_end_y, arrow2_x2, arrow2_y2,
                fill="blue"
            )

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

            text_id = self.canvas.create_text(
                text_x - text_offset_x, text_y - text_offset_y,
                text=f"{length:.2f}",
                fill="blue",
                angle=text_angle
            )

            self.temp_objects.extend([
                ext1_id, ext2_id, dim_id,
                start_arrow1_id, start_arrow2_id,
                end_arrow1_id, end_arrow2_id,
                text_id
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
