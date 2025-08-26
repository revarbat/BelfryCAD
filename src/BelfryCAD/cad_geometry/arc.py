"""
Arc Class for CAD Geometry
"""

from typing import List, Optional, Tuple, Union, Iterator
import numpy as np
import math
from .shapes import Shape2D, ShapeType
from .point import Point2D
from .line import Line2D
from .transform import Transform2D
from .polygon import Polygon
from .circle import Circle
from .polyline import PolyLine2D
from .bezier import BezierPath

class Arc(Shape2D):
    """
    A circular arc defined by center, radius, start angle, and end angle.
    This class represents a portion of a circle's circumference.
    """

    def __init__(
            self,
            center: Point2D,
            radius: float,
            start_degrees: float,
            span_degrees: float
    ):
        """
        Initialize an arc.
        
        Args:
            center: Center point of the arc
            radius: Radius of the arc
            start_degrees: Start angle in degrees (0 = positive x-axis, counter-clockwise)
            span_degrees: Span angle in degrees (positive = counter-clockwise, negative = clockwise)
        """
        self.center = Point2D(center)
        self.radius = float(radius)
        self._start_degrees = float(start_degrees)
        self._span_degrees = float(span_degrees)
        
        # Normalize start angle to [0, 2π)
        self._start_degrees = self._start_degrees % 360.0
        
        # Calculate end angle from start angle and span
        self._end_degrees = self._start_degrees + self._span_degrees
        
        # Ensure radius is positive
        if self.radius <= 0:
            raise ValueError("Radius must be positive")

    def __repr__(self) -> str:
        return f"Arc(center={self.center}, radius={self.radius}, start={self.start_degrees:.3f}, end={self.end_degrees:.3f})"

    def __str__(self) -> str:
        return f"Arc at {self.center} with radius {self.radius} from {self.start_degrees:.3f} to {self.end_degrees:.3f}"

    def decompose(self, into: List[ShapeType] = [], tolerance: float = 0.001) -> List['Shape2D']:
        if ShapeType.ARC in into:
            return [self]
        if ShapeType.POLYLINE in into:
            return [self.to_polyline(segments=int(2*np.pi*self.radius/tolerance))]
        if ShapeType.LINE in into:
            # Decompose like we would a polyline, but using multiple lines.
            polyline = self.to_polyline(segments=int(2*np.pi*self.radius/tolerance))
            return [Line2D(p1, p2) for p1, p2 in zip(polyline.points[:-1], polyline.points[1:])]
        raise ValueError(f"Cannot decompose arc into any of {into}")

    @property
    def start_degrees(self) -> float:
        """Get the start angle in degrees."""
        return self._start_degrees

    @start_degrees.setter
    def start_degrees(self, value: float):
        """Set the start angle in degrees."""
        self._start_degrees = value % 360.0
        self._end_degrees = self._start_degrees + self._span_degrees

    @property
    def end_degrees(self) -> float:
        """Get the end angle in degrees."""
        return self._end_degrees

    @property
    def span_degrees(self) -> float:
        """Get the span angle in degrees."""
        return self._span_degrees

    @span_degrees.setter
    def span_degrees(self, value: float):
        """Set the span angle in degrees."""
        self._span_degrees = value % 360.0
        self._end_degrees = self._start_degrees + self._span_degrees

    @property
    def start_radians(self) -> float:
        """Get the start angle in radians."""
        return np.radians(self._start_degrees)

    @start_radians.setter
    def start_radians(self, value: float):
        """Set the start angle in radians."""
        self._start_degrees = np.degrees(value)
        self._end_degrees = self._start_degrees + self._span_degrees

    @property
    def end_radians(self) -> float:
        """Get the end angle in radians."""
        return np.radians(self._end_degrees)

    @property
    def span_radians(self) -> float:
        """Get the span angle in radians."""
        return np.radians(self._span_degrees)

    @span_radians.setter
    def span_radians(self, value: float):
        """Set the span angle in radians."""
        self._span_degrees = np.degrees(value)
        self._end_degrees = self._start_degrees + self._span_degrees

    @property
    def diameter(self) -> float:
        """Get the diameter of the arc."""
        return 2 * self.radius

    @property
    def length(self) -> float:
        """Calculate the arc length."""
        # Use the span angle directly
        return self.radius * abs(self.span_radians)

    @property
    def area(self) -> float:
        """Calculate the area of the arc sector."""
        # Use the span angle directly
        return 0.5 * self.radius * self.radius * abs(self.span_degrees)

    @property
    def start_point(self) -> Point2D:
        """Get the start point of the arc."""
        return self.center + Point2D(self.radius, angle=self.start_degrees)

    @property
    def end_point(self) -> Point2D:
        """Get the end point of the arc."""
        return self.center + Point2D(self.radius, angle=self.end_degrees)

    @property
    def midpoint(self) -> Point2D:
        """Get the midpoint of the arc."""
        mid_angle = (self.start_degrees + self.end_degrees) / 2
        return self.center + Point2D(self.radius, angle=mid_angle)

    @property
    def bounds(self) -> Tuple[Point2D, Point2D]:
        """Get bounding box of the arc."""
        # Get all potential extreme points
        points = [self.start_point, self.end_point]
        
        # Add potential extreme points at 0, π/2, π, 3π/2
        for angle in [0, np.pi/2, np.pi, 3*np.pi/2]:
            if self.contains_angle(angle):
                points.append(self.center + Point2D(
                    self.radius * np.cos(angle),
                    self.radius * np.sin(angle)
                ))
        
        # Calculate bounds
        if not points:
            return Point2D(0, 0), Point2D(0, 0)
        
        points_array = np.array([[p.x, p.y] for p in points])
        min_coords = np.min(points_array, axis=0)
        max_coords = np.max(points_array, axis=0)
        
        return Point2D(min_coords[0], min_coords[1]), Point2D(max_coords[0], max_coords[1])

    def contains_angle(self, angle: float) -> bool:
        """Check if the arc contains a given angle."""
        # Normalize angle to [0, 2π)
        angle = angle % (2 * np.pi)
        
        # For positive span (counter-clockwise), check if angle is between start and end
        if self.span_degrees >= 0:
            # Handle the case where the arc crosses the 0/2π boundary
            if self.start_degrees > self.end_degrees:
                return angle >= self.start_degrees or angle <= self.end_degrees
            else:
                return self.start_degrees <= angle <= self.end_degrees
        else:
            # For negative span (clockwise), check if angle is between end and start
            if self.end_degrees > self.start_degrees:
                return angle >= self.end_degrees or angle <= self.start_degrees
            else:
                return self.end_degrees <= angle <= self.start_degrees

    def contains_point(self, point: Point2D, tolerance: float = 1e-6) -> bool:
        """Check if a point is on the arc within tolerance."""
        # Check if point is on the circle
        distance_to_center = point.distance_to(self.center)
        if abs(distance_to_center - self.radius) > tolerance:
            return False
        
        # Check if point is within the arc's angle range
        angle_to_point = np.arctan2(point.y - self.center.y, point.x - self.center.x)
        return self.contains_angle(angle_to_point)

    def point_at_angle(self, angle: float) -> Point2D:
        """Get point on the arc at a specific angle."""
        if not self.contains_angle(angle):
            raise ValueError(f"Angle {angle} is not within the arc's range")
        
        return self.center + Point2D(
            self.radius * np.cos(angle),
            self.radius * np.sin(angle)
        )

    def tangent_at_angle(self, angle: float) -> Point2D:
        """Get the tangent vector at a specific angle."""
        if not self.contains_angle(angle):
            raise ValueError(f"Angle {angle} is not within the arc's range")
        
        # Tangent is perpendicular to radius vector
        # For counter-clockwise arc, tangent points in the direction of increasing angle
        return Point2D(-np.sin(angle), np.cos(angle))

    def translate(self, vector) -> 'Arc':
        """Translate the arc by vector."""
        return Arc(self.center.translate(vector), self.radius, self.start_degrees, self.span_degrees)

    def rotate(self, angle: float, center = None) -> 'Arc':
        """Rotate the arc around a center point."""
        if center is None:
            center = Point2D(0, 0)
        else:
            center = Point2D(center)
        
        # Rotate center point
        return Arc(self.center.rotate(angle, center), self.radius, self.start_degrees+angle, self.span_degrees)
        

    def scale(self, scale, center = None) -> 'Shape2D':
        """Scale the arc around a center point."""
        if center is None:
            center = Point2D(0, 0)
        else:
            center = Point2D(center)
        
        # Scale center point
        new_center = self.center.scale(scale, center)
        
        # Scale radius
        if isinstance(scale, (int, float, np.integer, np.floating)):
            new_radius = self.radius * float(scale)
            return Arc(new_center, new_radius, self.start_degrees, self.span_degrees)
        else:
            scale_point = Point2D(scale)
            # Generate a BezierPath from this arc.
            points = []
            for angle in np.linspace(self.start_degrees, self.end_degrees, 72):
                pt = self.point_at_angle(angle)
                pt = pt.scale(scale_point, center)  # type: ignore
                points.append(pt)
            return BezierPath(points)

    def transform(self, transform: Transform2D) -> 'Shape2D':
        """Transform arc using a transformation matrix."""
        new_center = self.center.transform(transform)
        # For non-uniform scaling, we need to handle radius differently
        # For now, we'll use the determinant to scale the radius
        points = [
            self.point_at_angle(angle).transform(transform)
            for angle in np.linspace(self.start_degrees, self.end_degrees, 36)
        ]
        return BezierPath(points)

    def reverse(self) -> 'Arc':
        """Create a reversed arc (swap start and end angles)."""
        return Arc(self.center, self.radius, self.end_degrees, -self.span_degrees)

    def to_polyline(self, segments: int = 32) -> 'PolyLine2D':
        """Convert arc to a polyline with specified number of segments."""
        # Use span angle directly
        angle_step = self.span_degrees / segments
        
        # Generate points along the arc
        points = []
        for i in range(segments + 1):
            angle = self.start_degrees + (angle_step * i)
            points.append(self.point_at_angle(angle))
        
        return PolyLine2D(points)

    def to_polygon(self, segments: int = 32) -> Polygon:
        """Convert arc to a polygon by creating a sector."""
        # Create polyline from arc
        polyline = self.to_polyline(segments)
        
        # Add center point and close
        points = [self.center] + polyline.points + [self.center]
        return Polygon(points)

    def intersect_line(self, line: Line2D) -> List[Point2D]:
        """Find intersection points with a line."""
        # First find intersections with the full circle
        circle = Circle(self.center, self.radius)
        circle_intersections = circle.intersect_line(line)
        
        # Filter intersections that are on the arc
        arc_intersections = []
        for point in circle_intersections:
            if self.contains_point(point):
                arc_intersections.append(point)
        
        return arc_intersections

    def intersect_arc(self, other: 'Arc') -> List[Point2D]:
        """Find intersection points with another arc."""
        # First find intersections with the full circles
        circle1 = Circle(self.center, self.radius)
        circle2 = Circle(other.center, other.radius)
        circle_intersections = circle1.intersect_circle(circle2)
        
        # Filter intersections that are on both arcs
        arc_intersections = []
        for point in circle_intersections:
            if self.contains_point(point) and other.contains_point(point):
                arc_intersections.append(point)
        
        return arc_intersections

    @classmethod
    def from_three_points(cls, p1: Point2D, p2: Point2D, p3: Point2D) -> 'Arc':
        """Create an arc from three points on the circumference."""
        circle = Circle.from_3_points([p1, p2, p3])
        center = circle.center
        radius = circle.radius  
        start_degrees = (p1 - center).angle_degrees
        end_degrees = (p3 - center).angle_degrees
        span_degrees = end_degrees - start_degrees
        
        # Normalize span angle to [-360°, 360°]
        if span_degrees > 360.0:
            span_degrees -= 360.0
        elif span_degrees < -360.0:
            span_degrees += 360.0
            
        return cls(center, radius, start_degrees, span_degrees)

    @classmethod
    def from_line_and_perimeter_point(cls, line: Line2D, perimeter_point: Point2D) -> 'Arc':
        """Create an arc from a line and a perimeter point."""
        circle = Circle.from_line_and_perimeter_point(line, perimeter_point)
        center = circle.center
        radius = circle.radius
        start_degrees = (line.start - center).angle_degrees
        end_degrees = (perimeter_point - center).angle_degrees
        span_degrees = end_degrees - start_degrees
        
        # Normalize span angle to [-360°, 360°]
        if span_degrees > 360.0:
            span_degrees -= 360.0
        elif span_degrees < -360.0:
            span_degrees += 360.0
            
        return cls(center, radius, start_degrees, span_degrees)

    @classmethod
    def semicircle(cls, center: Point2D, radius: float, start_degrees: float = 0) -> 'Arc':
        """Create a semicircle arc."""
        return cls(center, radius, start_degrees, 180)

    @classmethod
    def quarter_circle(cls, center: Point2D, radius: float, start_degrees: float = 0) -> 'Arc':
        """Create a quarter circle arc."""
        return cls(center, radius, start_degrees, 90)

    @classmethod
    def from_tangent_rays(cls, point: Point2D, ray1: Point2D, ray2: Point2D, radius: float) -> 'Arc':
        """
        Create an arc tangent to two rays from a point with given radius.
        
        Args:
            point: The common point where the two rays start
            ray1: First ray direction vector (should be unit vector)
            ray2: Second ray direction vector (should be unit vector)
            radius: Radius of the arc
        
        Returns:
            Arc that is tangent to both rays with the specified radius
        """
        # Normalize ray vectors
        ray1_norm = ray1.unit_vector
        ray2_norm = ray2.unit_vector
        
        # Calculate the angle between the rays
        angle_between = ray1_norm.angle_between_vectors(ray2_norm)
        
        if abs(angle_between) < 1e-10:
            raise ValueError("Rays are parallel, cannot create tangent arc")
        
        # Calculate the center of the arc
        # The center lies at distance 'radius' from both rays
        # For a tangent arc, the center is at distance 'radius' from the point
        # along the angle bisector
        
        # Calculate the angle bisector
        if angle_between > 0:
            # Rays diverge, center is outside
            bisector_angle = (ray1_norm.angle_between_vectors(Point2D(1, 0)) + 
                            ray2_norm.angle_between_vectors(Point2D(1, 0))) / 2
            center_distance = radius / np.sin(angle_between / 2)
        else:
            # Rays converge, center is inside
            bisector_angle = (ray1_norm.angle_between_vectors(Point2D(1, 0)) + 
                            ray2_norm.angle_between_vectors(Point2D(1, 0))) / 2
            center_distance = radius / np.sin(abs(angle_between) / 2)
        
        # Create bisector vector
        bisector = Point2D(np.cos(bisector_angle), np.sin(bisector_angle))
        
        # Calculate center position
        center = point + bisector * center_distance
        
        # Calculate start and end angles for the arc
        # The arc should be tangent to both rays
        # We need to calculate angles relative to the center, not the origin
        start_degrees = np.degrees(np.arctan2(ray1_norm.y, ray1_norm.x))
        end_degrees = np.degrees(np.arctan2(ray2_norm.y, ray2_norm.x))
        
        # Ensure the arc goes in the correct direction
        # The arc should connect the rays in the shortest way
        angle_diff = end_degrees - start_degrees
        
        # Normalize angle difference to [-π, π]
        if angle_diff > np.pi:
            angle_diff -= 2 * np.pi
        elif angle_diff < -np.pi:
            angle_diff += 2 * np.pi
        
        # If the angle difference is too large, we need to go the other way
        if abs(angle_diff) > np.pi:
            if angle_diff > 0:
                end_degrees -= 360
            else:
                start_degrees -= 360
        
        return cls(center, radius, start_degrees, end_degrees - start_degrees)

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get the bounds of the arc as (min_x, min_y, max_x, max_y)."""
        min_pt, max_pt = self.bounds
        return (min_pt.x, min_pt.y, max_pt.x, max_pt.y)
