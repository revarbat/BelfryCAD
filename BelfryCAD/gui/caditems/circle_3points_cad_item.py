"""
Circle3PointsCadItem - A circle CAD item defined by three points on the perimeter.
If the three points are collinear, it draws a line instead.
"""

import math
from typing import List, Optional
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainterPathStroker, Qt
from BelfryCAD.gui.cad_item import CadItem
from BelfryCAD.gui.control_points import ControlPoint, SquareControlPoint, ControlDatum
from BelfryCAD.gui.cad_rect import CadRect


class Circle3PointsCadItem(CadItem):
    """A circle CAD item defined by three points on the perimeter."""

    def __init__(self, point1=None, point2=None, point3=None, color=QColor(255, 0, 0), line_width=0.05):
        self._point1 = point1 if point1 is not None else QPointF(-1, 0)
        self._point2 = point2 if point2 is not None else QPointF(0, 1)
        self._point3 = point3 if point3 is not None else QPointF(1, 0)
        self._color = color
        self._line_width = line_width
        self._point1_cp = None
        self._point2_cp = None
        self._point3_cp = None
        self._center_cp = None
        self._radius_datum = None

        # Convert points to QPointF if they aren't already
        if isinstance(self._point1, (list, tuple)):
            self._point1 = QPointF(self._point1[0], self._point1[1])
        if isinstance(self._point2, (list, tuple)):
            self._point2 = QPointF(self._point2[0], self._point2[1])
        if isinstance(self._point3, (list, tuple)):
            self._point3 = QPointF(self._point3[0], self._point3[1])

        # Calculate circle properties
        self._calculate_circle()

        super().__init__()

        # Position the item at the center point (or midpoint for lines)
        if self.is_line:
            # For lines, position at midpoint of first and last points
            midpoint = QPointF(
                (self._point1.x() + self._point3.x()) / 2,
                (self._point1.y() + self._point3.y()) / 2
            )
            self.setPos(midpoint)
        else:
            self.setPos(self._center)

    def _calculate_circle(self):
        """Calculate center and radius from three points, or determine if it's a line."""
        p1, p2, p3 = self._point1, self._point2, self._point3

        # Check if points are collinear using cross product
        # For three points A, B, C, they are collinear if: (B-A) × (C-A) = 0
        vec1 = QPointF(p2.x() - p1.x(), p2.y() - p1.y())
        vec2 = QPointF(p3.x() - p1.x(), p3.y() - p1.y())
        cross_product = vec1.x() * vec2.y() - vec1.y() * vec2.x()

        if abs(cross_product) < 1e-6:
            # Points are collinear - this becomes a line
            self._is_line = True
            self._center = QPointF(0, 0)
            self._radius = 0
            return

        self._is_line = False

        # Calculate center using perpendicular bisector method
        # Midpoints of two chords
        mx1 = (p1.x() + p2.x()) / 2.0
        my1 = (p1.y() + p2.y()) / 2.0
        mx2 = (p2.x() + p3.x()) / 2.0
        my2 = (p2.y() + p3.y()) / 2.0

        # Handle special cases where segments are horizontal/vertical
        if abs(p2.y() - p1.y()) < 1e-6:
            # First segment is horizontal, second bisector is vertical
            if abs(p3.y() - p2.y()) < 1e-6:
                # Both segments horizontal - this shouldn't happen for valid circles
                self._is_line = True
                self._center = QPointF(0, 0)
                self._radius = 0
                return
            m2 = -(p3.x() - p2.x()) / (p3.y() - p2.y())
            c2 = my2 - m2 * mx2
            cx = mx1
            cy = m2 * cx + c2
        elif abs(p3.y() - p2.y()) < 1e-6:
            # Second segment is horizontal, first bisector is vertical
            m1 = -(p2.x() - p1.x()) / (p2.y() - p1.y())
            c1 = my1 - m1 * mx1
            cx = mx2
            cy = m1 * cx + c1
        else:
            # General case - neither segment is horizontal
            m1 = -(p2.x() - p1.x()) / (p2.y() - p1.y())
            m2 = -(p3.x() - p2.x()) / (p3.y() - p2.y())

            if abs(m1 - m2) < 1e-6:
                # Perpendicular bisectors are parallel - points are collinear
                self._is_line = True
                self._center = QPointF(0, 0)
                self._radius = 0
                return

            c1 = my1 - m1 * mx1
            c2 = my2 - m2 * mx2
            cx = (c2 - c1) / (m1 - m2)
            cy = m1 * cx + c1

        self._center = QPointF(cx, cy)

        # Calculate radius as distance from center to any point
        dx = p1.x() - cx
        dy = p1.y() - cy
        self._radius = math.sqrt(dx * dx + dy * dy)

    def boundingRect(self):
        """Return the bounding rectangle of the circle or line."""
        if self.is_line:
            # For lines, get bounding box of all three points
            midpoint = self._get_midpoint()

            # Create a CadRect containing all three points in local coordinates
            rect = CadRect()
            rect.expandToPoint(self._point1 - midpoint)
            rect.expandToPoint(self._point2 - midpoint)
            rect.expandToPoint(self._point3 - midpoint)

            # Add padding for line width
            rect.expandByScalar(self._line_width / 2)

            return rect
        else:
            # For circles, use radius
            radius = self._radius

            # Create a CadRect centered at origin with the circle's diameter
            rect = CadRect(-radius, -radius, 2 * radius, 2 * radius)

            # Add padding for line width
            rect.expandByScalar(self._line_width / 2)

            return rect

    def shape(self):
        """Return the exact shape of the circle or line for collision detection."""
        if self.is_line:
            # Create a line path from point1 to point3
            midpoint = self._get_midpoint()

            # Convert to local coordinates
            start_local = self._point1 - midpoint
            end_local = self._point3 - midpoint

            path = QPainterPath()
            path.moveTo(start_local)
            path.lineTo(end_local)

            # Create a stroked path with the line width for better selection
            stroker = QPainterPathStroker()
            stroker.setWidth(max(self._line_width, 0.1))  # Minimum width for selection
            stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
            stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

            return stroker.createStroke(path)
        else:
            # For circles, create a proper ellipse path
            radius = self._radius

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
        """Check if a point is inside the circle or near the line."""
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
        # Create control points with direct setters
        self._point1_cp = ControlPoint(
            cad_item=self,
            setter=self._set_point1
        )
        self._point2_cp = ControlPoint(
            cad_item=self,
            setter=self._set_point2
        )
        self._point3_cp = ControlPoint(
            cad_item=self,
            setter=self._set_point3
        )
        
        cps = [self._point1_cp, self._point2_cp, self._point3_cp]
        
        if not self._is_line:
            self._center_cp = SquareControlPoint(
                cad_item=self,
                setter=self._set_center
            )
            self._radius_datum = ControlDatum(
                setter=self._set_radius_value,
                prefix="R",
                cad_item=self
            )
            cps.extend([self._center_cp, self._radius_datum])
        
        self.updateControls()
        
        # Return the list of control points
        return cps

    def updateControls(self):
        """Update control point positions and values."""
        if hasattr(self, '_point1_cp') and self._point1_cp:
            self._point1_cp.setPos(self._point1)
        
        if hasattr(self, '_point2_cp') and self._point2_cp:
            self._point2_cp.setPos(self._point2)
        
        if hasattr(self, '_point3_cp') and self._point3_cp:
            self._point3_cp.setPos(self._point3)
        
        if not self._is_line:
            if hasattr(self, '_center_cp') and self._center_cp:
                self._center_cp.setPos(self.center_point)  # Center is always at origin in local coordinates
            if hasattr(self, '_radius_datum') and self._radius_datum:
                # Update both position and value for the datum
                radius_value = self._get_radius_value()
                radius_position = self._get_radius_datum_position()
                self._radius_datum.update_datum(radius_value, radius_position)

    def getControlPoints(self, exclude_cps: Optional[List['ControlPoint']] = None) -> List[QPointF]:
        """Return list of control point positions (excluding ControlDatums)."""
        out = []
        for cp in [self._point1_cp, self._point2_cp, self._point3_cp]:
            if cp and (exclude_cps is None or cp not in exclude_cps):
                out.append(cp.pos())
        if not self._is_line and self._center_cp is not None:
            if exclude_cps is None or self._center_cp not in exclude_cps:
                out.append(self.center_point)
        return out
    
    def _get_control_point_objects(self) -> List['ControlPoint']:
        """Get the list of ControlPoint objects for this CAD item."""
        cps = [self._point1_cp, self._point2_cp, self._point3_cp]
        if not self._is_line:
            cps.append(self._center_cp)
        return [x for x in cps if x]

    def _set_point1(self, new_position):
        """Set point1 from control point movement."""
        self.point1 = new_position
        
    def _set_point2(self, new_position):
        """Set point2 from control point movement."""
        self.point2 = new_position
        
    def _set_point3(self, new_position):
        """Set point3 from control point movement."""
        self.point3 = new_position
        
    def _set_center(self, new_position):
        """Set center from control point movement."""
        if not self.is_line:
            # Translate the entire circle (all three points)
            # Calculate the delta from current center (which is at origin in local coords)
            scene_delta = new_position - self._center
            self._point1 += scene_delta
            self._point2 += scene_delta
            self._point3 += scene_delta
            self._center += scene_delta
            self.setPos(self.center_point)
        
    def _get_radius_datum_position(self) -> QPointF:
        """Get the position for the radius datum."""
        if self.is_line:
            return self._point1  # No radius datum for lines
        sc = math.sin(math.pi/4)
        return QPointF(self._radius * sc, self._radius * sc) + self._center

    def _get_radius_value(self):
        """Get the current radius value."""
        return self.radius

    def _set_radius_value(self, new_radius):
        """Set the radius value by adjusting the third point."""
        if self.is_line or new_radius <= 0:
            return

        # Calculate new position for point3 to achieve the desired radius
        # Keep point1 and point2 fixed, adjust point3
        center = self._center
        point1_vec = self._point1 - center
        point2_vec = self._point2 - center

        # Calculate the angle of point3 (average of point1 and point2 angles)
        angle1 = math.atan2(point1_vec.y(), point1_vec.x())
        angle2 = math.atan2(point2_vec.y(), point2_vec.x())

        # Use the angle that's 120 degrees from the average
        avg_angle = (angle1 + angle2) / 2
        point3_angle = avg_angle + math.pi * 2 / 3  # 120 degrees

        # Calculate new point3 position
        new_point3 = QPointF(
            center.x() + new_radius * math.cos(point3_angle),
            center.y() + new_radius * math.sin(point3_angle)
        )

        self._point3 = new_point3
        self._calculate_circle()
        self.setPos(self._center)

    def _get_midpoint(self):
        """Get the midpoint between point1 and point3."""
        return QPointF(
            (self._point1.x() + self._point3.x()) / 2,
            (self._point1.y() + self._point3.y()) / 2
        )

    def paint_item(self, painter, option, widget=None):
        """Draw the circle or line content."""
        painter.save()

        pen = QPen(self._color, self._line_width)
        painter.setPen(pen)

        if self.is_line:
            # Draw a line from point1 to point3
            midpoint = self._get_midpoint()

            # Convert to local coordinates
            start_local = self._point1 - midpoint
            end_local = self._point3 - midpoint

            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(start_local, end_local)
        else:
            # Draw the circle
            radius = self._radius
            rect = QRectF(-radius, -radius, 2*radius, 2*radius)
            painter.drawEllipse(rect)

        painter.restore()

    def _create_decorations(self):
        """Create decoration items for this circle or line."""
        if not self.is_line:
            # Add centerlines for valid circles
            self._add_centerlines(QPointF(0, 0))

    @property
    def center_point(self):
        """Get the center point of the circle (or midpoint for lines)."""
        if self.is_line:
            return self._get_midpoint()
        else:
            return QPointF(self._center)

    @property
    def radius(self):
        """Get the radius of the circle (0 for lines)."""
        return self._radius if not self.is_line else 0

    @property
    def is_line(self):
        """Check if the three points are collinear (making this a line)."""
        return self._is_line

    @property
    def point1(self):
        return QPointF(self._point1)

    @point1.setter
    def point1(self, value):
        if isinstance(value, (list, tuple)):
            value = QPointF(value[0], value[1])
        self._point1 = value
        self._calculate_circle()
        self.setPos(self.center_point)
        self.prepareGeometryChange()
        self.update()

    @property
    def point2(self):
        return QPointF(self._point2)

    @point2.setter
    def point2(self, value):
        if isinstance(value, (list, tuple)):
            value = QPointF(value[0], value[1])
        self._point2 = value
        self._calculate_circle()
        self.setPos(self.center_point)
        self.prepareGeometryChange()
        self.update()

    @property
    def point3(self):
        return QPointF(self._point3)

    @point3.setter
    def point3(self, value):
        if isinstance(value, (list, tuple)):
            value = QPointF(value[0], value[1])
        self._point3 = value
        self._calculate_circle()
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

    def moveBy(self, dx, dy):
        """Move all three points by the specified offset."""
        self.prepareGeometryChange()
        self._point1 = QPointF(self._point1.x() + dx, self._point1.y() + dy)
        self._point2 = QPointF(self._point2.x() + dx, self._point2.y() + dy)
        self._point3 = QPointF(self._point3.x() + dx, self._point3.y() + dy)
        self.update()