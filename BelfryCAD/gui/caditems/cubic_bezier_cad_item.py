"""
CubicBezierCadItem - A cubic Bezier curve CAD item defined by an arbitrary number of points.
Points follow the pattern: [path_point, control1, control2, path_point, control1, control2, ...]
"""

import math
from enum import Enum
from typing import List, Optional
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QPen, QColor, QBrush, QPainterPath, QPainterPathStroker
from BelfryCAD.gui.cad_item import CadItem
from BelfryCAD.gui.control_points import ControlPoint, SquareControlPoint, DiamondControlPoint
from BelfryCAD.gui.cad_rect import CadRect


class PathPointState(Enum):
    """States for path points in cubic Bezier curves."""
    SMOOTH = "smooth"           # Control points at opposite angles
    EQUIDISTANT = "equidistant" # Control points at opposite angles and equal distances
    DISJOINT = "disjoint"       # No constraints on control points


class CubicBezierCadItem(CadItem):
    """A cubic Bezier curve CAD item defined by an arbitrary number of points.
    
    Points follow the pattern:
    - 1st point: path point (on the curve)
    - 2nd point: control point for 1st segment
    - 3rd point: control point for 1st segment
    - 4th point: path point (on the curve)
    - 5th point: control point for 2nd segment
    - 6th point: control point for 2nd segment
    - And so on...
    
    This creates a smooth curve that passes through every 3rd point.
    """

    def __init__(self, points=None, color=QColor(0, 0, 255), line_width=0.05):
        super().__init__()
        
        # Initialize with default points if none provided
        if points is None:
            points = [
                QPointF(0, 0),    # 1st path point
                QPointF(1, 1),    # control1 for 1st segment
                QPointF(2, -1),   # control2 for 1st segment
                QPointF(3, 0),    # 2nd path point
            ]
        
        self._points = []
        self._color = color
        self._line_width = line_width
        self._control_points = []
        
        # Track state for each path point (every 3rd point)
        self._path_point_states = []
        
        # Convert all points to QPointF
        for point in points:
            if isinstance(point, (list, tuple)):
                self._points.append(QPointF(point[0], point[1]))
            else:
                self._points.append(QPointF(point))
        
        # Initialize states for path points
        self._initialize_path_point_states()

    def _initialize_path_point_states(self):
        """Initialize states for all path points based on their geometric relationships."""
        self._path_point_states = []
        for i in range(0, len(self._points), 3):
            path_point_index = i // 3
            state = self._determine_path_point_state(path_point_index)
            self._path_point_states.append(state)

    def _determine_path_point_state(self, path_point_index):
        """Determine the state of a path point based on its adjacent control points."""
        # Convert path point index to actual point index
        point_index = path_point_index * 3
        
        if point_index < 1 or point_index >= len(self._points) - 1:
            return PathPointState.DISJOINT  # Can't determine without both adjacent control points
        
        path_point = self._points[point_index]
        prev_control = self._points[point_index - 1]
        next_control = self._points[point_index + 1]
        
        # Calculate vectors from path point to control points
        prev_vector = prev_control - path_point
        next_vector = next_control - path_point
        
        # Calculate distances
        prev_distance = math.sqrt(prev_vector.x()**2 + prev_vector.y()**2)
        next_distance = math.sqrt(next_vector.x()**2 + next_vector.y()**2)
        
        # Calculate angles
        prev_angle = math.atan2(prev_vector.y(), prev_vector.x())
        next_angle = math.atan2(next_vector.y(), next_vector.x())
        
        # Calculate angle difference (normalized to [0, π])
        angle_diff = abs(prev_angle - next_angle)
        # Normalize to [0, π] range
        if angle_diff > math.pi:
            angle_diff = 2 * math.pi - angle_diff
        
        # Check if angles are nearly opposite (within 5 degrees = ~0.087 radians)
        # Angles are opposite if they differ by π (180 degrees)
        angles_opposite = abs(angle_diff - math.pi) < 0.087
        
        if angles_opposite:
            # Check if distances are nearly equal (within 5% of each other)
            if prev_distance > 0 and next_distance > 0:
                distance_ratio = min(prev_distance, next_distance) / max(prev_distance, next_distance)
                distances_equal = distance_ratio > 0.95
            else:
                distances_equal = False
            
            if distances_equal:
                return PathPointState.EQUIDISTANT
            else:
                return PathPointState.SMOOTH
        else:
            return PathPointState.DISJOINT

    def _get_path_point_index(self, point_index):
        """Get the path point index for a given point index."""
        return point_index // 3

    def _get_path_point_state(self, point_index):
        """Get the state of a path point."""
        path_index = self._get_path_point_index(point_index)
        if 0 <= path_index < len(self._path_point_states):
            return self._path_point_states[path_index]
        return PathPointState.DISJOINT

    def _set_path_point_state(self, point_index, state):
        """Set the state of a path point."""
        path_index = self._get_path_point_index(point_index)
        if 0 <= path_index < len(self._path_point_states):
            self._path_point_states[path_index] = state
            # Update the control point visual representation
            self._update_control_point_visual(point_index)

    def _cycle_path_point_state(self, point_index):
        """Cycle through states for a path point."""
        current_state = self._get_path_point_state(point_index)
        if current_state == PathPointState.SMOOTH:
            new_state = PathPointState.EQUIDISTANT
        elif current_state == PathPointState.EQUIDISTANT:
            new_state = PathPointState.DISJOINT
        else:  # DISJOINT
            new_state = PathPointState.SMOOTH
        
        self._set_path_point_state(point_index, new_state)
        
        # Apply transition constraints based on the state change
        self._apply_state_transition_constraints(point_index, current_state, new_state)

    def _apply_state_transition_constraints(self, point_index, old_state, new_state):
        """Apply constraints when transitioning between states."""
        path_point = self._points[point_index]
        prev_control = None
        next_control = None
        
        # Get adjacent control points
        if point_index > 0:
            prev_control = self._points[point_index - 1]
        if point_index < len(self._points) - 1:
            next_control = self._points[point_index + 1]
        
        if prev_control is None or next_control is None:
            return
        
        # Calculate current vectors and distances
        prev_vector = prev_control - path_point
        next_vector = next_control - path_point
        prev_distance = math.sqrt(prev_vector.x()**2 + prev_vector.y()**2)
        next_distance = math.sqrt(next_vector.x()**2 + next_vector.y()**2)
        prev_angle = math.atan2(prev_vector.y(), prev_vector.x())
        next_angle = math.atan2(next_vector.y(), next_vector.x())
        
        # Apply transition-specific constraints
        if old_state == PathPointState.SMOOTH and new_state == PathPointState.EQUIDISTANT:
            # Average and equalize the distances
            avg_distance = (prev_distance + next_distance) / 2
            
            # Update both control points to be equidistant while maintaining their current angles
            new_prev_control = QPointF(
                path_point.x() + avg_distance * math.cos(prev_angle),
                path_point.y() + avg_distance * math.sin(prev_angle)
            )
            new_next_control = QPointF(
                path_point.x() + avg_distance * math.cos(next_angle),
                path_point.y() + avg_distance * math.sin(next_angle)
            )
            
            self._points[point_index - 1] = new_prev_control
            self._points[point_index + 1] = new_next_control
            
        elif old_state == PathPointState.DISJOINT and new_state == PathPointState.SMOOTH:
            # Make angles exactly opposite (180 degrees apart)
            # Handle angle averaging properly by converting to unit vectors
            prev_unit_x = math.cos(prev_angle)
            prev_unit_y = math.sin(prev_angle)
            next_unit_x = math.cos(next_angle)
            next_unit_y = math.sin(next_angle)
            
            # Average the unit vectors
            avg_unit_x = (prev_unit_x + next_unit_x) / 2
            avg_unit_y = (prev_unit_y + next_unit_y) / 2
            
            # Normalize to get the average angle
            avg_magnitude = math.sqrt(avg_unit_x**2 + avg_unit_y**2)
            if avg_magnitude > 0:
                avg_unit_x /= avg_magnitude
                avg_unit_y /= avg_magnitude
                avg_angle = math.atan2(avg_unit_y, avg_unit_x)
            else:
                # Fallback: use the first angle
                avg_angle = prev_angle
            
            # Set one control point to the average angle and the other to the opposite
            new_prev_control = QPointF(
                path_point.x() + prev_distance * avg_unit_x,
                path_point.y() + prev_distance * avg_unit_y
            )
            new_next_control = QPointF(
                path_point.x() + next_distance * (-avg_unit_x),
                path_point.y() + next_distance * (-avg_unit_y)
            )
            
            self._points[point_index - 1] = new_prev_control
            self._points[point_index + 1] = new_next_control

    def _update_control_point_visual(self, point_index):
        """Update the visual representation of a control point based on its state."""
        if not hasattr(self, '_control_points') or point_index >= len(self._control_points):
            return
        
        state = self._get_path_point_state(point_index)
        current_cp = self._control_points[point_index]
        
        # Create new control point with appropriate type
        if state == PathPointState.SMOOTH:
            new_cp = SquareControlPoint(cad_item=self, setter=current_cp.setter)
        elif state == PathPointState.EQUIDISTANT:
            new_cp = ControlPoint(cad_item=self, setter=current_cp.setter)
        else:  # DISJOINT
            new_cp = DiamondControlPoint(cad_item=self, setter=current_cp.setter)
        
        # Copy position and other properties
        new_cp.setPos(current_cp.pos())
        new_cp.setZValue(current_cp.zValue())
        
        # Remove the old control point from the scene
        scene = current_cp.scene() if hasattr(current_cp, 'scene') else None
        if scene is not None:
            scene.removeItem(current_cp)
        
        # Replace the control point in the list
        self._control_points[point_index] = new_cp
        
        # Add the new control point to the scene if needed
        if scene is not None:
            scene.addItem(new_cp)

    def _apply_path_point_constraints(self, point_index):
        """Apply constraints for a path point based on its state. Only applies when the path point itself is moved."""
        state = self._get_path_point_state(point_index)
        if state == PathPointState.DISJOINT:
            return  # No constraints
        # Only apply when the path point itself is moved
        # (i.e., do not adjust angles/distances for control point moves)
        # When a path point is moved, move both adjacent control points by the same delta (already handled in _set_point)
        # No further action needed here for SMOOTH/EQUIDISTANT
        pass

    def _adjust_control_point_angles(self, path_point_index, moved_control_index):
        """Adjust control point angles when a control point is moved.
        
        Args:
            path_point_index: Index of the path point (on-bezier point)
            moved_control_index: Index of the control point that was moved
        """
        state = self._get_path_point_state(path_point_index)
        if state == PathPointState.DISJOINT:
            return  # No angle constraints for disjoint state
        
        path_point = self._points[path_point_index]
        prev_control = None
        next_control = None
        
        if path_point_index > 0:
            prev_control = self._points[path_point_index - 1]
        if path_point_index < len(self._points) - 1:
            next_control = self._points[path_point_index + 1]
        
        if prev_control is None or next_control is None:
            return
        
        if moved_control_index == path_point_index - 1:  # prev_control was moved
            moved_vector = prev_control - path_point
            moved_angle = math.atan2(moved_vector.y(), moved_vector.x())
            moved_distance = math.sqrt(moved_vector.x()**2 + moved_vector.y()**2)
            opposite_angle = moved_angle + math.pi
            
            if state == PathPointState.EQUIDISTANT:
                # Set the other control point to the same distance, opposite angle
                new_next_control = QPointF(
                    path_point.x() + moved_distance * math.cos(opposite_angle),
                    path_point.y() + moved_distance * math.sin(opposite_angle)
                )
                self._points[path_point_index + 1] = new_next_control
            else:  # SMOOTH
                # Keep the other control point's distance, but set to opposite angle
                other_vector = next_control - path_point
                other_distance = math.sqrt(other_vector.x()**2 + other_vector.y()**2)
                new_next_control = QPointF(
                    path_point.x() + other_distance * math.cos(opposite_angle),
                    path_point.y() + other_distance * math.sin(opposite_angle)
                )
                self._points[path_point_index + 1] = new_next_control
                
        elif moved_control_index == path_point_index + 1:  # next_control was moved
            moved_vector = next_control - path_point
            moved_angle = math.atan2(moved_vector.y(), moved_vector.x())
            moved_distance = math.sqrt(moved_vector.x()**2 + moved_vector.y()**2)
            opposite_angle = moved_angle + math.pi
            
            if state == PathPointState.EQUIDISTANT:
                # Set the other control point to the same distance, opposite angle
                new_prev_control = QPointF(
                    path_point.x() + moved_distance * math.cos(opposite_angle),
                    path_point.y() + moved_distance * math.sin(opposite_angle)
                )
                self._points[path_point_index - 1] = new_prev_control
            else:  # SMOOTH
                # Keep the other control point's distance, but set to opposite angle
                other_vector = prev_control - path_point
                other_distance = math.sqrt(other_vector.x()**2 + other_vector.y()**2)
                new_prev_control = QPointF(
                    path_point.x() + other_distance * math.cos(opposite_angle),
                    path_point.y() + other_distance * math.sin(opposite_angle)
                )
                self._points[path_point_index - 1] = new_prev_control

    def _handle_control_point_click(self, point_index, modifiers):
        """Handle control point click events."""
        # Check if this is a path point (every 3rd point) and Command is pressed
        if point_index % 3 == 0 and modifiers & Qt.KeyboardModifier.ControlModifier:
            self._cycle_path_point_state(point_index)
            self.updateControls()
            self.update()
            return True
        return False

    def boundingRect(self):
        """Return the bounding rectangle of the Bezier curve."""
        if len(self._points) < 4:
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
            
            # Use different control point styles based on position and state
            if i % 3 == 0:  # Path points (every 3rd point, starting with 0)
                state = self._get_path_point_state(i)
                if state == PathPointState.SMOOTH:
                    cp = SquareControlPoint(cad_item=self, setter=make_setter(i))
                elif state == PathPointState.EQUIDISTANT:
                    cp = ControlPoint(cad_item=self, setter=make_setter(i))
                else:  # DISJOINT
                    cp = DiamondControlPoint(cad_item=self, setter=make_setter(i))
            else:  # Control points
                cp = ControlPoint(cad_item=self, setter=make_setter(i))
            
            self._control_points.append(cp)
        
        self.updateControls()
        
        # Return the list of control points
        return self._control_points

    def updateControls(self):
        """Update control point positions."""
        if not hasattr(self, '_control_points'):
            return
        for i, cp in enumerate(self._control_points):
            if cp and i < len(self._points):
                # Points are already in local coordinates
                cp.setPos(self._points[i])

    def getControlPoints(self, exclude_cps: Optional[List['ControlPoint']] = None) -> List[QPointF]:
        """Return list of control point positions (excluding ControlDatums)."""
        if exclude_cps is None:
            return self._points.copy()
        control_points = []
        for i, pt in enumerate(self._points):
            if not self._should_exclude_control_point(i, exclude_cps):
                control_points.append(pt)
        return control_points

    def _set_point(self, index, new_position):
        """Set a specific point from control point movement."""
        # new_position is already in local coordinates
        
        if 0 <= index < len(self._points):
            old_position = self._points[index]
            self._points[index] = new_position

            # If this is an on-bezier point, move adjacent control points by the same delta
            if index % 3 == 0:
                delta = new_position - old_position
                if index - 1 >= 0:
                    self._points[index - 1] = self._points[index - 1] + delta
                if index + 1 < len(self._points):
                    self._points[index + 1] = self._points[index + 1] + delta

            # Handle control point angle adjustment, only if not DISJOINT
            if index % 3 == 1:  # This is control1, affects previous path point
                prev_path_index = index - 1
                if prev_path_index >= 0:
                    state = self._get_path_point_state(prev_path_index)
                    if state != PathPointState.DISJOINT:
                        self._adjust_control_point_angles(prev_path_index, index)
            elif index % 3 == 2:  # This is control2, affects next path point
                next_path_index = index + 1
                if next_path_index < len(self._points):
                    state = self._get_path_point_state(next_path_index)
                    if state != PathPointState.DISJOINT:
                        self._adjust_control_point_angles(next_path_index, index)

            # Only apply constraints if the path point is not in DISJOINT state
            if index % 3 == 0:  # This is a path point
                if self._get_path_point_state(index) != PathPointState.DISJOINT:
                    self._apply_path_point_constraints(index)
            elif index % 3 == 1:  # This is control1, affects previous path point
                prev_path_index = index - 1
                if prev_path_index >= 0 and self._get_path_point_state(prev_path_index) != PathPointState.DISJOINT:
                    self._apply_path_point_constraints(prev_path_index)
            elif index % 3 == 2:  # This is control2, affects next path point
                next_path_index = index + 1
                if next_path_index < len(self._points) and self._get_path_point_state(next_path_index) != PathPointState.DISJOINT:
                    self._apply_path_point_constraints(next_path_index)

    def paint_item(self, painter, option, widget=None):
        """Draw the Bezier curve content."""
        if len(self._points) < 4:
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
            for i in range(0, len(self._points) - 3, 3):
                if i + 3 < len(self._points):
                    # Draw control lines for this segment
                    painter.drawLine(self._points[i], self._points[i + 1])      # path to control1
                    painter.drawLine(self._points[i + 2], self._points[i + 3])  # control2 to next path
            
            painter.restore()

    def _create_bezier_path(self):
        """Create the Bezier curve path."""
        path = QPainterPath()
        
        if len(self._points) < 4:
            return path
        
        # Start at the first point
        path.moveTo(self._points[0])
        
        # Create cubic Bezier segments
        for i in range(0, len(self._points) - 3, 3):
            if i + 3 < len(self._points):
                # Each segment uses 4 points: current, control1, control2, next
                path.cubicTo(
                    self._points[i + 1],  # control1
                    self._points[i + 2],  # control2
                    self._points[i + 3]   # next path point
                )
        
        return path

    def add_segment(self, control1, control2, end_point):
        """Add a new segment to the Bezier curve."""
        if isinstance(control1, (list, tuple)):
            control1 = QPointF(control1[0], control1[1])
        if isinstance(control2, (list, tuple)):
            control2 = QPointF(control2[0], control2[1])
        if isinstance(end_point, (list, tuple)):
            end_point = QPointF(end_point[0], end_point[1])
        
        self._points.extend([control1, control2, end_point])

    def insert_segment(self, segment_index, control1, control2, end_point):
        """Insert a new segment at the specified index."""
        if isinstance(control1, (list, tuple)):
            control1 = QPointF(control1[0], control1[1])
        if isinstance(control2, (list, tuple)):
            control2 = QPointF(control2[0], control2[1])
        if isinstance(end_point, (list, tuple)):
            end_point = QPointF(end_point[0], end_point[1])
        
        # Calculate the insertion index (3 points per segment)
        insert_index = segment_index * 3 + 1
        
        if insert_index <= len(self._points):
            self._points.insert(insert_index, control1)
            self._points.insert(insert_index + 1, control2)
            self._points.insert(insert_index + 2, end_point)

    def remove_segment(self, segment_index):
        """Remove a segment at the specified index."""
        # Calculate the start index of the segment (3 points per segment)
        start_index = segment_index * 3 + 1
        
        if start_index + 2 < len(self._points):
            # Remove the 3 points of the segment
            del self._points[start_index:start_index + 3]

    def get_path_points(self):
        """Get all path points (every 3rd point, starting with 0)."""
        return [self._points[i] for i in range(0, len(self._points), 3)]

    def get_control_points(self):
        """Get all control points (not path points)."""
        return [self._points[i] for i in range(len(self._points)) if i % 3 != 0]

    def get_segment(self, segment_index):
        """Get the 4 points of a specific segment."""
        start_index = segment_index * 3
        if start_index + 3 < len(self._points):
            return [
                self._points[start_index],     # path point
                self._points[start_index + 1], # control1
                self._points[start_index + 2], # control2
                self._points[start_index + 3]  # next path point
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
        
        # Reinitialize path point states
        self._initialize_path_point_states()

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
        if len(self._points) < 4:
            return 0
        return (len(self._points) - 1) // 3

    def point_at_parameter(self, t):
        """Get a point on the curve at parameter t (0.0 to 1.0)."""
        if len(self._points) < 4:
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
        
        # Get the 4 points for this segment
        segment = self.get_segment(segment_index)
        if not segment:
            return self._points[0] if self._points else QPointF(0, 0)
        
        # Calculate cubic Bezier point
        p0, p1, p2, p3 = segment
        
        # Cubic Bezier formula: B(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
        t2 = local_t * local_t
        t3 = t2 * local_t
        mt = 1 - local_t
        mt2 = mt * mt
        mt3 = mt2 * mt
        
        x = mt3 * p0.x() + 3 * mt2 * local_t * p1.x() + 3 * mt * t2 * p2.x() + t3 * p3.x()
        y = mt3 * p0.y() + 3 * mt2 * local_t * p1.y() + 3 * mt * t2 * p2.y() + t3 * p3.y()
        
        return QPointF(x, y)

    def tangent_at_parameter(self, t):
        """Get the tangent vector at parameter t (0.0 to 1.0)."""
        if len(self._points) < 4:
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
        
        # Get the 4 points for this segment
        segment = self.get_segment(segment_index)
        if not segment:
            return QPointF(1, 0)
        
        # Calculate cubic Bezier tangent
        p0, p1, p2, p3 = segment
        
        # Tangent formula: B'(t) = 3(1-t)²(P₁-P₀) + 6(1-t)t(P₂-P₁) + 3t²(P₃-P₂)
        t2 = local_t * local_t
        mt = 1 - local_t
        mt2 = mt * mt
        
        dx = 3 * mt2 * (p1.x() - p0.x()) + 6 * mt * local_t * (p2.x() - p1.x()) + 3 * t2 * (p3.x() - p2.x())
        dy = 3 * mt2 * (p1.y() - p0.y()) + 6 * mt * local_t * (p2.y() - p1.y()) + 3 * t2 * (p3.y() - p2.y())
        
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

    def sceneEvent(self, event):
        """Handle scene events to detect Command-clicks on path points."""
        if (event.type() == event.Type.GraphicsSceneMousePress and 
            event.button() == Qt.MouseButton.LeftButton and
            event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            
            # Check if click is on a path point control point
            for i in range(0, len(self._points), 3):
                if i < len(self._control_points):
                    cp = self._control_points[i]
                    if cp and cp.contains(event.pos() - cp.scenePos()):
                        self._cycle_path_point_state(i)
                        self.updateControls()
                        self.update()
                        return True
        
        return super().sceneEvent(event)

    def get_path_point_state(self, path_point_index):
        """Get the state of a path point by its index (0, 1, 2, etc.)."""
        if 0 <= path_point_index < len(self._path_point_states):
            return self._path_point_states[path_point_index]
        return PathPointState.DISJOINT

    def set_path_point_state(self, path_point_index, state):
        """Set the state of a path point by its index (0, 1, 2, etc.)."""
        if 0 <= path_point_index < len(self._path_point_states):
            self._path_point_states[path_point_index] = state
            # Apply constraints
            point_index = path_point_index * 3
            if point_index < len(self._points):
                self._apply_path_point_constraints(point_index)
                self._update_control_point_visual(point_index)
            self.updateControls()
            self.update()

    def get_all_path_point_states(self):
        """Get all path point states as a list."""
        return self._path_point_states.copy()

    def set_all_path_point_states(self, states):
        """Set all path point states from a list."""
        if len(states) == len(self._path_point_states):
            self._path_point_states = states.copy()
            # Apply constraints to all path points
            for i in range(0, len(self._points), 3):
                self._apply_path_point_constraints(i)
                self._update_control_point_visual(i)
            self.updateControls()
            self.update()