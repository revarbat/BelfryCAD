"""
ArcCornerCadItem - An arc CAD item defined by a corner point and two tangent rays.
The arc is drawn between the tangent points where a circle would touch the rays.
"""

import math
from typing import List, Optional
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainterPathStroker, Qt
from BelfryCAD.gui.cad_item import CadItem
from BelfryCAD.gui.control_points import (
    ControlPoint, SquareControlPoint, ControlDatum, DiamondControlPoint
)
from BelfryCAD.gui.cad_rect import CadRect


class ArcCornerCadItem(CadItem):
    """An arc CAD item defined by corner point, two ray points, and center point."""

    def __init__(self, corner_point=None, ray1_point=None, ray2_point=None, center_point=None,
                 color=QColor(255, 0, 0), line_width=0.05):
        self._corner_point = corner_point if corner_point is not None else QPointF(0, 0)
        self._ray1_point = ray1_point if ray1_point is not None else QPointF(1, 0)
        self._ray2_point = ray2_point if ray2_point is not None else QPointF(0, 1)
        self._center_point = center_point if center_point is not None else QPointF(0.5, 0.5)
        self._color = color
        self._line_width = line_width
        self._corner_cp = None
        self._ray1_cp = None
        self._ray2_cp = None
        self._center_cp = None
        self._radius_datum = None

        # Convert points to QPointF if they aren't already
        if isinstance(self._corner_point, (list, tuple)):
            self._corner_point = QPointF(self._corner_point[0], self._corner_point[1])
        if isinstance(self._ray1_point, (list, tuple)):
            self._ray1_point = QPointF(self._ray1_point[0], self._ray1_point[1])
        if isinstance(self._ray2_point, (list, tuple)):
            self._ray2_point = QPointF(self._ray2_point[0], self._ray2_point[1])
        if isinstance(self._center_point, (list, tuple)):
            self._center_point = QPointF(self._center_point[0], self._center_point[1])

        # Calculate arc properties
        self._calculate_arc()

        super().__init__()

        # Position the item at the calculated center
        self.setPos(self._calculated_center)

    def boundingRect(self):
        """Return the bounding rectangle of the arc."""
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

        # For valid arcs, use arc bounding box
        # Convert tangent points to local coordinates (relative to arc center)
        t1_local = self._tangent_point1 - self._calculated_center
        t2_local = self._tangent_point2 - self._calculated_center

        # Calculate angles from center to tangent points
        start_angle = math.atan2(t1_local.y(), t1_local.x())
        end_angle = math.atan2(t2_local.y(), t2_local.x())

        # Create a CadRect and expand it to include the arc
        rect = CadRect()
        rect.expandWithArc(QPointF(0, 0), self._radius, start_angle, end_angle)

        # Add padding for line width
        rect.expandByScalar(self._line_width / 2)

        return rect

    def shape(self):
        """Return the exact shape of the arc for collision detection."""
        if not self._is_valid or self._radius <= 0:
            # Return empty path for invalid arcs
            return QPainterPath()

        path = self._create_arc_path()

        # Use QPainterPathStroker to create a stroked path with line width
        stroker = QPainterPathStroker()
        stroker.setWidth(max(self._line_width, 0.01))  # Minimum width for selection
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

        return stroker.createStroke(path)

    def contains(self, point):
        """Check if a point is near the arc."""
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
        """Create control points for the arc and return them."""
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
        self._center_cp = DiamondControlPoint(
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
        if hasattr(self, '_corner_cp') and self._corner_cp:
            self._corner_cp.setPos(self._corner_point)
        if hasattr(self, '_ray1_cp') and self._ray1_cp:
            self._ray1_cp.setPos(self._ray1_point)
        if hasattr(self, '_ray2_cp') and self._ray2_cp:
            self._ray2_cp.setPos(self._ray2_point)
        if hasattr(self, '_center_cp') and self._center_cp:
            self._center_cp.setPos(self._center_point)
        if not self._is_valid:
            return
        if hasattr(self, '_radius_datum') and self._radius_datum:
            # Update both position and value for the datum
            radius_value = self._get_radius_value()
            radius_position = self._get_radius_datum_position()
            self._radius_datum.update_datum(radius_value, radius_position)

    def getControlPoints(self, exclude_cps: Optional[List['ControlPoint']] = None) -> List[QPointF]:
        """Return list of control point positions (excluding ControlDatums)."""
        out = []
        for cp in [self._corner_cp, self._ray1_cp, self._ray2_cp, self._center_cp]:
            if cp and (exclude_cps is None or cp not in exclude_cps):
                out.append(cp.pos())
        return out

    def _set_corner(self, new_position):
        """Set corner point from control point movement."""
        # When corner moves, recalculate and update center spec point
        delta = new_position - self._corner_point
        self._corner_point = new_position
        self._ray1_point += delta
        self._ray2_point += delta
        self._center_point += delta
        self._calculate_arc(update_center_spec=True)
        self.setPos(self._calculated_center)
        
    def _set_ray1(self, new_position):
        """Set ray1 point from control point movement."""
        # When ray1 moves, recalculate and update center spec point
        self._ray1_point = new_position
        self._calculate_arc(update_center_spec=True)
        self.setPos(self._calculated_center)
        
    def _set_ray2(self, new_position):
        """Set ray2 point from control point movement."""
        # When ray2 moves, recalculate and update center spec point
        self._ray2_point = new_position
        self._calculate_arc(update_center_spec=True)
        self.setPos(self._calculated_center)
        
    def _set_center(self, new_position):
        """Set center from control point movement."""
        # Constrain center movement to the angle bisector
        self._move_center_along_bisector(new_position)
        
    def _get_radius_datum_position(self) -> QPointF:
        """Get the position for the radius datum."""
        if not self._is_valid:
            return self._corner_point
        sc = math.sin(math.pi/4)
        return QPointF(self._radius * sc, self._radius * sc) + self._calculated_center

    def _get_radius_value(self):
        """Get the current radius value."""
        return self.radius

    def _set_radius_value(self, new_radius):
        """Set the radius value."""
        if new_radius > 0:
            # Use the same logic as circle corner item
            self._set_radius(new_radius)

    def paint_item(self, painter, option, widget=None):
        """Draw the arc and construction lines."""
        painter.save()

        pen = QPen(self._color, self._line_width)
        painter.setPen(pen)

        # Convert points to local coordinates
        corner_local = self._corner_point - self._calculated_center
        ray1_local = self._ray1_point - self._calculated_center
        ray2_local = self._ray2_point - self._calculated_center

        if self._is_valid and self._radius > 0:
            # Draw the arc
            arc_path = self._create_arc_path()
            painter.drawPath(arc_path)
        else:
            # Draw construction points for invalid geometry
            construction_pen = QPen(QColor(255, 0, 0), self._line_width)
            construction_pen.setStyle(Qt.PenStyle.DashDotLine)
            painter.setPen(construction_pen)

            # Draw lines to show the invalid configuration
            painter.drawLine(corner_local, ray1_local)
            painter.drawLine(corner_local, ray2_local)

        if self.isSelected():
            pen = QPen(QColor(127, 127, 127), 3.0)
            pen.setCosmetic(True)
            pen.setDashPattern([2.0, 2.0])
            painter.setPen(pen)
            center_local = self._center_point - self._calculated_center
            painter.drawLine(corner_local, ray1_local)
            painter.drawLine(corner_local, ray2_local)
            painter.drawLine(corner_local, center_local)

            if self._is_valid:
                # Calculate ray vectors from corner
                ray1_vec = self._ray1_point - self._corner_point
                ray2_vec = self._ray2_point - self._corner_point

                # Normalize ray vectors
                ray1_len = math.sqrt(ray1_vec.x() ** 2 + ray1_vec.y() ** 2)
                ray2_len = math.sqrt(ray2_vec.x() ** 2 + ray2_vec.y() ** 2)

                ray1_unit = QPointF(ray1_vec.x() / ray1_len, ray1_vec.y() / ray1_len)
                ray2_unit = QPointF(ray2_vec.x() / ray2_len, ray2_vec.y() / ray2_len)

                tang_point1 = self._find_tangent_point(self._corner_point, ray1_unit) - self._center_point
                tang_point2 = self._find_tangent_point(self._corner_point, ray2_unit) - self._center_point

                painter.drawLine(tang_point1, QPointF(0, 0))
                painter.drawLine(tang_point2, QPointF(0, 0))
                rect = QRectF(-self.radius,-self.radius, 2 * self._radius, 2 * self._radius)
                painter.drawEllipse(rect)

        painter.restore()

    def _calculate_arc(self, update_center_spec=True):
        """Calculate the arc center, radius, and tangent points from the four defining points."""
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
            # Rays are parallel - no valid arc
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
        self._radius = self._point_to_ray_distance(
            self._calculated_center, corner, ray1_unit
        )

        # Calculate tangent points
        self._tangent_point1 = self._find_tangent_point(corner, ray1_unit)
        self._tangent_point2 = self._find_tangent_point(corner, ray2_unit)

        # Calculate arc angles
        self._start_angle = math.atan2(
            self._tangent_point1.y() - self._calculated_center.y(),
            self._tangent_point1.x() - self._calculated_center.x()
        )
        self._end_angle = math.atan2(
            self._tangent_point2.y() - self._calculated_center.y(),
            self._tangent_point2.x() - self._calculated_center.x()
        )

        self._ray1_point = self._tangent_point1
        self._ray2_point = self._tangent_point2
        
        # Determine the shorter arc direction
        angle_diff = self._end_angle - self._start_angle
        if angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        elif angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        # Store the span angle (always positive)
        self._span_angle = abs(angle_diff)

        # Update the center specification point to match the calculated center
        # (unless we're being called because the center_spec itself moved)
        if update_center_spec:
            self._center_point = QPointF(self._calculated_center)

        self._is_valid = True

    def _find_tangent_point(self, ray_start, ray_direction):
        """Find the tangent point where the circle touches a ray."""
        # The tangent point is the point on the ray closest to the circle center
        # Vector from ray start to circle center
        to_center = QPointF(self._calculated_center.x() - ray_start.x(),
                           self._calculated_center.y() - ray_start.y())

        # Project onto ray direction to find the closest point
        projection = (to_center.x() * ray_direction.x() +
                     to_center.y() * ray_direction.y())

        # The tangent point
        tangent_point = QPointF(
            ray_start.x() + projection * ray_direction.x(),
            ray_start.y() + projection * ray_direction.y()
        )

        return tangent_point

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
        if projection_length <= 0:
            return  # Don't allow center behind the corner

        # Calculate the projected position on the bisector
        projected_center = QPointF(
            corner.x() + projection_length * bisector_unit.x(),
            corner.y() + projection_length * bisector_unit.y()
        )

        # Update the center specification point to the projected position
        self._center_point = projected_center
        self._calculate_arc(update_center_spec=False)
        self.setPos(self._calculated_center)
        self.prepareGeometryChange()
        self.update()

    def _create_arc_path(self):
        """Create the arc path for drawing."""
        path = QPainterPath()

        if not self._is_valid or self._radius <= 0:
            return path

        # Convert tangent points to local coordinates (relative to arc center)
        t1_local = self._tangent_point1 - self._calculated_center
        t2_local = self._tangent_point2 - self._calculated_center

        # Calculate angles from center to tangent points
        angle1 = math.atan2(t1_local.y(), t1_local.x())
        angle2 = math.atan2(t2_local.y(), t2_local.x())

        # Convert to degrees for Qt
        # Qt's arcTo assumes 0° is at 9 o'clock (negative X), but atan2 gives 0° at 3 o'clock (positive X)
        # So we need to add 180° to convert from standard math angles to Qt's expected angles
        angle1_deg = math.degrees(angle1)
        angle2_deg = math.degrees(angle2)

        # Calculate both possible sweep angles
        sweep_ccw = angle2_deg - angle1_deg
        sweep_cw = angle1_deg - angle2_deg

        # Normalize both to [0, 360)
        while sweep_ccw < 0:
            sweep_ccw += 360
        while sweep_ccw >= 360:
            sweep_ccw -= 360

        while sweep_cw < 0:
            sweep_cw += 360
        while sweep_cw >= 360:
            sweep_cw -= 360

        # Choose the smaller arc (the one that's less than 180 degrees)
        if sweep_ccw <= 180:
            # Use counter-clockwise sweep
            sweep_angle = sweep_ccw
        else:
            # Use clockwise sweep (negative angle for Qt)
            sweep_angle = -sweep_cw

        # Create the arc
        radius = self._radius
        rect = QRectF(-radius, -radius, 2 * radius, 2 * radius)

        # Draw the arc with the chosen sweep
        path.arcMoveTo(rect, -angle1_deg)
        path.arcTo(rect, -angle1_deg, -sweep_angle)

        return path

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
        self._calculate_arc()
        self.setPos(self._calculated_center)
        self.prepareGeometryChange()
        self.update()

    @property
    def center_point(self):
        """Get the calculated center point of the arc."""
        return QPointF(self._calculated_center)

    @property
    def radius(self):
        """Get the radius of the arc (0 for invalid arcs)."""
        return self._radius if self._is_valid else 0

    @property
    def is_valid(self):
        """Check if the arc configuration is valid."""
        return self._is_valid

    @property
    def tangent_point1(self):
        """Get the first tangent point."""
        return QPointF(self._tangent_point1) if self._is_valid else QPointF()

    @property
    def tangent_point2(self):
        """Get the second tangent point."""
        return QPointF(self._tangent_point2) if self._is_valid else QPointF()

    @property
    def corner_point(self):
        return QPointF(self._corner_point)

    @corner_point.setter
    def corner_point(self, value):
        if isinstance(value, (list, tuple)):
            value = QPointF(value[0], value[1])
        self._corner_point = value
        self._calculate_arc()
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
        self._calculate_arc()
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
        self._calculate_arc()
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
        self._calculate_arc(update_center_spec=False)  # Don't update center_spec when it's being explicitly set
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
        # For an arc tangent to two rays, the distance from corner to center
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
        self._calculate_arc(update_center_spec=False)
        self.setPos(self._calculated_center)
        self.prepareGeometryChange()
        self.update()

    def moveBy(self, dx, dy):
        """Move all defining points by the specified offset."""
        self.prepareGeometryChange()
        self._corner_point = QPointF(self._corner_point.x() + dx, self._corner_point.y() + dy)
        self._ray1_point = QPointF(self._ray1_point.x() + dx, self._ray1_point.y() + dy)
        self._ray2_point = QPointF(self._ray2_point.x() + dx, self._ray2_point.y() + dy)
        self._center_spec_point = QPointF(self._center_spec_point.x() + dx, self._center_spec_point.y() + dy)
        self.update()