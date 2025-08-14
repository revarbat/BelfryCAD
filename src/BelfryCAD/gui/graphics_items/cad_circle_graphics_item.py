"""
CadCircleGraphicsItem - A custom graphics item for drawing circles with selection indication.
"""

from typing import Optional
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen, QBrush, QPainterPath, QPainterPathStroker
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt

from .cad_graphics_items_base import CadGraphicsItemBase


class CadCircleGraphicsItem(CadGraphicsItemBase):
    """A custom graphics item for drawing circles with selection indication."""
    
    def __init__(self, center_point: QPointF, radius: float,
                 pen: Optional[QPen] = None, brush: Optional[QBrush] = None,
                 parent: Optional[QGraphicsItem] = None):
        super().__init__(parent=parent)
        
        # Store circle geometry
        self._center_point = center_point
        self._radius = radius
        if pen is not None:
            self.setPen(pen)
        if brush is not None:
            self.setBrush(brush)
    
    def _draw_shape_geometry(self, painter):
        """Draw the circle geometry using the current pen and brush."""
        painter.save()
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawPath(self._make_circle_path())
        painter.restore()
    
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the circle."""
        # Start with the circle's natural bounding rectangle
        base_rect = QRectF(
            self._center_point.x() - self._radius,
            self._center_point.y() - self._radius,
            self._radius * 2,
            self._radius * 2
        )
        
        # Expand for pen width and selection outline
        pen_width = self.pen().widthF()
        if self.isSelected():
            # Account for selection outline width
            scale = self.scene().views()[0].transform().m11()
            selection_extra = 3.0 / scale
            pen_width += selection_extra
        
        # Add half pen width as margin on all sides
        margin = pen_width / 2.0
        
        return base_rect.adjusted(-margin, -margin, margin, margin)
    
    def _make_circle_path(self) -> QPainterPath:
        """Make a circle path."""
        path = QPainterPath()
        path.addEllipse(
            self._center_point.x() - self._radius,
            self._center_point.y() - self._radius,
            self._radius * 2,
            self._radius * 2
        )
        return path
    
    def shape(self) -> QPainterPath:
        """Return the shape for hit testing."""
        
        # Use the circle outline for hit testing, with some thickness for easier clicking
        scale = self.scene().views()[0].transform().m11()
        width = self.pen().widthF()
        hit_width = max(width, 3.0/scale)  # At least 3 pixels for easy clicking
        
        path = self._make_circle_path()
        if self.brush().style() == Qt.BrushStyle.NoBrush:
            stroker = QPainterPathStroker()
            stroker.setWidth(hit_width)
            stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
            stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            path = stroker.createStroke(path)
        
        return path
    
    # Property getters and setters
    @property
    def center_point(self) -> QPointF:
        """Get the center point of the circle."""
        return self._center_point
    
    @property
    def radius(self) -> float:
        """Get the radius of the circle."""
        return self._radius
    
    def setCenterPoint(self, point: QPointF):
        """Set the center point of the circle."""
        self.prepareGeometryChange()
        self._center_point = point
        self.update()
    
    def setRadius(self, radius: float):
        """Set the radius of the circle."""
        self.prepareGeometryChange()
        self._radius = max(0, radius)  # Ensure non-negative radius
        self.update()
    
    def setCircle(self, center_point: QPointF, radius: float):
        """Set both center and radius of the circle."""
        self.prepareGeometryChange()
        self._center_point = center_point
        self._radius = max(0, radius)
        self.update() 