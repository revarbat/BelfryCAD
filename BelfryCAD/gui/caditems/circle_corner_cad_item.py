"""
CircleCornerCadItem - A circle CAD item defined by a corner point and two tangent rays.
The circle is tangent to both rays, with center specified by a point on the angle bisector.
"""

import math
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainterPathStroker
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

    def boundingRect(self):
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

        # For valid circles, use circle bounding box
        radius = self._radius
        rect = CadRect(-radius, -radius, 2 * radius, 2 * radius)

        # Add padding for line width
        rect.expandByScalar(self._line_width / 2)

        return rect

    def shape(self):
        """Return the exact shape of the circle for collision detection."""
        if not self._is_valid or self._radius <= 0:
            # Return empty path for invalid circles
            return QPainterPath()

        path = QPainterPath()
        path.addEllipse(QPointF(0, 0), self._radius, self._radius)

        # Use QPainterPathStroker to create a stroked path with line width
        stroker = QPainterPathStroker()
        stroker.setWidth(max(self._line_width, 0.01))  # Minimum width for selection
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

        return stroker.createStroke(path)

    def contains(self, point):
        """Check if a point is near the circle."""
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
        shape_path = self.shape()
        return shape_path.contains(local_point)

    def createControls(self):
        """Create control points for the circle and return them."""
        if not self._is_valid:
            return []

        # Create control points with direct setters
        self._corner_cp = SquareControlPoint(
            cad_item=self,
            setter=self._set_corner
        )
        self._ray1_cp = ControlPoint(
            cad_item=self,
            setter=self._set_ray1
        )
        self._ray2_cp = ControlPoint(
            cad_item=self,
            setter=self._set_ray2
        )
        self._center_cp = SquareControlPoint(
            cad_item=self,
            setter=self._set_center
        )
        self._radius_datum = ControlDatum(
            setter=self._set_radius_value,
            prefix="R",
            cad_item=self
        )
        self.updateControls()
        
        # Return the list of control points
        return [self._corner_cp, self._ray1_cp, self._ray2_cp, self._center_cp, self._radius_datum]

    def updateControls(self):
        """Update control point positions and values."""
        if not self._is_valid:
            return
            
        if hasattr(self, '_corner_cp') and self._corner_cp:
            self._corner_cp.setPos(self._corner_point - self._calculated_center)
        if hasattr(self, '_ray1_cp') and self._ray1_cp:
            self._ray1_cp.setPos(self._ray1_point - self._calculated_center)
        if hasattr(self, '_ray2_cp') and self._ray2_cp:
            self._ray2_cp.setPos(self._ray2_point - self._calculated_center)
        if hasattr(self, '_center_cp') and self._center_cp:
            self._center_cp.setPos(QPointF(0, 0))  # Center is always at origin in local coordinates
        if hasattr(self, '_radius_datum') and self._radius_datum:
            # Update both position and value for the datum
            radius_value = self._get_radius_value()
            radius_position = self._get_radius_datum_position()
            self._radius_datum.update_datum(radius_value, radius_position)

    def _set_corner(self, new_position):
        """Set corner point from control point movement."""
        # When corner moves, recalculate and update center spec point
        local_pos = self.mapToScene(new_position)
        self._corner_point = local_pos
        self._calculate_circle(update_center_spec=True)
        self.setPos(self._calculated_center)
        
    def _set_ray1(self, new_position):
        """Set ray1 point from control point movement."""
        # When ray1 moves, recalculate and update center spec point
        local_pos = self.mapToScene(new_position)
        self._ray1_point = local_pos
        self._calculate_circle(update_center_spec=True)
        self.setPos(self._calculated_center)
        
    def _set_ray2(self, new_position):
        """Set ray2 point from control point movement."""
        # When ray2 moves, recalculate and update center spec point
        local_pos = self.mapToScene(new_position)
        self._ray2_point = local_pos
        self._calculate_circle(update_center_spec=True)
        self.setPos(self._calculated_center)
        
    def _set_center(self, new_position):
        """Set center from control point movement."""
        # Constrain center movement to the angle bisector
        local_pos = self.mapToScene(new_position)
        self._move_center_along_bisector(local_pos)
        
    def _get_radius_datum_position(self) -> QPointF:
        """Get the position for the radius datum."""
        if not self._is_valid:
            return QPointF(0, 0)
        import math
        sc = math.sin(math.pi/4)
        return QPointF(self._radius * sc, self._radius * sc)

    def _get_radius_value(self):
        """Get the current radius value."""
        return self.radius

    def _set_radius_value(self, new_radius):
        """Set the radius value."""
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
        """Adjust the center point when rays change to maintain a reasonable radius."""
        if not self._is_valid:
            return

        # Calculate a reasonable radius based on the current configuration
        corner = self._corner_point
        ray1 = self._ray1_point
        ray2 = self._ray2_point

        # Calculate ray vectors
        ray1_vec = QPointF(ray1.x() - corner.x(), ray1.y() - corner.y())
        ray2_vec = QPointF(ray2.x() - corner.x(), ray2.y() - corner.y())

        ray1_len = math.sqrt(ray1_vec.x() ** 2 + ray1_vec.y() ** 2)
        ray2_len = math.sqrt(ray2_vec.x() ** 2 + ray2_vec.y() ** 2)

        if ray1_len < 1e-6 or ray2_len < 1e-6:
            return

        # Use the smaller of the two ray lengths as a reasonable radius
        reasonable_radius = min(ray1_len, ray2_len) * 0.3

        # Set the radius, which will adjust the center position
        self._set_radius(reasonable_radius)

    def _create_decorations(self):
        """Create decoration items for this circle."""
        if self._is_valid and self._radius > 0:
            # Add dashed circle outline
            self._add_dashed_circle(QPointF(0, 0), self._radius)

            # Add radius lines to tangent points
            corner_local = self._corner_point - self._calculated_center
            ray1_local = self._ray1_point - self._calculated_center
            ray2_local = self._ray2_point - self._calculated_center

            self._add_radius_lines(
                QPointF(0, 0),
                [corner_local, ray1_local, ray2_local]
            )

            # Add dashed rays from corner
            self._add_dashed_lines([
                (corner_local, ray1_local),
                (corner_local, ray2_local)
            ])

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

    def moveBy(self, dx, dy):
        """Move all defining points by the specified offset."""
        self.prepareGeometryChange()
        self._corner_point = QPointF(self._corner_point.x() + dx, self._corner_point.y() + dy)
        self._ray1_point = QPointF(self._ray1_point.x() + dx, self._ray1_point.y() + dy)
        self._ray2_point = QPointF(self._ray2_point.x() + dx, self._ray2_point.y() + dy)
        self._center_point = QPointF(self._center_point.x() + dx, self._center_point.y() + dy)
        self.update()