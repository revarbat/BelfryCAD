"""
CadRect - A QRectF subclass with additional utility methods for CAD operations.
"""

from PySide6.QtCore import QRectF, QPointF, QSizeF
import math


class CadRect(QRectF):
    """A QRectF subclass with additional utility methods for CAD operations."""

    def __init__(self, *args):
        """Initialize CadRect with the same parameters as QRectF."""
        super().__init__(*args)

    def expandToPoint(self, point: QPointF) -> None:
        """Expand the rectangle to include the given point."""
        if not self.contains(point):
            # Expand left if point is to the left
            if point.x() < self.left():
                self.setLeft(point.x())

            # Expand right if point is to the right
            if point.x() > self.right():
                self.setRight(point.x())

            # Expand top if point is above
            if point.y() < self.top():
                self.setTop(point.y())

            # Expand bottom if point is below
            if point.y() > self.bottom():
                self.setBottom(point.y())

    def expandTo(self, point: QPointF, x_offset: float, y_offset: float) -> None:
        """Expand the rectangle to include a point offset from the given point."""
        offset_point = QPointF(point.x() + x_offset, point.y() + y_offset)
        self.expandToPoint(offset_point)

    def expandWithRect(self, rect: QRectF) -> None:
        """Expand the rectangle to include the given rectangle."""
        # If this rectangle is empty, set it to the input rectangle
        if self.isEmpty():
            self.setRect(rect.x(), rect.y(), rect.width(), rect.height())
            return

        # Expand to include all four corners of the given rectangle
        self.expandToPoint(QPointF(rect.left(), rect.top()))
        self.expandToPoint(QPointF(rect.right(), rect.top()))
        self.expandToPoint(QPointF(rect.left(), rect.bottom()))
        self.expandToPoint(QPointF(rect.right(), rect.bottom()))

    def expandBy(self, size: QSizeF) -> None:
        """Expand the rectangle outwards by the given size."""
        half_width = size.width() / 2
        half_height = size.height() / 2

        self.setLeft(self.left() - half_width)
        self.setRight(self.right() + half_width)
        self.setTop(self.top() - half_height)
        self.setBottom(self.bottom() + half_height)

    def expandByScalar(self, amount: float) -> None:
        """Expand the rectangle outwards by a scalar amount in all directions."""
        self.expandBy(QSizeF(amount, amount))

    def _angle_in_arc(self, test_angle, start_angle, end_angle):
        """Check if a test angle is within the arc span (counter-clockwise)."""
        # Normalize angles to [0, 2π) range
        def normalize_angle(angle):
            while angle < 0:
                angle += 2 * math.pi
            while angle >= 2 * math.pi:
                angle -= 2 * math.pi
            return angle

        test_angle = normalize_angle(test_angle)
        start_angle = normalize_angle(start_angle)
        end_angle = normalize_angle(end_angle)

        if start_angle <= end_angle:
            # Arc doesn't cross 0°
            return start_angle <= test_angle <= end_angle
        else:
            # Arc crosses 0°
            return test_angle >= start_angle or test_angle <= end_angle

    def expandWithArc(self, center_point: QPointF, radius: float, start_angle: float, end_angle: float) -> None:
        """Expand the rectangle to include the extents of an arc.
        - center_point: center of the arc (QPointF)
        - radius: radius of the arc (float)
        - start_angle: start angle in radians (float)
        - end_angle: end angle in radians (float)
        """
        # Start and end points
        self.expandTo(center_point, radius * math.cos(start_angle), radius * math.sin(start_angle))
        self.expandTo(center_point, radius * math.cos(end_angle), radius * math.sin(end_angle))
        # Cardinal directions (0, 90, 180, 270 degrees)
        for angle, x_off, y_off in [
            (0, radius, 0),
            (math.pi/2, 0, radius),
            (math.pi, -radius, 0),
            (3*math.pi/2, 0, -radius)
        ]:
            if self._angle_in_arc(angle, start_angle, end_angle):
                self.expandTo(center_point, x_off, y_off)