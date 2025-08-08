"""
2D Point Class for CAD Geometry

This module provides the Point2D class for representing 2D points
with various geometric operations and conversions.
"""

import math
import numpy as np
from typing import Tuple, List, Iterator, Any, TYPE_CHECKING
from PySide6.QtCore import QPointF

from .shapes import Shape2D, ShapeType

if TYPE_CHECKING:
    from .transform import Transform2D


# Type aliases for convenience

EPSILON = 1e-10


class Point2D(Shape2D):
    """
    A 2D point with x and y coordinates.
    
    This class provides various geometric operations including vector arithmetic,
    distance calculations, and conversions to other formats.
    """

    def __init__(self, x, y = None, angle = None):
        """
        Initialize a 2D point.
        
        Args:
            x: X coordinate, or another point, or magnitude if angle is provided
            y: Y coordinate (ignored if x is a point or angle is provided)
            angle: Angle in radians (creates point at distance x from origin)
        """
        if y is not None:
            try:
                y = float(y)
            except:
                raise ValueError(f"Invalid y value: {y}")
            try:
                x = float(x)
            except:
                raise ValueError(f"Invalid x value: {x}")
            self._x = x
            self._y = y
            return

        if angle is not None:
            try:
                angle = float(angle)
            except:
                raise ValueError(f"Invalid angle value: {angle}")
            try:
                x = float(x)
            except:
                raise ValueError(f"Invalid x value: {x}")
            self._x = x * math.cos(angle)
            self._y = x * math.sin(angle)
            return

        # Only one argument provided (in x)
        try:  # get x and y from properties
            self._x = float(x.x)
            self._y = float(x.y)
            return
        except:
            pass

        try:  # get x and y from QPointF or x() and y()
            self._x = float(x.x())
            self._y = float(x.y())
            return
        except:
            pass

        try:  # get x and y from list-like object
            self._x = float(x[0])
            self._y = float(x[1])
            return
        except:
            pass

        raise ValueError(f"Invalid x value: {x}")

    @classmethod
    def from_string(cls, string: str) -> 'Point2D':
        """Create a point from a string representation like 'x,y'."""
        try:
            parts = string.strip().split(',')
            if len(parts) != 2:
                raise ValueError("Point string must have exactly 2 coordinates")
            return cls(float(parts[0]), float(parts[1]))
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid point string '{string}': {e}")

    def to_string(self) -> str:
        """Convert the point to a string representation."""
        return f"{self._x},{self._y}"

    def decompose(self, into: List['ShapeType'] = [], tolerance: float = 0.001) -> List['Shape2D']:
        """Decompose point into other shape types."""
        if ShapeType.POINT in into:
            return [self]
        raise ValueError(f"Cannot decompose point into any of {into}")

    @property
    def x(self) -> float:
        """Get the x coordinate."""
        return self._x

    @x.setter
    def x(self, value: float):
        """Set the x coordinate."""
        self._x = float(value)

    @property
    def y(self) -> float:
        """Get the y coordinate."""
        return self._y

    @y.setter
    def y(self, value: float):
        """Set the y coordinate."""
        self._y = float(value)

    @property
    def magnitude(self) -> float:
        """Get the distance from origin."""
        return math.sqrt(self._x * self._x + self._y * self._y)

    @property
    def magnitude_squared(self) -> float:
        """Get the squared distance from origin."""
        return self._x * self._x + self._y * self._y

    @property
    def unit_vector(self) -> 'Point2D':
        """Get the unit vector in this direction."""
        mag = self.magnitude
        if mag < EPSILON:
            return Point2D(0, 0)
        return Point2D(self._x / mag, self._y / mag)

    @property
    def perpendicular_vector(self) -> 'Point2D':
        """Get the perpendicular vector (rotated 90 degrees counterclockwise)."""
        return Point2D(-self._y, self._x)

    @property
    def angle_degrees(self) -> float:
        """Get the angle in degrees."""
        return math.degrees(self.angle_radians)

    @property
    def angle_radians(self) -> float:
        """Get the angle in radians."""
        return math.atan2(self._y, self._x)

    def __hash__(self) -> int:
        """Hash the point for use in sets and dictionaries."""
        return hash((self._x, self._y))

    def __add__(self, other) -> 'Point2D':
        """Add two points (vector addition)."""
        if not isinstance(other, Point2D):
            other = Point2D(other)
        return Point2D(self._x + other._x, self._y + other._y)

    def __radd__(self, other) -> 'Point2D':
        """Add two points (vector addition)."""
        return self.__add__(other)

    def __sub__(self, other) -> 'Point2D':
        """Subtract two points (vector subtraction)."""
        if not isinstance(other, Point2D):
            other = Point2D(other)
        return Point2D(self._x - other._x, self._y - other._y)

    def __rsub__(self, other) -> 'Point2D':
        """Subtract this point from another."""
        if not isinstance(other, Point2D):
            other = Point2D(other)
        return Point2D(other._x - self._x, other._y - self._y)

    def __mul__(self, other) -> 'Point2D':
        """Multiply by scalar or component-wise by another point."""
        try:
            other_f = float(other)
            return Point2D(self._x * other_f, self._y * other_f)
        except:
            pass
        if not isinstance(other, Point2D):
            other = Point2D(other)
        return Point2D(self._x * other._x, self._y * other._y)

    def __rmul__(self, other) -> 'Point2D':
        """Multiply by scalar (commutative)."""
        try:
            other_f = float(other)
            return Point2D(self._x * other_f, self._y * other_f)
        except:
            pass
        if not isinstance(other, Point2D):
            other = Point2D(other)
        return Point2D(self._x * other._x, self._y * other._y)

    def __truediv__(self, other) -> 'Point2D':
        """Divide by scalar or component-wise by another point."""
        try:
            other_f = float(other)
            if abs(other_f) < EPSILON:
                raise ZeroDivisionError("Cannot divide by zero")
            return Point2D(self._x / other_f, self._y / other_f)
        except:
            pass
        if not isinstance(other, Point2D):
            other = Point2D(other)
        if abs(other._x) < EPSILON or abs(other._y) < EPSILON:
            raise ZeroDivisionError("Cannot divide by zero")
        return Point2D(self._x / other._x, self._y / other._y)

    def __rtruediv__(self, other) -> 'Point2D':
        """Divide scalar by this point (component-wise)."""
        if abs(self._x) < EPSILON or abs(self._y) < EPSILON:
            raise ZeroDivisionError("Cannot divide by zero")
        try:
            other_f = float(other)
            return Point2D(other_f / self._x, other_f / self._y)
        except:
            pass
        if not isinstance(other, Point2D):
            other = Point2D(other)
        return Point2D(other._x / self._x, other._y / self._y)

    def __neg__(self) -> 'Point2D':
        """Negate the point."""
        return Point2D(-self._x, -self._y)

    def __abs__(self) -> 'Point2D':
        """Get absolute value of each component."""
        return Point2D(abs(self._x), abs(self._y))

    def __str__(self) -> str:
        return f"Point2D({self._x}, {self._y})"

    def __repr__(self) -> str:
        return f"Point2D({self._x}, {self._y})"

    def __getitem__(self, index: int) -> float:
        """Get coordinate by index (0=x, 1=y)."""
        if index == 0:
            return self._x
        elif index == 1:
            return self._y
        raise IndexError(f"Index out of range: {index}")

    def __setitem__(self, index: int, value: float):
        """Set coordinate by index (0=x, 1=y)."""
        if index == 0:
            self._x = value
        elif index == 1:
            self._y = value
        raise IndexError(f"Index out of range: {index}")

    def __iter__(self) -> Iterator[float]:
        """Iterate over the coordinates."""
        return iter((self._x, self._y))

    def __len__(self) -> int:
        """Get the number of coordinates."""
        return 2

    def __eq__(self, other) -> bool:
        """Check if two points are equal."""
        if not isinstance(other, Point2D):
            return False
        return abs(self._x - other._x) < EPSILON and abs(self._y - other._y) < EPSILON

    def is_collinear_to(self, points: List[Any], tolerance: float = EPSILON) -> bool:
        """
        Check if this point is collinear with a list of other points.
        
        Args:
            points: List of points to check collinearity with
            tolerance: Tolerance for floating point comparisons
            
        Returns:
            True if all points are collinear
        """
        if len(points) < 2:
            return True
        
        # Convert to Point2D objects
        point_list = [Point2D(p) if not isinstance(p, Point2D) else p for p in points]
        point_list.append(self)
        
        # Check if all points are the same
        if all(p == point_list[0] for p in point_list):
            return True
        
        # Find two distinct points to define the line
        p1 = point_list[0]
        p2 = None
        for p in point_list[1:]:
            if p != p1:
                p2 = p
                break
        
        if p2 is None:
            return True
        
        # Check if all points lie on the line defined by p1 and p2
        for p in point_list:
            if p == p1 or p == p2:
                continue
            
            # Calculate area of triangle (p1, p2, p)
            # If area is zero, points are collinear
            area = abs((p2._x - p1._x) * (p._y - p1._y) - (p._x - p1._x) * (p2._y - p1._y))
            if area > tolerance:
                return False
        
        return True

    def distance_to(self, other) -> float:
        """
        Calculate the distance to another point.
        
        Args:
            other: The other point
            
        Returns:
            Distance between the points
        """
        if not isinstance(other, Point2D):
            other = Point2D(other)
        return math.sqrt((self._x - other._x) ** 2 + (self._y - other._y) ** 2)

    def dot(self, other) -> float:
        """
        Calculate the dot product with another point.
        
        Args:
            other: The other point
            
        Returns:
            Dot product
        """
        if not isinstance(other, Point2D):
            other = Point2D(other)
        return self._x * other._x + self._y * other._y

    def cross(self, other) -> float:
        """
        Calculate the cross product with another point.
        
        Args:
            other: The other point
            
        Returns:
            Cross product (scalar in 2D)
        """
        if not isinstance(other, Point2D):
            other = Point2D(other)
        return self._x * other._y - self._y * other._x

    def angle_between_vectors(self, other) -> float:
        """
        Calculate the angle between this vector and another.
        
        Args:
            other: The other vector
            
        Returns:
            Angle in radians
        """
        if not isinstance(other, Point2D):
            other = Point2D(other)
        
        dot_product = self.dot(other)
        mag1 = self.magnitude
        mag2 = other.magnitude
        
        if mag1 < EPSILON or mag2 < EPSILON:
            return 0.0
        
        cos_angle = dot_product / (mag1 * mag2)
        cos_angle = max(-1.0, min(1.0, cos_angle))  # Clamp to [-1, 1]
        return math.acos(cos_angle)

    def to_qpointf(self) -> QPointF:
        """Convert to Qt QPointF."""
        return QPointF(self._x, self._y)

    def to_tuple(self) -> Tuple[float, float]:
        """Convert to tuple."""
        return (self._x, self._y)

    def to_list(self) -> List[float]:
        """Convert to list."""
        return [self._x, self._y]

    def to_numpy(self) -> np.ndarray:
        """Convert to numpy array."""
        return np.array([self._x, self._y])

    @classmethod
    def from_numpy(cls, arr: np.ndarray) -> 'Point2D':
        """Create from numpy array."""
        return cls(arr[0], arr[1])

    def translate(self, vector) -> 'Point2D':
        """Translate the point by a vector."""
        if not isinstance(vector, Point2D):
            vector = Point2D(vector)
        return Point2D(self._x + vector._x, self._y + vector._y)

    def rotate(self, angle: float, center = None) -> 'Point2D':
        """
        Rotate the point around a center.
        
        Args:
            angle: Rotation angle in radians
            center: Center of rotation (defaults to origin)
            
        Returns:
            Rotated point
        """
        if center is None:
            center = Point2D(0, 0)
        elif not isinstance(center, Point2D):
            center = Point2D(center)
        
        # Translate to origin
        translated = self - center
        
        # Rotate
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        rotated = Point2D(
            translated._x * cos_a - translated._y * sin_a,
            translated._x * sin_a + translated._y * cos_a
        )
        
        # Translate back
        return rotated + center

    def scale(self, scale, center = None) -> 'Point2D':
        """
        Scale the point around a center.
        
        Args:
            scale: Scale factor or scale vector
            center: Center of scaling (defaults to origin)
            
        Returns:
            Scaled point
        """
        if center is None:
            center = Point2D(0, 0)
        elif not isinstance(center, Point2D):
            center = Point2D(center)
        
        if isinstance(scale, (int, float)):
            scale = Point2D(scale, scale)
        elif not isinstance(scale, Point2D):
            scale = Point2D(scale)
        
        # Translate to origin
        translated = self - center
        
        # Scale
        scaled = Point2D(translated._x * scale._x, translated._y * scale._y)
        
        # Translate back
        return scaled + center

    def transform(self, transform: 'Transform2D') -> 'Point2D':
        """Transform the point using a transformation matrix."""
        return transform.transform_point(self)

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get the bounding box (degenerate for a point)."""
        return (self._x, self._y, self._x, self._y) 