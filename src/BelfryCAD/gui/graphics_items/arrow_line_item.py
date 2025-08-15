"""
ArrowLineItem - A QGraphicsLineItem with optional arrowhead endcaps.

This class extends QGraphicsLineItem to add arrowheads at either or both ends
of the line. The arrowheads are proportionally sized based on the line width
and are drawn as filled polygons without outlines.
"""

import math
from typing import Optional, Tuple, TYPE_CHECKING, Union

from PySide6.QtCore import Qt, QPointF, QLineF, QRectF, QLine
from PySide6.QtGui import (
    QPen, QBrush, QColor, QPainter, QPolygonF,
    QPainterPath, QPainterPathStroker
)
from PySide6.QtWidgets import QGraphicsLineItem, QStyleOptionGraphicsItem, QWidget

if TYPE_CHECKING:
    from PySide6.QtWidgets import QGraphicsItem


class ArrowLineItem(QGraphicsLineItem):
    """
    A line item with optional arrowhead endcaps.
    
    The arrowheads are proportionally sized based on the line width:
    - Length: 4 * line_width along the line axis
    - Width: 3 * line_width perpendicular to the line
    """
    
    def __init__(
        self,
        line: QLineF,
        start_arrow: bool = False,
        end_arrow: bool = False,
        pen: Optional[QPen] = None,
        brush: Optional[QBrush] = None,
        parent: Optional['QGraphicsItem'] = None
    ):
        super().__init__(line, parent)
        
        # Arrow configuration
        self._start_arrow = start_arrow
        self._end_arrow = end_arrow
        
        # Arrow proportions (relative to line width) - MUST be set before setPen()
        self._arrow_length_factor = 8.0  # Length along line axis
        self._arrow_width_factor = 5.0   # Total width perpendicular to line
        
        # Recursion prevention flag
        self._updating_line = False
        
        # Set pen and brush
        if pen is not None:
            self.setPen(pen)
        if brush is not None:
            self._arrow_brush = brush
        else:
            # Default to same color as pen
            self._arrow_brush = QBrush(self.pen().color())        
    
    def setStartArrow(self, enabled: bool):
        """Enable or disable the start arrowhead."""
        if self._start_arrow != enabled:
            self._start_arrow = enabled
            self.update()
    
    def setEndArrow(self, enabled: bool):
        """Enable or disable the end arrowhead."""
        if self._end_arrow != enabled:
            self._end_arrow = enabled
            self.update()
    
    def setArrows(self, start_arrow: bool, end_arrow: bool):
        """Set both arrowheads at once."""
        if self._start_arrow != start_arrow or self._end_arrow != end_arrow:
            self._start_arrow = start_arrow
            self._end_arrow = end_arrow
            self.update()
    
    def setArrowBrush(self, brush: QBrush):
        """Set the brush for arrowhead fill."""
        self._arrow_brush = brush
        self.update()
    
    def setArrowColor(self, color: QColor):
        """Set the color for arrowhead fill."""
        self._arrow_brush = QBrush(color)
        self.update()
        
    def _create_arrowhead_polygon(self, tip_point: QPointF, direction: QPointF, is_start: bool) -> QPolygonF:
        """
        Create a polygon for an arrowhead.
        
        Args:
            tip_point: The tip point of the arrowhead
            direction: Normalized direction vector (from start to end)
            is_start: True if this is the start arrowhead (direction needs to be reversed)
        
        Returns:
            QPolygonF representing the arrowhead
        """
        line_width = self.pen().widthF()
        arrow_length = line_width * self._arrow_length_factor
        arrow_width = line_width * self._arrow_width_factor
        
        # For start arrowhead, reverse the direction
        if is_start:
            direction = -direction
        
        # Calculate the back point of the arrowhead
        back_point = tip_point - direction * arrow_length
        
        # Calculate perpendicular vector (90 degrees counterclockwise)
        perp_vector = QPointF(-direction.y(), direction.x())
        
        # Calculate the side points
        half_width = arrow_width / 2.0
        side1 = back_point + perp_vector * half_width
        side2 = back_point - perp_vector * half_width
        
        # Create the polygon: tip -> side1 -> back -> side2 -> tip
        polygon = QPolygonF()
        polygon.append(tip_point)
        polygon.append(side1)
        polygon.append(back_point)
        polygon.append(side2)
        polygon.append(tip_point)
        
        return polygon
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        """Paint the line and arrowheads."""
        # Draw the line from arrow tail to arrow tail (not tip to tip)
        line = self.line()
        start_point = line.p1()
        end_point = line.p2()
        line_vector = end_point - start_point
        line_length = math.hypot(line_vector.x(), line_vector.y())
        if line_length > 0:
            direction = line_vector * (1.0 / line_length)
            line_width = self.pen().widthF()
            arrow_length = line_width * self._arrow_length_factor if (self._start_arrow or self._end_arrow) else 0.0

            # Adjust start and end points to be at the arrow tails
            adj_start = start_point
            adj_end = end_point
            if self._start_arrow:
                adj_start = start_point + direction * arrow_length
            if self._end_arrow:
                adj_end = end_point - direction * arrow_length

            painter.save()
            painter.setPen(self.pen())
            painter.drawLine(adj_start, adj_end)
            painter.restore()
        
        # Then paint the arrowheads
        if self._start_arrow or self._end_arrow:
            # Save painter state
            painter.save()
            
            # Set up arrowhead painting (no pen, only brush)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self._arrow_brush)
            
            # Get the current line
            line = self.line()
            start_point = line.p1()
            end_point = line.p2()
            
            # Calculate line direction
            line_vector = end_point - start_point
            line_length = math.hypot(line_vector.x(), line_vector.y())
            
            if line_length > 0:
                # Normalize direction vector
                direction = line_vector * (1.0 / line_length)
                
                # Paint start arrowhead
                if self._start_arrow:
                    start_arrow = self._create_arrowhead_polygon(start_point, direction, True)
                    painter.drawPolygon(start_arrow)
                
                # Paint end arrowhead
                if self._end_arrow:
                    end_arrow = self._create_arrowhead_polygon(end_point, direction, False)
                    painter.drawPolygon(end_arrow)
            
            # Restore painter state
            painter.restore()
    
    def boundingRect(self) -> QRectF:
        """Calculate the bounding rectangle including arrowheads."""
        # Get the base line bounding rect
        base_rect = super().boundingRect()
        
        # Add space for arrowheads if they exist
        if self._start_arrow or self._end_arrow:
            line_width = self.pen().widthF()
            arrow_width = line_width * self._arrow_width_factor
            
            # Expand the bounding rect to accommodate arrowheads
            expansion = arrow_width / 2.0
            base_rect.adjust(-expansion, -expansion, expansion, expansion)
        
        return base_rect
    
    def shape(self):
        """Return the shape including arrowheads for hit testing."""        
        # Create a path for the line
        path = QPainterPath()
        line = self.line()
        path.moveTo(line.p1())
        path.lineTo(line.p2())
        
        # Use QPainterPathStroker to account for pen width
        stroker = QPainterPathStroker()
        
        # Create a solid pen for hit testing (ignore dashes)
        solid_pen = QPen(self.pen())
        solid_pen.setStyle(Qt.PenStyle.SolidLine)
        
        stroker.setWidth(solid_pen.widthF())
        stroker.setCapStyle(solid_pen.capStyle())
        stroker.setJoinStyle(solid_pen.joinStyle())
        
        # Create the stroked path (solid line for hit testing)
        path = stroker.createStroke(path)
        
        # Add arrowhead shapes if they exist
        if self._start_arrow or self._end_arrow:
            # Calculate line direction
            line_vector = line.p2() - line.p1()
            line_length = math.hypot(line_vector.x(), line_vector.y())
            
            if line_length > 0:
                direction = line_vector * (1.0 / line_length)
                
                # Add start arrowhead
                if self._start_arrow:
                    start_arrow = self._create_arrowhead_polygon(line.p1(), direction, True)
                    arrow_path = QPainterPath()
                    arrow_path.addPolygon(start_arrow)
                    path = path.united(arrow_path)
                
                # Add end arrowhead
                if self._end_arrow:
                    end_arrow = self._create_arrowhead_polygon(line.p2(), direction, False)
                    arrow_path = QPainterPath()
                    arrow_path.addPolygon(end_arrow)
                    path = path.united(arrow_path)
        
        return path
    
    def setPen(self, pen: Union[QPen, Qt.PenStyle, QColor]) -> None:
        """Override setPen to update arrowhead dimensions."""
        super().setPen(pen)
        self.update()
    
    def setLine(self, line: Union[QLineF, QLine]) -> None:  # type: ignore
        """Override setLine to update arrowhead positions."""
        super().setLine(line)
        self.update() 
    
    def setLineCoords(self, x1: float, y1: float, x2: float, y2: float) -> None:
        """Override setLine to update arrowhead positions."""
        super().setLine(x1, y1, x2, y2)
        self.update()
