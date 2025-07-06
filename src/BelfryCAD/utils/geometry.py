"""
Geometry utility classes and functions for BelfryCAD.

This module provides comprehensive geometric operations including:
- Point2D and Point3D classes for point operations
- Vector2D and Vector3D classes for vector mathematics
- Line2D and Line3D classes for line operations
- Circle and Arc classes for circular geometry
- Polygon class for polygon operations
- Utility functions for geometric calculations

Refactored from geometry.py to use object-oriented design.
"""

import math
from typing import List, Tuple, Optional, Union, Iterator


# Constants
EPSILON = 1e-10


class Point2D:
    """2D point with coordinate operations."""

    def __init__(self, x: float = 0.0, y: float = 0.0):
        """Initialize a 2D point."""
        self.x = float(x)
        self.y = float(y)

    def __repr__(self) -> str:
        return f"Point2D({self.x}, {self.y})"

    def __str__(self) -> str:
        return f"({self.x:.3f}, {self.y:.3f})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Point2D):
            return False
        return \
            abs(self.x - other.x) < EPSILON and \
            abs(self.y - other.y) < EPSILON

    def __add__(self, other) -> 'Point2D':
        if isinstance(other, Point2D):
            return Point2D(self.x + other.x, self.y + other.y)
        elif isinstance(other, Vector2D):
            return Point2D(self.x + other.dx, self.y + other.dy)
        else:
            raise TypeError(f"Cannot add Point2D with {type(other)}")

    def __sub__(self, other) -> Union['Point2D', 'Vector2D']:
        if isinstance(other, Point2D):
            return Vector2D(self.x - other.x, self.y - other.y)
        elif isinstance(other, Vector2D):
            return Point2D(self.x - other.dx, self.y - other.dy)
        else:
            raise TypeError(f"Cannot subtract {type(other)} from Point2D")

    def __mul__(self, scalar: float) -> 'Point2D':
        return Point2D(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> 'Point2D':
        return self.__mul__(scalar)

    def distance_to(self, other: 'Point2D') -> float:
        """Calculate distance to another point."""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def distance_squared_to(self, other: 'Point2D') -> float:
        """
        Calculate squared distance to another point.
        (faster when comparison only)
        """
        return (self.x - other.x) ** 2 + (self.y - other.y) ** 2

    def midpoint_to(self, other: 'Point2D') -> 'Point2D':
        """Calculate midpoint to another point."""
        return Point2D((self.x + other.x) / 2, (self.y + other.y) / 2)

    def rotate_around(self, center: 'Point2D', angle: float) -> 'Point2D':
        """Rotate point around a center point by angle in radians."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        dx = self.x - center.x
        dy = self.y - center.y

        new_x = dx * cos_a - dy * sin_a + center.x
        new_y = dx * sin_a + dy * cos_a + center.y

        return Point2D(new_x, new_y)

    def scale_around(
            self,
            center: 'Point2D',
            sx: float, sy: float
    ) -> 'Point2D':
        """Scale point around a center point."""
        dx = self.x - center.x
        dy = self.y - center.y

        new_x = dx * sx + center.x
        new_y = dy * sy + center.y

        return Point2D(new_x, new_y)

    def to_tuple(self) -> Tuple[float, float]:
        """Convert to tuple."""
        return (self.x, self.y)

    @classmethod
    def from_tuple(cls, coords: Tuple[float, float]) -> 'Point2D':
        """Create from tuple."""
        return cls(coords[0], coords[1])

    @classmethod
    def origin(cls) -> 'Point2D':
        """Create origin point (0, 0)."""
        return cls(0.0, 0.0)


class Vector2D:
    """2D vector with vector operations."""

    def __init__(self, dx: float = 0.0, dy: float = 0.0):
        """Initialize a 2D vector."""
        self.dx = float(dx)
        self.dy = float(dy)

    def __repr__(self) -> str:
        return f"Vector2D({self.dx}, {self.dy})"

    def __str__(self) -> str:
        return f"<{self.dx:.3f}, {self.dy:.3f}>"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Vector2D):
            return False
        return \
            abs(self.dx - other.dx) < EPSILON and \
            abs(self.dy - other.dy) < EPSILON

    def __add__(self, other: 'Vector2D') -> 'Vector2D':
        return Vector2D(self.dx + other.dx, self.dy + other.dy)

    def __sub__(self, other: 'Vector2D') -> 'Vector2D':
        return Vector2D(self.dx - other.dx, self.dy - other.dy)

    def __mul__(self, scalar: float) -> 'Vector2D':
        return Vector2D(self.dx * scalar, self.dy * scalar)

    def __rmul__(self, scalar: float) -> 'Vector2D':
        return self.__mul__(scalar)

    def __neg__(self) -> 'Vector2D':
        return Vector2D(-self.dx, -self.dy)

    @property
    def magnitude(self) -> float:
        """Calculate vector magnitude."""
        return math.sqrt(self.dx ** 2 + self.dy ** 2)

    @property
    def magnitude_squared(self) -> float:
        """Calculate squared magnitude (faster when comparison only)."""
        return self.dx ** 2 + self.dy ** 2

    @property
    def angle(self) -> float:
        """Calculate angle in radians."""
        return math.atan2(self.dy, self.dx)

    def normalized(self) -> 'Vector2D':
        """Return normalized vector."""
        mag = self.magnitude
        if mag < EPSILON:
            return Vector2D(0, 0)
        return Vector2D(self.dx / mag, self.dy / mag)

    def dot(self, other: 'Vector2D') -> float:
        """Calculate dot product."""
        return self.dx * other.dx + self.dy * other.dy

    def cross(self, other: 'Vector2D') -> float:
        """Calculate cross product (z-component in 2D)."""
        return self.dx * other.dy - self.dy * other.dx

    def perpendicular(self) -> 'Vector2D':
        """
        Return perpendicular vector (rotated 90 degrees counterclockwise).
        """
        return Vector2D(-self.dy, self.dx)

    def angle_to(self, other: 'Vector2D') -> float:
        """Calculate angle to another vector."""
        return math.atan2(self.cross(other), self.dot(other))

    def project_onto(self, other: 'Vector2D') -> 'Vector2D':
        """Project this vector onto another vector."""
        other_mag_sq = other.magnitude_squared
        if other_mag_sq < EPSILON:
            return Vector2D(0, 0)

        projection_length = self.dot(other) / other_mag_sq
        return other * projection_length

    def reflect(self, normal: 'Vector2D') -> 'Vector2D':
        """Reflect vector about a normal vector."""
        normal_unit = normal.normalized()
        return self - 2 * self.dot(normal_unit) * normal_unit

    def rotate(self, angle: float) -> 'Vector2D':
        """Rotate vector by angle in radians."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        new_dx = self.dx * cos_a - self.dy * sin_a
        new_dy = self.dx * sin_a + self.dy * cos_a

        return Vector2D(new_dx, new_dy)

    @classmethod
    def from_points(cls, start: Point2D, end: Point2D) -> 'Vector2D':
        """Create vector from two points."""
        return cls(end.x - start.x, end.y - start.y)

    @classmethod
    def from_angle(cls, angle: float, magnitude: float = 1.0) -> 'Vector2D':
        """Create vector from angle and magnitude."""
        return cls(magnitude * math.cos(angle), magnitude * math.sin(angle))

    @classmethod
    def zero(cls) -> 'Vector2D':
        """Create zero vector."""
        return cls(0.0, 0.0)


class Line2D:
    """2D line segment with line operations."""

    def __init__(self, start: Point2D, end: Point2D):
        """Initialize a 2D line segment."""
        self.start = start
        self.end = end

    def __repr__(self) -> str:
        return f"Line2D({self.start}, {self.end})"

    def __str__(self) -> str:
        return f"Line from {self.start} to {self.end}"

    @property
    def vector(self) -> Vector2D:
        """Get the direction vector of the line."""
        return Vector2D.from_points(self.start, self.end)

    @property
    def length(self) -> float:
        """Get the length of the line segment."""
        return self.start.distance_to(self.end)

    @property
    def midpoint(self) -> Point2D:
        """Get the midpoint of the line segment."""
        return self.start.midpoint_to(self.end)

    def point_at_parameter(self, t: float) -> Point2D:
        """Get point at parameter t (0 = start, 1 = end)."""
        return Point2D(
            self.start.x + t * (self.end.x - self.start.x),
            self.start.y + t * (self.end.y - self.start.y)
        )

    def distance_to_point(self, point: Point2D) -> float:
        """Calculate shortest distance from line to a point."""
        if self.length < EPSILON:
            return self.start.distance_to(point)

        # Project point onto line
        line_vec = self.vector
        point_vec = Vector2D.from_points(self.start, point)

        t = point_vec.dot(line_vec) / line_vec.magnitude_squared
        t = max(0, min(1, t))  # Clamp to line segment

        closest_point = self.point_at_parameter(t)
        return point.distance_to(closest_point)

    def closest_point_to(self, point: Point2D) -> Point2D:
        """Find closest point on line to given point."""
        if self.length < EPSILON:
            return self.start

        line_vec = self.vector
        point_vec = Vector2D.from_points(self.start, point)

        t = point_vec.dot(line_vec) / line_vec.magnitude_squared
        t = max(0, min(1, t))  # Clamp to line segment

        return self.point_at_parameter(t)

    def intersect_line(self, other: 'Line2D') -> Optional[Point2D]:
        """Find intersection point with another line."""
        # Line 1: P1 + t1 * (P2 - P1)
        # Line 2: P3 + t2 * (P4 - P3)

        x1, y1 = self.start.x, self.start.y
        x2, y2 = self.end.x, self.end.y
        x3, y3 = other.start.x, other.start.y
        x4, y4 = other.end.x, other.end.y

        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

        if abs(denom) < EPSILON:
            return None  # Lines are parallel

        t1 = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        t2 = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

        # Check if intersection is within both line segments
        if 0 <= t1 <= 1 and 0 <= t2 <= 1:
            return Point2D(x1 + t1 * (x2 - x1), y1 + t1 * (y2 - y1))

        return None

    def is_parallel_to(
            self,
            other: 'Line2D',
            tolerance: float = EPSILON
    ) -> bool:
        """Check if line is parallel to another line."""
        vec1 = self.vector.normalized()
        vec2 = other.vector.normalized()

        # Check if cross product is near zero
        return abs(vec1.cross(vec2)) < tolerance

    def is_perpendicular_to(
            self,
            other: 'Line2D',
            tolerance: float = EPSILON
    ) -> bool:
        """Check if line is perpendicular to another line."""
        vec1 = self.vector.normalized()
        vec2 = other.vector.normalized()

        # Check if dot product is near zero
        return abs(vec1.dot(vec2)) < tolerance

    def extend(self, start_distance: float, end_distance: float) -> 'Line2D':
        """Extend line by given distances at start and end."""
        direction = self.vector.normalized()

        new_start = Point2D(
            self.start.x - direction.dx * start_distance,
            self.start.y - direction.dy * start_distance
        )
        new_end = Point2D(
            self.end.x + direction.dx * end_distance,
            self.end.y + direction.dy * end_distance
        )

        return Line2D(new_start, new_end)

    def translate(self, vector: Vector2D) -> 'Line2D':
        """Translate line by vector."""
        return Line2D(self.start + vector, self.end + vector)

    def rotate_around(self, center: Point2D, angle: float) -> 'Line2D':
        """Rotate line around a center point."""
        new_start = self.start.rotate_around(center, angle)
        new_end = self.end.rotate_around(center, angle)
        return Line2D(new_start, new_end)


class Circle:
    """Circle with geometric operations."""

    def __init__(self, center: Point2D, radius: float):
        """Initialize a circle."""
        self.center = center
        self.radius = abs(radius)

    def __repr__(self) -> str:
        return f"Circle({self.center}, {self.radius})"

    def __str__(self) -> str:
        return f"Circle at {self.center} with radius {self.radius:.3f}"

    @property
    def area(self) -> float:
        """Calculate circle area."""
        return math.pi * self.radius ** 2

    @property
    def circumference(self) -> float:
        """Calculate circle circumference."""
        return 2 * math.pi * self.radius

    @property
    def diameter(self) -> float:
        """Get circle diameter."""
        return 2 * self.radius

    def contains_point(self, point: Point2D) -> bool:
        """Check if point is inside circle."""
        return self.center.distance_squared_to(point) <= self.radius ** 2

    def point_on_circle(self, angle: float) -> Point2D:
        """Get point on circle at given angle (radians)."""
        return Point2D(
            self.center.x + self.radius * math.cos(angle),
            self.center.y + self.radius * math.sin(angle)
        )

    def tangent_points_from_point(self, point: Point2D) -> List[Point2D]:
        """Find tangent points from external point to circle."""
        dist_to_center = self.center.distance_to(point)

        if dist_to_center < self.radius:
            return []  # Point is inside circle

        if dist_to_center == self.radius:
            return [point]  # Point is on circle

        # Calculate tangent points
        angle_to_center = math.atan2(point.y - self.center.y, point.x - self.center.x)
        tangent_angle = math.asin(self.radius / dist_to_center)

        angle1 = angle_to_center + tangent_angle
        angle2 = angle_to_center - tangent_angle

        # Distance from external point to tangent points
        tangent_dist = math.sqrt(dist_to_center ** 2 - self.radius ** 2)

        tangent1 = Point2D(
            point.x + tangent_dist * math.cos(angle1),
            point.y + tangent_dist * math.sin(angle1)
        )
        tangent2 = Point2D(
            point.x + tangent_dist * math.cos(angle2),
            point.y + tangent_dist * math.sin(angle2)
        )

        return [tangent1, tangent2]

    def intersect_line(self, line: Line2D) -> List[Point2D]:
        """Find intersection points with a line."""
        # Vector from line start to circle center
        to_center = Vector2D.from_points(line.start, self.center)
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
        chord_half_length = math.sqrt(self.radius ** 2 - dist_to_center ** 2)
        line_unit = line_vec.normalized()

        intersection1 = Point2D(
            closest_point.x - line_unit.dx * chord_half_length,
            closest_point.y - line_unit.dy * chord_half_length
        )
        intersection2 = Point2D(
            closest_point.x + line_unit.dx * chord_half_length,
            closest_point.y + line_unit.dy * chord_half_length
        )

        # Check if intersections are within line segment
        intersections = []

        # Check intersection1
        t1 = Vector2D.from_points(
            line.start, intersection1).dot(line_vec) / line_length_sq
        if 0 <= t1 <= 1:
            intersections.append(intersection1)

        # Check intersection2
        t2 = Vector2D.from_points(
            line.start, intersection2).dot(line_vec) / line_length_sq
        if 0 <= t2 <= 1:
            intersections.append(intersection2)

        return intersections

    def intersect_circle(self, other: 'Circle') -> List[Point2D]:
        """Find intersection points with another circle."""
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
            direction = Vector2D.from_points(
                self.center, other.center).normalized()
            point = self.center + direction * self.radius
            return [point]

        # Two intersections
        a = (self.radius ** 2 - other.radius ** 2 + dist ** 2) / (2 * dist)
        h = math.sqrt(self.radius ** 2 - a ** 2)

        # Point on line between centers
        direction = Vector2D.from_points(
            self.center, other.center
        ).normalized()
        midpoint = Point2D(
            self.center.x + direction.dx * a,
            self.center.y + direction.dy * a
        )

        # Perpendicular direction
        perp = direction.perpendicular()

        intersection1 = Point2D(
            midpoint.x + perp.dx * h,
            midpoint.y + perp.dy * h
        )
        intersection2 = Point2D(
            midpoint.x - perp.dx * h,
            midpoint.y - perp.dy * h
        )

        return [intersection1, intersection2]

    def translate(self, vector: Vector2D) -> 'Circle':
        """Translate circle by vector."""
        return Circle(self.center + vector, self.radius)

    def scale(self, factor: float, center: Optional[Point2D] = None) -> 'Circle':
        """Scale circle around a point."""
        if center is None:
            center = self.center

        new_center = self.center.scale_around(center, factor, factor)
        new_radius = self.radius * abs(factor)

        return Circle(new_center, new_radius)


class Polygon:
    """Polygon with geometric operations."""

    def __init__(self, vertices: List[Point2D]):
        """Initialize a polygon from vertices."""
        if len(vertices) < 3:
            raise ValueError("Polygon must have at least 3 vertices")
        self.vertices = vertices[:]

    def __repr__(self) -> str:
        return f"Polygon({len(self.vertices)} vertices)"

    def __str__(self) -> str:
        return f"Polygon with {len(self.vertices)} vertices"

    def __len__(self) -> int:
        return len(self.vertices)

    def __iter__(self) -> Iterator[Point2D]:
        return iter(self.vertices)

    def __getitem__(self, index: int) -> Point2D:
        return self.vertices[index]

    @property
    def edges(self) -> List[Line2D]:
        """Get polygon edges as line segments."""
        edges = []
        for i in range(len(self.vertices)):
            start = self.vertices[i]
            end = self.vertices[(i + 1) % len(self.vertices)]
            edges.append(Line2D(start, end))
        return edges

    @property
    def area(self) -> float:
        """Calculate polygon area using shoelace formula."""
        if len(self.vertices) < 3:
            return 0.0

        area = 0.0
        for i in range(len(self.vertices)):
            j = (i + 1) % len(self.vertices)
            area += self.vertices[i].x * self.vertices[j].y
            area -= self.vertices[j].x * self.vertices[i].y

        return abs(area) / 2.0

    @property
    def perimeter(self) -> float:
        """Calculate polygon perimeter."""
        perimeter = 0.0
        for edge in self.edges:
            perimeter += edge.length
        return perimeter

    @property
    def centroid(self) -> Point2D:
        """Calculate polygon centroid."""
        if len(self.vertices) < 3:
            return Point2D(0, 0)

        area = self.area
        if area == 0:
            # Degenerate polygon, return average of vertices
            sum_x = sum(v.x for v in self.vertices)
            sum_y = sum(v.y for v in self.vertices)
            return Point2D(sum_x / len(self.vertices), sum_y / len(self.vertices))

        cx = cy = 0.0
        for i in range(len(self.vertices)):
            j = (i + 1) % len(self.vertices)
            cross = self.vertices[i].x * self.vertices[j].y - self.vertices[j].x * self.vertices[i].y
            cx += (self.vertices[i].x + self.vertices[j].x) * cross
            cy += (self.vertices[i].y + self.vertices[j].y) * cross

        factor = 1.0 / (6.0 * area)
        return Point2D(cx * factor, cy * factor)

    @property
    def bounds(self) -> Tuple[Point2D, Point2D]:
        """Get bounding box as (min_point, max_point)."""
        if not self.vertices:
            return Point2D(0, 0), Point2D(0, 0)

        min_x = min(v.x for v in self.vertices)
        max_x = max(v.x for v in self.vertices)
        min_y = min(v.y for v in self.vertices)
        max_y = max(v.y for v in self.vertices)

        return Point2D(min_x, min_y), Point2D(max_x, max_y)

    def is_clockwise(self) -> bool:
        """Check if polygon vertices are ordered clockwise."""
        if len(self.vertices) < 3:
            return False

        # Calculate signed area (positive = counterclockwise, negative = clockwise)
        signed_area = 0.0
        for i in range(len(self.vertices)):
            j = (i + 1) % len(self.vertices)
            signed_area += (self.vertices[j].x - self.vertices[i].x) * (self.vertices[j].y + self.vertices[i].y)

        return signed_area > 0

    def is_convex(self) -> bool:
        """Check if polygon is convex."""
        if len(self.vertices) < 3:
            return False

        if len(self.vertices) == 3:
            return True

        # Check if all cross products have the same sign
        cross_products = []
        for i in range(len(self.vertices)):
            p1 = self.vertices[i]
            p2 = self.vertices[(i + 1) % len(self.vertices)]
            p3 = self.vertices[(i + 2) % len(self.vertices)]

            v1 = Vector2D.from_points(p1, p2)
            v2 = Vector2D.from_points(p2, p3)
            cross = v1.cross(v2)

            if abs(cross) > EPSILON:
                cross_products.append(cross)

        if not cross_products:
            return False

        # All cross products should have the same sign
        first_sign = cross_products[0] > 0
        return all((cp > 0) == first_sign for cp in cross_products)

    def contains_point(self, point: Point2D) -> bool:
        """Check if point is inside polygon using ray casting algorithm."""
        if len(self.vertices) < 3:
            return False

        x, y = point.x, point.y
        inside = False

        j = len(self.vertices) - 1
        for i in range(len(self.vertices)):
            xi, yi = self.vertices[i].x, self.vertices[i].y
            xj, yj = self.vertices[j].x, self.vertices[j].y

            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i

        return inside

    def translate(self, vector: Vector2D) -> 'Polygon':
        """Translate polygon by vector."""
        new_vertices = [v + vector for v in self.vertices]
        return Polygon(new_vertices)

    def rotate_around(self, center: Point2D, angle: float) -> 'Polygon':
        """Rotate polygon around a center point."""
        new_vertices = [v.rotate_around(center, angle) for v in self.vertices]
        return Polygon(new_vertices)

    def scale_around(self, center: Point2D, sx: float, sy: float) -> 'Polygon':
        """Scale polygon around a center point."""
        new_vertices = [v.scale_around(center, sx, sy) for v in self.vertices]
        return Polygon(new_vertices)

    @classmethod
    def rectangle(cls, center: Point2D, width: float, height: float) -> 'Polygon':
        """Create a rectangle polygon."""
        half_w = width / 2
        half_h = height / 2

        vertices = [
            Point2D(center.x - half_w, center.y - half_h),
            Point2D(center.x + half_w, center.y - half_h),
            Point2D(center.x + half_w, center.y + half_h),
            Point2D(center.x - half_w, center.y + half_h)
        ]

        return cls(vertices)

    @classmethod
    def regular_polygon(cls, center: Point2D, radius: float, sides: int) -> 'Polygon':
        """Create a regular polygon."""
        if sides < 3:
            raise ValueError("Regular polygon must have at least 3 sides")

        vertices = []
        angle_step = 2 * math.pi / sides

        for i in range(sides):
            angle = i * angle_step
            x = center.x + radius * math.cos(angle)
            y = center.y + radius * math.sin(angle)
            vertices.append(Point2D(x, y))

        return cls(vertices)


# Utility functions for backward compatibility

def geometry_points_are_collinear(x0: float, y0: float, x1: float, y1: float,
                                 x2: float, y2: float, tolerance: float = 1e-4) -> bool:
    """Check if three points are collinear within tolerance."""
    p0 = Point2D(x0, y0)
    p1 = Point2D(x1, y1)
    p2 = Point2D(x2, y2)

    v1 = Vector2D.from_points(p0, p1)
    v2 = Vector2D.from_points(p0, p2)

    # Check if cross product is near zero
    return abs(v1.cross(v2)) < tolerance


def geometry_distance_point_to_line(px: float, py: float,
                                   x1: float, y1: float,
                                   x2: float, y2: float) -> float:
    """Calculate distance from point to line segment."""
    point = Point2D(px, py)
    line = Line2D(Point2D(x1, y1), Point2D(x2, y2))
    return line.distance_to_point(point)


def geometry_line_intersection(x1: float, y1: float, x2: float, y2: float,
                              x3: float, y3: float, x4: float, y4: float) -> Optional[Tuple[float, float]]:
    """Find intersection of two line segments."""
    line1 = Line2D(Point2D(x1, y1), Point2D(x2, y2))
    line2 = Line2D(Point2D(x3, y3), Point2D(x4, y4))

    intersection = line1.intersect_line(line2)
    if intersection:
        return intersection.to_tuple()
    return None


def geometry_circle_line_intersection(cx: float, cy: float, radius: float,
                                     x1: float, y1: float, x2: float, y2: float) -> List[Tuple[float, float]]:
    """Find intersections between circle and line segment."""
    circle = Circle(Point2D(cx, cy), radius)
    line = Line2D(Point2D(x1, y1), Point2D(x2, y2))

    intersections = circle.intersect_line(line)
    return [p.to_tuple() for p in intersections]


def geometry_polygon_area(vertices: List[Tuple[float, float]]) -> float:
    """Calculate polygon area from vertex list."""
    points = [Point2D.from_tuple(v) for v in vertices]
    polygon = Polygon(points)
    return polygon.area


def geometry_point_in_polygon(px: float, py: float, vertices: List[Tuple[float, float]]) -> bool:
    """Check if point is inside polygon."""
    point = Point2D(px, py)
    points = [Point2D.from_tuple(v) for v in vertices]
    polygon = Polygon(points)
    return polygon.contains_point(point)
