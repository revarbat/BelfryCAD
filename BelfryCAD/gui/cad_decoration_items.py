"""
CAD decoration items for drawing behind main CAD items.
"""

from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPen, QColor, QBrush, QPainterPath


class CadDecorationItem(QGraphicsItem):
    """Base class for CAD decoration items that draw behind the main items."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setZValue(-1)  # Draw behind other items
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
    
    def shape(self):
        """Return empty shape since decorations are not interactive."""
        return QPainterPath()


class CenterlinesDecorationItem(CadDecorationItem):
    """Decoration item for centerlines (cross pattern)."""
    
    def __init__(self, center_point, radius=33.0, parent=None):
        super().__init__(parent)
        self.center_point = center_point
        self.radius = radius
    
    def boundingRect(self):
        """Return bounding rectangle of centerlines."""
        return QRectF(
            self.center_point.x() - self.radius,
            self.center_point.y() - self.radius,
            2 * self.radius,
            2 * self.radius
        ).adjusted(-10, -10, 10, 10)
    
    def paint(self, painter, option, widget=None):
        """Paint centerlines from center point."""
        painter.save()
        
        scale = painter.transform().m11()
        radius = 33/scale
        
        # Standardized centerline styling
        dash_pattern = [10.0, 2.0, 2.0, 2.0]  # 10, 2, 2, 2 pattern
        pen = QPen(QColor(128, 128, 128), 3.0)  # Gray color
        pen.setCosmetic(True)
        pen.setDashPattern(dash_pattern)
        painter.setPen(pen)
        
        # Draw four centerlines from center to radius distance
        painter.drawLine(self.center_point, self.center_point + QPointF(radius, 0))    # Right
        painter.drawLine(self.center_point, self.center_point + QPointF(0, radius))    # Up
        painter.drawLine(self.center_point, self.center_point + QPointF(-radius, 0))   # Left
        painter.drawLine(self.center_point, self.center_point + QPointF(0, -radius))   # Down
        
        painter.restore()


class DashedCircleDecorationItem(CadDecorationItem):
    """Decoration item for dashed circles."""
    
    def __init__(self, center_point, radius, color=QColor(127, 127, 127), line_width=3.0, parent=None):
        super().__init__(parent)
        self.center_point = center_point
        self.radius = radius
        self.color = color
        self.line_width = line_width
    
    def boundingRect(self):
        """Return bounding rectangle of dashed circle."""
        return QRectF(
            self.center_point.x() - self.radius,
            self.center_point.y() - self.radius,
            2 * self.radius,
            2 * self.radius
        ).adjusted(-10, -10, 10, 10)
    
    def paint(self, painter, option, widget=None):
        """Paint a dashed circle."""
        painter.save()
        
        pen = QPen(self.color, self.line_width)
        pen.setCosmetic(True)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(QBrush())  # No fill
        
        circle_rect = QRectF(
            self.center_point.x() - self.radius,
            self.center_point.y() - self.radius,
            2 * self.radius,
            2 * self.radius
        )
        painter.drawEllipse(circle_rect)
        
        painter.restore()


class DashedLinesDecorationItem(CadDecorationItem):
    """Decoration item for dashed lines."""
    
    def __init__(self, lines, color=QColor(127, 127, 127), line_width=3.0, parent=None):
        super().__init__(parent)
        self.lines = lines  # List of (start_point, end_point) tuples
        self.color = color
        self.line_width = line_width
    
    def boundingRect(self):
        """Return bounding rectangle of all dashed lines."""
        if not self.lines:
            return QRectF()
        
        bounds = QRectF()
        for line in self.lines:
            bounds = bounds.united(QRectF(line[0], line[1]).normalized())
        
        return bounds.adjusted(-10, -10, 10, 10)
    
    def paint(self, painter, option, widget=None):
        """Paint dashed lines."""
        painter.save()
        
        pen = QPen(self.color, self.line_width)
        pen.setCosmetic(True)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        
        for line in self.lines:
            painter.drawLine(line[0], line[1])
        
        painter.restore()


class RadiusLinesDecorationItem(CadDecorationItem):
    """Decoration item for radius lines from center to points."""
    
    def __init__(self, center_point, radius_points, color=QColor(127, 127, 127), line_width=3.0, parent=None):
        super().__init__(parent)
        self.center_point = center_point
        self.radius_points = radius_points  # List of QPointF
        self.color = color
        self.line_width = line_width
    
    def boundingRect(self):
        """Return bounding rectangle of all radius lines."""
        if not self.radius_points:
            return QRectF()
        
        bounds = QRectF()
        for point in self.radius_points:
            bounds = bounds.united(QRectF(self.center_point, point).normalized())
        
        return bounds.adjusted(-10, -10, 10, 10)
    
    def paint(self, painter, option, widget=None):
        """Paint radius lines from center to points."""
        painter.save()
        
        pen = QPen(self.color, self.line_width)
        pen.setCosmetic(True)
        painter.setPen(pen)
        
        for point in self.radius_points:
            painter.drawLine(self.center_point, point)
        
        painter.restore() 