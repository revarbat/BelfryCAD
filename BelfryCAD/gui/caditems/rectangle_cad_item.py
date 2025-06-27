"""
RectangleCadItem - A rectangle CAD item defined by four corner points.
"""

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QBrush, QPainterPath, QPainterPathStroker, Qt
from BelfryCAD.gui.cad_item import CadItem
from BelfryCAD.gui.control_points import ControlPoint, SquareControlPoint
from BelfryCAD.gui.cad_rect import CadRect


class RectangleCadItem(CadItem):
    """A rectangle CAD item defined by four corner points."""
    
    def __init__(self, top_left=None, top_right=None, bottom_right=None, bottom_left=None, 
                 color=QColor(0, 0, 0), line_width=0.05):
        super().__init__()
        # Default to a 2x1 rectangle if no points provided
        self._top_left = top_left if top_left else QPointF(0, 1)
        self._top_right = top_right if top_right else QPointF(2, 1)
        self._bottom_right = bottom_right if bottom_right else QPointF(2, 0)
        self._bottom_left = bottom_left if bottom_left else QPointF(0, 0)
        self._color = color
        self._line_width = line_width
        
        # Convert points to QPointF if they aren't already
        if isinstance(self._top_left, (list, tuple)):
            self._top_left = QPointF(self._top_left[0], self._top_left[1])
        if isinstance(self._top_right, (list, tuple)):
            self._top_right = QPointF(self._top_right[0], self._top_right[1])
        if isinstance(self._bottom_right, (list, tuple)):
            self._bottom_right = QPointF(self._bottom_right[0], self._bottom_right[1])
        if isinstance(self._bottom_left, (list, tuple)):
            self._bottom_left = QPointF(self._bottom_left[0], self._bottom_left[1])
    
    def boundingRect(self):
        """Return the bounding rectangle of the rectangle."""
        # Create a CadRect containing all four corner points
        rect = CadRect()
        rect.expandToPoint(self._top_left)
        rect.expandToPoint(self._top_right)
        rect.expandToPoint(self._bottom_right)
        rect.expandToPoint(self._bottom_left)
        
        # Add padding for line width
        rect.expandByScalar(self._line_width / 2)
        
        return rect
    
    def shape(self):
        """Return the exact shape of the rectangle for collision detection."""
        path = self._create_rectangle_path()
        
        # Create a stroked path with the line width for better selection
        stroker = QPainterPathStroker()
        stroker.setWidth(max(self._line_width, 0.1))  # Minimum width for selection
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        
        return stroker.createStroke(path)
    
    def contains(self, point):
        """Check if a point is near the rectangle outline."""
        # Convert point to local coordinates if needed
        if hasattr(point, 'x') and hasattr(point, 'y'):
            local_point = point
        else:
            local_point = self.mapFromScene(point)
        
        # Use the stroked shape for accurate contains check
        shape_path = self.shape()
        return shape_path.contains(local_point)
    
    def _get_control_points(self):
        """Return control points for the rectangle corners and center."""
        # Calculate center point
        center_x = (self._top_left.x() + self._bottom_right.x()) / 2
        center_y = (self._top_left.y() + self._bottom_right.y()) / 2
        center = QPointF(center_x, center_y)
        
        return [
            ControlPoint('top_left', self._top_left),
            ControlPoint('top_right', self._top_right),
            ControlPoint('bottom_right', self._bottom_right),
            ControlPoint('bottom_left', self._bottom_left),
            SquareControlPoint('center', center)
        ]

    def _control_point_changed(self, name: str, new_position: QPointF):
        """Handle control point changes while maintaining rectangular shape."""
        # When a corner is moved, adjust the adjacent corners to maintain rectangularity
        self.prepareGeometryChange()
        
        if name == 'center':
            # Moving center: translate the entire rectangle
            # Calculate current center
            current_center_x = (self._top_left.x() + self._bottom_right.x()) / 2
            current_center_y = (self._top_left.y() + self._bottom_right.y()) / 2
            
            # Calculate offset from current center to new position
            offset_x = new_position.x() - current_center_x
            offset_y = new_position.y() - current_center_y
            
            # Move all corners by the offset
            self._top_left = QPointF(self._top_left.x() + offset_x, self._top_left.y() + offset_y)
            self._top_right = QPointF(self._top_right.x() + offset_x, self._top_right.y() + offset_y)
            self._bottom_right = QPointF(self._bottom_right.x() + offset_x, self._bottom_right.y() + offset_y)
            self._bottom_left = QPointF(self._bottom_left.x() + offset_x, self._bottom_left.y() + offset_y)
            
        elif name == 'top_left':
            # Moving top-left: adjust top-right and bottom-left to maintain right angles
            self._top_left = new_position
            # Top-right keeps its Y coordinate, takes new X from top-left
            self._top_right = QPointF(self._top_right.x(), new_position.y())
            # Bottom-left keeps its X coordinate, takes new Y from top-left  
            self._bottom_left = QPointF(new_position.x(), self._bottom_left.y())
            
        elif name == 'top_right':
            # Moving top-right: adjust top-left and bottom-right to maintain right angles
            self._top_right = new_position
            # Top-left keeps its Y coordinate, takes new X from top-right
            self._top_left = QPointF(self._top_left.x(), new_position.y())
            # Bottom-right keeps its X coordinate, takes new Y from top-right
            self._bottom_right = QPointF(new_position.x(), self._bottom_right.y())
            
        elif name == 'bottom_right':
            # Moving bottom-right: adjust bottom-left and top-right to maintain right angles
            self._bottom_right = new_position
            # Bottom-left keeps its Y coordinate, takes new X from bottom-right
            self._bottom_left = QPointF(self._bottom_left.x(), new_position.y())
            # Top-right keeps its X coordinate, takes new Y from bottom-right
            self._top_right = QPointF(new_position.x(), self._top_right.y())
            
        elif name == 'bottom_left':
            # Moving bottom-left: adjust bottom-right and top-left to maintain right angles
            self._bottom_left = new_position
            # Bottom-right keeps its Y coordinate, takes new X from bottom-left
            self._bottom_right = QPointF(self._bottom_right.x(), new_position.y())
            # Top-left keeps its X coordinate, takes new Y from bottom-left
            self._top_left = QPointF(new_position.x(), self._top_left.y())
        
        self.update()
        
        # Call parent method to refresh all control points
        super()._control_point_changed(name, new_position)
    
    def paint_item(self, painter, option, widget=None):
        """Draw the rectangle content."""
        painter.save()
        
        pen = QPen(self._color, self._line_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(QBrush())  # No fill
        
        # Draw the rectangle
        rectangle_path = self._create_rectangle_path()
        painter.drawPath(rectangle_path)
        
        painter.restore()
    
    def _create_rectangle_path(self):
        """Create the rectangle path."""
        path = QPainterPath()
        path.moveTo(self._top_left)
        path.lineTo(self._top_right)
        path.lineTo(self._bottom_right)
        path.lineTo(self._bottom_left)
        path.closeSubpath()  # Close the rectangle
        return path
    
    @property
    def top_left(self):
        """Get the top-left corner point."""
        return QPointF(self._top_left)
    
    @top_left.setter
    def top_left(self, value):
        """Set the top-left corner point."""
        self.prepareGeometryChange()
        if isinstance(value, (list, tuple)):
            value = QPointF(value[0], value[1])
        self._top_left = value
        self.update()
    
    @property
    def top_right(self):
        """Get the top-right corner point."""
        return QPointF(self._top_right)
    
    @top_right.setter
    def top_right(self, value):
        """Set the top-right corner point."""
        self.prepareGeometryChange()
        if isinstance(value, (list, tuple)):
            value = QPointF(value[0], value[1])
        self._top_right = value
        self.update()
    
    @property
    def bottom_right(self):
        """Get the bottom-right corner point."""
        return QPointF(self._bottom_right)
    
    @bottom_right.setter
    def bottom_right(self, value):
        """Set the bottom-right corner point."""
        self.prepareGeometryChange()
        if isinstance(value, (list, tuple)):
            value = QPointF(value[0], value[1])
        self._bottom_right = value
        self.update()
    
    @property
    def bottom_left(self):
        """Get the bottom-left corner point."""
        return QPointF(self._bottom_left)
    
    @bottom_left.setter
    def bottom_left(self, value):
        """Set the bottom-left corner point."""
        self.prepareGeometryChange()
        if isinstance(value, (list, tuple)):
            value = QPointF(value[0], value[1])
        self._bottom_left = value
        self.update()
    
    @property
    def points(self):
        """Get all four corner points as a tuple."""
        return (QPointF(self._top_left), QPointF(self._top_right), 
                QPointF(self._bottom_right), QPointF(self._bottom_left))
    
    @points.setter
    def points(self, value):
        """Set all four corner points from a tuple/list of four points."""
        if len(value) != 4:
            raise ValueError("Points must contain exactly 4 points")
        self.prepareGeometryChange()
        top_left, top_right, bottom_right, bottom_left = value
        if isinstance(top_left, (list, tuple)):
            top_left = QPointF(top_left[0], top_left[1])
        if isinstance(top_right, (list, tuple)):
            top_right = QPointF(top_right[0], top_right[1])
        if isinstance(bottom_right, (list, tuple)):
            bottom_right = QPointF(bottom_right[0], bottom_right[1])
        if isinstance(bottom_left, (list, tuple)):
            bottom_left = QPointF(bottom_left[0], bottom_left[1])
        self._top_left = top_left
        self._top_right = top_right
        self._bottom_right = bottom_right
        self._bottom_left = bottom_left
        self.update()
    
    @property
    def color(self):
        return self._color
    
    @color.setter
    def color(self, value):
        self._color = value
        self.update()
    
    @property
    def line_width(self):
        return self._line_width
    
    @line_width.setter
    def line_width(self, value):
        self.prepareGeometryChange()  # Line width affects bounding rect
        self._line_width = value
        self.update()
    
    @property
    def width(self):
        """Calculate the width of the rectangle."""
        return abs(self._top_right.x() - self._top_left.x())
    
    @property
    def height(self):
        """Calculate the height of the rectangle."""
        return abs(self._top_left.y() - self._bottom_left.y())
    
    @property
    def area(self):
        """Calculate the area of the rectangle."""
        return self.width * self.height
    
    @property
    def center(self):
        """Calculate the center point of the rectangle."""
        center_x = (self._top_left.x() + self._bottom_right.x()) / 2
        center_y = (self._top_left.y() + self._bottom_right.y()) / 2
        return QPointF(center_x, center_y) 