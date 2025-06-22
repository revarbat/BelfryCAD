"""
CircleCenterRadiusCadItem - A circle CAD item defined by center point and perimeter point.
"""

import math
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainterPathStroker, Qt
from BelfryCAD.gui.cad_item import CadItem
from BelfryCAD.gui.control_points import ControlPoint, SquareControlPoint


class CircleCenterRadiusCadItem(CadItem):
    """A circle CAD item defined by center point and perimeter point."""
    
    def __init__(self, center_point=None, perimeter_point=None, color=QColor(255, 0, 0), line_width=0.05):
        super().__init__()
        self._center_point = center_point if center_point else QPointF(0, 0)
        self._perimeter_point = perimeter_point if perimeter_point else QPointF(1, 0)
        self._color = color
        self._line_width = line_width
        
        # Convert points to QPointF if they aren't already
        if isinstance(self._center_point, (list, tuple)):
            self._center_point = QPointF(self._center_point[0], self._center_point[1])
        if isinstance(self._perimeter_point, (list, tuple)):
            self._perimeter_point = QPointF(self._perimeter_point[0], self._perimeter_point[1])
        
        # Position the item at the center point
        self.setPos(self._center_point)
    
    def _get_control_points(self):
        """Return control points for the circle."""
        perimeter_local = self._perimeter_point - self._center_point
        return [
            SquareControlPoint('center', QPointF(0, 0)),
            ControlPoint('perimeter', perimeter_local)
        ]
    
    def _boundingRect(self):
        """Return the bounding rectangle of the circle."""
        radius = self.radius
        # Add padding for line width
        padding = self._line_width / 2
        return QRectF(-radius - padding, -radius - padding, 
                     2 * radius + 2 * padding, 2 * radius + 2 * padding)
    
    def _shape(self):
        """Return the exact shape of the circle for collision detection."""
        radius = self.radius
        
        # Create a custom 90-point circle path
        path = QPainterPath()
        num_points = 90
        
        # Calculate the first point
        angle = 0
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        path.moveTo(x, y)
        
        # Add the remaining 89 points
        for i in range(1, num_points):
            angle = (2 * math.pi * i) / num_points
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            path.lineTo(x, y)
        
        # Close the path back to the starting point
        path.closeSubpath()
        
        # Use QPainterPathStroker to create a stroked path with line width
        stroker = QPainterPathStroker()
        stroker.setWidth(max(self._line_width, 0.01))  # Minimum width for selection
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        
        return stroker.createStroke(path)
    
    def _contains(self, point):
        """Check if a point is inside the circle."""
        # Convert point to local coordinates if it's in scene coordinates
        if hasattr(point, 'x') and hasattr(point, 'y'):
            # Point is already in local coordinates
            local_point = point
        else:
            # Convert from scene coordinates to local coordinates
            local_point = self.mapFromScene(point)
        
        # Use the stroked shape for accurate contains check
        shape_path = self._shape()
        return shape_path.contains(local_point)
    
    def paint_item(self, painter, option, widget=None):
        """Draw the circle content."""
        radius = self.radius
        rect = QRectF(-radius, -radius, 2*radius, 2*radius)

        painter.save()
        
        pen = QPen(self._color, self._line_width)
        painter.setPen(pen)
        painter.drawEllipse(rect)

        painter.restore()        
    
    def _draw_decorations(self, painter):
        """Draw centerlines and control points when selected."""
        # Draw centerlines using base class method
        self.draw_centerlines(painter, QPointF(0, 0), self.radius)

    @property
    def radius(self):
        """Calculate the radius from center to perimeter point."""
        delta = self._perimeter_point - self._center_point
        return (delta.x() ** 2 + delta.y() ** 2) ** 0.5
    
    @radius.setter
    def radius(self, value):
        """Set the radius by moving the perimeter point."""
        # Calculate current angle from center to perimeter point
        delta = self._perimeter_point - self._center_point
        current_angle = math.atan2(delta.y(), delta.x())
        
        # Calculate new perimeter point position
        new_perimeter_x = self._center_point.x() + value * math.cos(current_angle)
        new_perimeter_y = self._center_point.y() + value * math.sin(current_angle)
        
        self._perimeter_point = QPointF(new_perimeter_x, new_perimeter_y)
        self.prepareGeometryChange()
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
    
    def _control_point_changed(self, name: str, new_position: QPointF):
        """Handle control point changes."""
        if name == 'center':
            # Translate the entire circle (both center and perimeter points)
            # Calculate the delta from current center (which is at origin in local coords)
            delta = new_position  # new_position is the delta from origin
            scene_delta = self.mapToScene(delta) - self.mapToScene(QPointF(0, 0))
            self._center_point += scene_delta
            self._perimeter_point += scene_delta
            self.setPos(self._center_point)
        elif name == 'perimeter':
            # Change the perimeter point position
            # Convert to scene coordinates and set new perimeter point
            scene_pos = self.mapToScene(new_position)
            self._perimeter_point = scene_pos
            self.prepareGeometryChange()
            self.update() 