"""
Circle2PointsCadItem - A circle CAD item defined by two points on opposite sides (diameter endpoints).
"""

import math
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainterPathStroker, Qt
from BelfryCAD.gui.cad_item import CadItem
from BelfryCAD.gui.control_points import ControlPoint, SquareControlPoint, ControlDatum
from BelfryCAD.gui.cad_rect import CadRect


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

    def _get_control_points(self):
        """Return control points for the circle."""
        return [
            ControlPoint(
                parent=self,
                getter=self._get_point1_position,
                setter=self._set_point1_position),
            ControlPoint(
                parent=self,
                getter=self._get_point2_position,
                setter=self._set_point2_position),
            SquareControlPoint(
                parent=self,
                getter=self._get_center_position,
                setter=self._set_center_position),
            ControlDatum(
                parent=self,
                getter=self._get_radius_value,
                setter=self._set_radius_value,
                pos_getter=self._get_radius_datum_position,
                prefix="R"
            )
        ]

    def _get_point1_position(self) -> QPointF:
        """Get the point1 position."""
        return self._point1 - self.center_point  # Convert to local coordinates

    def _set_point1_position(self, new_position: QPointF):
        """Set the point1 position."""
        # Change point1 position
        scene_pos = self.mapToScene(new_position)
        self._point1 = scene_pos
        self.setPos(self.center_point)
        self.prepareGeometryChange()
        self.update()

    def _get_point2_position(self) -> QPointF:
        """Get the point2 position."""
        return self._point2 - self.center_point  # Convert to local coordinates

    def _set_point2_position(self, new_position: QPointF):
        """Set the point2 position."""
        # Change point2 position
        scene_pos = self.mapToScene(new_position)
        self._point2 = scene_pos
        self.setPos(self.center_point)
        self.prepareGeometryChange()
        self.update()

    def _get_center_position(self) -> QPointF:
        """Get the center position."""
        return QPointF(0, 0)  # Center is always at origin in local coordinates

    def _set_center_position(self, new_position: QPointF):
        """Set the center position."""
        # Translate the entire circle (both points)
        # Calculate the delta from current center (which is at origin in local coords)
        delta = new_position  # new_position is the delta from origin
        scene_delta = self.mapToScene(delta) - self.mapToScene(QPointF(0, 0))
        self._point1 += scene_delta
        self._point2 += scene_delta
        self.setPos(self.center_point)

    def _get_radius_datum_position(self) -> QPointF:
        """Get the position for the radius datum."""
        sc = math.sin(math.pi/4)
        return QPointF(self.radius * sc, self.radius * sc)

    def _get_radius_value(self):
        """Get the current radius value."""
        return self.radius

    def _set_radius_value(self, new_radius):
        """Set the radius value."""
        self.radius = new_radius

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