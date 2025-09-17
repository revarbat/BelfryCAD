"""
CadPolylineGraphicsItem - A custom graphics item for drawing polylines with selection indication.
"""

from typing import Optional, List
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QPen, QBrush, QPainterPath, QPolygonF, QPainterPathStroker
from PySide6.QtWidgets import QGraphicsItem

from .cad_graphics_items_base import CadGraphicsItemBase


class CadPolylineGraphicsItem(CadGraphicsItemBase):
    """A custom graphics item for drawing polylines with selection indication."""
    
    def __init__(self, points: List[QPointF],
                 pen: Optional[QPen] = None, parent: Optional[QGraphicsItem] = None):
        super().__init__(parent=parent)
        
        # Store polyline geometry
        self._points = points.copy() if points else []
        if pen is not None:
            self.setPen(pen)
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))
    
    def _draw_shape_geometry(self, painter):
        """Draw the polyline geometry using the current pen."""
        if len(self._points) >= 2:
            painter.save()
            painter.setPen(self.pen())
            painter.drawPolyline(QPolygonF(self._points))
            painter.restore()
    
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the polyline."""
        if not self._points:
            return QRectF()
        
        # Find the bounds of all points
        x_coords = [p.x() for p in self._points]
        y_coords = [p.y() for p in self._points]
        
        left = min(x_coords)
        right = max(x_coords)
        top = min(y_coords)
        bottom = max(y_coords)
        
        # Create base rectangle
        base_rect = QRectF(left, top, right - left, bottom - top)
        
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
        path = QPainterPath()
        
        if len(self._points) < 2:
            return path
        
        # Create a thick path around the polyline for easier clicking
        scale = self.scene().views()[0].transform().m11()
        hit_width = max(self.pen().widthF(), 3.0 / scale)  # At least 3 units for easy clicking
        
        # Build the stroke path for the polyline
        path.moveTo(self._points[0])
        for point in self._points[1:]:
            path.lineTo(point)
        
        # Create a stroked version of the path for hit testing
        stroker = QPainterPathStroker()
        stroker.setWidth(hit_width)
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        path = stroker.createStroke(path)
        return path
    
    # Property getters and setters
    @property
    def points(self) -> List[QPointF]:
        """Get the list of points that make up the polyline."""
        return self._points.copy()  # Return a copy to prevent external modification
    
    def setPoints(self, points: List[QPointF]):
        """Set the points that make up the polyline."""
        self.prepareGeometryChange()
        self._points = points if points else []
        self.update()
    
    def addPoint(self, point: QPointF):
        """Add a point to the end of the polyline."""
        self.prepareGeometryChange()
        self._points.append(point)
        self.update()
    
    def insertPoint(self, index: int, point: QPointF):
        """Insert a point at the specified index."""
        self.prepareGeometryChange()
        self._points.insert(index, point)
        self.update()
    
    def removePoint(self, index: int):
        """Remove the point at the specified index."""
        if 0 <= index < len(self._points):
            self.prepareGeometryChange()
            self._points.pop(index)
            self.update()
    
    def movePoint(self, index: int, new_position: QPointF):
        """Move the point at the specified index to a new position."""
        if 0 <= index < len(self._points):
            self.prepareGeometryChange()
            self._points[index] = new_position
            self.update()
    
    def getPointCount(self) -> int:
        """Get the number of points in the polyline."""
        return len(self._points)
