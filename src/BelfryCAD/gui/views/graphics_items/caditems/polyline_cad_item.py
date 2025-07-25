"""
PolylineCadItem - A polyline CAD item defined by a list of points.
"""

from typing import List, Optional, TYPE_CHECKING

from PySide6.QtCore import QPointF
from PySide6.QtGui import QPen, QColor, QBrush, QPainterPath, QPainterPathStroker, Qt

from ..cad_item import CadItem
from ..control_points import ControlPoint
from ..cad_rect import CadRect

if TYPE_CHECKING:
    from ....main_window import MainWindow


class PolylineCadItem(CadItem):
    """A polyline CAD item defined by a list of points."""

    def __init__(self, main_window: 'MainWindow', points=None, color=QColor(0, 0, 0), line_width=0.05):
        super().__init__(main_window)
        self._points = points if points is not None else [QPointF(0, 0), QPointF(1, 0)]
        self._color = color
        self._line_width = line_width
        self.setZValue(1)
        self.createControls()

        # Convert points to QPointF if they aren't already
        self._points = [QPointF(p[0], p[1]) if isinstance(p, (list, tuple)) else p
                      for p in self._points]

    def boundingRect(self):
        """Return the bounding rectangle of the polyline."""
        if len(self._points) < 2:
            # If we don't have at least 2 points, return a small default rect
            return CadRect(-0.1, -0.1, 0.2, 0.2)

        # Create a CadRect containing all points
        rect = CadRect()
        for point in self._points:
            rect.expandToPoint(point)

        # Add padding for line width
        rect.expandByScalar(max(self._line_width / 2, 0.1))

        return rect

    def shape(self):
        """Return the exact shape of the polyline for collision detection."""
        path = QPainterPath()

        if len(self._points) < 2:
            return path

        # Create a path that follows the polyline
        path.moveTo(self._points[0])
        for i in range(1, len(self._points)):
            path.lineTo(self._points[i])

        # Create a stroked path with the line width for better selection
        stroker = QPainterPathStroker()
        stroker.setWidth(max(self._line_width, 0.1))  # Minimum width for selection
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

        return stroker.createStroke(path)

    def contains(self, point):
        """Check if a point is near the polyline."""
        if len(self._points) < 2:
            return False

        # Convert point to local coordinates if needed
        if hasattr(point, 'x') and hasattr(point, 'y'):
            local_point = point
        else:
            local_point = self.mapFromScene(point)

        # Check distance to each line segment
        tolerance = max(self._line_width, 0.1)  # Minimum tolerance for selection

        for i in range(len(self._points) - 1):
            p1 = self._points[i]
            p2 = self._points[i + 1]

            # Calculate distance from point to line segment
            distance = self._point_to_line_distance(local_point, p1, p2)
            if distance <= tolerance:
                return True

        return False

    def _create_controls_impl(self):
        """Create control points for the polyline and return them."""
        # Create control points with direct setters
        self._point_control_points = []
        for i in range(len(self._points)):
            # Use a default argument to capture the current value of i
            def make_setter(index):
                return lambda pos: self._set_point(index, pos)
            
            cp = ControlPoint(
                cad_item=self,
                setter=make_setter(i)
            )
            self._point_control_points.append(cp)
        
        self.updateControls()

        # Return the list of control points
        return self._point_control_points

    def updateControls(self):
        """Update control point positions."""
        for i, cp in enumerate(self._point_control_points):
            if cp and i < len(self._points):
                # Points are already in local coordinates
                cp.setPos(self._points[i])

    def getControlPoints(
            self,
            exclude_cps: Optional[List['ControlPoint']] = None
    ) -> List[QPointF]:
        """Return list of control point positions (excluding ControlDatums)."""
        out = []
        for cp in self._point_control_points:
            if cp and (exclude_cps is None or cp not in exclude_cps):
                out.append(cp.pos())
        return out
    
    def _get_control_point_objects(self) -> List['ControlPoint']:
        """Get the list of ControlPoint objects for this CAD item."""
        return self._point_control_points

    def _set_point(self, index, new_position):
        """Set a specific point from control point movement."""
        # new_position is already in local coordinates
        
        if 0 <= index < len(self._points):
            self._points[index] = new_position

    def paint_item_with_color(self, painter, option, widget=None, color=None):
        """Draw the polyline content with a custom color."""
        if len(self._points) < 2:
            return

        painter.save()

        # Use provided color or fall back to default
        pen_color = color if color is not None else self._color
        pen = QPen(pen_color, self._line_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(QBrush())  # No fill

        # Draw lines between consecutive points
        for i in range(len(self._points) - 1):
            painter.drawLine(self._points[i], self._points[i + 1])

        painter.restore()

    def paint_item(self, painter, option, widget=None):
        """Draw the polyline content."""
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

    def add_point(self, point):
        """Add a point to the end of the polyline."""
        self.prepareGeometryChange()
        if isinstance(point, (list, tuple)):
            point = QPointF(point[0], point[1])
        self._points.append(point)
        self.update()

    def insert_point(self, index, point):
        """Insert a point at the specified index."""
        self.prepareGeometryChange()
        if isinstance(point, (list, tuple)):
            point = QPointF(point[0], point[1])
        self._points.insert(index, point)
        self.update()

    def remove_point(self, index):
        """Remove a point at the specified index."""
        if 0 <= index < len(self._points):
            self.prepareGeometryChange()
            self._points.pop(index)
            self.update()

    @property
    def points(self):
        """Get the list of points."""
        return self._points.copy()

    @points.setter
    def points(self, value):
        """Set the list of points."""
        self.prepareGeometryChange()  # Notify Qt that geometry will change
        self._points = [QPointF(p[0], p[1]) if isinstance(p, (list, tuple)) else p
                       for p in value]
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
        """Move all points by the specified offset."""
        self.prepareGeometryChange()
        self._points = [QPointF(pt.x() + dx, pt.y() + dy) for pt in self._points]
        self.update()