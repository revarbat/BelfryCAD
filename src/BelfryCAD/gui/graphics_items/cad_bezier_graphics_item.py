"""
CadBezierGraphicsItem - A custom graphics item for drawing bezier curves with selection indication.
"""

from typing import Optional
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen, QBrush, QPainterPath, QPainterPathStroker
from PySide6.QtWidgets import QGraphicsItem

from .cad_graphics_items_base import CadGraphicsItemBase


class CadBezierGraphicsItem(CadGraphicsItemBase):
    """A custom graphics item for drawing bezier curves with selection indication."""
    
    def __init__(self, bezier_path: QPainterPath,
                 pen: Optional[QPen] = None, parent: Optional[QGraphicsItem] = None):
        super().__init__(parent=parent)
        
        # Store bezier curve geometry
        self._bezier_path = bezier_path if bezier_path else QPainterPath()
        if pen is not None:
            self.setPen(pen)
    
    def _draw_shape_geometry(self, painter):
        """Draw the bezier curve geometry using the current pen."""
        if not self._bezier_path.isEmpty():
            painter.save()
            painter.setPen(self.pen())
            painter.setBrush(self.brush())
            painter.drawPath(self._bezier_path)
            painter.restore()
    
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the bezier curve."""
        if self._bezier_path.isEmpty():
            return QRectF()
        
        # Start with the path's natural bounding rectangle
        base_rect = self._bezier_path.boundingRect()
        
        # Expand for pen width and selection outline
        pen_width = self.pen().widthF()
        if self.isSelected():
            # Account for selection outline width
            scale = self.scene().views()[0].transform().m11()
            selection_extra = 4.0 / scale
            pen_width += selection_extra
        
        # Add half pen width as margin on all sides
        margin = pen_width / 2.0
        
        return base_rect.adjusted(-margin, -margin, margin, margin)
    
    def shape(self) -> QPainterPath:
        """Return the shape for hit testing."""
        if self._bezier_path.isEmpty():
            return QPainterPath()
        
        # Create a thick path around the bezier curve for easier clicking
        scale = self.scene().views()[0].transform().m11()
        hit_width = max(self.pen().widthF(), 3.0 / scale)  # At least 3 units for easy clicking
        
        # Create a stroked version of the path for hit testing
        stroker = QPainterPathStroker()
        stroker.setWidth(hit_width)
        stroker.setCapStyle(self.pen().capStyle())
        stroker.setJoinStyle(self.pen().joinStyle())
        
        return stroker.createStroke(self._bezier_path)
    
    # Property getters and setters
    @property
    def bezier_path(self) -> QPainterPath:
        """Get the bezier path."""
        return QPainterPath(self._bezier_path)  # Return a copy
    
    def setBezierPath(self, path: QPainterPath):
        """Set the bezier path."""
        self.prepareGeometryChange()
        self._bezier_path = QPainterPath(path) if path else QPainterPath()
        self.update()
    
    def setFromControlPoints(self, start: QPointF, control1: QPointF, 
                           control2: QPointF, end: QPointF):
        """Set the bezier curve from four control points (cubic bezier)."""
        self.prepareGeometryChange()
        self._bezier_path = QPainterPath()
        self._bezier_path.moveTo(start)
        self._bezier_path.cubicTo(control1, control2, end)
        self.update()
    
    def setFromQuadraticControlPoints(self, start: QPointF, control: QPointF, end: QPointF):
        """Set the bezier curve from three control points (quadratic bezier)."""
        self.prepareGeometryChange()
        self._bezier_path = QPainterPath()
        self._bezier_path.moveTo(start)
        self._bezier_path.quadTo(control, end)
        self.update()
    
    def isEmpty(self) -> bool:
        """Check if the bezier path is empty."""
        return self._bezier_path.isEmpty()
    
    def getStartPoint(self) -> QPointF:
        """Get the start point of the bezier curve."""
        if not self._bezier_path.isEmpty():
            return self._bezier_path.pointAtPercent(0.0)
        return QPointF()
    
    def getEndPoint(self) -> QPointF:
        """Get the end point of the bezier curve."""
        if not self._bezier_path.isEmpty():
            return self._bezier_path.pointAtPercent(1.0)
        return QPointF() 