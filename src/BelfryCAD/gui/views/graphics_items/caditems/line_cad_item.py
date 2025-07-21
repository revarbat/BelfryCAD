"""
LineCadItem - A line CAD item defined by two points.
"""

import math

from typing import List, Optional

from PySide6.QtCore import QPointF
from PySide6.QtGui import (
    QPen, QColor, QBrush, QPainterPath, QPainterPathStroker, Qt
)
from ..cad_item import CadItem
from ..control_points import (
    ControlPoint, SquareControlPoint, DiamondControlPoint, ControlDatum
)
from ..cad_rect import CadRect


class LineCadItem(CadItem):
    """A line CAD item defined by two points."""

    def __init__(self, start_point=None, end_point=None, color=QColor(255, 0, 0), line_width=0.05):
        super().__init__()
        self._start_point = start_point if start_point is not None else QPointF(0, 0)
        self._end_point = end_point if end_point is not None else QPointF(1, 0)
        self._color = color
        self._line_width = line_width
        self.setZValue(1)
        self.createControls()

    def boundingRect(self):
        """Return the bounding rectangle of the line."""
        # Create a CadRect containing both points
        rect = CadRect()
        rect.expandToPoint(self._start_point)
        rect.expandToPoint(self._end_point)
        
        pvec = self.get_perpendicular_vector()
        rect.expandToPoint(self._start_point + pvec)
        rect.expandToPoint(self._end_point + pvec)

        # Add padding for line width
        rect.expandByScalar(max(self._line_width / 2, 0.1))

        return rect

    def shape(self):
        """Return the exact shape of the line for collision detection."""
        path = QPainterPath()
        path.moveTo(self._start_point)
        path.lineTo(self._end_point)

        # Create a stroked path with the line width for better selection
        stroker = QPainterPathStroker()
        stroker.setWidth(max(self._line_width, 0.1))  # Minimum width for selection
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

        return stroker.createStroke(path)

    def contains(self, point):
        """Check if a point is near the line segment."""
        # Convert point to local coordinates if needed
        if hasattr(point, 'x') and hasattr(point, 'y'):
            local_point = point
        else:
            local_point = self.mapFromScene(point)

        # Check distance to the line segment
        tolerance = max(self._line_width, 0.1)  # Minimum tolerance for selection
        distance = self._point_to_line_distance(
            local_point, self._start_point, self._end_point)
        return distance <= tolerance

    def _create_controls_impl(self):
        """Create control points for the line and return them."""
        # Create control points with direct setters
        self._start_cp = SquareControlPoint(
            cad_item=self,
            setter=self._set_start_point
        )
        self._end_cp = ControlPoint(
            cad_item=self,
            setter=self._set_end_point
        )
        self._mid_cp = DiamondControlPoint(
            cad_item=self,
            setter=self._set_mid_point
        )
        precision = 4
        self._length_datum = ControlDatum(
            setter=self._set_length,
            format_string=f"{{:.{precision}f}}",
            cad_item=self,
            label="Line Length",
            precision=precision
        )
        self.updateControls()

        # Return the list of control points
        return [self._start_cp, self._end_cp, self._mid_cp, self._length_datum]

    def updateControls(self):
        """Update control point positions."""
        if hasattr(self, '_start_cp') and self._start_cp:
            self._start_cp.setPos(self._start_point)
        if hasattr(self, '_end_cp') and self._end_cp:
            self._end_cp.setPos(self._end_point)
        if hasattr(self, '_mid_cp') and self._mid_cp:
            self._mid_cp.setPos(self.midpoint)
        if hasattr(self, '_length_datum') and self._length_datum:
            self._length_datum.update_datum(
                self.length,
                self.midpoint + self.get_perpendicular_vector() * 0.75
            )

    def get_perpendicular_vector(self) -> QPointF:
        """Get the perpendicular vector to the line segment."""
        vec = self._end_point - self._start_point
        pvec = QPointF(vec.y(), -vec.x())
        scale = self.scene().views()[0].transform().m11()
        pvec *= 50.0 / scale / math.hypot(pvec.x(), pvec.y())
        return pvec

    def getControlPoints(
            self,
            exclude_cps: Optional[List['ControlPoint']] = None
    ) -> List[QPointF]:
        """Return list of control point positions (excluding ControlDatums)."""
        out = []
        for cp in [self._start_cp, self._end_cp, self._mid_cp]:
            if cp and (exclude_cps is None or cp not in exclude_cps):
                out.append(cp.pos())
        return out
    
    def _get_control_point_objects(self) -> List['ControlPoint']:
        """Get the list of ControlPoint objects for this CAD item."""
        return [x for x in [self._start_cp, self._end_cp, self._mid_cp] if x]

    def _set_start_point(self, new_position):
        """Set the start point from control point movement."""
        # new_position is already in local coordinates
        
        # When start point moves, move end point to maintain the same relative position
        current_vector = QPointF(self._end_point.x() - self._start_point.x(),
                               self._end_point.y() - self._start_point.y())
        self._start_point = new_position
        self._end_point = QPointF(new_position.x() + current_vector.x(),
                                 new_position.y() + current_vector.y())

    def _set_end_point(self, new_position):
        """Set the end point from control point movement."""
        # new_position is already in local coordinates
        self._end_point = new_position

    def _set_mid_point(self, new_position):
        """Set the midpoint from control point movement."""
        # new_position is already in local coordinates
        
        # Calculate the vector from start to new midpoint
        start_to_mid = QPointF(new_position.x() - self._start_point.x(),
                              new_position.y() - self._start_point.y())
        # The end point should be equidistant on the opposite side
        self._end_point = QPointF(new_position.x() + start_to_mid.x(),
                                 new_position.y() + start_to_mid.y())

    def _get_line_width(self):
        """Get the line width for this CAD item."""
        return self._line_width

    def paint_item_with_color(self, painter, option, widget=None, color=None):
        """Draw the line content with a specific color."""
        painter.save()

        # Use the provided color or fall back to the item's color
        line_color = color if color is not None else self._color
        pen = QPen(line_color, self._line_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(QBrush())  # No fill

        # Draw the line
        painter.drawLine(self._start_point, self._end_point)

        if self._is_singly_selected():
            pvec = self.get_perpendicular_vector()
            self.draw_construction_line(painter, self._start_point + pvec * 0.75, self._end_point + pvec * 0.75)
            self.draw_construction_line(painter, self._start_point, self._start_point + pvec)
            self.draw_construction_line(painter, self._end_point, self._end_point + pvec)

        painter.restore()

    def paint_item(self, painter, option, widget=None):
        """Draw the line content."""
        self.paint_item_with_color(painter, option, widget, self._color)

    def _point_to_line_distance(self, point, line_start, line_end):
        """Calculate the shortest distance from a point to a line segment."""
        # Vector from line_start to line_end
        line_vec = QPointF(line_end.x() - line_start.x(), line_end.y() - line_start.y())
        line_length_squared = line_vec.x() ** 2 + line_vec.y() ** 2

        if line_length_squared == 0:
            # Line segment is actually a point
            dx = point.x() - line_start.x()
            dy = point.y() - line_start.y()
            return (dx ** 2 + dy ** 2) ** 0.5

        # Vector from line_start to point
        point_vec = QPointF(point.x() - line_start.x(), point.y() - line_start.y())

        # Project point onto line (parameterized by t)
        t = (point_vec.x() * line_vec.x() + point_vec.y() * line_vec.y()) / line_length_squared

        # Clamp t to [0, 1] to stay within the line segment
        t = max(0, min(1, t))

        # Find the closest point on the line segment
        closest_x = line_start.x() + t * line_vec.x()
        closest_y = line_start.y() + t * line_vec.y()

        # Calculate distance from point to closest point on line
        dx = point.x() - closest_x
        dy = point.y() - closest_y
        return (dx ** 2 + dy ** 2) ** 0.5

    @property
    def start_point(self):
        """Get the start point."""
        return QPointF(self._start_point)

    @start_point.setter
    def start_point(self, value):
        """Set the start point."""
        self.prepareGeometryChange()  # Notify Qt that geometry will change
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
        self.prepareGeometryChange()  # Notify Qt that geometry will change
        if isinstance(value, (list, tuple)):
            value = QPointF(value[0], value[1])
        self._end_point = value
        self.update()

    @property
    def points(self):
        """Get both points as a tuple."""
        return (QPointF(self._start_point), QPointF(self._end_point))

    @points.setter
    def points(self, value):
        """Set both points from a tuple/list of two points."""
        if len(value) != 2:
            raise ValueError("Points must contain exactly 2 points")
        self.prepareGeometryChange()
        start, end = value
        if isinstance(start, (list, tuple)):
            start = QPointF(start[0], start[1])
        if isinstance(end, (list, tuple)):
            end = QPointF(end[0], end[1])
        self._start_point = start
        self._end_point = end
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
    def length(self):
        """Calculate the length of the line segment."""
        dx = self._end_point.x() - self._start_point.x()
        dy = self._end_point.y() - self._start_point.y()
        return (dx ** 2 + dy ** 2) ** 0.5

    @length.setter
    def length(self, value):
        """Set the length of the line segment by moving the endpoint."""
        current_angle = self.angle
        self._end_point = QPointF(
            self._start_point.x() + value * math.cos(current_angle),
            self._start_point.y() + value * math.sin(current_angle)
        )
        self.prepareGeometryChange()
        self.update()

    def _set_length(self, value):
        """Set the length of the line segment by moving the endpoint."""
        current_angle = self.angle
        self._end_point = QPointF(
            self._start_point.x() + value * math.cos(current_angle),
            self._start_point.y() + value * math.sin(current_angle)
        )
        self.prepareGeometryChange()
        self.update()

    @property
    def angle(self):
        """Calculate the angle of the line segment in radians."""
        dx = self._end_point.x() - self._start_point.x()
        dy = self._end_point.y() - self._start_point.y()
        return math.atan2(dy, dx)

    @angle.setter
    def angle(self, value):
        """Set the angle of the line segment by moving the endpoint."""
        current_length = self.length
        self._end_point = QPointF(
            self._start_point.x() + current_length * math.cos(value),
            self._start_point.y() + current_length * math.sin(value)
        )
        self.prepareGeometryChange()
        self.update()

    @property
    def midpoint(self):
        """Calculate the midpoint of the line segment."""
        mid_x = (self._start_point.x() + self._end_point.x()) / 2
        mid_y = (self._start_point.y() + self._end_point.y()) / 2
        return QPointF(mid_x, mid_y)

    @midpoint.setter
    def midpoint(self, value):
        """Set the midpoint of the line segment by moving both endpoints."""
        if isinstance(value, (list, tuple)):
            value = QPointF(value[0], value[1])

        # Calculate the current vector from start to end
        current_vector = QPointF(self._end_point.x() - self._start_point.x(),
                               self._end_point.y() - self._start_point.y())

        # Calculate half the vector
        half_vector = QPointF(current_vector.x() / 2, current_vector.y() / 2)

        # Set start and end points relative to the new midpoint
        self._start_point = QPointF(value.x() - half_vector.x(), value.y() - half_vector.y())
        self._end_point = QPointF(value.x() + half_vector.x(), value.y() + half_vector.y())

        self.prepareGeometryChange()
        self.update()

    def moveBy(self, dx, dy):
        """Move both endpoints by the specified offset."""
        self.prepareGeometryChange()
        self._start_point = QPointF(self._start_point.x() + dx, self._start_point.y() + dy)
        self._end_point = QPointF(self._end_point.x() + dx, self._end_point.y() + dy)
        self.update()