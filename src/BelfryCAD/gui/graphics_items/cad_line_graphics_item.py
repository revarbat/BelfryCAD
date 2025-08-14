"""
CadLineGraphicsItem - A custom graphics item for drawing lines with selection indication.
"""

from typing import Optional
from PySide6.QtCore import QPointF, QRectF, QLineF, Qt
from PySide6.QtGui import QPen, QBrush, QPainterPath, QPainterPathStroker
from PySide6.QtWidgets import QGraphicsItem

from .cad_graphics_items_base import CadGraphicsItemBase


class CadLineGraphicsItem(CadGraphicsItemBase):
    """A custom graphics item for drawing lines with selection indication."""
    
    def __init__(self, start_point: QPointF, end_point: QPointF, 
                 pen: Optional[QPen] = None, parent: Optional[QGraphicsItem] = None):
        super().__init__(parent=parent)
        
        # Store line geometry
        self._start_point = start_point
        self._end_point = end_point
        if pen is not None:
            self.setPen(pen)
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))
    
    def _draw_shape_geometry(self, painter):
        """Draw the line geometry using the current pen."""
        painter.save()
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawLine(self._start_point, self._end_point)
        painter.restore()
    
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the line."""
        # Create a rectangle that encompasses both endpoints
        x1, y1 = self._start_point.x(), self._start_point.y()
        x2, y2 = self._end_point.x(), self._end_point.y()
        
        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        # Expand the bounding rect to account for pen width and selection outline
        pen_width = self.pen().widthF()
        if self.isSelected():
            # Account for selection outline width
            scale = self.scene().views()[0].transform().m11()
            selection_extra = 4.0 / scale
            pen_width += selection_extra
        
        # Add half pen width as margin on all sides
        margin = pen_width / 2.0
        
        return QRectF(left - margin, top - margin, 
                      width + 2 * margin, height + 2 * margin)
    
    def shape(self) -> QPainterPath:
        """Return the shape for hit testing."""
        # Create a path along the line with some thickness for easier clicking
        path = QPainterPath()
        
        # Use a minimum hit area width
        scale = self.scene().views()[0].transform().m11()
        hit_width = max(self.pen().widthF(), 3.0 / scale)  # At least 3 units for easy clicking
        
        # Create a thick line path for hit testing
        line = QLineF(self._start_point, self._end_point)
        if line.length() <= 0:
            path.addEllipse(self.boundingRect())
        else:
            # Create rectangular path around the line
            path.moveTo(self._start_point.x(), self._start_point.y())
            path.lineTo(self._end_point.x(), self._end_point.y())

            stroker = QPainterPathStroker()
            stroker.setWidth(hit_width)
            stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
            stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            path = stroker.createStroke(path)

        return path
    
    # Property getters and setters
    @property
    def start_point(self) -> QPointF:
        """Get the start point of the line."""
        return self._start_point
    
    @property
    def end_point(self) -> QPointF:
        """Get the end point of the line."""
        return self._end_point
    
    def setStartPoint(self, point: QPointF):
        """Set the start point of the line."""
        self.prepareGeometryChange()
        self._start_point = point
        self.update()
    
    def setEndPoint(self, point: QPointF):
        """Set the end point of the line."""
        self.prepareGeometryChange()
        self._end_point = point
        self.update()
    
    def setLine(self, start_point: QPointF, end_point: QPointF):
        """Set both endpoints of the line."""
        self.prepareGeometryChange()
        self._start_point = start_point
        self._end_point = end_point
        self.update() 