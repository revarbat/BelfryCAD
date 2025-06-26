"""
Circle2PointsCadItem - A circle CAD item defined by two points on opposite sides (diameter endpoints).
"""

import math
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainterPathStroker, Qt
from BelfryCAD.gui.cad_item import CadItem
from BelfryCAD.gui.control_points import ControlPoint, SquareControlPoint, ControlDatum


class Circle2PointsCadItem(CadItem):
    """A circle CAD item defined by two points on opposite sides (diameter endpoints)."""
    
    def __init__(self, point1=None, point2=None, color=QColor(255, 0, 0), line_width=0.05):
        self._point1 = point1 if point1 is not None else QPointF(-1, 0)
        self._point2 = point2 if point2 is not None else QPointF(1, 0)
        self._color = color
        self._line_width = line_width
        self._radius_datum = None
        
        # Convert points to QPointF if they aren't already
        if isinstance(self._point1, (list, tuple)):
            self._point1 = QPointF(self._point1[0], self._point1[1])
        if isinstance(self._point2, (list, tuple)):
            self._point2 = QPointF(self._point2[0], self._point2[1])
        
        super().__init__()
        
        # Position the item at the center point
        self.setPos(self.center_point)
    
    def _get_control_points(self):
        """Return control points for the circle."""
        # Control points are relative to the center
        center = self.center_point
        point1_local = self._point1 - center
        point2_local = self._point2 - center
        
        # Create radius datum if it doesn't exist
        if not self._radius_datum:
            sc = math.sin(math.pi/4)
            datum_pos = QPointF(self.radius * sc, self.radius * sc)
            self._radius_datum = ControlDatum(
                name="radius",
                position=datum_pos,
                value_getter=self._get_radius_value,
                value_setter=self._set_radius_value,
                prefix="R",
                parent_item=self
            )
        else:
            sc = math.sin(math.pi/4)
            datum_pos = QPointF(self.radius * sc, self.radius * sc)
            self._radius_datum.position = datum_pos
        
        return [
            ControlPoint('point1', point1_local),
            ControlPoint('point2', point2_local),
            SquareControlPoint('center', QPointF(0, 0)),
            self._radius_datum
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
    
    def _create_decorations(self):
        """Create decoration items for this circle."""
        # Add centerlines decoration
        self._add_centerlines(QPointF(0, 0))

    @property
    def center_point(self):
        """Calculate the center point between the two diameter endpoints."""
        return QPointF(
            (self._point1.x() + self._point2.x()) / 2,
            (self._point1.y() + self._point2.y()) / 2
        )
    
    @property
    def radius(self):
        """Calculate the radius as half the distance between the two points."""
        delta = self._point2 - self._point1
        diameter = (delta.x() ** 2 + delta.y() ** 2) ** 0.5
        return diameter / 2
    
    @radius.setter
    def radius(self, value):
        """Set the radius by moving both points symmetrically from center."""
        center = self.center_point
        # Calculate current direction vector from point1 to point2
        direction = self._point2 - self._point1
        direction_length = (direction.x() ** 2 + direction.y() ** 2) ** 0.5
        
        if direction_length > 0:
            # Normalize direction and scale by new diameter
            normalized = QPointF(direction.x() / direction_length, direction.y() / direction_length)
            half_diameter = value
            
            self._point1 = center - QPointF(normalized.x() * half_diameter, normalized.y() * half_diameter)
            self._point2 = center + QPointF(normalized.x() * half_diameter, normalized.y() * half_diameter)
        else:
            # If points are coincident, create horizontal diameter
            self._point1 = QPointF(center.x() - value, center.y())
            self._point2 = QPointF(center.x() + value, center.y())
        
        self.setPos(self.center_point)
        self.prepareGeometryChange()
        self.update()

    @property
    def point1(self):
        return self._point1
    
    @point1.setter
    def point1(self, value):
        self._point1 = value
        self.setPos(self.center_point)
        self.prepareGeometryChange()
        self.update()

    @property
    def point2(self):
        return self._point2
    
    @point2.setter
    def point2(self, value):
        self._point2 = value
        self.setPos(self.center_point)
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
        self.prepareGeometryChange()
        if name == 'center':
            # Translate the entire circle (both points)
            # Calculate the delta from current center (which is at origin in local coords)
            delta = new_position  # new_position is the delta from origin
            scene_delta = self.mapToScene(delta) - self.mapToScene(QPointF(0, 0))
            self._point1 += scene_delta
            self._point2 += scene_delta
            self.setPos(self.center_point)
        elif name == 'point1':
            # Change point1 position
            scene_pos = self.mapToScene(new_position)
            self._point1 = scene_pos
            self.setPos(self.center_point)
            self.prepareGeometryChange()
            self.update()
        elif name == 'point2':
            # Change point2 position
            scene_pos = self.mapToScene(new_position)
            self._point2 = scene_pos
            self.setPos(self.center_point)
            self.prepareGeometryChange()
            self.update()
        
        # Call parent method to refresh all control points
        super()._control_point_changed(name, new_position)

    def diameter(self):
        """Get the diameter of the circle."""
        return self.radius * 2
    
    def set_diameter_points(self, point1, point2):
        """Set both diameter endpoint at once."""
        self._point1 = point1
        self._point2 = point2
        self.setPos(self.center_point)
        self.prepareGeometryChange()
        self.update()

    def _get_radius_value(self):
        """Get the current radius value."""
        return self.radius
    
    def _set_radius_value(self, new_radius):
        """Set the radius value."""
        self.radius = new_radius 