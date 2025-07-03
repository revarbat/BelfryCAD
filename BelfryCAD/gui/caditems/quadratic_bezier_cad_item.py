"""
QuadraticBezierCadItem - A quadratic Bezier curve CAD item defined by an arbitrary number of points.
Points follow the pattern: [path_point, control_point, path_point, control_point, ...]
"""

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QBrush, QPainterPath, QPainterPathStroker, Qt
from BelfryCAD.gui.cad_item import CadItem
from BelfryCAD.gui.control_points import ControlPoint, SquareControlPoint, DiamondControlPoint
from BelfryCAD.gui.cad_rect import CadRect


class QuadraticBezierCadItem(CadItem):
    """A quadratic Bezier curve CAD item defined by an arbitrary number of points.
    
    Points follow the pattern:
    - 1st point: path point (on the curve)
    - 2nd point: control point for 1st segment
    - 3rd point: path point (on the curve)
    - 4th point: control point for 2nd segment
    - 5th point: path point (on the curve)
    - And so on...
    
    This creates a smooth curve that passes through every other point.
    """

    def __init__(self, points=None, color=QColor(0, 0, 255), line_width=0.05):
        super().__init__()
        
        # Initialize with default points if none provided
        if points is None:
            points = [
                QPointF(0, 0),    # 1st path point
                QPointF(1, 1),    # control point for 1st segment
                QPointF(2, 0),    # 2nd path point
            ]
        
        self._points = []
        self._color = color
        self._line_width = line_width
        
        # Convert all points to QPointF
        for point in points:
            if isinstance(point, (list, tuple)):
                self._points.append(QPointF(point[0], point[1]))
            else:
                self._points.append(QPointF(point))

    def boundingRect(self):
        """Return the bounding rectangle of the Bezier curve."""
        if len(self._points) < 3:
            # If we don't have enough points, return a small default rect
            return CadRect(-0.1, -0.1, 0.2, 0.2)

        # Create a CadRect containing all points
        rect = CadRect()
        for point in self._points:
            rect.expandToPoint(point)

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
        """Create control points for the Bezier curve and return them."""
        # Create control points for all points
        self._control_points = []
        
        for i in range(len(self._points)):
            # Use a default argument to capture the current value of i
            def make_setter(index):
                return lambda pos: self._set_point(index, pos)
            
            # Use different control point styles based on position
            if i % 2 == 0:  # Path points (every 2nd point, starting with 0)
                cp = SquareControlPoint(
                    cad_item=self,
                    setter=make_setter(i)
                )
            else:  # Control points
                cp = ControlPoint(
                    cad_item=self,
                    setter=make_setter(i)
                )
            
            self._control_points.append(cp)
        
        self.updateControls()
        
        # Return the list of control points
        return self._control_points

    def updateControls(self):
        """Update control point positions."""
        for i, cp in enumerate(self._control_points):
            if cp and i < len(self._points):
                # Points are already in local coordinates
                cp.setPos(self._points[i])

    def _set_point(self, index, new_position):
        """Set a specific point from control point movement."""
        # new_position is already in local coordinates
        
        if 0 <= index < len(self._points):
            self._points[index] = new_position

    def paint_item(self, painter, option, widget=None):
        """Draw the Bezier curve content."""
        if len(self._points) < 3:
            return

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

        # Draw control lines when selected
        if self.isSelected():
            painter.save()
            pen = QPen(QColor(127, 127, 127), 3.0)
            pen.setCosmetic(True)
            pen.setDashPattern([2.0, 2.0])
            painter.setPen(pen)
            
            # Draw control lines for each segment
            for i in range(0, len(self._points) - 2, 2):
                if i + 2 < len(self._points):
                    # Draw control lines for this segment
                    painter.drawLine(self._points[i], self._points[i + 1])      # path to control
                    painter.drawLine(self._points[i + 1], self._points[i + 2])  # control to next path
            
            painter.restore()

    def _create_bezier_path(self):
        """Create the Bezier curve path."""
        path = QPainterPath()
        
        if len(self._points) < 3:
            return path
        
        # Start at the first point
        path.moveTo(self._points[0])
        
        # Create quadratic Bezier segments
        for i in range(0, len(self._points) - 2, 2):
            if i + 2 < len(self._points):
                # Each segment uses 3 points: current, control, next
                path.quadTo(
                    self._points[i + 1],  # control point
                    self._points[i + 2]   # next path point
                )
        
        return path

    def add_segment(self, control_point, end_point):
        """Add a new segment to the Bezier curve."""
        if isinstance(control_point, (list, tuple)):
            control_point = QPointF(control_point[0], control_point[1])
        if isinstance(end_point, (list, tuple)):
            end_point = QPointF(end_point[0], end_point[1])
        
        self._points.extend([control_point, end_point])

    def insert_segment(self, segment_index, control_point, end_point):
        """Insert a new segment at the specified index."""
        if isinstance(control_point, (list, tuple)):
            control_point = QPointF(control_point[0], control_point[1])
        if isinstance(end_point, (list, tuple)):
            end_point = QPointF(end_point[0], end_point[1])
        
        # Calculate the insertion index (2 points per segment)
        insert_index = segment_index * 2 + 1
        
        if insert_index <= len(self._points):
            self._points.insert(insert_index, control_point)
            self._points.insert(insert_index + 1, end_point)

    def remove_segment(self, segment_index):
        """Remove a segment at the specified index."""
        # Calculate the start index of the segment (2 points per segment)
        start_index = segment_index * 2 + 1
        
        if start_index + 1 < len(self._points):
            # Remove the 2 points of the segment
            del self._points[start_index:start_index + 2]

    def get_path_points(self):
        """Get all path points (every 2nd point, starting with 0)."""
        return [self._points[i] for i in range(0, len(self._points), 2)]

    def get_control_points(self):
        """Get all control points (not path points)."""
        return [self._points[i] for i in range(len(self._points)) if i % 2 != 0]

    def get_segment(self, segment_index):
        """Get the 3 points of a specific segment."""
        start_index = segment_index * 2
        if start_index + 2 < len(self._points):
            return [
                self._points[start_index],     # path point
                self._points[start_index + 1], # control point
                self._points[start_index + 2]  # next path point
            ]
        return None

    @property
    def points(self):
        """Get all points."""
        return self._points.copy()

    @points.setter
    def points(self, value):
        """Set all points."""
        self._points = []
        for point in value:
            if isinstance(point, (list, tuple)):
                self._points.append(QPointF(point[0], point[1]))
            else:
                self._points.append(QPointF(point))

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
    def segment_count(self):
        """Get the number of segments in the Bezier curve."""
        if len(self._points) < 3:
            return 0
        return (len(self._points) - 1) // 2

    def point_at_parameter(self, t):
        """Get a point on the curve at parameter t (0.0 to 1.0)."""
        if len(self._points) < 3:
            return QPointF(0, 0)
        
        # Calculate which segment t falls into
        total_segments = self.segment_count
        if total_segments == 0:
            return self._points[0] if self._points else QPointF(0, 0)
        
        segment_t = t * total_segments
        segment_index = int(segment_t)
        local_t = segment_t - segment_index
        
        # Clamp segment_index to valid range
        segment_index = max(0, min(segment_index, total_segments - 1))
        
        # Get the 3 points for this segment
        segment = self.get_segment(segment_index)
        if not segment:
            return self._points[0] if self._points else QPointF(0, 0)
        
        # Calculate quadratic Bezier point
        p0, p1, p2 = segment
        
        # Quadratic Bezier formula: B(t) = (1-t)²P₀ + 2(1-t)tP₁ + t²P₂
        t2 = local_t * local_t
        mt = 1 - local_t
        mt2 = mt * mt
        
        x = mt2 * p0.x() + 2 * mt * local_t * p1.x() + t2 * p2.x()
        y = mt2 * p0.y() + 2 * mt * local_t * p1.y() + t2 * p2.y()
        
        return QPointF(x, y)

    def tangent_at_parameter(self, t):
        """Get the tangent vector at parameter t (0.0 to 1.0)."""
        if len(self._points) < 3:
            return QPointF(1, 0)
        
        # Calculate which segment t falls into
        total_segments = self.segment_count
        if total_segments == 0:
            return QPointF(1, 0)
        
        segment_t = t * total_segments
        segment_index = int(segment_t)
        local_t = segment_t - segment_index
        
        # Clamp segment_index to valid range
        segment_index = max(0, min(segment_index, total_segments - 1))
        
        # Get the 3 points for this segment
        segment = self.get_segment(segment_index)
        if not segment:
            return QPointF(1, 0)
        
        # Calculate quadratic Bezier tangent
        p0, p1, p2 = segment
        
        # Tangent formula: B'(t) = 2(1-t)(P₁-P₀) + 2t(P₂-P₁)
        mt = 1 - local_t
        
        dx = 2 * mt * (p1.x() - p0.x()) + 2 * local_t * (p2.x() - p1.x())
        dy = 2 * mt * (p1.y() - p0.y()) + 2 * local_t * (p2.y() - p1.y())
        
        # Normalize the tangent vector
        length = (dx * dx + dy * dy) ** 0.5
        if length > 0:
            return QPointF(dx / length, dy / length)
        else:
            return QPointF(1, 0)

    def moveBy(self, dx, dy):
        """Move all points by the specified offset."""
        self.prepareGeometryChange()
        self._points = [QPointF(pt.x() + dx, pt.y() + dy) for pt in self._points]
        self.update() 