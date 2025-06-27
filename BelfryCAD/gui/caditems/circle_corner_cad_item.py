"""
CircleCornerCadItem - A circle CAD item defined by a corner point and two tangent rays.
The circle is tangent to both rays, with center specified by a point on the angle bisector.
"""

import math
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainterPathStroker, QFont, QFontMetrics
from PySide6.QtWidgets import QLineEdit, QGraphicsProxyWidget
from BelfryCAD.gui.cad_item import CadItem
from BelfryCAD.gui.control_points import ControlPoint, SquareControlPoint, ControlDatum
from BelfryCAD.gui.cad_rect import CadRect


class CircleCornerCadItem(CadItem):
    """A circle CAD item defined by corner point, two ray points, and center point."""
    
    def __init__(self, corner_point=None, ray1_point=None, ray2_point=None, center_point=None, 
                 color=QColor(255, 0, 0), line_width=0.05):
        self._corner_point = corner_point if corner_point is not None else QPointF(0, 0)
        self._ray1_point = ray1_point if ray1_point is not None else QPointF(1, 0)
        self._ray2_point = ray2_point if ray2_point is not None else QPointF(0, 1)
        self._center_point = center_point if center_point is not None else QPointF(0.5, 0.5)
        self._color = color
        self._line_width = line_width
        
        # Convert points to QPointF if they aren't already
        if isinstance(self._corner_point, (list, tuple)):
            self._corner_point = QPointF(self._corner_point[0], self._corner_point[1])
        if isinstance(self._ray1_point, (list, tuple)):
            self._ray1_point = QPointF(self._ray1_point[0], self._ray1_point[1])
        if isinstance(self._ray2_point, (list, tuple)):
            self._ray2_point = QPointF(self._ray2_point[0], self._ray2_point[1])
        if isinstance(self._center_point, (list, tuple)):
            self._center_point = QPointF(self._center_point[0], self._center_point[1])
        
        super().__init__()
        
        # Initialize circle calculation
        self._calculated_center = QPointF(0, 0)
        self._radius = 0
        self._is_valid = False
        self._radius_datum = None
        
        # Calculate initial circle
        self._calculate_circle()
        
        # Position the item at the calculated center
        self.setPos(self._calculated_center)
    
    def _get_radius_value(self):
        """Get the current radius value for the control datum."""
        return self._radius if self._is_valid else 0.0
    
    def _set_radius_value(self, new_radius):
        """Set the radius value from the control datum."""
        if new_radius > 0:
            self._set_radius(new_radius)
    
    def _calculate_circle(self, update_center_spec=True):
        """Calculate the circle center and radius from the four defining points."""
        corner = self._corner_point
        ray1 = self._ray1_point
        ray2 = self._ray2_point
        center_spec = self._center_point
        
        # Calculate ray vectors from corner
        ray1_vec = QPointF(ray1.x() - corner.x(), ray1.y() - corner.y())
        ray2_vec = QPointF(ray2.x() - corner.x(), ray2.y() - corner.y())
        
        # Normalize ray vectors
        ray1_len = math.sqrt(ray1_vec.x() ** 2 + ray1_vec.y() ** 2)
        ray2_len = math.sqrt(ray2_vec.x() ** 2 + ray2_vec.y() ** 2)
        
        if ray1_len < 1e-6 or ray2_len < 1e-6:
            # Degenerate case: one of the rays has zero length
            self._is_valid = False
            self._calculated_center = corner
            self._radius = 0
            return
        
        ray1_unit = QPointF(ray1_vec.x() / ray1_len, ray1_vec.y() / ray1_len)
        ray2_unit = QPointF(ray2_vec.x() / ray2_len, ray2_vec.y() / ray2_len)
        
        # Check if rays are parallel (or nearly so)
        cross_product = ray1_unit.x() * ray2_unit.y() - ray1_unit.y() * ray2_unit.x()
        if abs(cross_product) < 1e-6:
            # Rays are parallel - no valid circle
            self._is_valid = False
            self._calculated_center = corner
            self._radius = 0
            return
        
        # Calculate angle bisector direction
        # The bisector direction is the normalized sum of the two unit vectors
        bisector_vec = QPointF(ray1_unit.x() + ray2_unit.x(), ray1_unit.y() + ray2_unit.y())
        bisector_len = math.sqrt(bisector_vec.x() ** 2 + bisector_vec.y() ** 2)
        
        if bisector_len < 1e-6:
            # This happens when rays are opposite (180 degrees) - degenerate case
            self._is_valid = False
            self._calculated_center = corner
            self._radius = 0
            return
        
        bisector_unit = QPointF(bisector_vec.x() / bisector_len, bisector_vec.y() / bisector_len)
        
        # Project the specified center point onto the angle bisector
        # Vector from corner to specified center
        to_center_vec = QPointF(center_spec.x() - corner.x(), center_spec.y() - corner.y())
        
        # Project onto bisector direction
        projection_length = (to_center_vec.x() * bisector_unit.x() + 
                           to_center_vec.y() * bisector_unit.y())
        
        if projection_length <= 0:
            # Center point is behind the corner on the bisector - invalid
            self._is_valid = False
            self._calculated_center = corner
            self._radius = 0
            return
        
        # Calculate actual center on the bisector
        self._calculated_center = QPointF(
            corner.x() + projection_length * bisector_unit.x(),
            corner.y() + projection_length * bisector_unit.y()
        )
        
        # Calculate radius as perpendicular distance from center to either ray
        # Using ray1: distance from point to line
        self._radius = self._point_to_ray_distance(
            self._calculated_center, corner, ray1_unit
        )
        
        # Update the center specification point to match the calculated center
        # (unless we're being called because the center_spec itself moved)
        if update_center_spec:
            self._center_point = QPointF(self._calculated_center)
        
        self._is_valid = True
    
    def _point_to_ray_distance(self, point, ray_start, ray_direction):
        """Calculate perpendicular distance from a point to a ray."""
        # Vector from ray start to point
        to_point = QPointF(point.x() - ray_start.x(), point.y() - ray_start.y())
        
        # Cross product gives the perpendicular distance (with sign)
        cross = abs(to_point.x() * ray_direction.y() - to_point.y() * ray_direction.x())
        return cross
    
    def _move_center_along_bisector(self, new_pos):
        """Move the center to a new position, constraining it to the angle bisector."""
        corner = self._corner_point
        ray1 = self._ray1_point
        ray2 = self._ray2_point
        
        # Calculate ray vectors from corner
        ray1_vec = QPointF(ray1.x() - corner.x(), ray1.y() - corner.y())
        ray2_vec = QPointF(ray2.x() - corner.x(), ray2.y() - corner.y())
        
        # Normalize ray vectors
        ray1_len = math.sqrt(ray1_vec.x() ** 2 + ray1_vec.y() ** 2)
        ray2_len = math.sqrt(ray2_vec.x() ** 2 + ray2_vec.y() ** 2)
        
        if ray1_len < 1e-6 or ray2_len < 1e-6:
            return  # Can't move center if rays are degenerate
        
        ray1_unit = QPointF(ray1_vec.x() / ray1_len, ray1_vec.y() / ray1_len)
        ray2_unit = QPointF(ray2_vec.x() / ray2_len, ray2_vec.y() / ray2_len)
        
        # Check if rays are parallel
        cross_product = ray1_unit.x() * ray2_unit.y() - ray1_unit.y() * ray2_unit.x()
        if abs(cross_product) < 1e-6:
            return  # Can't move center if rays are parallel
        
        # Calculate angle bisector direction
        bisector_vec = QPointF(ray1_unit.x() + ray2_unit.x(), ray1_unit.y() + ray2_unit.y())
        bisector_len = math.sqrt(bisector_vec.x() ** 2 + bisector_vec.y() ** 2)
        
        if bisector_len < 1e-6:
            return  # Can't move center if rays are opposite
        
        bisector_unit = QPointF(bisector_vec.x() / bisector_len, bisector_vec.y() / bisector_len)
        
        # Project the new position onto the angle bisector
        to_new_pos = QPointF(new_pos.x() - corner.x(), new_pos.y() - corner.y())
        projection_length = (to_new_pos.x() * bisector_unit.x() + 
                           to_new_pos.y() * bisector_unit.y())
        
        # Ensure the projection is in the positive direction (away from corner)
        if projection_length < 0:
            projection_length = abs(projection_length)
        if projection_length < 1e-6:
            projection_length = 1
        
        # Calculate the projected position on the bisector
        projected_center = QPointF(
            corner.x() + projection_length * bisector_unit.x(),
            corner.y() + projection_length * bisector_unit.y()
        )
        
        # Update the center specification point to the projected position
        self._center_point = projected_center
        self._calculate_circle(update_center_spec=False)
        self.setPos(self._calculated_center)
        self.prepareGeometryChange()
        self.update()

    def _set_radius(self, new_radius):
        """Set the radius by moving the center point along the bisector."""
        if not self._is_valid or new_radius <= 0:
            return
            
        corner = self._corner_point
        ray1 = self._ray1_point
        ray2 = self._ray2_point
        
        # Calculate ray vectors and bisector
        ray1_vec = QPointF(ray1.x() - corner.x(), ray1.y() - corner.y())
        ray2_vec = QPointF(ray2.x() - corner.x(), ray2.y() - corner.y())
        
        ray1_len = math.sqrt(ray1_vec.x() ** 2 + ray1_vec.y() ** 2)
        ray2_len = math.sqrt(ray2_vec.x() ** 2 + ray2_vec.y() ** 2)
        
        if ray1_len < 1e-6 or ray2_len < 1e-6:
            return
            
        ray1_unit = QPointF(ray1_vec.x() / ray1_len, ray1_vec.y() / ray1_len)
        ray2_unit = QPointF(ray2_vec.x() / ray2_len, ray2_vec.y() / ray2_len)
        
        # Calculate angle bisector
        bisector_vec = QPointF(ray1_unit.x() + ray2_unit.x(), ray1_unit.y() + ray2_unit.y())
        bisector_len = math.sqrt(bisector_vec.x() ** 2 + bisector_vec.y() ** 2)
        
        if bisector_len < 1e-6:
            return
            
        bisector_unit = QPointF(bisector_vec.x() / bisector_len, bisector_vec.y() / bisector_len)
        
        # Calculate the distance along bisector needed for the desired radius
        # For a circle tangent to two rays, the distance from corner to center
        # relates to radius by: distance = radius / sin(angle/2)
        # where angle is the angle between the rays
        dot_product = ray1_unit.x() * ray2_unit.x() + ray1_unit.y() * ray2_unit.y()
        angle_between_rays = math.acos(max(-1.0, min(1.0, dot_product)))
        
        if angle_between_rays < 1e-6 or angle_between_rays > math.pi - 1e-6:
            return  # Degenerate cases
            
        distance_to_center = new_radius / math.sin(angle_between_rays / 2)
        
        # Calculate new center position
        new_center = QPointF(
            corner.x() + distance_to_center * bisector_unit.x(),
            corner.y() + distance_to_center * bisector_unit.y()
        )
        
        # Update center specification point
        self._center_point = new_center
        self._calculate_circle(update_center_spec=False)
        self.setPos(self._calculated_center)
        self.prepareGeometryChange()
        self.update()
        
    def _adjust_center_for_ray_change(self):
        """Adjust the center position to maintain the current radius with the new ray positions."""
        if not self._is_valid or self._radius <= 0:
            return
            
        corner = self._corner_point
        ray1 = self._ray1_point
        ray2 = self._ray2_point
        target_radius = self._radius
        
        # Calculate ray vectors from corner
        ray1_vec = QPointF(ray1.x() - corner.x(), ray1.y() - corner.y())
        ray2_vec = QPointF(ray2.x() - corner.x(), ray2.y() - corner.y())
        
        # Normalize ray vectors
        ray1_len = math.sqrt(ray1_vec.x() ** 2 + ray1_vec.y() ** 2)
        ray2_len = math.sqrt(ray2_vec.x() ** 2 + ray2_vec.y() ** 2)
        
        if ray1_len < 1e-6 or ray2_len < 1e-6:
            return  # Can't adjust if rays are degenerate
        
        ray1_unit = QPointF(ray1_vec.x() / ray1_len, ray1_vec.y() / ray1_len)
        ray2_unit = QPointF(ray2_vec.x() / ray2_len, ray2_vec.y() / ray2_len)
        
        # Check if rays are parallel
        cross_product = ray1_unit.x() * ray2_unit.y() - ray1_unit.y() * ray2_unit.x()
        if abs(cross_product) < 1e-6:
            return  # Can't adjust if rays are parallel
        
        # Calculate angle bisector direction
        bisector_vec = QPointF(ray1_unit.x() + ray2_unit.x(), ray1_unit.y() + ray2_unit.y())
        bisector_len = math.sqrt(bisector_vec.x() ** 2 + bisector_vec.y() ** 2)
        
        if bisector_len < 1e-6:
            return  # Can't adjust if rays are opposite
        
        bisector_unit = QPointF(bisector_vec.x() / bisector_len, bisector_vec.y() / bisector_len)
        
        # Calculate the distance along bisector needed for the target radius
        # For a circle tangent to two rays, the distance from corner to center
        # relates to radius by: distance = radius / sin(angle/2)
        # where angle is the angle between the rays
        dot_product = ray1_unit.x() * ray2_unit.x() + ray1_unit.y() * ray2_unit.y()
        angle_between_rays = math.acos(max(-1.0, min(1.0, dot_product)))
        
        if angle_between_rays < 1e-6 or angle_between_rays > math.pi - 1e-6:
            return  # Degenerate cases
            
        distance_to_center = target_radius / math.sin(angle_between_rays / 2)
        
        # Calculate new center position
        new_center = QPointF(
            corner.x() + distance_to_center * bisector_unit.x(),
            corner.y() + distance_to_center * bisector_unit.y()
        )
        
        # Update center specification point and recalculate
        self._center_point = new_center
        self._calculate_circle(update_center_spec=False)

    def _get_control_points(self):
        """Return control points for the circle."""
        if not self._is_valid:
            return []
        
        # Control points are relative to the calculated center
        corner_local = self._corner_point - self._calculated_center
        ray1_local = self._ray1_point - self._calculated_center
        ray2_local = self._ray2_point - self._calculated_center
        sc = math.sin(math.pi/4)
        datum_local = QPointF(self._radius * sc, self._radius * sc)
 
        # Datums must persist between calls to _get_control_points()
        if not self._radius_datum:
            self._radius_datum = ControlDatum(
                name="radius",
                position=datum_local,
                value_getter=self._get_radius_value,
                value_setter=self._set_radius_value,
                prefix="R",
                parent_item=self
            )
        else:
            self._radius_datum.position = datum_local

        control_points = [
            SquareControlPoint('corner', corner_local),
            ControlPoint('ray1', ray1_local),
            ControlPoint('ray2', ray2_local),
            SquareControlPoint('center', QPointF(0, 0)),
            self._radius_datum
        ]
        return control_points
    
    def _boundingRect(self):
        """Return the bounding rectangle of the circle."""
        if not self._is_valid or self._radius <= 0:
            # Fallback to bounding box of all points
            center = self._calculated_center
            
            # Create a CadRect containing all points in local coordinates
            rect = CadRect()
            rect.expandToPoint(self._corner_point - center)
            rect.expandToPoint(self._ray1_point - center)
            rect.expandToPoint(self._ray2_point - center)
            rect.expandToPoint(self._center_point - center)
            
            # Add padding for line width
            rect.expandByScalar(self._line_width / 2)
            
            return rect
        
        # For valid circles, use radius
        radius = self._radius
        
        # Create a CadRect centered at origin with the circle's diameter
        rect = CadRect(-radius, -radius, 2 * radius, 2 * radius)
        
        # Add padding for line width
        rect.expandByScalar(self._line_width / 2)
        
        return rect
    
    def _shape(self):
        """Return the exact shape of the circle for collision detection."""
        if not self._is_valid or self._radius <= 0:
            # Return empty path for invalid circles
            return QPainterPath()
        
        radius = self._radius
        
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
        if not self._is_valid:
            return False
        
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
        """Draw the circle and construction lines."""
        painter.save()
        
        pen = QPen(self._color, self._line_width)
        painter.setPen(pen)
        
        if self._is_valid and self._radius > 0:
            # Draw the circle
            radius = self._radius
            rect = QRectF(-radius, -radius, 2*radius, 2*radius)
            painter.drawEllipse(rect)
            
            # Draw construction lines (rays) with lighter color when selected
        else:
            # Draw construction points for invalid geometry
            construction_pen = QPen(QColor(255, 0, 0), self._line_width)
            construction_pen.setStyle(Qt.PenStyle.DashDotLine)
            painter.setPen(construction_pen)
            
            # Convert points to local coordinates
            corner_local = self._corner_point - self._calculated_center
            ray1_local = self._ray1_point - self._calculated_center
            ray2_local = self._ray2_point - self._calculated_center
            center_spec_local = self._center_point - self._calculated_center
            
            # Draw lines to show the invalid configuration
            painter.drawLine(corner_local, ray1_local)
            painter.drawLine(corner_local, ray2_local)
            painter.drawLine(corner_local, center_spec_local)

        painter.restore()
    
    def _create_decorations(self):
        """Create decoration items for this circle."""
        if self._is_valid and self._radius > 0:
            # Add centerlines
            self._add_centerlines(QPointF(0, 0))
            
            # Add dashed rays from corner
            corner_local = self._corner_point - self._calculated_center
            ray1_local = self._ray1_point - self._calculated_center
            ray2_local = self._ray2_point - self._calculated_center
            center_spec_local = self._center_point - self._calculated_center
            
            self._add_dashed_lines([
                (corner_local, ray1_local),
                (corner_local, ray2_local),
                (corner_local, center_spec_local)
            ])

    @property
    def center_point(self):
        """Get the calculated center point of the circle."""
        return QPointF(self._calculated_center)
    
    @property
    def radius(self):
        """Get the radius of the circle (0 for invalid circles)."""
        return self._radius if self._is_valid else 0
    
    @property
    def is_valid(self):
        """Check if the circle configuration is valid."""
        return self._is_valid
    
    @property
    def corner_point(self):
        return QPointF(self._corner_point)
    
    @corner_point.setter
    def corner_point(self, value):
        if isinstance(value, (list, tuple)):
            value = QPointF(value[0], value[1])
        self._corner_point = value
        self._calculate_circle()
        self.setPos(self._calculated_center)
        self.prepareGeometryChange()
        self.update()

    @property
    def ray1_point(self):
        return QPointF(self._ray1_point)
    
    @ray1_point.setter
    def ray1_point(self, value):
        if isinstance(value, (list, tuple)):
            value = QPointF(value[0], value[1])
        self._ray1_point = value
        self._calculate_circle()
        self.setPos(self._calculated_center)
        self.prepareGeometryChange()
        self.update()

    @property
    def ray2_point(self):
        return QPointF(self._ray2_point)
    
    @ray2_point.setter
    def ray2_point(self, value):
        if isinstance(value, (list, tuple)):
            value = QPointF(value[0], value[1])
        self._ray2_point = value
        self._calculate_circle()
        self.setPos(self._calculated_center)
        self.prepareGeometryChange()
        self.update()

    @property
    def center_spec_point(self):
        return QPointF(self._center_point)
    
    @center_spec_point.setter
    def center_spec_point(self, value):
        if isinstance(value, (list, tuple)):
            value = QPointF(value[0], value[1])
        self._center_point = value
        self._calculate_circle(update_center_spec=False)  # Don't update center_spec when it's being explicitly set
        self.setPos(self._calculated_center)
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
        local_pos = self.mapToScene(new_position)
        
        if name == 'center' and self._is_valid:
            # Constrain center movement to the angle bisector
            self._move_center_along_bisector(local_pos)
        elif name == 'corner':
            # When corner moves, recalculate and update center spec point
            self._corner_point = local_pos
            self._calculate_circle(update_center_spec=True)
            self.setPos(self._calculated_center)
            self.prepareGeometryChange()
            self.update()
        elif name == 'ray1':
            # When ray1 moves, preserve radius and adjust center to maintain tangency
            if self._is_valid and self._radius > 0:
                self._ray1_point = local_pos
                self._adjust_center_for_ray_change()
            else:
                # For invalid circles, just update the ray and recalculate
                self._ray1_point = local_pos
                self._calculate_circle(update_center_spec=True)
            self.setPos(self._calculated_center)
            self.prepareGeometryChange()
            self.update()
        elif name == 'ray2':
            # When ray2 moves, preserve radius and adjust center to maintain tangency
            if self._is_valid and self._radius > 0:
                self._ray2_point = local_pos
                self._adjust_center_for_ray_change()
            else:
                # For invalid circles, just update the ray and recalculate
                self._ray2_point = local_pos
                self._calculate_circle(update_center_spec=True)
            self.setPos(self._calculated_center)
            self.prepareGeometryChange()
            self.update()
        
        # Call parent method to refresh all control points
        super()._control_point_changed(name, new_position)

    def set_points(self, corner_point, ray1_point, ray2_point, center_point):
        """Set all four points at once."""
        if isinstance(corner_point, (list, tuple)):
            corner_point = QPointF(corner_point[0], corner_point[1])
        if isinstance(ray1_point, (list, tuple)):
            ray1_point = QPointF(ray1_point[0], ray1_point[1])
        if isinstance(ray2_point, (list, tuple)):
            ray2_point = QPointF(ray2_point[0], ray2_point[1])
        if isinstance(center_point, (list, tuple)):
            center_point = QPointF(center_point[0], center_point[1])
        
        self._corner_point = corner_point
        self._ray1_point = ray1_point
        self._ray2_point = ray2_point
        self._center_point = center_point
        self._calculate_circle()
        self.setPos(self._calculated_center)
        self.prepareGeometryChange()
        self.update() 