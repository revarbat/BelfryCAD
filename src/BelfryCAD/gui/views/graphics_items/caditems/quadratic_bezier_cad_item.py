"""
QuadraticBezierCadItem - A quadratic Bezier curve CAD item defined by an arbitrary number of points.
Points follow the pattern: [path_point, control_point, path_point, control_point, ...]
"""

import math

from enum import Enum
from typing import List, Optional

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QBrush, QPainterPath, QPainterPathStroker, Qt

from ..cad_item import CadItem
from ..control_points import ControlPoint, SquareControlPoint, DiamondControlPoint
from ..cad_rect import CadRect


class PathPointState(Enum):
    """States for path points in quadratic Bezier curves."""
    SMOOTH = "smooth"           # Control points at opposite angles
    EQUIDISTANT = "equidistant" # Control points at opposite angles and equal distances
    DISJOINT = "disjoint"       # No constraints on control points


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
        self._control_points = []
        
        # Track state for each path point (every 2nd point)
        self._path_point_states = []
        
        # Convert all points to QPointF
        for point in points:
            if isinstance(point, (list, tuple)):
                self._points.append(QPointF(point[0], point[1]))
            else:
                self._points.append(QPointF(point))
        
        # Initialize states for path points
        self._initialize_path_point_states()
        
        # Create control points
        self.createControls()

    def _initialize_path_point_states(self):
        """Initialize states for all path points based on their geometric relationships."""
        self._path_point_states = []
        for i in range(0, len(self._points), 2):
            path_point_index = i // 2
            state = self._determine_path_point_state(path_point_index)
            self._path_point_states.append(state)

    def _determine_path_point_state(self, path_point_index):
        """Determine the state of a path point based on its adjacent control points."""
        # Convert path point index to actual point index
        point_index = path_point_index * 2
        
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
        return point_index // 2

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
            
            # Normalize the average unit vector
            avg_length = math.sqrt(avg_unit_x**2 + avg_unit_y**2)
            if avg_length > 0:
                avg_unit_x /= avg_length
                avg_unit_y /= avg_length
            
            # Set both control points to be opposite to this average direction
            # First control point in the average direction
            new_prev_control = QPointF(
                path_point.x() + prev_distance * avg_unit_x,
                path_point.y() + prev_distance * avg_unit_y
            )
            # Second control point in the opposite direction
            new_next_control = QPointF(
                path_point.x() + next_distance * (-avg_unit_x),
                path_point.y() + next_distance * (-avg_unit_y)
            )
            
            self._points[point_index - 1] = new_prev_control
            self._points[point_index + 1] = new_next_control

    def _update_control_point_visual(self, point_index):
        """Update the visual representation of a control point based on its state."""
        if hasattr(self, '_control_points') and self._control_points:
            state = self._get_path_point_state(point_index)
            
            # Remove old control point from scene if it exists
            if point_index < len(self._control_points):
                old_cp = self._control_points[point_index]
                if old_cp and old_cp.scene():
                    old_cp.scene().removeItem(old_cp)
            
            # Create new control point with appropriate type
            def make_setter(index):
                return lambda pos: self._set_point(index, pos)
            
            if state == PathPointState.SMOOTH:
                new_cp = SquareControlPoint(
                    cad_item=self,
                    setter=make_setter(point_index)
                )
            elif state == PathPointState.EQUIDISTANT:
                new_cp = ControlPoint(
                    cad_item=self,
                    setter=make_setter(point_index)
                )
            else:  # DISJOINT
                new_cp = DiamondControlPoint(
                    cad_item=self,
                    setter=make_setter(point_index)
                )
            
            # Update the control point list
            if point_index < len(self._control_points):
                self._control_points[point_index] = new_cp
            else:
                # Extend the list if needed
                while len(self._control_points) <= point_index:
                    self._control_points.append(None)
                self._control_points[point_index] = new_cp
            
            # Update position
            if point_index < len(self._points):
                new_cp.setPos(self._points[point_index])
            
            # Add the new control point to the scene
            if self.scene():
                self.scene().addItem(new_cp)

    def _apply_path_point_constraints(self, point_index):
        """Apply constraints when a control point is moved."""
        # This method can be called when control points are moved to maintain state constraints
        pass

    def _adjust_control_point_angles(self, path_point_index, moved_control_index):
        """Adjust the opposite control point when one is moved to maintain state constraints."""
        point_index = path_point_index * 2
        state = self._get_path_point_state(point_index)
        
        if state == PathPointState.DISJOINT:
            return  # No constraints to apply
        
        path_point = self._points[point_index]
        prev_control = self._points[point_index - 1]
        next_control = self._points[point_index + 1]
        
        # Determine which control point was moved and which needs adjustment
        if moved_control_index == point_index - 1:
            # Previous control was moved, adjust next control
            moved_control = prev_control
            target_control = next_control
            target_index = point_index + 1
        elif moved_control_index == point_index + 1:
            # Next control was moved, adjust previous control
            moved_control = next_control
            target_control = prev_control
            target_index = point_index - 1
        else:
            return  # Not a relevant control point
        
        # Calculate vector from path point to moved control
        moved_vector = moved_control - path_point
        moved_angle = math.atan2(moved_vector.y(), moved_vector.x())
        moved_distance = math.sqrt(moved_vector.x()**2 + moved_vector.y()**2)
        
        if state == PathPointState.SMOOTH:
            # Make the target control point opposite in angle
            target_angle = moved_angle + math.pi
            target_distance = math.sqrt((target_control.x() - path_point.x())**2 + 
                                      (target_control.y() - path_point.y())**2)
            
            new_target_control = QPointF(
                path_point.x() + target_distance * math.cos(target_angle),
                path_point.y() + target_distance * math.sin(target_angle)
            )
            
        elif state == PathPointState.EQUIDISTANT:
            # Make the target control point opposite in angle and equal in distance
            target_angle = moved_angle + math.pi
            
            new_target_control = QPointF(
                path_point.x() + moved_distance * math.cos(target_angle),
                path_point.y() + moved_distance * math.sin(target_angle)
            )
        
        else:
            return  # DISJOINT state, no constraints
        
        # Update the target control point
        self._points[target_index] = new_target_control
        
        # Update the visual representation
        if hasattr(self, '_control_points') and target_index < len(self._control_points):
            cp = self._control_points[target_index]
            if cp:
                cp.setPos(new_target_control)

    def _handle_control_point_click(self, point_index, modifiers):
        """Handle control point clicks for state cycling."""
        # Check if this is a path point (every 2nd point)
        if point_index % 2 == 0:
            # Check for Command key (Ctrl on Windows/Linux, Cmd on Mac)
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                self._cycle_path_point_state(point_index)
                return True
        return False

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

    def _create_controls_impl(self):
        """Create control points for the Bezier curve and return them."""
        # Create control points for all points
        self._control_points = []
        
        for i in range(len(self._points)):
            # Use a default argument to capture the current value of i
            def make_setter(index):
                return lambda pos: self._set_point(index, pos)
            
            # Use different control point styles based on state for path points
            if i % 2 == 0:  # Path points (every 2nd point, starting with 0)
                state = self._get_path_point_state(i)
                if state == PathPointState.SMOOTH:
                    cp = SquareControlPoint(
                        cad_item=self,
                        setter=make_setter(i)
                    )
                elif state == PathPointState.EQUIDISTANT:
                    cp = ControlPoint(
                        cad_item=self,
                        setter=make_setter(i)
                    )
                else:  # DISJOINT
                    cp = DiamondControlPoint(
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

    def getControlPoints(
            self,
            exclude_cps: Optional[List['ControlPoint']] = None
    ) -> List[QPointF]:
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
            self._points[index] = new_position
            
            # Apply state constraints if this is a control point adjacent to a path point
            if index % 2 == 1:  # Control point
                # Check if this control point is adjacent to a path point
                if index > 0 and index < len(self._points) - 1:
                    # This control point is between two path points
                    path_point_index = index // 2
                    self._adjust_control_point_angles(path_point_index, index)

    def paint_item_with_color(self, painter, option, widget=None, color=None):
        """Draw the Bezier curve content with a custom color."""
        if len(self._points) < 3:
            return

        painter.save()

        # Use provided color or fall back to default
        pen_color = color if color is not None else self._color
        pen = QPen(pen_color, self._line_width)
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

    def get_path_point_state(self, path_point_index):
        """Get the state of a path point by its path point index."""
        if 0 <= path_point_index < len(self._path_point_states):
            return self._path_point_states[path_point_index]
        return PathPointState.DISJOINT

    def set_path_point_state(self, path_point_index, state):
        """Set the state of a path point by its path point index."""
        if 0 <= path_point_index < len(self._path_point_states):
            self._path_point_states[path_point_index] = state
            # Update the visual representation
            point_index = path_point_index * 2
            self._update_control_point_visual(point_index)

    def get_all_path_point_states(self):
        """Get all path point states."""
        return self._path_point_states.copy()

    def set_all_path_point_states(self, states):
        """Set all path point states."""
        if len(states) == len(self._path_point_states):
            self._path_point_states = states.copy()
            # Update all visual representations
            for i in range(0, len(self._points), 2):
                self._update_control_point_visual(i) 