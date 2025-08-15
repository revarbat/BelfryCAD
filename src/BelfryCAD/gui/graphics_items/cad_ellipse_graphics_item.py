"""
CadEllipseGraphicsItem - A custom graphics item for drawing ellipses with selection indication.
"""

from typing import Optional
from PySide6.QtCore import QPointF, QRectF, Qt, QLineF
from PySide6.QtGui import QPen, QBrush, QPainterPath, QPainterPathStroker
from PySide6.QtWidgets import QGraphicsItem

from .cad_graphics_items_base import CadGraphicsItemBase


class CadEllipseGraphicsItem(CadGraphicsItemBase):
    """A custom graphics item for drawing ellipses with selection indication."""
    
    def __init__(self, bounding_rect: QRectF,
                 pen: Optional[QPen] = None, brush: Optional[QBrush] = None,
                 parent: Optional[QGraphicsItem] = None):
        super().__init__(parent=parent)
        
        # Store ellipse geometry
        self._bounding_rect = bounding_rect
        
        if pen is not None:
            self.setPen(pen)
        if brush is not None:
            self.setBrush(brush)
    
    def _draw_shape_geometry(self, painter):
        """Draw the ellipse geometry using the current pen and brush."""
        painter.save()
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawEllipse(self._bounding_rect)
        painter.restore()
    
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the ellipse."""
        # Start with the ellipse's natural bounding rectangle
        base_rect = self._bounding_rect
        
        # Expand for pen width and selection outline
        pen_width = self.pen().widthF()

        # Account for selection outline width
        scale = self.scene().views()[0].transform().m11()
        selection_extra = 4.0 / scale
        pen_width += selection_extra
        
        # Add half pen width as margin on all sides
        margin = pen_width / 2.0
        
        return base_rect.adjusted(-margin, -margin, margin, margin)
    
    def shape(self) -> QPainterPath:
        """Return the shape for hit testing."""
        path = QPainterPath()
        path.addEllipse(self._bounding_rect)
        
        if self.brush().style() == Qt.BrushStyle.NoBrush:
            # If ellipse is just an outline, create a thick outline for clicking
            scale = self.scene().views()[0].transform().m11()
            hit_width = max(self.pen().widthF(), 3.0 / scale)  # At least 3 units for easy clicking
            
            stroker = QPainterPathStroker()
            stroker.setWidth(hit_width)
            stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
            stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            path = stroker.createStroke(path)
        
        return path
    
    # Property getters and setters
    @property
    def ellipse_rect(self) -> QRectF:
        """Get the bounding rectangle of the ellipse."""
        return self._bounding_rect
    
    @property
    def center_point(self) -> QPointF:
        """Get the center point of the ellipse."""
        return self._bounding_rect.center()
    
    @property
    def width(self) -> float:
        """Get the width of the ellipse."""
        return self._bounding_rect.width()
    
    @property
    def height(self) -> float:
        """Get the height of the ellipse."""
        return self._bounding_rect.height()
    
    def setEllipseRect(self, rect: QRectF):
        """Set the bounding rectangle of the ellipse."""
        self.prepareGeometryChange()
        self._bounding_rect = rect
        self.update()
    
    def setCenterAndSize(self, center: QPointF, width: float, height: float):
        """Set the ellipse by center point and dimensions."""
        self.prepareGeometryChange()
        self._bounding_rect = QRectF(
            center.x() - width / 2,
            center.y() - height / 2,
            width,
            height
        )
        self.update()
    
    def setFromTwoPoints(self, point1: QPointF, point2: QPointF):
        """Set the ellipse from two opposite corner points."""
        self.prepareGeometryChange()
        self._bounding_rect = QRectF(point1, point2).normalized()
        self.update() 