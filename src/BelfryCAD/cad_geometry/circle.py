"""
Circle Class for CAD Geometry

This module provides the Circle class for representing 2D circles
with various geometric operations and calculations.
"""

from typing import List, Optional, Tuple, Union, TYPE_CHECKING
import numpy as np
import math
from .shapes import Shape2D, ShapeType
from .point import Point2D
from .line import Line2D
from .transform import Transform2D
from .ellipse import Ellipse

if TYPE_CHECKING:
    from .ellipse import Ellipse
    from .arc import Arc
    from .polygon import Polygon
    from .polyline import PolyLine2D
    from .bezier import BezierPath
    from .region import Region

EPSILON = 1e-10

class Circle(Shape2D):
    """Circle with geometric operations - optimized with numpy."""

    def __init__(self, center: Point2D, radius: float):
        """Initialize a circle."""
        self._center = center
        self._radius = abs(radius)

    def __repr__(self) -> str:
        return f"Circle({self.center}, {self.radius})"

    def __str__(self) -> str:
        return f"Circle at {self.center} with radius {self.radius:.3f}"

    def decompose(self, into: List[ShapeType] = [], tolerance: float = 0.001) -> List['Shape2D']:
        if ShapeType.CIRCLE in into:
            return [self]
        if ShapeType.ELLIPSE in into:
            return [Ellipse(self.center, self.radius, self.radius, 0.0)]
        if ShapeType.ARC in into:
            return [Arc(self.center, self.radius, 0, 360)]
        if ShapeType.BEZIER in into:
            return [BezierPath.circle(self.center, self.radius)]
        if ShapeType.POLYGON in into:
            return [Polygon(self._to_points(tolerance))]
        if ShapeType.REGION in into:
            return [Region(perimeters=[Polygon(self._to_points(tolerance))], holes=[])]
        if ShapeType.POLYLINE in into:
            return [PolyLine2D(self._to_points(tolerance))]
        if ShapeType.LINE in into:
            points = self._to_points(tolerance)
            return [
                Line2D(points[i], points[i + 1])
                for i in range(len(points) - 1)
            ]
        raise ValueError(f"Cannot decompose circle into any of {into}")

    def _to_points(self, tolerance: float = 0.001) -> List[Point2D]:
        # Calculate number of segments based on tolerance
        # For a circle, the maximum deviation from the true circle is approximately r * (1 - cos(π/n))
        # Setting this equal to tolerance: r * (1 - cos(π/n)) = tolerance
        # Solving for n: n = π / arccos(1 - tolerance/r)
        if tolerance <= 0:
            segments = 100  # Default fallback
        else:
            segments = max(8, int(np.pi / np.arccos(1 - tolerance / self.radius)))
        
        return [
            self.center + Point2D(self.radius, angle)
            for angle in np.linspace(0, 2 * np.pi, segments)
        ]

    @property
    def center(self) -> Point2D:
        return self._center
    
    @center.setter
    def center(self, value: Point2D):
        self._center = value
    
    @property
    def radius(self) -> float:
        return self._radius
    
    @radius.setter
    def radius(self, value: float):
        self._radius = abs(value)

    @property
    def diameter(self) -> float:
        return 2 * self.radius
    
    @property
    def area(self) -> float:
        """Calculate circle area."""
        return np.pi * self.radius ** 2

    @property
    def circumference(self) -> float:
        """Calculate circle circumference."""
        return 2 * np.pi * self.radius

    def contains_point(self, point, tolerance: float = EPSILON) -> bool:
        """Check if point is inside circle."""
        if not isinstance(point, Point2D):
            point = Point2D(point)
        return (point - self.center).magnitude_squared <= (self.radius + tolerance) ** 2

    def perimeter_point(self, angle: float) -> Point2D:
        """Get point on circle at given angle (radians)."""
        return self.center + Point2D(self.radius, angle)

    def tangent_points_from_point(self, point: Point2D) -> List[Point2D]:
        """Find tangent points from external point to circle - optimized."""
        dist_to_center = self.center.distance_to(point)

        if dist_to_center < self.radius:
            return []  # Point is inside circle

        if dist_to_center == self.radius:
            return [point]  # Point is on circle

        # Calculate tangent points using numpy
        angle_to_center = np.arctan2(point.y - self.center.y, point.x - self.center.x)
        tangent_angle = np.arcsin(self.radius / dist_to_center)

        angle1 = angle_to_center + tangent_angle
        angle2 = angle_to_center - tangent_angle

        # Distance from external point to tangent points
        tangent_dist = np.sqrt(dist_to_center ** 2 - self.radius ** 2)

        tangent1 = point + Point2D(tangent_dist, angle=angle1)
        tangent2 = point + Point2D(tangent_dist, angle=angle2)

        return [tangent1, tangent2]

    def intersect_line(self, line: Line2D) -> List[Point2D]:
        """Find intersection points with a line - optimized."""
        # Vector from line start to circle center
        to_center = line.start - self.center
        line_vec = line.vector

        # Project center onto line
        line_length_sq = line_vec.magnitude_squared
        if line_length_sq < EPSILON:
            # Line is a point
            if self.contains_point(line.start):
                return [line.start]
            return []

        t = to_center.dot(line_vec) / line_length_sq

        # Find closest point on line to circle center
        closest_point = line.point_at_parameter(t)
        dist_to_center = self.center.distance_to(closest_point)

        if dist_to_center > self.radius:
            return []  # No intersection

        if dist_to_center == self.radius:
            # Tangent - one intersection
            if 0 <= t <= 1:
                return [closest_point]
            return []

        # Two intersections
        chord_half_length = np.sqrt(self.radius ** 2 - dist_to_center ** 2)
        line_unit = line_vec.unit_vector

        intersection1 = closest_point - line_unit * chord_half_length
        intersection2 = closest_point + line_unit * chord_half_length

        # Check if intersections are within line segment
        intersections = []

        # Check intersection1
        t1 = (intersection1 - line.start).dot(line_vec) / line_length_sq
        if 0 <= t1 <= 1:
            intersections.append(intersection1)

        # Check intersection2
        t2 = (intersection2 - line.start).dot(line_vec) / line_length_sq
        if 0 <= t2 <= 1:
            intersections.append(intersection2)

        return intersections

    def intersect_circle(self, other: 'Circle') -> List[Point2D]:
        """Find intersection points with another circle - optimized."""
        dist = self.center.distance_to(other.center)

        # Check for no intersection cases
        if dist > self.radius + other.radius:  # Too far apart
            return []
        if dist < abs(self.radius - other.radius):  # One inside the other
            return []
        if dist == 0 and self.radius == other.radius:  # Same circle
            return []  # Infinite intersections

        # One intersection (tangent circles)
        if (
            dist == self.radius + other.radius or
            dist == abs(self.radius - other.radius)
        ):
            direction = (other.center - self.center).unit_vector
            point = self.center + direction * self.radius
            return [point]

        # Two intersections
        a = (self.radius ** 2 - other.radius ** 2 + dist ** 2) / (2 * dist)
        h = np.sqrt(self.radius ** 2 - a ** 2)

        # Point on line between centers
        direction = (other.center - self.center).unit_vector
        midpoint = self.center + direction * a

        # Perpendicular direction
        perp = direction.perpendicular_vector

        intersection1 = midpoint + perp * h
        intersection2 = midpoint - perp * h

        return [intersection1, intersection2]

    def translate(self, vector) -> 'Circle':
        """Make a new circle, translated by vector."""
        return Circle(self.center.translate(vector), self.radius)

    def scale(self, scale, center = None) -> Optional['Shape2D']:
        """Make a new circle, scaled around a point."""
        new_center = self.center.scale(scale, center)
        if isinstance(scale, (int, float, np.integer, np.floating)):
            new_radius = self.radius * abs(float(scale))
            return Circle(new_center, new_radius)
        else:
            scale_point = Point2D(scale)
            r1 = self.radius * scale_point.x
            r2 = self.radius * scale_point.y
            return Ellipse(new_center, r1, r2, 0.0)

    def rotate(self, angle: float, center = None) -> 'Circle':
        """Make a new circle, rotated around a point."""
        new_center = self.center.rotate(angle, center)
        return Circle(new_center, self.radius)

    def transform(self, transform: Transform2D) -> Optional['Shape2D']:
        """Make a new circle, transformed using a transformation matrix."""
        # Lets calculate three of the transformed bounding parallelogram corners.
        p1 = self.center + Point2D(-self.radius, -self.radius)
        p2 = self.center + Point2D(self.radius, -self.radius)
        p3 = self.center + Point2D(self.radius, self.radius)
        p1 = p1.transform(transform)
        p2 = p2.transform(transform)
        p3 = p3.transform(transform)
        return Ellipse.from_parallelogram_corners(p1, p3, p2)

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get the bounds of the circle as (min_x, min_y, max_x, max_y)."""
        return (
            self._center.x - self._radius,
            self._center.y - self._radius,
            self._center.x + self._radius,
            self._center.y + self._radius
        )

    @classmethod
    def from_3_points(cls, points: List[Point2D]) -> 'Circle':
        """Create a circle from three points."""
        if len(points) < 3:
            raise ValueError("Circle must have at least 3 points")
        # Calculate the center and radius of the circle
        vec1 = (points[1] - points[0]).unit_vector.perpendicular_vector
        vec2 = (points[2] - points[1]).unit_vector.perpendicular_vector
        midpt1 = (points[0] + points[1]) / 2
        midpt2 = (points[1] + points[2]) / 2
        line1 = Line2D(midpt1, midpt1+vec1)
        line2 = Line2D(midpt2, midpt2+vec2)
        center = line1.intersects_at(line2, bounded=False)
        if center is None:
            raise ValueError("Failed to calculate circle from three points")
        radius = center.distance_to(points[0])
        return cls(center, radius)
    
    @classmethod
    def from_line_and_perimeter_point(cls, line: Line2D, perimeter_point: Point2D) -> 'Circle':
        """Create a circle from a line and a perimeter point."""
        vec1 = line.vector.perpendicular_vector
        vec2 = (perimeter_point - line.start).unit_vector.perpendicular_vector
        midpt1 = (line.start + line.end) / 2
        line1 = Line2D(midpt1, midpt1 + vec1)
        line2 = Line2D(midpt1, midpt1 + vec2)
        center = line1.intersects_at(line2, bounded=False)
        if center is None:
            raise ValueError("Failed to calculate circle from line and perimeter point")
        radius = center.distance_to(perimeter_point)
        return cls(center, radius)

    @classmethod
    def from_lines_and_radius(cls, line1: Line2D, line2: Line2D, radius: float) -> 'Circle':
        """Creates a Circle that it tangent to two lines and has a given radius."""
        isect = line1.intersects_at(line2, bounded=False)
        if isect is None:
            raise ValueError("Lines do not intersect")
        center = isect
        radius = radius
        return cls(center, radius)

    @classmethod
    def from_corner_and_radius(cls, corner: List[Point2D], radius: float) -> 'Circle':
        """
        Given three points, where the first and second points define one ray,
        and the third and second points define the other ray, creates a circle
        that is tangent to the two rays and has a given radius.
        """
        line1 = Line2D(corner[0], corner[1])
        line2 = Line2D(corner[2], corner[1])
        return cls.from_lines_and_radius(line1, line2, radius)

    @classmethod
    def from_opposite_points(cls, p1: Point2D, p2: Point2D) -> 'Circle':
        """
        Given two opposite points on a circle, creates a circle that is tangent
        to the two points and has a radius of half the distance between the two points.
        """
        center = (p1 + p2) / 2
        radius = (p1 - p2).magnitude / 2
        return cls(center, radius)

    @classmethod
    def from_center_and_perimeter_point(cls, center: Point2D, perimeter_point: Point2D) -> 'Circle':
        """Creates a circle from a center point and a perimeter point."""
        radius = center.distance_to(perimeter_point)
        return cls(center, radius)
