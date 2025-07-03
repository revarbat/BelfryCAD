"""
CubicBezierCadItem - A cubic Bezier curve CAD item defined by four control points.
"""

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QBrush, QPainterPath, QPainterPathStroker, Qt
from BelfryCAD.gui.cad_item import CadItem
from BelfryCAD.gui.control_points import ControlPoint, SquareControlPoint, DiamondControlPoint
from BelfryCAD.gui.cad_rect import CadRect


class CubicBezierCadItem(CadItem):
    """A cubic Bezier curve CAD item defined by four control points."""

    def __init__(self, start_point=None, control1=None, control2=None, end_point=None,
                 color=QColor(0, 0, 255), line_width=0.05):
        super().__init__()
        # Default to a simple S-curve if no points provided
        self._start_point = start_point if start_point else QPointF(0, 0)
        self._control1 = control1 if control1 else QPointF(1, 1)
        self._control2 = control2 if control2 else QPointF(2, -1)
        self._end_point = end_point if end_point else QPointF(3, 0)
        self._color = color
        self._line_width = line_width

        # Convert points to QPointF if they aren't already
        if isinstance(self._start_point, (list, tuple)):
            self._start_point = QPointF(self._start_point[0], self._start_point[1])
        if isinstance(self._control1, (list, tuple)):
            self._control1 = QPointF(self._control1[0], self._control1[1])
        if isinstance(self._control2, (list, tuple)):
            self._control2 = QPointF(self._control2[0], self._control2[1])
        if isinstance(self._end_point, (list, tuple)):
            self._end_point = QPointF(self._end_point[0], self._end_point[1])

    def boundingRect(self):
        """Return the bounding rectangle of the Bezier curve."""
        # For a cubic Bezier, the bounding box includes all four control points
        # plus some padding for the curve that might extend beyond the control polygon

        # Create a CadRect containing all four control points
        rect = CadRect()
        rect.expandToPoint(self._start_point)
        rect.expandToPoint(self._control1)
        rect.expandToPoint(self._control2)
        rect.expandToPoint(self._end_point)

        # Add padding for line width and potential curve overshoot
        padding = max(self._line_width / 2, 0.1)
        rect.expandByScalar(padding)

        return rect

    def shape(self):
        """Return the exact shape of the Bezier curve for collision detection."""
        path = self._create_bezier_path()

        # Use QPainterPathStroker to create a stroked path with line width
        stroker = QPainterPathStroker()
        stroker.setWidth(max(self._line_width, 0.01))  # Minimum width for selection
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

        return stroker.createStroke(path)

    def contains(self, point):
        """Check if a point is near the Bezier curve."""
        # Convert point to local coordinates if needed
        if hasattr(point, 'x') and hasattr(point, 'y'):
            local_point = point
        else:
            local_point = self.mapFromScene(point)

        # Use the stroked shape for accurate contains check
        shape_path = self.shape()
        return shape_path.contains(local_point)

    def createControls(self):
        """Create control points for the cubic Bezier curve and return them."""
        # Create control points with direct setters
        self._start_cp = SquareControlPoint(
            cad_item=self,
            setter=self._set_start
        )
        self._control1_cp = ControlPoint(
            cad_item=self,
            setter=self._set_control1
        )
        self._control2_cp = ControlPoint(
            cad_item=self,
            setter=self._set_control2
        )
        self._end_cp = DiamondControlPoint(
            cad_item=self,
            setter=self._set_end
        )
        self.updateControls()
        
        # Return the list of control points
        return [self._start_cp, self._control1_cp, self._control2_cp, self._end_cp]

    def updateControls(self):
        """Update control point positions."""
        if hasattr(self, '_start_cp') and self._start_cp:
            # Convert scene coordinates to local coordinates
            local_start = self.mapFromScene(self._start_point)
            self._start_cp.setPos(local_start)
        if hasattr(self, '_control1_cp') and self._control1_cp:
            # Convert scene coordinates to local coordinates
            local_control1 = self.mapFromScene(self._control1)
            self._control1_cp.setPos(local_control1)
        if hasattr(self, '_control2_cp') and self._control2_cp:
            # Convert scene coordinates to local coordinates
            local_control2 = self.mapFromScene(self._control2)
            self._control2_cp.setPos(local_control2)
        if hasattr(self, '_end_cp') and self._end_cp:
            # Convert scene coordinates to local coordinates
            local_end = self.mapFromScene(self._end_point)
            self._end_cp.setPos(local_end)

    def _set_start(self, new_position):
        """Set start point from control point movement."""
        # Convert local coordinates to scene coordinates
        scene_position = self.mapToScene(new_position)
        self._start_point = scene_position
        
    def _set_control1(self, new_position):
        """Set control1 point from control point movement."""
        # Convert local coordinates to scene coordinates
        scene_position = self.mapToScene(new_position)
        self._control1 = scene_position

    def _set_control2(self, new_position):
        """Set control2 point from control point movement."""
        # Convert local coordinates to scene coordinates
        scene_position = self.mapToScene(new_position)
        self._control2 = scene_position
        
    def _set_end(self, new_position):
        """Set end point from control point movement."""
        # Convert local coordinates to scene coordinates
        scene_position = self.mapToScene(new_position)
        self._end_point = scene_position
        
    def paint_item(self, painter, option, widget=None):
        """Draw the Bezier curve content."""
        painter.save()

        pen = QPen(self._color, self._line_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(QBrush())  # No fill

        # Draw the Bezier curve
        bezier_path = self._create_bezier_path()
        painter.drawPath(bezier_path)

        painter.restore()

        if self.isSelected():
            painter.save()
            pen = QPen(QColor(127, 127, 127), 3.0)
            pen.setCosmetic(True)
            pen.setDashPattern([2.0, 2.0])
            painter.setPen(pen)
            painter.drawLine(self._start_point, self._control1)
            painter.drawLine(self._control2, self._end_point)
            painter.restore()

    def _create_bezier_path(self):
        """Create the Bezier curve path."""
        path = QPainterPath()
        path.moveTo(self._start_point)
        path.cubicTo(self._control1, self._control2, self._end_point)
        return path

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
    def control1(self):
        """Get the first control point."""
        return QPointF(self._control1)

    @control1.setter
    def control1(self, value):
        """Set the first control point."""
        self.prepareGeometryChange()
        if isinstance(value, (list, tuple)):
            value = QPointF(value[0], value[1])
        self._control1 = value
        self.update()

    @property
    def control2(self):
        """Get the second control point."""
        return QPointF(self._control2)

    @control2.setter
    def control2(self, value):
        """Set the second control point."""
        self.prepareGeometryChange()
        if isinstance(value, (list, tuple)):
            value = QPointF(value[0], value[1])
        self._control2 = value
        self.update()

    @property
    def points(self):
        """Get all four points as a tuple."""
        return (QPointF(self._start_point), QPointF(self._control1),
                QPointF(self._control2), QPointF(self._end_point))

    @points.setter
    def points(self, value):
        """Set all four points from a tuple/list."""
        if len(value) != 4:
            raise ValueError("Points must contain exactly 4 points: start, control1, control2, end")
        self.prepareGeometryChange()
        start, control1, control2, end = value
        if isinstance(start, (list, tuple)):
            start = QPointF(start[0], start[1])
        if isinstance(control1, (list, tuple)):
            control1 = QPointF(control1[0], control1[1])
        if isinstance(control2, (list, tuple)):
            control2 = QPointF(control2[0], control2[1])
        if isinstance(end, (list, tuple)):
            end = QPointF(end[0], end[1])
        self._start_point = start
        self._control1 = control1
        self._control2 = control2
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

    def length_at_parameter(self, t):
        """Calculate the approximate length of the curve from start to parameter t (0-1)."""
        # Simple approximation using line segments
        segments = 20
        total_length = 0.0
        prev_point = self._start_point

        for i in range(1, int(segments * t) + 1):
            param = i / segments
            current_point = self.point_at_parameter(param)
            dx = current_point.x() - prev_point.x()
            dy = current_point.y() - prev_point.y()
            total_length += (dx * dx + dy * dy) ** 0.5
            prev_point = current_point

        return total_length

    def point_at_parameter(self, t):
        """Calculate a point on the Bezier curve at parameter t (0-1)."""
        # Cubic Bezier formula: B(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
        t_inv = 1.0 - t
        t_inv2 = t_inv * t_inv
        t_inv3 = t_inv2 * t_inv
        t2 = t * t
        t3 = t2 * t

        x = (t_inv3 * self._start_point.x() +
             3 * t_inv2 * t * self._control1.x() +
             3 * t_inv * t2 * self._control2.x() +
             t3 * self._end_point.x())

        y = (t_inv3 * self._start_point.y() +
             3 * t_inv2 * t * self._control1.y() +
             3 * t_inv * t2 * self._control2.y() +
             t3 * self._end_point.y())

        return QPointF(x, y)

    def tangent_at_parameter(self, t):
        """Calculate the tangent vector at parameter t (0-1)."""
        # Derivative of cubic Bezier: B'(t) = 3(1-t)²(P₁-P₀) + 6(1-t)t(P₂-P₁) + 3t²(P₃-P₂)
        t_inv = 1.0 - t
        t_inv2 = t_inv * t_inv
        t2 = t * t

        # Calculate tangent components
        dx = (3 * t_inv2 * (self._control1.x() - self._start_point.x()) +
              6 * t_inv * t * (self._control2.x() - self._control1.x()) +
              3 * t2 * (self._end_point.x() - self._control2.x()))

        dy = (3 * t_inv2 * (self._control1.y() - self._start_point.y()) +
              6 * t_inv * t * (self._control2.y() - self._control1.y()) +
              3 * t2 * (self._end_point.y() - self._control2.y()))

        return QPointF(dx, dy)