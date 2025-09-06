"""
CadRectangleGraphicsItem - A custom graphics item for drawing rectangles with selection indication.
"""

from typing import Optional
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QPen, QBrush, QPainterPath, QPainterPathStroker, QPolygonF
from PySide6.QtWidgets import QGraphicsItem

from .cad_graphics_items_base import CadGraphicsItemBase


class CadRectangleGraphicsItem(CadGraphicsItemBase):
    """A custom graphics item for drawing rectangles with selection indication."""
    
    def __init__(self, corner_point: QPointF, width: float, height: float,
                 pen: Optional[QPen] = None, brush: Optional[QBrush] = None,
                 parent: Optional[QGraphicsItem] = None):
        super().__init__(parent=parent)
        
        # Store rectangle geometry
        self._corner_point = corner_point
        self._width = width
        self._height = height
        if pen is not None:
            self.setPen(pen)
        if brush is not None:
            self.setBrush(brush)
        else:
            self.setBrush(QBrush(Qt.BrushStyle.NoBrush))
    
    def _draw_shape_geometry(self, painter):
        """Draw the rectangle geometry using the current pen and brush."""
        painter.save()
        pen = self.pen()
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        pen.setCapStyle(Qt.PenCapStyle.SquareCap)
        painter.setPen(pen)
        painter.setBrush(self.brush())
        painter.drawPath(self._make_rectangle_path())
        painter.restore()
    
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the rectangle."""
        # Start with the rectangle's natural bounding rectangle
        base_rect = QRectF(
            self._corner_point.x(),
            self._corner_point.y(),
            self._width,
            self._height
        )
        
        # Expand for pen width and selection outline
        pen_width = self.pen().widthF()
        if self.isSelected():
            # Account for selection outline width
            try:
                scale = self.scene().views()[0].transform().m11()
                selection_extra = 3.0 / scale
                pen_width += selection_extra
            except (IndexError, AttributeError):
                # Fallback if view or scene not available
                pen_width += 3.0
        
        # Add half pen width as margin on all sides
        margin = pen_width / 2.0
        
        return base_rect.adjusted(-margin, -margin, margin, margin)
    
    def shape(self) -> QPainterPath:
        """Return the shape for hit detection."""
        # Use the rectangle path for hit detection
        return self._make_rectangle_path()
    
    def _make_rectangle_path(self) -> QPainterPath:
        """Create a QPainterPath for the rectangle."""
        path = QPainterPath()
        rect = QRectF(
            self._corner_point.x(),
            self._corner_point.y(),
            self._width,
            self._height
        )
        path.addRect(rect)
        return path
    
    def contains(self, point) -> bool:
        """Check if the rectangle contains the given point."""
        return self._make_rectangle_path().contains(point)
    
    def update_geometry(self, corner_point: QPointF, width: float, height: float):
        """Update the rectangle geometry."""
        self.prepareGeometryChange()
        self._corner_point = corner_point
        self._width = width
        self._height = height
        self.update()
    
    @property
    def corner_point(self) -> QPointF:
        """Get the corner point."""
        return self._corner_point
    
    @property
    def width(self) -> float:
        """Get the width."""
        return self._width
    
    @property
    def height(self) -> float:
        """Get the height."""
        return self._height
    
    @property
    def center_point(self) -> QPointF:
        """Get the center point."""
        return QPointF(
            self._corner_point.x() + self._width / 2,
            self._corner_point.y() + self._height / 2
        )
    
    @property
    def opposite_corner(self) -> QPointF:
        """Get the opposite corner point."""
        return QPointF(
            self._corner_point.x() + self._width,
            self._corner_point.y() + self._height
        ) 