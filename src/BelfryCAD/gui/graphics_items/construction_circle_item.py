"""
ConstructionCircleItem - A QGraphicsEllipseItem for drawing construction circles.

This class provides a specialized ellipse item for construction circles with
configurable dash patterns and styling.
"""

from enum import Enum
from typing import Optional
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem
from PySide6.QtCore import QRectF, Qt, QPointF
from PySide6.QtGui import QPen, QColor, QPainter, QPainterPath


class DashPattern(Enum):
    """Enumeration for different dash patterns."""
    SOLID = "solid"
    DASHED = "dashed"
    CENTERLINE = "centerline"


class ConstructionCircleItem(QGraphicsEllipseItem):
    """A QGraphicsEllipseItem for drawing construction circles with configurable styling."""
    
    def __init__(
            self,
            center: QPointF,
            radius: float,
            dash_pattern: DashPattern = DashPattern.DASHED,
            line_width: float = 1.0,
            parent: Optional[QGraphicsEllipseItem] = None
    ):
        rect = QRectF(
            center.x() - radius,
            center.y() - radius,
            radius * 2, radius * 2
        )
        super().__init__(rect, parent)
        
        # Set up the circle with construction styling
        self._dash_pattern = dash_pattern
        self._construction_color = QColor(0x7f, 0x7f, 0x7f)  # #7f7f7f
        self._line_width = line_width
        
        # Configure the circle item
        self.setLineWidth(self._line_width)
        self._update_pen()
        
        # Set high Z value to appear above other items
        self.setZValue(1000)
        
        # Make construction circles unselectable and unmovable
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, False)
        
        # Ensure the item is visible
        self.setVisible(True)
    
    def setDashPattern(self, pattern: DashPattern):
        """Set the dash pattern for the construction circle."""
        self._dash_pattern = pattern
        self._update_pen()
    
    def setLineWidth(self, width: float):
        """Set the line width."""
        self._line_width = width
        self._update_pen()
    
    def setConstructionColor(self, color: QColor):
        """Set the construction circle color."""
        self._construction_color = color
        self._update_pen()
    
    def _update_pen(self):
        """Update the pen based on current settings."""
        pen = QPen(self._construction_color, self._line_width)
        
        if self._dash_pattern == DashPattern.SOLID:
            pen.setStyle(Qt.PenStyle.SolidLine)
        elif self._dash_pattern == DashPattern.DASHED:
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setDashPattern([5.0, 5.0])
        elif self._dash_pattern == DashPattern.CENTERLINE:
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setDashPattern([8.0, 5.0, 5.0, 5.0, 7.0])
        
        self.setPen(pen)
        # No brush for construction circles (outline only)
        self.setBrush(QColor(0, 0, 0, 0))  # Transparent
    
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
