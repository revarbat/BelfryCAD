"""
PolylineCadItem - A polyline CAD item defined by a list of points.
"""

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QBrush, QPainterPath, QPainterPathStroker, Qt
from BelfryCAD.gui.cad_item import CadItem
from BelfryCAD.gui.control_points import ControlPoint
from BelfryCAD.gui.cad_rect import CadRect


class PolylineCadItem(CadItem):
    """A polyline CAD item defined by a list of points."""

    def __init__(self, points=None, color=QColor(0, 255, 0), line_width=0.05):
        super().__init__()
        self._points = points if points else []
        self._color = color
        self._line_width = line_width

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
        rect.expandByScalar(self._line_width / 2)

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

    def _get_control_points(self):
        """Return control points for the polyline."""
        control_points = []
        for i in range(len(self._points)):
            control_points.append(
                ControlPoint(
                    parent=self, 
                    getter=lambda idx=i: self._get_point_position(idx),
                    setter=lambda pos, ii=i: self._set_point_position(ii, pos))
            )
        return control_points

    def _get_point_position(self, index: int) -> QPointF:
        """Get the position of a specific point."""
        if 0 <= index < len(self._points):
            return self._points[index]
        return QPointF(0, 0)

    def _set_point_position(self, index: int, new_position: QPointF):
        """Set the position of a specific point."""
        if 0 <= index < len(self._points):
            self._points[index] = new_position
            self.prepareGeometryChange()
            self.update()

    def paint_item(self, painter, option, widget=None):
        """Draw the polyline content."""
        if len(self._points) < 2:
            return

        painter.save()

        pen = QPen(self._color, self._line_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(QBrush())  # No fill

        # Draw lines between consecutive points
        for i in range(len(self._points) - 1):
            painter.drawLine(self._points[i], self._points[i + 1])

        painter.restore()

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