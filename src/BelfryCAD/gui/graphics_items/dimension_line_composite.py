"""
DimensionLineComposite - A composite graphics item for drawing dimension lines.

This class creates separate QGraphicsItems for extension lines, arrow lines, and text,
providing better maintainability and flexibility.
"""

import math
from enum import Enum

from typing import Optional, Callable, List

from PySide6.QtCore import (
    Qt, QPointF, QRectF, QLineF
)
from PySide6.QtGui import (
    QPen, QColor, QPainter, QFont, QPainterPath, QFontMetrics,
    QPainterPathStroker
)
from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsLineItem, QGraphicsTextItem
)


class DimensionLineOrientation(Enum):
    """
    Enum for the different Orientation styles of the dimension line.
    """
    ANGLED = "angled"
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"



class DimensionLineComposite(QGraphicsItem):
    """A composite graphics item for drawing dimension lines with separate components."""
    
    def __init__(
            self,
            start_point: QPointF,
            end_point: QPointF,
            extension: float = 10.0,
            orientation: DimensionLineOrientation = DimensionLineOrientation.ANGLED,
            excess: float = 5.0,
            gap: float = 5.0,
            pen: Optional[QPen] = None,
            show_text: bool = False,
            text_format_callback: Optional[Callable[[float], str]] = None,
            text_rotation: float = 0.0,
            opposite_side: bool = False,
            parent: Optional[QGraphicsItem] = None
    ):
        super().__init__(parent)
        
        # Store the dimension line parameters
        self._start_point = start_point
        self._end_point = end_point
        self._extension = extension
        self._orientation = orientation
        self._excess_length = excess
        self._gap_length = gap
        
        # Set up the pen - default to black with width 1 if not provided
        if pen is None:
            self._pen = QPen(QColor(0, 0, 0), 1.0)
        else:
            self._pen = pen
        
        # Extract styling properties from pen for backward compatibility
        self._color = self._pen.color()
        self._line_width = self._pen.widthF()
        self._is_dashed = self._pen.style() == Qt.PenStyle.DashLine
        
        # Text properties
        self._show_text = show_text
        self._text_format_callback = text_format_callback
        self._text_rotation = text_rotation
        self._text_gap = 5.0  # Fixed constant gap size
        
        # Side selection
        self._opposite_side = opposite_side
        
        # Calculate the main vector from start to end
        self._main_vector = end_point - start_point
        print(f"mv={self._main_vector}")
        print(f"start={start_point}")
        print(f"end={end_point}")

        # Initialize component items
        self._extension_lines = []
        self._arrow_lines = []
        self._text_item = None
        
        # Set up the graphics item
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
        
        # Initialize drag mode
        self._drag_mode = "none"
        self._drag_start_pos = QPointF(0, 0)
        
        # Ensure the item is visible
        self.setVisible(True)
        
        # Create the component items
        self._create_components()
    
    def _create_components(self):
        """Create all the component graphics items."""
        # Calculate all points
        self._calculate_dimension_points()
        
        # Create extension lines
        self._create_extension_lines()
        
        # Create arrow lines
        self._create_arrow_lines()
        
        # Create text item
        if self._show_text:
            self._create_text_item()
    
    def _calculate_dimension_points(self):
        """Calculate all the points needed for drawing the dimension line."""
        # Calculate the arrow line vector (dimension line direction)
        # First, calculate where the arrow line should be positioned
        gap = self._gap_length
        excess = self._excess_length
        ext1 = self._extension
        ext2 = self._extension
        if self._orientation == DimensionLineOrientation.ANGLED:
            side_vector = QPointF(-self._main_vector.y(), self._main_vector.x())
        elif self._orientation == DimensionLineOrientation.HORIZONTAL:
            side_vector = QPointF(0, 1)
            dy = abs(self._main_vector.y())
            if self._main_vector.y() < 0:
                ext2 += dy
            else:
                ext1 += dy
        elif self._orientation == DimensionLineOrientation.VERTICAL:
            side_vector = QPointF(-1, 0)
            if self._main_vector.x() > 0:
                ext2 += abs(self._main_vector.x())
            else:
                ext1 += abs(self._main_vector.x())
        else:
            raise ValueError(f"Invalid Orientation: {self._orientation}")

        side_vector_length = math.hypot(side_vector.x(), side_vector.y())
        side_vector = side_vector * (1.0 / side_vector_length)
        if self._opposite_side:
            side_vector = -side_vector
        
        self._arrow_line_start = self._start_point + side_vector * (gap + ext1)
        self._arrow_line_end = self._end_point + side_vector * (gap + ext2)
        self._arrow_midpoint = (self._arrow_line_start + self._arrow_line_end) * 0.5
        self._side_line1_start = self._start_point + side_vector * gap
        self._side_line1_end = self._arrow_line_start + side_vector * excess
        self._side_line2_start = self._end_point + side_vector * gap
        self._side_line2_end = self._arrow_line_end + side_vector * excess
        self._text_position = self._arrow_midpoint
        
    def _create_extension_lines(self):
        """Create the extension line graphics items."""
        # Clear existing extension lines
        for line in self._extension_lines:
            if line.scene():
                line.scene().removeItem(line)
        self._extension_lines.clear()
                
        # Start extension line
        start_ext_line = QGraphicsLineItem(
            QLineF(self._side_line1_start, self._side_line1_end),
            self
        )
        start_ext_line.setPen(self._pen)
        self._extension_lines.append(start_ext_line)
        
        # End extension line
        end_ext_line = QGraphicsLineItem(
            QLineF(self._side_line2_start, self._side_line2_end),
            self
        )
        end_ext_line.setPen(self._pen)
        self._extension_lines.append(end_ext_line)
    
    def _create_arrow_lines(self):
        """Create the arrow line graphics items."""
        # Clear existing arrow lines
        for line in self._arrow_lines:
            if line.scene():
                line.scene().removeItem(line)
        self._arrow_lines.clear()
        
        # Calculate arrow line segments (with gap for text if needed)
        if self._show_text and self._text_gap > 0:
            # Calculate text width and gap
            font = QFont("Arial", 10)
            font_metrics = QFontMetrics(font)
            arrow_line_vector = self._arrow_line_end - self._arrow_line_start
            arrow_line_length = math.hypot(arrow_line_vector.x(), arrow_line_vector.y())
            arrow_line_vector = arrow_line_vector * (1.0 / arrow_line_length)
            
            if self._text_format_callback:
                text = self._text_format_callback(arrow_line_length)
            else:
                text = f"{arrow_line_length:.2f}"
            
            text_rect = font_metrics.boundingRect(text)
            text_width = text_rect.width()
            
            # Use constant gap size (text width + 2 * gap_length)
            total_gap_needed = text_width + 2 * self._text_gap
            
            if arrow_line_length > total_gap_needed:
                # Create two arrow line segments with gap
                gap_ratio = total_gap_needed / arrow_line_length
                gap_start_x = self._arrow_line_start.x() + (self._arrow_line_end.x() - self._arrow_line_start.x()) * (0.5 - gap_ratio/2)
                gap_start_y = self._arrow_line_start.y() + (self._arrow_line_end.y() - self._arrow_line_start.y()) * (0.5 - gap_ratio/2)
                gap_end_x = self._arrow_line_start.x() + (self._arrow_line_end.x() - self._arrow_line_start.x()) * (0.5 + gap_ratio/2)
                gap_end_y = self._arrow_line_start.y() + (self._arrow_line_end.y() - self._arrow_line_start.y()) * (0.5 + gap_ratio/2)
                
                # First segment
                arrow_line1 = QGraphicsLineItem(
                    QLineF(self._arrow_line_start, QPointF(gap_start_x, gap_start_y)),
                    self
                )
                arrow_line1.setPen(self._pen)
                self._arrow_lines.append(arrow_line1)
                
                # Second segment
                arrow_line2 = QGraphicsLineItem(
                    QLineF(QPointF(gap_end_x, gap_end_y), self._arrow_line_end),
                    self
                )
                arrow_line2.setPen(self._pen)
                self._arrow_lines.append(arrow_line2)
                
                # Add arrowheads
                self._create_arrowhead(self._arrow_line_start, self._arrow_line_start + QPointF(gap_start_x - self._arrow_line_start.x(), gap_start_y - self._arrow_line_start.y()))
                self._create_arrowhead(self._arrow_line_end, self._arrow_line_end + QPointF(gap_end_x - self._arrow_line_end.x(), gap_end_y - self._arrow_line_end.y()))
            else:
                # Single arrow line
                arrow_line = QGraphicsLineItem(
                    QLineF(self._arrow_line_start, self._arrow_line_end),
                    self
                )
                arrow_line.setPen(self._pen)
                self._arrow_lines.append(arrow_line)
                
        else:
            # Single arrow line without gap
            arrow_line = QGraphicsLineItem(
                QLineF(self._arrow_line_start, self._arrow_line_end),
                self
            )
            arrow_line.setPen(self._pen)
            self._arrow_lines.append(arrow_line)
            
        # Add arrowheads
        self._create_arrowhead(self._arrow_line_start, self._arrow_line_end)
        self._create_arrowhead(self._arrow_line_end, self._arrow_line_start)
    
    def _create_arrowhead(self, arrow_tip: QPointF, arrow_base: QPointF):
        """Create an arrowhead at the specified position."""
        arrow_length = 8.0
        arrow_width = 4.0
        
        # Calculate arrow direction vector
        direction = QPointF(arrow_tip.x() - arrow_base.x(), arrow_tip.y() - arrow_base.y())
        length = math.sqrt(direction.x()**2 + direction.y()**2)
        
        if length > 0:
            # Normalize direction
            direction = QPointF(direction.x() / length, direction.y() / length)
            
            # Calculate perpendicular vector
            perp = QPointF(-direction.y(), direction.x())
            
            # Calculate arrow points
            arrow_point1 = QPointF(
                arrow_tip.x() - direction.x() * arrow_length + perp.x() * arrow_width,
                arrow_tip.y() - direction.y() * arrow_length + perp.y() * arrow_width
            )
            arrow_point2 = QPointF(
                arrow_tip.x() - direction.x() * arrow_length - perp.x() * arrow_width,
                arrow_tip.y() - direction.y() * arrow_length - perp.y() * arrow_width
            )
            
            # Create arrowhead lines
            arrowhead_line1 = QGraphicsLineItem(
                QLineF(arrow_tip, arrow_point1),
                self
            )
            arrowhead_line1.setPen(QPen(self._color, self._line_width))
            self._arrow_lines.append(arrowhead_line1)
            
            arrowhead_line2 = QGraphicsLineItem(
                QLineF(arrow_tip, arrow_point2),
                self
            )
            arrowhead_line2.setPen(QPen(self._color, self._line_width))
            self._arrow_lines.append(arrowhead_line2)
    
    def _create_text_item(self):
        """Create the text graphics item."""
        # Remove existing text item
        if self._text_item and self._text_item.scene():
            self._text_item.scene().removeItem(self._text_item)
        
        # Calculate arrow line length
        arrow_line_vector = self._arrow_line_end - self._arrow_line_start
        arrow_line_length = math.hypot(arrow_line_vector.x(), arrow_line_vector.y())
        
        # Format the text
        if self._text_format_callback:
            text = self._text_format_callback(arrow_line_length)
        else:
            text = f"{arrow_line_length:.2f}"
        
        # Create text item
        self._text_item = QGraphicsTextItem(text, self)
        self._text_item.setDefaultTextColor(self._color)
        
        # Set font
        font = QFont("Arial", 10)
        self._text_item.setFont(font)
        
        # Calculate text angle
        line_angle = math.atan2(
            self._arrow_line_end.y() - self._arrow_line_start.y(),
            self._arrow_line_end.x() - self._arrow_line_start.x()
        )
        total_rotation = math.degrees(line_angle) + self._text_rotation
        
        # Position text at center of dimension line
        self._text_item.setPos(self._text_position)
        
        # Get text bounding rect before rotation
        text_rect = self._text_item.boundingRect()
        
        # Center the text on the dimension line
        self._text_item.setPos(
            self._text_position.x() - text_rect.width()/2,
            self._text_position.y() - text_rect.height()/2
        )
        
        # Apply rotation around the center of the text
        self._text_item.setTransformOriginPoint(text_rect.width()/2, text_rect.height()/2)
        self._text_item.setRotation(total_rotation)
    
    def setPoints(self, start_point: QPointF, end_point: QPointF):
        """Update the start and end points of the dimension line."""
        self._start_point = start_point
        self._end_point = end_point
        
        # Recalculate the main vector
        self._main_vector = QPointF(
            end_point.x() - start_point.x(),
            end_point.y() - start_point.y()
        )
        
        # Recalculate perpendicular vector
        main_length = math.sqrt(self._main_vector.x()**2 + self._main_vector.y()**2)
        if main_length > 0:
            self._perpendicular_vector = QPointF(
                -self._main_vector.y() / main_length,
                self._main_vector.x() / main_length
            )
        else:
            self._perpendicular_vector = QPointF(1, 0)
        
        # Flip perpendicular vector if drawing on opposite side
        if self._opposite_side:
            self._perpendicular_vector = QPointF(-self._perpendicular_vector.x(), -self._perpendicular_vector.y())
        
        # Recreate all components
        self._create_components()
    
    def setExtension(self, extension: float):
        """Update the extension lengths."""
        self._extension = extension
        self._create_components()
    
    def setExcessLength(self, excess_length: float):
        """Update the excess length."""
        self._excess_length = excess_length
        self._create_components()
    
    def setGapLength(self, gap_length: float):
        """Update the gap length."""
        self._gap_length = gap_length
        self._create_components()

    def setOrientation(self, orientation: DimensionLineOrientation):
        """Update the orientation."""
        self._orientation = orientation
        self._create_components()
    
    def setShowText(self, show_text: bool):
        """Set whether to show text."""
        self._show_text = show_text
        if show_text:
            self._create_text_item()
        else:
            # Remove text item if it exists
            if self._text_item and self._text_item.scene():
                self._text_item.scene().removeItem(self._text_item)
            self._text_item = None
        # Recreate arrow lines to update gap
        self._create_arrow_lines()
    
    def setTextFormatCallback(self, callback: Optional[Callable[[float], str]]):
        """Set the text formatting callback."""
        self._text_format_callback = callback
        if self._show_text:
            self._create_text_item()
    
    def setTextRotation(self, rotation: float):
        """Set the text rotation angle in degrees."""
        self._text_rotation = rotation
        if self._show_text:
            self._create_text_item()
    
    def setColor(self, color: QColor):
        """Set the color of the dimension line."""
        self._color = color
        self._pen.setColor(color)
        self._create_components()
    
    def setLineWidth(self, line_width: float):
        """Set the line width."""
        self._line_width = line_width
        self._pen.setWidthF(line_width)
        self._create_components()
    
    def setDashed(self, is_dashed: bool):
        """Set whether the lines should be dashed."""
        self._is_dashed = is_dashed
        if is_dashed:
            self._pen.setStyle(Qt.PenStyle.DashLine)
        else:
            self._pen.setStyle(Qt.PenStyle.SolidLine)
        self._create_components()
    
    def setOppositeSide(self, opposite_side: bool):
        """Set whether to draw on the opposite side of the dimension line."""
        self._opposite_side = opposite_side
        
        # Recalculate perpendicular vector with new side setting
        main_length = math.sqrt(self._main_vector.x()**2 + self._main_vector.y()**2)
        if main_length > 0:
            self._perpendicular_vector = QPointF(
                -self._main_vector.y() / main_length,
                self._main_vector.x() / main_length
            )
        else:
            self._perpendicular_vector = QPointF(1, 0)
        
        # Flip perpendicular vector if drawing on opposite side
        if self._opposite_side:
            self._perpendicular_vector = QPointF(-self._perpendicular_vector.x(), -self._perpendicular_vector.y())
        
        # Recreate all components to recalculate arrow perpendicular vector
        self._create_components()
    
    def setPen(self, pen: QPen):
        """Set the pen for the dimension line."""
        self._pen = pen
        # Update internal styling properties from pen
        self._color = pen.color()
        self._line_width = pen.widthF()
        self._is_dashed = pen.style() == Qt.PenStyle.DashLine
        # Recreate components with new pen
        self._create_components()
    
    def pen(self) -> QPen:
        """Get the current pen."""
        return self._pen
    
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the dimension line."""
        # Find the minimum and maximum coordinates
        points = [
            self._start_point,
            self._end_point,
            self._arrow_line_start,
            self._arrow_line_end,
            self._side_line1_start,
            self._side_line1_end,
            self._side_line2_start,
            self._side_line2_end,
            self._text_position
        ]
        
        min_x = min(p.x() for p in points)
        max_x = max(p.x() for p in points)
        min_y = min(p.y() for p in points)
        max_y = max(p.y() for p in points)
        
        # Add padding for line width and arrow heads
        padding = self._line_width * 2
        return QRectF(min_x - padding, min_y - padding, 
                     max_x - min_x + 2 * padding, max_y - min_y + 2 * padding)
    
    def shape(self) -> QPainterPath:
        """Return the shape of the dimension line for hit testing."""
        path = QPainterPath()
        
        # Add shapes from all child items
        for child in self.childItems():
            if child.isVisible():
                child_shape = child.shape()
                # Map the child's shape to this item's coordinate system
                child_transform = child.transform()
                child_pos = child.pos()
                
                # Apply child's transformation and position
                transformed_shape = child_transform.map(child_shape)
                final_shape = QPainterPath()
                final_shape.addPath(transformed_shape)
                final_shape.translate(child_pos.x(), child_pos.y())
                
                path.addPath(final_shape)
        
        # Create a stroked path for better hit testing
        pen = QPen(self._color, self._line_width)
        stroker = QPainterPathStroker()
        stroker.setWidth(self._line_width)
        return stroker.createStroke(path)
    
    def paint(self, painter: QPainter, option, widget=None):
        """Paint the dimension line and selection indication."""
        # The actual painting is done by the child items
        # But we need to draw selection indication if this item is selected
        
        if self.isSelected():
            # Draw selection indication
            from PySide6.QtCore import Qt
            from PySide6.QtGui import QPen, QColor
            from PySide6.QtWidgets import QApplication
            
            # Create selection pen using Qt's standard selection color
            standard_selection_color = QApplication.palette().highlight().color()
            selection_pen = QPen(standard_selection_color, 2.0)
            selection_pen.setStyle(Qt.PenStyle.DashLine)
            selection_pen.setCosmetic(True)
            
            # Draw selection rectangle around the bounding rect
            painter.setPen(selection_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.boundingRect())
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if clicking near endpoints
            click_pos = event.pos()
            start_dist = math.sqrt((click_pos.x() - self._start_point.x())**2 + (click_pos.y() - self._start_point.y())**2)
            end_dist = math.sqrt((click_pos.x() - self._end_point.x())**2 + (click_pos.y() - self._end_point.y())**2)
            
            # Set drag mode based on what was clicked
            if start_dist < 10:  # Within 10 pixels of start point
                self._drag_mode = "start_point"
                self._drag_start_pos = click_pos
            elif end_dist < 10:  # Within 10 pixels of end point
                self._drag_mode = "end_point"
                self._drag_start_pos = click_pos
            else:
                # Check if clicking on dimension line itself
                line_dist = self._distance_to_line(click_pos, self._arrow_line_start, self._arrow_line_end)
                if line_dist < 10:
                    self._drag_mode = "dimension_line"
                    self._drag_start_pos = click_pos
                else:
                    self._drag_mode = "none"
        else:
            self._drag_mode = "none"
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        if hasattr(self, '_drag_mode') and self._drag_mode != "none":
            current_pos = event.pos()
            delta = current_pos - self._drag_start_pos
            
            if self._drag_mode == "start_point":
                # Move start point
                new_start = self._start_point + delta
                self.setPoints(new_start, self._end_point)
                self._drag_start_pos = current_pos
            elif self._drag_mode == "end_point":
                # Move end point
                new_end = self._end_point + delta
                self.setPoints(self._start_point, new_end)
                self._drag_start_pos = current_pos
            elif self._drag_mode == "dimension_line":
                # Move entire dimension line
                new_start = self._start_point + delta
                new_end = self._end_point + delta
                self.setPoints(new_start, new_end)
                self._drag_start_pos = current_pos
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        self._drag_mode = "none"
        super().mouseReleaseEvent(event)
    
    def _distance_to_line(self, point: QPointF, line_start: QPointF, line_end: QPointF) -> float:
        """Calculate the distance from a point to a line segment."""
        # Vector from line start to end
        line_vec = QPointF(line_end.x() - line_start.x(), line_end.y() - line_start.y())
        line_length = math.sqrt(line_vec.x()**2 + line_vec.y()**2)
        
        if line_length == 0:
            return math.sqrt((point.x() - line_start.x())**2 + (point.y() - line_start.y())**2)
        
        # Vector from line start to point
        point_vec = QPointF(point.x() - line_start.x(), point.y() - line_start.y())
        
        # Project point onto line
        t = (point_vec.x() * line_vec.x() + point_vec.y() * line_vec.y()) / (line_length * line_length)
        t = max(0, min(1, t))  # Clamp to line segment
        
        # Closest point on line
        closest = QPointF(
            line_start.x() + t * line_vec.x(),
            line_start.y() + t * line_vec.y()
        )
        
        # Distance to closest point
        return math.sqrt((point.x() - closest.x())**2 + (point.y() - closest.y())**2) 