"""
CircleCenterRadiusCadItem - A circle CAD item defined by center point and perimeter point.
"""

import math
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainterPathStroker, Qt
from BelfryCAD.gui.cad_item import CadItem
from BelfryCAD.gui.control_points import ControlPoint, SquareControlPoint, ControlDatum
from BelfryCAD.gui.cad_rect import CadRect


class CircleCenterRadiusCadItem(CadItem):
    """A circle CAD item defined by center point and perimeter point."""
    
    def __init__(self, center_point=None, perimeter_point=None, color=QColor(255, 0, 0), line_width=0.05):
        super().__init__()
        self._center_point = center_point if center_point else QPointF(0, 0)
        self._perimeter_point = perimeter_point if perimeter_point else QPointF(1, 0)
        self._color = color
        self._line_width = line_width
        self._radius_datum = None
        
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
            # Update radius datum position
            sc = math.sin(math.pi/4)
            datum_pos = QPointF(self.radius * sc, self.radius * sc)
            self._radius_datum.position = datum_pos
        
        return [
            SquareControlPoint('center', QPointF(0, 0)),
            ControlPoint('perimeter', perimeter_local),
            self._radius_datum
        ]
    
    def boundingRect(self):
        """Return the bounding rectangle of the circle."""
        radius = self.radius
        
        # Create a CadRect centered at origin with the circle's diameter
        rect = CadRect(-radius, -radius, 2 * radius, 2 * radius)
        
        # Add padding for line width
        rect.expandByScalar(self._line_width / 2)
        
        return rect
    
    def shape(self):
        """Return the exact shape of the circle for collision detection."""
        radius = self.radius
        
        # Create a proper ellipse path
        path = QPainterPath()
        rect = QRectF(-radius, -radius, 2 * radius, 2 * radius)
        path.addEllipse(rect)
        
        # Use QPainterPathStroker to create a stroked path with line width
        stroker = QPainterPathStroker()
        stroker.setWidth(max(self._line_width, 0.01))  # Minimum width for selection
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        
        return stroker.createStroke(path)
    
    def contains(self, point):
        """Check if a point is inside the circle."""
        # Convert point to local coordinates if it's in scene coordinates
        if hasattr(point, 'x') and hasattr(point, 'y'):
            # Point is already in local coordinates
            local_point = point
        else:
            # Convert from scene coordinates to local coordinates
            local_point = self.mapFromScene(point)
        
        # Use the stroked shape for accurate contains check
        shape_path = self.shape()
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
    
    def _update_geometry_from_control_point(self, name: str, new_position: QPointF):
        """Update the CAD item geometry based on control point changes."""
        if name == 'center':
            # new_position is in scene coordinates
            # Update the center point in scene coordinates
            old_center = self._center_point
            self._center_point = new_position
            # Move the CAD item to the new center
            self.setPos(self._center_point)
            # Update perimeter point to maintain the same relative position
            delta = new_position - old_center
            self._perimeter_point += delta
            self.prepareGeometryChange()
            self.update()
        elif name == 'perimeter':
            # new_position is in scene coordinates
            # Update perimeter point in scene coordinates
            self._perimeter_point = new_position
            self.prepareGeometryChange()
            self.update()
    
    def _control_point_changed(self, name: str, new_position: QPointF):
        """Handle control point changes using the optimized update method."""
        # Call the parent method which handles the optimized update logic
        super()._control_point_changed(name, new_position)

    def _get_radius_value(self):
        """Get the current radius value."""
        return self.radius
    
    def _set_radius_value(self, new_radius):
        """Set the radius value."""
        self.radius = new_radius 