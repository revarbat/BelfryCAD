"""
ArcCadItem - An arc CAD item defined by center point, start radius point, and end angle point.
"""

import math

from typing import List, Optional
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QBrush, QPainterPath, QPainterPathStroker, Qt
from typing import cast

from ..cad_item import CadItem
from ..control_points import ControlPoint, SquareControlPoint, DiamondControlPoint, ControlDatum
from ..cad_rect import CadRect
from ...widgets.cad_scene import CadScene


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
        self._center_cp = None
        self._start_cp = None
        self._end_cp = None
        self._radius_datum = None

        # Convert points to QPointF if they aren't already
        if isinstance(self._center_point, (list, tuple)):
            self._center_point = QPointF(self._center_point[0], self._center_point[1])
        if isinstance(self._start_point, (list, tuple)):
            self._start_point = QPointF(self._start_point[0], self._start_point[1])
        if isinstance(self._end_point, (list, tuple)):
            self._end_point = QPointF(self._end_point[0], self._end_point[1])
            
        # Create control points
        self.createControls()

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

    def _create_controls_impl(self):
        """Create control points for the arc and return them."""
        # Get precision from scene
        precision = 3  # Default fallback
        scene = self.scene()
        if scene and isinstance(scene, CadScene):
            precision = scene.get_precision()
        
        # Create control points with direct setters
        self._center_cp = SquareControlPoint(
            cad_item=self,
            setter=self._set_center
        )
        self._start_cp = DiamondControlPoint(
            cad_item=self,
            setter=self._set_start
        )
        self._end_cp = ControlPoint(
            cad_item=self,
            setter=self._set_end
        )
        self._radius_datum = ControlDatum(
            setter=self._set_radius_value,
            prefix="R",
            cad_item=self,
            precision=precision
        )

        self.updateControls()
        
        # Store control points in the list that the scene expects
        control_points = [self._center_cp, self._start_cp, self._end_cp, self._radius_datum]
        self._control_point_items.extend(control_points)
        
        # Return the list of control points
        return control_points

    def updateControls(self):
        """Update control point positions and values."""
        if hasattr(self, '_center_cp') and self._center_cp:
            self._center_cp.setPos(self._center_point)
        if hasattr(self, '_start_cp') and self._start_cp:
            self._start_cp.setPos(self._start_point)
        if hasattr(self, '_end_cp') and self._end_cp:
            self._end_cp.setPos(self._end_point)
        if hasattr(self, '_radius_datum') and self._radius_datum:
            # Update both position and value for the datum
            radius_value = self._get_radius_value()
            radius_position = self._get_radius_datum_position()
            self._radius_datum.update_datum(radius_value, radius_position)

    def getControlPoints(self, exclude_cps: Optional[List['ControlPoint']] = None) -> List[QPointF]:
        """Return list of control point positions in scene coordinates (excluding ControlDatums)."""
        out = []
        # Return scene coordinates for all control points
        if self._center_cp and (exclude_cps is None or self._center_cp not in exclude_cps):
            out.append(self._center_point)
        if self._start_cp and (exclude_cps is None or self._start_cp not in exclude_cps):
            out.append(self._start_point)
        if self._end_cp and (exclude_cps is None or self._end_cp not in exclude_cps):
            out.append(self._end_point)
        return out

    def _get_control_point_objects(self) -> List['ControlPoint']:
        """Get the list of ControlPoint objects for this CAD item."""
        control_points = []
        if hasattr(self, '_center_cp') and self._center_cp:
            control_points.append(self._center_cp)
        if hasattr(self, '_start_cp') and self._start_cp:
            control_points.append(self._start_cp)
        if hasattr(self, '_end_cp') and self._end_cp:
            control_points.append(self._end_cp)
        return control_points

    def _set_center(self, new_position):
        """Set the center from control point movement."""
        # Translate the entire arc
        scene_delta = new_position - self._center_point
        self._start_point += scene_delta
        self._end_point += scene_delta
        self._center_point += scene_delta
        #self.setPos(self._center_point)
        
    def _set_start(self, new_position):
        """Set the start point from control point movement."""
        self._start_point = new_position
        end_angle = self._angle_from_center(self._end_point)
        new_radius = self._distance(self._center_point, new_position)
        self._end_point = QPointF(
            self._center_point.x() + new_radius * math.cos(end_angle),
            self._center_point.y() + new_radius * math.sin(end_angle)
        )
        
    def _set_end(self, new_position):
        """Set the end point from control point movement."""
        self._end_point = new_position
        start_angle = self._angle_from_center(self._start_point)
        new_radius = self._distance(self._center_point, new_position)
        self._start_point = QPointF(
            self._center_point.x() + new_radius * math.cos(start_angle),
            self._center_point.y() + new_radius * math.sin(start_angle)
        )
        
    def _get_radius_datum_position(self) -> QPointF:
        """Get the position for the radius datum."""
        sc = math.sin(math.pi/4)
        return QPointF(self.radius * sc, self.radius * sc) + self._center_point

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

    def paint_item_with_color(self, painter, option, widget=None, color=None):
        """Draw the arc content with a custom color."""
        painter.save()

        # Use provided color or fall back to default
        pen_color = color if color is not None else self._color
        pen = QPen(pen_color, self._line_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(QBrush())  # No fill

        # Draw the arc
        arc_path = self._create_arc_path()
        painter.drawPath(arc_path)

        # Use dashed construction pen for construction lines
        self.draw_construction_line(painter, self._center_point, self._start_point)
        self.draw_construction_line(painter, self._center_point, self._end_point)
        
        # Use solid construction pen for construction circle
        self.draw_construction_circle(painter, self._center_point, self.radius)
        
        self.draw_radius_arrow(painter, self._center_point, 45, self.radius, self._line_width)
        self.draw_center_cross(painter, self._center_point)

        painter.restore()

    def paint_item(self, painter, option, widget=None):
        """Draw the arc content."""
        self.paint_item_with_color(painter, option, widget, self._color)

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

    def moveBy(self, dx, dy):
        """Move all defining points by the specified offset."""
        self.prepareGeometryChange()
        self._start_point = QPointF(self._start_point.x() + dx, self._start_point.y() + dy)
        self._end_point = QPointF(self._end_point.x() + dx, self._end_point.y() + dy)
        self._center_point = QPointF(self._center_point.x() + dx, self._center_point.y() + dy)
        self.update()

