"""
ConstructionCrossItem - A QGraphicsItem for drawing construction crosshairs.

This class provides a specialized graphics item for drawing construction crosshairs
with centerline dashed patterns to mark circle centers.
"""
import math
from enum import Enum
from typing import Optional
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import QRectF, Qt, QPointF
from PySide6.QtGui import QPen, QColor, QPainter, QPainterPath


class DashPattern(Enum):
    """Enumeration for different dash patterns."""
    SOLID = "solid"
    DASHED = "dashed"
    CENTERLINE = "centerline"


class ConstructionCrossItem(QGraphicsItem):
    """A QGraphicsItem for drawing construction crosshairs with centerline patterns."""
    
    def __init__(
            self,
            center: QPointF,
            size: float = 20.0,
            dash_pattern: DashPattern = DashPattern.CENTERLINE,
            line_width: float = 1.0,
            parent: Optional[QGraphicsItem] = None
    ):
        super().__init__(parent)
        
        # Set up the crosshair with construction styling
        self._center = center
        self._size = size
        self._dash_pattern = dash_pattern
        self._construction_color = QColor(0x7f, 0x7f, 0x7f)  # #7f7f7f
        self._line_width = line_width
        
        # Configure the crosshair item
        self._update_pen()
        
        # Set high Z value to appear above other items
        self.setZValue(1000)
        
        # Make construction crosshairs unselectable and unmovable
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, False)
        
        # Ensure the item is visible
        self.setVisible(True)
    
    def setCenter(self, center: QPointF):
        """Set the center point of the crosshair."""
        self._center = center
        self.update()
    
    def setSize(self, size: float):
        """Set the size of the crosshair."""
        self._size = size
        self.update()
    
    def setDashPattern(self, pattern: DashPattern):
        """Set the dash pattern for the construction crosshair."""
        self._dash_pattern = pattern
        self._update_pen()
        self.update()
    
    def setLineWidth(self, width: float):
        """Set the line width."""
        self._line_width = width
        self._update_pen()
        self.update()
    
    def setConstructionColor(self, color: QColor):
        """Set the construction crosshair color."""
        self._construction_color = color
        self._update_pen()
        self.update()
    
    def _update_pen(self):
        """Update the pen based on current settings."""
        self._pen = QPen(self._construction_color, self._line_width)
        
        if self._dash_pattern == DashPattern.SOLID:
            self._pen.setStyle(Qt.PenStyle.SolidLine)
        elif self._dash_pattern == DashPattern.DASHED:
            self._pen.setStyle(Qt.PenStyle.DashLine)
            self._pen.setDashPattern([5.0, 5.0])
        elif self._dash_pattern == DashPattern.CENTERLINE:
            self._pen.setStyle(Qt.PenStyle.DashLine)
            self._pen.setDashPattern([8.0, 5.0, 5.0, 5.0, 7.0])
    
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the crosshair."""
        half_size = self._size / 2
        return QRectF(
            self._center.x() - half_size,
            self._center.y() - half_size,
            self._size,
            self._size
        )
    
    def shape(self) -> QPainterPath:
        """Return the shape of the crosshair for hit testing."""
        path = QPainterPath()
        half_size = self._size / 2
        
        # Horizontal line
        path.moveTo(self._center.x() - half_size, self._center.y())
        path.lineTo(self._center.x() + half_size, self._center.y())
        
        # Vertical line
        path.moveTo(self._center.x(), self._center.y() - half_size)
        path.lineTo(self._center.x(), self._center.y() + half_size)
        
        return path
    
    def paint(self, painter: QPainter, option, widget=None):
        """Paint the construction crosshair."""
        painter.save()
        painter.setPen(self._pen)
        
        half_size = self._size / 2
        
        # Draw horizontal line
        center = self._center
        for a in [0, 90, 180, 270]:
            painter.drawLine(
                center, center + QPointF(
                    half_size * math.cos(math.radians(a)),
                    half_size * math.sin(math.radians(a))),
            )
        painter.restore()
    
    def mousePressEvent(self, event):
        """Ignore mouse press events."""
        event.ignore()
    
    def mouseMoveEvent(self, event):
        """Ignore mouse move events."""
        event.ignore()
    
    def mouseReleaseEvent(self, event):
        """Ignore mouse release events."""
        event.ignore()
    
    def mouseDoubleClickEvent(self, event):
        """Ignore mouse double click events."""
        event.ignore()
    
    def contextMenuEvent(self, event):
        """Ignore context menu events."""
        event.ignore()
    
    def keyPressEvent(self, event):
        """Ignore key press events."""
        event.ignore()
    
    def keyReleaseEvent(self, event):
        """Ignore key release events."""
        event.ignore()
    
    def focusInEvent(self, event):
        """Ignore focus in events."""
        event.ignore()
    
    def focusOutEvent(self, event):
        """Ignore focus out events."""
        event.ignore()
