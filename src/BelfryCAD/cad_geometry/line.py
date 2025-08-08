"""
2D Line Class for CAD Geometry

This module provides the Line2D class for representing 2D line segments
with various geometric operations and calculations.
"""

import math
from typing import Optional, Tuple, Union, List
from .shapes import Shape2D, ShapeType
from .point import Point2D, EPSILON
from .transform import Transform2D


class Line2D(Shape2D):
    """
    A 2D line segment defined by start and end points.
    
    This class provides various geometric operations including intersection,
    distance calculations, and transformations.
    """

    def __init__(self, start, end = None):
        """
        Initialize a line segment.
        
        Args:
            start: Start point of the line
            end: End point of the line (if None, creates a point at start)
        """
        if not isinstance(start, Point2D):
            start = Point2D(start)

        # If end is provided, use it to create a line
        if end is not None:
            if not isinstance(end, Point2D):
                end = Point2D(end)
            self._start = start
            self._end = end
            return

        # Only one argument provided (in start)
        # If start is a line, use it to create a line
        if isinstance(start, Line2D):
            self._start = start._start
            self._end = start._end
            return
        
        # If start has p1 and p2 properties, use them to create a line
        try:
            self._start = Point2D(start.p1)  # type: ignore
            self._end = Point2D(start.p2)  # type: ignore
            return
        except:
            pass

        # If start has p1() and p2(), use them to create a line
        try:
            self._start = Point2D(start.p1())  # type: ignore
            self._end = Point2D(start.p2())  # type: ignore
            return
        except:
            pass

        # If start is a list-like object, use it to create a line
        try:
            if len(start) == 2:
                self._start = Point2D(start[0])
                self._end = Point2D(start[1])
                return
            elif len(start) == 4:
                self._start = Point2D(start[0], start[1])
                self._end = Point2D(start[2], start[3])
                return
        except:
            pass

        raise ValueError(f"Invalid start point: {start}")

    def __repr__(self) -> str:
        return f"Line2D({self._start}, {self._end})"

    def __str__(self) -> str:
        return f"Line2D({self._start}, {self._end})"

    def decompose(self, into: List[ShapeType] = [], tolerance: float = 0.001) -> List['Shape2D']:
        """Decompose line into other shape types."""
        if ShapeType.LINE in into:
            return [self]
        if ShapeType.POLYLINE in into:
            from .polyline import PolyLine2D
            return [PolyLine2D([self._start, self._end])]
        raise ValueError(f"Cannot decompose line into any of {into}")

    @property
    def start(self) -> Point2D:
        """Get the start point."""
        return self._start

    @start.setter
    def start(self, value: Point2D):
        """Set the start point."""
        if not isinstance(value, Point2D):
            value = Point2D(value)
        self._start = value

    @property
    def end(self) -> Point2D:
        """Get the end point."""
        return self._end

    @end.setter
    def end(self, value: Point2D):
        """Set the end point."""
        if not isinstance(value, Point2D):
            value = Point2D(value)
        self._end = value

    @property
    def vector(self) -> Point2D:
        """Get the vector from start to end."""
        return self._end - self._start

    @property
    def unit_vector(self) -> Point2D:
        """Get the unit vector in the direction of the line."""
        return self.vector.unit_vector

    @property
    def perpendicular_vector(self) -> Point2D:
        """Get the perpendicular vector (rotated 90 degrees counterclockwise)."""
        return self.vector.perpendicular_vector

    @property
    def length(self) -> float:
        """Get the length of the line segment."""
        return self._start.distance_to(self._end)

    @property
    def midpoint(self) -> Point2D:
        """Get the midpoint of the line segment."""
        return Point2D(
            (self._start._x + self._end._x) / 2,
            (self._start._y + self._end._y) / 2
        )

    @midpoint.setter
    def midpoint(self, value: Point2D):
        """Set the midpoint (moves the line while preserving length and direction)."""
        if not isinstance(value, Point2D):
            value = Point2D(value)
        
        current_mid = self.midpoint
        offset = value - current_mid
        self._start = self._start + offset
        self._end = self._end + offset

    @property
    def angle_radians(self) -> float:
        """Get the angle of the line in radians."""
        return self.vector.angle_radians

    @angle_radians.setter
    def angle_radians(self, value: float):
        """Set the angle of the line (rotates around start point)."""
        current_length = self.length
        self._end = self._start + Point2D(current_length, 0).rotate(value)

    @property
    def angle_degrees(self) -> float:
        """Get the angle of the line in degrees."""
        return math.degrees(self.angle_radians)

    @angle_degrees.setter
    def angle_degrees(self, value: float):
        """Set the angle of the line in degrees."""
        self.angle_radians = math.radians(value)

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get the bounding box of the line."""
        min_x = min(self._start._x, self._end._x)
        max_x = max(self._start._x, self._end._x)
        min_y = min(self._start._y, self._end._y)
        max_y = max(self._start._y, self._end._y)
        return (min_x, min_y, max_x, max_y)

    def point_at_parameter(self, t: float) -> Point2D:
        """
        Get the point at parameter t along the line (0 <= t <= 1).
        
        Args:
            t: Parameter value (0 = start, 1 = end)
            
        Returns:
            Point at parameter t
        """
        return Point2D(
            self._start._x + t * (self._end._x - self._start._x),
            self._start._y + t * (self._end._y - self._start._y)
        )

    def distance_to_point(self, point: Point2D) -> float:
        """
        Calculate the distance from a point to this line.
        
        Args:
            point: The point to measure distance from
            
        Returns:
            Distance from point to line
        """
        # Vector from start to point
        to_point = point - self._start
        
        # Vector from start to end
        line_vector = self.vector
        
        # Project to_point onto line_vector
        line_length_sq = line_vector.magnitude_squared
        if line_length_sq < EPSILON:
            # Degenerate line (point)
            return self._start.distance_to(point)
        
        # Parameter of closest point on line
        t = to_point.dot(line_vector) / line_length_sq
        
        # Clamp to line segment
        t = max(0.0, min(1.0, t))
        
        # Closest point on line
        closest = self.point_at_parameter(t)
        
        return point.distance_to(closest)

    def closest_point_to(self, point: Point2D) -> Point2D:
        """
        Find the closest point on this line to a given point.
        
        Args:
            point: The point to find closest point to
            
        Returns:
            Closest point on the line
        """
        # Vector from start to point
        to_point = point - self._start
        
        # Vector from start to end
        line_vector = self.vector
        
        # Project to_point onto line_vector
        line_length_sq = line_vector.magnitude_squared
        if line_length_sq < EPSILON:
            # Degenerate line (point)
            return self._start
        
        # Parameter of closest point on line
        t = to_point.dot(line_vector) / line_length_sq
        
        # Clamp to line segment
        t = max(0.0, min(1.0, t))
        
        return self.point_at_parameter(t)

    def intersects_at_parameter(
            self,
            other: 'Line2D',
            bounded: Union[bool, Tuple[bool, bool]] = (True, True)
    ) -> Optional[Tuple[float, float]]:
        """
        Find intersection parameters with another line.
        
        Args:
            other: The other line
            bounded: Whether to treat lines as bounded segments
                    Can be bool (both lines) or tuple (line1, line2)
            
        Returns:
            Tuple of (t1, t2) parameters or None if no intersection
        """
        if isinstance(bounded, bool):
            bounded = (bounded, bounded)
        
        # Vectors
        u = self.vector
        v = other.vector
        
        # Vector from self.start to other.start
        w = other._start - self._start
        
        # Cross products
        uv_cross = u.cross(v)
        wv_cross = w.cross(v)
        wu_cross = w.cross(u)
        
        # Check if lines are parallel
        if abs(uv_cross) < EPSILON:
            # Lines are parallel
            if abs(wv_cross) < EPSILON:
                # Lines are collinear
                # Find overlap parameters
                if abs(u._x) > EPSILON:
                    t1 = w._x / u._x
                    t2 = (w._x + v._x) / u._x
                else:
                    t1 = w._y / u._y
                    t2 = (w._y + v._y) / u._y
                
                # Ensure t1 <= t2
                if t1 > t2:
                    t1, t2 = t2, t1
                
                # Check bounds
                if bounded[0]:
                    t1 = max(0.0, min(1.0, t1))
                    t2 = max(0.0, min(1.0, t2))
                if bounded[1]:
                    t2 = max(0.0, min(1.0, t2))
                
                if t1 <= t2:
                    return (t1, t2)
            return None
        
        # Lines intersect
        t1 = wv_cross / uv_cross
        t2 = wu_cross / uv_cross
        
        # Check bounds
        if bounded[0] and (t1 < 0 or t1 > 1):
            return None
        if bounded[1] and (t2 < 0 or t2 > 1):
            return None
        
        return (t1, t2)

    def intersects_at(
            self,
            other: 'Line2D',
            bounded: Union[bool, Tuple[bool, bool]] = (True, True)
    ) -> Optional[Point2D]:
        """
        Find intersection point with another line.
        
        Args:
            other: The other line
            bounded: Whether to treat lines as bounded segments
            
        Returns:
            Intersection point or None if no intersection
        """
        params = self.intersects_at_parameter(other, bounded)
        if params is None:
            return None
        
        t1, t2 = params
        return self.point_at_parameter(t1)

    def is_parallel_to(
            self,
            other: 'Line2D',
            tolerance: float = EPSILON
    ) -> bool:
        """
        Check if this line is parallel to another line.
        
        Args:
            other: The other line
            tolerance: Tolerance for floating point comparisons
            
        Returns:
            True if lines are parallel
        """
        cross_product = self.vector.cross(other.vector)
        return abs(cross_product) < tolerance

    def is_perpendicular_to(
            self,
            other: 'Line2D',
            tolerance: float = EPSILON
    ) -> bool:
        """
        Check if this line is perpendicular to another line.
        
        Args:
            other: The other line
            tolerance: Tolerance for floating point comparisons
            
        Returns:
            True if lines are perpendicular
        """
        dot_product = self.vector.dot(other.vector)
        return abs(dot_product) < tolerance

    def is_collinear_with(self, other: Union['Line2D', Point2D], tolerance: float = EPSILON) -> bool:
        """
        Check if this line is collinear with another line or point.
        
        Args:
            other: Another line or point
            tolerance: Tolerance for floating point comparisons
            
        Returns:
            True if collinear
        """
        if isinstance(other, Point2D):
            return self._start.is_collinear_to([self._end, other], tolerance)
        else:
            return self._start.is_collinear_to([self._end, other._start, other._end], tolerance)

    def angle_between_lines(self, other: 'Line2D', tolerance: float = EPSILON) -> float:
        """
        Calculate the angle between this line and another line.
        
        Args:
            other: The other line
            tolerance: Tolerance for floating point comparisons
            
        Returns:
            Angle in radians
        """
        return self.vector.angle_between_vectors(other.vector)

    def extend(self, start_distance: float, end_distance: float):
        """
        Extend the line by given distances.
        
        Args:
            start_distance: Distance to extend from start point
            end_distance: Distance to extend from end point
        """
        unit_vec = self.unit_vector
        self._start = self._start - unit_vec * start_distance
        self._end = self._end + unit_vec * end_distance

    def translate(self, vector) -> 'Line2D':
        """Translate the line by a vector."""
        if not isinstance(vector, Point2D):
            vector = Point2D(vector)
        return Line2D(self._start + vector, self._end + vector)

    def rotate(self, angle: float, center = None) -> 'Line2D':
        """Rotate the line around a center point."""
        if center is None:
            center = Point2D(0, 0)
        elif not isinstance(center, Point2D):
            center = Point2D(center)
        
        return Line2D(
            self._start.rotate(angle, center),
            self._end.rotate(angle, center)
        )

    def scale(self, scale, center = None) -> 'Line2D':
        """Scale the line around a center point."""
        if center is None:
            center = Point2D(0, 0)
        elif not isinstance(center, Point2D):
            center = Point2D(center)
        
        return Line2D(
            self._start.scale(scale, center),
            self._end.scale(scale, center)
        )

    def transform(self, transform: 'Transform2D') -> 'Line2D':
        """Transform the line using a transformation matrix."""
        return Line2D(
            transform.transform_point(self._start),
            transform.transform_point(self._end)
        )

    def __add__(self, other) -> 'Line2D':
        """Add a vector to the line."""
        return Line2D(self._start + other, self._end + other)

    def __sub__(self, other) -> 'Line2D':
        """Subtract a vector from the line."""
        return Line2D(self._start - other, self._end - other)

    def __mul__(self, other) -> 'Line2D':
        """Multiply the line by a scalar or component-wise by a point."""
        return Line2D(self._start * other, self._end * other)

    def __rmul__(self, other) -> 'Line2D':
        """Multiply the line by a scalar (commutative)."""
        return Line2D(other * self._start, other * self._end)

    def __truediv__(self, other) -> 'Line2D':
        """Divide the line by a scalar or component-wise by a point."""
        return Line2D(self._start / other, self._end / other)

    def __rtruediv__(self, other) -> 'Line2D':
        """Divide a scalar by the line (component-wise)."""
        return Line2D(other / self._start, other / self._end)

    def __neg__(self) -> 'Line2D':
        """Negate the line."""
        return Line2D(-self._start, -self._end)

    def __abs__(self) -> 'Line2D':
        """Get absolute value of each component."""
        return Line2D(abs(self._start), abs(self._end))

    def __eq__(self, other: object) -> bool:
        """Check if two lines are equal."""
        if not isinstance(other, Line2D):
            try:
                other = Line2D(other)
            except:
                return False
        return (self._start == other._start and self._end == other._end) or \
               (self._start == other._end and self._end == other._start)

    def __ne__(self, other: object) -> bool:
        """Check if two lines are not equal."""
        return not self.__eq__(other)

    def __hash__(self) -> int:
        """Hash the line for use in sets and dictionaries."""
        # Normalize direction for hash
        if self._start._x < self._end._x or (self._start._x == self._end._x and self._start._y < self._end._y):
            return hash((self._start, self._end))
        else:
            return hash((self._end, self._start))  # type: ignore

    def to_qlinef(self) -> 'QLineF':  # type: ignore
        """Convert to Qt QLineF."""
        try:
            from PySide6.QtCore import QLineF
            return QLineF(self._start.to_qpointf(), self._end.to_qpointf()) 
        except ImportError:
            raise NotImplementedError("Qt is not installed.  Cannot convert to QLineF.")
