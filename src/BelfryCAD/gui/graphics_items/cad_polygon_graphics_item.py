"""
CadPolygonGraphicsItem - A custom graphics item for drawing polygons with selection indication.
"""

from typing import Optional, List
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QPen, QBrush, QPainterPath, QPolygonF, QPainterPathStroker
from PySide6.QtWidgets import QGraphicsItem

from .cad_graphics_items_base import CadGraphicsItemBase


class CadPolygonGraphicsItem(CadGraphicsItemBase):
    """A custom graphics item for drawing polygons with selection indication."""
    
    def __init__(self, points: List[QPointF],
                 pen: Optional[QPen] = None, brush: Optional[QBrush] = None,
                 parent: Optional[QGraphicsItem] = None):
        super().__init__(parent=parent)
        
        # Store polygon geometry
        self._points = points if points else []
        if pen is not None:
            self.setPen(pen)
        if brush is not None:
            self.setBrush(brush)
    
    def _draw_shape_geometry(self, painter):
        """Draw the polygon geometry using the current pen and brush."""
        if len(self._points) >= 3:
            painter.save()
            painter.setPen(self.pen())
            painter.setBrush(self.brush())
            painter.drawPolygon(QPolygonF(self._points))
            painter.restore()
    
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the polygon."""
        if len(self._points) < 3:
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
            selection_extra = 3.0 / scale
            pen_width += selection_extra
        
        # Add half pen width as margin on all sides
        margin = pen_width / 2.0
        
        return base_rect.adjusted(-margin, -margin, margin, margin)
    
    def shape(self) -> QPainterPath:
        """Return the shape for hit testing."""
        path = QPainterPath()
        
        if len(self._points) < 3:
            return path
        
        if self.brush().style() != Qt.BrushStyle.NoBrush:
            # If polygon is filled, the entire polygon area is clickable
            polygon = QPolygonF(self._points)
            path.addPolygon(polygon)
        
        else:
            # If polygon is just an outline, create a thick outline for clicking
            scale = self.scene().views()[0].transform().m11()
            hit_width = max(self.pen().widthF(), 3.0 / scale)  # At least 3 units for easy clicking
            
            path.moveTo(self._points[0])
            for point in self._points[1:]:
                path.lineTo(point)
            path.closeSubpath()
            
            # Create a stroked version of the polygon outline for hit testing
            stroker = QPainterPathStroker()
            stroker.setWidth(hit_width)
            stroker.setCapStyle(Qt.PenCapStyle.SquareCap)
            stroker.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
            path = stroker.createStroke(path)
        
        return path
    
    # Property getters and setters
    @property
    def points(self) -> List[QPointF]:
        """Get the list of points that make up the polygon."""
        return self._points.copy()  # Return a copy to prevent external modification
    
    def setPoints(self, points: List[QPointF]):
        """Set the points that make up the polygon."""
        self.prepareGeometryChange()
        self._points = points if points else []
        self.update()
    
    def addPoint(self, point: QPointF):
        """Add a point to the polygon."""
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
        """Get the number of points in the polygon."""
        return len(self._points)
    
    def isClosed(self) -> bool:
        """Check if the polygon is closed (has at least 3 points)."""
        return len(self._points) >= 3
    
    def getArea(self) -> float:
        """Calculate the area of the polygon using the shoelace formula."""
        if len(self._points) < 3:
            return 0.0
        
        area = 0.0
        n = len(self._points)
        
        for i in range(n):
            j = (i + 1) % n
            area += self._points[i].x() * self._points[j].y()
            area -= self._points[j].x() * self._points[i].y()
        
        return abs(area) / 2.0
    
    def getCentroid(self) -> QPointF:
        """Calculate the centroid of the polygon."""
        if not self._points:
            return QPointF()
        
        if len(self._points) == 1:
            return self._points[0]
        
        # Simple centroid calculation (average of all vertices)
        x_sum = sum(p.x() for p in self._points)
        y_sum = sum(p.y() for p in self._points)
        
        return QPointF(x_sum / len(self._points), y_sum / len(self._points)) 