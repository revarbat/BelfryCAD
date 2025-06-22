"""
ControlPoint - A class representing a control point for CAD items.
"""

from PySide6.QtCore import QRectF, QPointF
from PySide6.QtGui import QPen, QColor, QBrush, QPainterPath


class ControlPoint:
    """A control point with a name, position, and drawing capability."""
    
    def __init__(self, name: str, position: QPointF):
        """
        Initialize a control point.
        
        Args:
            name: String identifier for the control point
            position: QPointF position of the control point
        """
        self.name = name
        self.position = position
    
    def draw(self, painter):
        """Draw the control point at its position."""
        painter.save()
        
        # Standardized control point styling
        control_pen = QPen(QColor(255, 0, 0), 1.0)  # Red color
        control_pen.setCosmetic(True)
        control_brush = QBrush(QColor(255, 255, 255))  # White fill
        painter.setPen(control_pen)
        painter.setBrush(control_brush)
        
        # Standardized control point size
        control_size = 0.1
        control_padding = control_size / 2
        
        # Draw the control point ellipse
        control_rect = QRectF(
            self.position.x() - control_padding,
            self.position.y() - control_padding,
            control_size, control_size
        )
        painter.drawEllipse(control_rect)
        
        painter.restore()
    
    def contains(self, point: QPointF) -> bool:
        """Check if a point is within this control point."""
        control_size = 0.1
        control_padding = control_size / 2
        
        control_rect = QRectF(
            self.position.x() - control_padding,
            self.position.y() - control_padding,
            control_size, control_size
        )
        return control_rect.contains(point)
    
    def bounding_rect(self) -> QRectF:
        """Return the bounding rectangle of this control point."""
        control_size = 0.1
        control_padding = control_size / 2
        
        return QRectF(
            self.position.x() - control_padding,
            self.position.y() - control_padding,
            control_size, control_size
        ) 
    
    
class SquareControlPoint(ControlPoint):
    """Control point that draws as a square instead of a circle."""
    
    def draw(self, painter):
        """Draw the control point as a square at its position."""
        painter.save()
        
        # Standardized control point styling
        control_pen = QPen(QColor(255, 0, 0), 1.0)  # Red color
        control_pen.setCosmetic(True)
        control_brush = QBrush(QColor(255, 255, 255))  # White fill
        painter.setPen(control_pen)
        painter.setBrush(control_brush)
        
        # Standardized control point size
        control_size = 0.1
        control_padding = control_size / 2
        
        # Draw the control point as a square
        control_rect = QRectF(
            self.position.x() - control_padding,
            self.position.y() - control_padding,
            control_size, control_size
        )
        painter.drawRect(control_rect)
        
        painter.restore()


class DiamondControlPoint(ControlPoint):
    """Control point that draws as a diamond instead of a circle."""
    
    def draw(self, painter):
        """Draw the control point as a diamond at its position."""
        painter.save()
        
        # Standardized control point styling
        control_pen = QPen(QColor(255, 0, 0), 1.0)  # Red color
        control_pen.setCosmetic(True)
        control_brush = QBrush(QColor(255, 255, 255))  # White fill
        painter.setPen(control_pen)
        painter.setBrush(control_brush)
        
        # Larger diamond size (44% larger than standard)
        control_size = 0.1 * 1.44  # 44% larger
        control_padding = control_size / 2
        
        # Create diamond shape using QPainterPath
        diamond_path = QPainterPath()
        center_x = self.position.x()
        center_y = self.position.y()
        
        # Define diamond vertices (top, right, bottom, left)
        diamond_path.moveTo(center_x, center_y - control_padding)  # Top
        diamond_path.lineTo(center_x + control_padding, center_y)  # Right
        diamond_path.lineTo(center_x, center_y + control_padding)  # Bottom
        diamond_path.lineTo(center_x - control_padding, center_y)  # Left
        diamond_path.closeSubpath()
        
        painter.drawPath(diamond_path)
        
        painter.restore()
    
    def contains(self, point: QPointF) -> bool:
        """Check if a point is within this diamond control point."""
        # Use larger size for hit detection
        control_size = 0.1 * 1.44  # 44% larger
        control_padding = control_size / 2
        
        # For diamond shape, we need to check if the point is within the diamond's area
        # using a proper diamond containment test
        center_x = self.position.x()
        center_y = self.position.y()
        
        # Calculate relative position from center
        dx = abs(point.x() - center_x)
        dy = abs(point.y() - center_y)
        
        # Diamond containment test: point is inside if dx + dy <= radius
        # This creates a diamond shape rotated 45 degrees
        return (dx + dy) <= control_padding
    
    def bounding_rect(self) -> QRectF:
        """Return the bounding rectangle of this diamond control point."""
        # Use larger size for bounding rectangle
        control_size = 0.1 * 1.44  # 44% larger
        control_padding = control_size / 2
        
        return QRectF(
            self.position.x() - control_padding,
            self.position.y() - control_padding,
            control_size, control_size
        )
