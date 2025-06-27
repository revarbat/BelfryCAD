"""
ArcCadItem - An arc CAD item defined by center point, start radius point, and end angle point.
"""

import math
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QBrush, QPainterPath, QPainterPathStroker, Qt
from BelfryCAD.gui.cad_item import CadItem
from BelfryCAD.gui.control_points import ControlPoint, SquareControlPoint, DiamondControlPoint, ControlDatum
from BelfryCAD.gui.cad_rect import CadRect


class ArcCadItem(CadItem):
    """An arc CAD item defined by center point, start radius point, and end angle point."""

    def __init__(self, center_point=None, start_point=None, end_point=None,
                 color=QColor(0, 0, 0), line_width=0.05):
        super().__init__()
        # Default to a quarter-circle arc if no points provided
        self._center_point = center_point if center_point else QPointF(0, 0)
        self._start_point = start_point if start_point else QPointF(1, 0)
        self._end_point = end_point if end_point else QPointF(0, 1)
        self._color = color
        self._line_width = line_width
        self._radius_datum = None

        # Convert points to QPointF if they aren't already
        if isinstance(self._center_point, (list, tuple)):
            self._center_point = QPointF(self._center_point[0], self._center_point[1])
        if isinstance(self._start_point, (list, tuple)):
            self._start_point = QPointF(self._start_point[0], self._start_point[1])
        if isinstance(self._end_point, (list, tuple)):
            self._end_point = QPointF(self._end_point[0], self._end_point[1])

    def boundingRect(self):
        """Return the bounding rectangle of the arc."""
        # Get the radius from center to start point
        radius = self._distance(self._center_point, self._start_point)

        # Calculate start and end angles
        start_angle = self._angle_from_center(self._start_point)
        end_angle = self._angle_from_center(self._end_point)

        # Normalize angles
        start_angle = self._normalize_angle(start_angle)
        end_angle = self._normalize_angle(end_angle)

        # Create a CadRect and expand it to include the arc
        rect = CadRect()
        rect.expandWithArc(self._center_point, radius, start_angle, end_angle)

        # Add padding for line width
        rect.expandByScalar(self._line_width / 2)

        return rect

    def shape(self):
        """Return the exact shape of the arc for collision detection."""
        path = self._create_arc_path()

        # Use QPainterPathStroker to create a stroked path with line width
        stroker = QPainterPathStroker()
        stroker.setWidth(max(self._line_width, 0.01))  # Minimum width for selection
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

        return stroker.createStroke(path)

    def contains(self, point):
        """Check if a point is near the arc."""
        # Convert point to local coordinates if needed
        if hasattr(point, 'x') and hasattr(point, 'y'):
            local_point = point
        else:
            local_point = self.mapFromScene(point)

        # Use the stroked shape for accurate contains check
        shape_path = self.shape()
        return shape_path.contains(local_point)

    def _get_control_points(self):
        """Return control points for the arc."""
        # Create radius datum if it doesn't exist
        if not self._radius_datum:
            sc = math.sin(math.pi/4)
            datum_pos = QPointF(self.radius * sc, self.radius * sc) + self._center_point
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
            datum_pos = QPointF(self.radius * sc, self.radius * sc) + self._center_point
            self._radius_datum.position = datum_pos

        return [
            SquareControlPoint('center', self._center_point),
            DiamondControlPoint('start', self._start_point),
            ControlPoint('end', self._end_point),
            self._radius_datum
        ]

    def _control_point_changed(self, name: str, new_position: QPointF):
        """Handle control point changes."""
        self.prepareGeometryChange()

        if name == 'center':
            # Moving center: translate start and end points by the same offset
            offset_x = new_position.x() - self._center_point.x()
            offset_y = new_position.y() - self._center_point.y()

            self._center_point = new_position
            self._start_point = QPointF(self._start_point.x() + offset_x,
                                       self._start_point.y() + offset_y)
            self._end_point = QPointF(self._end_point.x() + offset_x,
                                     self._end_point.y() + offset_y)

        elif name == 'start':
            # Moving start point: changes radius and start angle, preserves relative angle to end point
            # Calculate the current angular span between start and end points
            current_start_angle = self._angle_from_center(self._start_point)
            current_end_angle = self._angle_from_center(self._end_point)

            # Calculate the current span angle (counter-clockwise from start to end)
            span_angle = current_end_angle - current_start_angle
            if span_angle < 0:
                span_angle += 2 * math.pi

            # Calculate the new radius and start angle
            new_radius = self._distance(self._center_point, new_position)
            new_start_angle = self._angle_from_center(new_position)

            # Update start point
            self._start_point = new_position

            # Calculate new end angle by preserving the span
            new_end_angle = new_start_angle + span_angle

            # Position end point at the new angle with the new radius
            self._end_point = QPointF(
                self._center_point.x() + new_radius * math.cos(new_end_angle),
                self._center_point.y() + new_radius * math.sin(new_end_angle)
            )

        elif name == 'end':
            # Moving end point: changes end angle and adjusts start point radius to match
            # Calculate the new radius from center to end point
            new_radius = self._distance(self._center_point, new_position)

            # Calculate the current start angle
            start_angle = self._angle_from_center(self._start_point)

            # Update end point
            self._end_point = new_position

            # Adjust start point to have the same radius as the new end point
            # Account for flipped Y-axis: negate the sin component
            self._start_point = QPointF(
                self._center_point.x() + new_radius * math.cos(start_angle),
                self._center_point.y() + new_radius * math.sin(start_angle)
            )

        self.update()

    def paint_item(self, painter, option, widget=None):
        """Draw the arc content."""
        painter.save()

        pen = QPen(self._color, self._line_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(QBrush())  # No fill

        # Draw the arc
        arc_path = self._create_arc_path()
        painter.drawPath(arc_path)

        painter.restore()

    def _distance(self, point1, point2):
        """Calculate distance between two points."""
        dx = point2.x() - point1.x()
        dy = point2.y() - point1.y()
        return math.sqrt(dx * dx + dy * dy)

    def _angle_from_center(self, point):
        """Calculate angle from center to point in radians."""
        delta = point - self._center_point
        angle = math.atan2(delta.y(), delta.x())
        return angle

    def _normalize_angle(self, angle):
        """Normalize angle to [0, 2π) range."""
        while angle < 0:
            angle += 2 * math.pi
        while angle >= 2 * math.pi:
            angle -= 2 * math.pi
        return angle

    def _create_arc_path(self):
        """Create the arc path."""
        path = QPainterPath()

        # Calculate radius and angles
        radius = self._distance(self._center_point, self._start_point)
        start_angle = self._angle_from_center(self._start_point)
        end_angle = self._angle_from_center(self._end_point)

        # Convert to degrees for Qt (Qt uses degrees)
        start_degrees = math.degrees(start_angle)
        end_degrees = math.degrees(end_angle)

        # Calculate span angle (counter-clockwise in mathematical sense)
        span_degrees = end_degrees - start_degrees
        if span_degrees < 0:
            span_degrees += 360

        arc_rect = QRectF(
            self._center_point.x() - radius,
            self._center_point.y() - radius,
            2 * radius,
            2 * radius
        )
        path.arcMoveTo(arc_rect, -start_degrees)
        path.arcTo(arc_rect, -start_degrees, -span_degrees)

        return path

    def _get_radius_value(self):
        """Get the current radius value."""
        return self.radius

    def _set_radius_value(self, new_radius):
        """Set the radius value by adjusting both start and end points."""
        if new_radius <= 0:
            return

        # Calculate current angles
        start_angle = self._angle_from_center(self._start_point)
        end_angle = self._angle_from_center(self._end_point)

        # Update both points to the new radius
        self._start_point = QPointF(
            self._center_point.x() + new_radius * math.cos(start_angle),
            self._center_point.y() + new_radius * math.sin(start_angle)
        )
        self._end_point = QPointF(
            self._center_point.x() + new_radius * math.cos(end_angle),
            self._center_point.y() + new_radius * math.sin(end_angle)
        )

        self.prepareGeometryChange()
        self.update()

    def _create_decorations(self):
        """Create decoration items for this arc."""
        # Add centerlines decoration
        self._add_centerlines(self._center_point)

        # Add dashed circle at the radius
        radius = self._distance(self._center_point, self._start_point)
        self._add_dashed_circle(self._center_point, radius, self._color, self._line_width)

    @property
    def center_point(self):
        """Get the center point."""
        return QPointF(self._center_point)

    @center_point.setter
    def center_point(self, value):
        """Set the center point."""
        self.prepareGeometryChange()
        if isinstance(value, (list, tuple)):
            value = QPointF(value[0], value[1])
        self._center_point = value
        self.update()

    @property
    def start_point(self):
        """Get the start point."""
        return QPointF(self._start_point)

    @start_point.setter
    def start_point(self, value):
        """Set the start point."""
        self.prepareGeometryChange()
        if isinstance(value, (list, tuple)):
            value = QPointF(value[0], value[1])
        self._start_point = value
        self.update()

    @property
    def end_point(self):
        """Get the end point."""
        return QPointF(self._end_point)

    @end_point.setter
    def end_point(self, value):
        """Set the end point."""
        self.prepareGeometryChange()
        if isinstance(value, (list, tuple)):
            value = QPointF(value[0], value[1])
        self._end_point = value
        self.update()

    @property
    def radius(self):
        """Get the radius of the arc."""
        return self._distance(self._center_point, self._start_point)

    @property
    def start_angle(self):
        """Get the start angle in radians."""
        return self._angle_from_center(self._start_point)

    @property
    def end_angle(self):
        """Get the end angle in radians."""
        return self._angle_from_center(self._end_point)

    @property
    def span_angle(self):
        """Get the span angle in radians (counter-clockwise)."""
        start = self._normalize_angle(self.start_angle)
        end = self._normalize_angle(self.end_angle)

        if end < start:
            return end + 2 * math.pi - start
        else:
            return end - start

    @property
    def color(self):
        """Get the color."""
        return self._color

    @color.setter
    def color(self, value):
        """Set the color."""
        self._color = value
        self.update()

    @property
    def line_width(self):
        """Get the line width."""
        return self._line_width

    @line_width.setter
    def line_width(self, value):
        """Set the line width."""
        self.prepareGeometryChange()
        self._line_width = value
        self.update()

