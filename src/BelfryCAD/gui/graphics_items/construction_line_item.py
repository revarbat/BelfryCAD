"""
ConstructionLineItem - A QGraphicsLineItem for drawing construction lines.

This class provides a specialized line item for construction lines with
configurable dash patterns and optional arrow tips.
"""

from enum import Enum
from typing import Optional, List
from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsItem
from PySide6.QtCore import QLineF, QPointF, Qt, QRectF
from PySide6.QtGui import QPen, QColor, QPainter, QPainterPath, QBrush, QPainterPathStroker
import math
from PySide6.QtGui import QTransform


class DashPattern(Enum):
    """Enumeration for different dash patterns."""
    SOLID = "solid"
    DASHED = "dashed"
    CENTERLINE = "centerline"


class ArrowTip(Enum):
    """Enumeration for arrow tip positions."""
    NONE = "none"
    START = "start"
    END = "end"
    BOTH = "both"


class ConstructionLineItem(QGraphicsLineItem):
    """A QGraphicsLineItem for drawing construction lines with configurable styling."""
    arrow_length = 10.0
    arrow_width = 5.0
    
    def __init__(
            self,
            line: QLineF,
            dash_pattern: DashPattern = DashPattern.DASHED,
            arrow_tips: ArrowTip = ArrowTip.NONE,
            line_width: Optional[float] = None,
            parent: Optional[QGraphicsLineItem] = None
    ):
        super().__init__(line, parent)
        
        # Set up the line with construction styling
        self._dash_pattern = dash_pattern
        self._arrow_tips = arrow_tips
        self._construction_color = QColor(0x7f, 0x7f, 0x7f)  # #7f7f7f
        self._line_width = line_width

        # Configure the line item
        self._update_pen()
        
        # Set high Z value to appear above other items
        self.setZValue(1000)
        
        # Make construction lines unselectable and unmovable
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, False)
        
        # Ensure the item is visible
        self.setVisible(True)
    
    def setDashPattern(self, pattern: DashPattern):
        """Set the dash pattern for the construction line."""
        self._dash_pattern = pattern
        self._update_pen()
    
    def setArrowTips(self, arrow_tips: ArrowTip):
        """Set the arrow tip configuration."""
        self._arrow_tips = arrow_tips
        self.update()  # Trigger repaint for arrow tips
    
    def setLineWidth(self, width: float):
        """Set the line width."""
        self._line_width = width
        self._update_pen()
    
    def setConstructionColor(self, color: QColor):
        """Set the construction line color."""
        self._construction_color = color
        self._update_pen()
    
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle including arrow tips."""

        # If there are no arrow tips, just return the base rect
        width = self._line_width
        if width is None:
            width = 1.0
        if self._arrow_tips != ArrowTip.NONE:
            width *= self.arrow_width

        # Create a rect that includes the arrows
        rect = super().boundingRect()
        
        # Add some padding to ensure nothing is clipped
        rect.adjust(-width/2, -width/2, width/2, width/2)
        
        return rect

    def shape(self) -> QPainterPath:
        """Return the shape for hit testing, including arrow tips."""
        width = self._line_width
        if width is None:
            width = 1.0
        if self._arrow_tips != ArrowTip.NONE:
            width *= self.arrow_width

        path = QPainterPath()
        path.moveTo(self.line().p1())
        path.lineTo(self.line().p2())

        # Create a stroked path with the line width for better selection
        stroker = QPainterPathStroker()
        stroker.setWidth(width)
        return stroker.createStroke(path)

    def paint(self, painter: QPainter, option, widget=None):
        """Paint the construction line with optional arrow tips."""
        painter.save()

        # Set up the pen for the line
        painter.setPen(self.pen())
        
        # Paint the line and arrows
        """Paint arrow tips at the specified ends of the line."""
        line = self.line()
        start_point = line.p1()
        end_point = line.p2()
        delta = end_point - start_point
        length = math.hypot(delta.x(), delta.y())
        vector = delta * (1.0 / length)
        
        # Calculate the actual line endpoints (where the line should start/end)
        # based on which arrows are present
        actual_start = start_point
        actual_end = end_point
        line_width = self._line_width
        if line_width is None:
            line_width = 1.0
        offset = vector * (self.arrow_length * line_width)
        
        if self._arrow_tips in [ArrowTip.START, ArrowTip.BOTH]:
            actual_start = start_point + offset
        if self._arrow_tips in [ArrowTip.END, ArrowTip.BOTH]:
            actual_end = end_point - offset
        
        # Paint the line between the actual start and end points
        painter.drawLine(actual_start, actual_end)

        # Paint start arrow if needed
        if self._arrow_tips in [ArrowTip.START, ArrowTip.BOTH]:
            self._paint_arrowhead(painter, start_point, -vector, self._line_width)
        
        # Paint end arrow if needed
        if self._arrow_tips in [ArrowTip.END, ArrowTip.BOTH]:
            self._paint_arrowhead(painter, end_point, vector, self._line_width)

        painter.restore()
            
    def _paint_arrowhead(self, painter, point, vector, width):
        """Draw an arrow at the given point with the given angle and length."""
        painter.save()
        color = self._construction_color
        painter.translate(point)
        painter.rotate(math.degrees(math.atan2(vector.y(), vector.x())))
        pen = self.pen()
        pen.setWidth(0)
        pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.setBrush(QBrush(color))
        painter.drawPolygon([
            QPointF(0, 0),
            QPointF(-self.arrow_length * width,  self.arrow_width / 2 * width),
            QPointF(-self.arrow_length * width, -self.arrow_width / 2 * width),
            QPointF(0, 0)
        ])
        painter.restore()

    def _update_pen(self):
        """Update the pen based on current settings."""
        if self._line_width is None:
            pen = QPen(self._construction_color, 2.0)
            pen.setCosmetic(True)
        else:
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
    
    def mousePressEvent(self, event):
        """Override to ignore mouse press events."""
        event.ignore()
    
    def mouseMoveEvent(self, event):
        """Override to ignore mouse move events."""
        event.ignore()
    
    def mouseReleaseEvent(self, event):
        """Override to ignore mouse release events."""
        event.ignore()
    
    def mouseDoubleClickEvent(self, event):
        """Override to ignore mouse double click events."""
        event.ignore()
    
    def contextMenuEvent(self, event):
        """Override to ignore context menu events."""
        event.ignore()
    
    def keyPressEvent(self, event):
        """Override to ignore key press events."""
        event.ignore()
    
    def keyReleaseEvent(self, event):
        """Override to ignore key release events."""
        event.ignore()
    
    def focusInEvent(self, event):
        """Override to ignore focus in events."""
        event.ignore()
    
    def focusOutEvent(self, event):
        """Override to ignore focus out events."""
        event.ignore()

