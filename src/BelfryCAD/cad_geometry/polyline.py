"""
PolyLine2D Class for CAD Geometry

This module provides the PolyLine2D class for representing 2D polylines
with various geometric operations and calculations.
"""

from typing import List, Optional, Tuple, Union, Iterator, TYPE_CHECKING
import numpy as np
import math
from .shapes import Shape2D, ShapeType
from .point import Point2D
from .line import Line2D
from .transform import Transform2D

if TYPE_CHECKING:
    from .polygon import Polygon
    from .bezier import BezierPath
    from .region import Region

class PolyLine2D(Shape2D):
    """
    A polyline consisting of a list of connected points.
    This class represents a path or contour made up of line segments.
    """

    def __init__(self, points: List[Point2D]):
        """
        Initialize a polyline with a list of points.
        
        Args:
            points: List of connected points forming the polyline
        """
        if len(points) < 2:
            raise ValueError("PolyLine2D must have at least 2 points")
        self.points = points.copy()

    def __repr__(self) -> str:
        return f"PolyLine2D({len(self.points)} points)"

    def __str__(self) -> str:
        return f"PolyLine2D with {len(self.points)} points"

    def decompose(self, into: List[ShapeType] = [], tolerance: float = 0.001) -> List['Shape2D']:
        if ShapeType.POLYLINE in into:
            return [self]
        if ShapeType.LINE in into:
            return [Line2D(self.points[i], self.points[i + 1]) for i in range(len(self.points) - 1)]
        raise ValueError(f"Cannot decompose polyline into any of {into}")

    def __len__(self) -> int:
        return len(self.points)

    def __iter__(self) -> Iterator[Point2D]:
        """Iterate over all points in the polyline."""
        yield from self.points

    def __getitem__(self, index: int) -> Point2D:
        """Get point by index."""
        return self.points[index]

    def __setitem__(self, index: int, point: Point2D):
        """Set point at index."""
        self.points[index] = point

    @property
    def length(self) -> float:
        """Calculate total length of the polyline."""
        if len(self.points) < 2:
            return 0.0
        
        total_length = 0.0
        for i in range(len(self.points) - 1):
            total_length += self.points[i].distance_to(self.points[i + 1])
        return total_length

    @property
    def bounds(self) -> Tuple[Point2D, Point2D]:
        """Get bounding box as (min_point, max_point)."""
        if not self.points:
            return Point2D(0, 0), Point2D(0, 0)

        # Use numpy for efficient min/max calculation
        points_array = np.array([[p.x, p.y] for p in self.points])
        min_coords = np.min(points_array, axis=0)
        max_coords = np.max(points_array, axis=0)

        return Point2D(min_coords[0], min_coords[1]), Point2D(max_coords[0], max_coords[1])

    @property
    def segments(self) -> List[Line2D]:
        """Get list of line segments that make up the polyline."""
        segments = []
        for i in range(len(self.points) - 1):
            segments.append(Line2D(self.points[i], self.points[i + 1]))
        return segments

    def add_point(self, point: Point2D):
        """Add a point to the end of the polyline."""
        self.points.append(point)

    def insert_point(self, index: int, point: Point2D):
        """Insert a point at the specified index."""
        if index < 0 or index > len(self.points):
            raise IndexError("Index out of range")
        self.points.insert(index, point)

    def remove_point(self, index: int):
        """Remove a point at the specified index."""
        if index < 0 or index >= len(self.points):
            raise IndexError("Index out of range")
        if len(self.points) <= 2:
            raise ValueError("Cannot remove point: PolyLine2D must have at least 2 points")
        del self.points[index]

    def translate(self, vector) -> 'PolyLine2D':
        """Translate all points in the polyline by vector."""
        return PolyLine2D([point.translate(vector) for point in self.points])

    def rotate(self, angle: float, center = None) -> 'PolyLine2D':
        """Rotate all points in the polyline around a center point."""
        return PolyLine2D([point.rotate(angle, center) for point in self.points])

    def scale(self, scale, center = None) -> 'PolyLine2D':
        """Scale all points in the polyline around a center point."""
        return PolyLine2D([point.scale(scale, center) for point in self.points])

    def transform(self, transform: Transform2D) -> 'PolyLine2D':
        """Transform polyline using a transformation matrix."""
        return PolyLine2D([point.transform(transform) for point in self.points])

    def reverse(self):
        """Reverse the order of points in the polyline."""
        self.points.reverse()

    def close(self) -> 'Polygon':
        """Create a closed polyline by adding the first point to the end and return as a polygon."""
        if len(self.points) < 3:
            raise ValueError("Cannot close polyline with fewer than 3 points")
        if self.points[0] == self.points[-1]:
            # Already closed, return as polygon
            return Polygon(self.points[:-1])  # Remove duplicate last point
        closed_points = self.points + [self.points[0]]
        return Polygon(closed_points[:-1])  # Remove duplicate last point

    def is_closed(self) -> bool:
        """Check if the polyline is closed (first and last points are the same)."""
        return len(self.points) >= 3 and self.points[0] == self.points[-1]

    def distance_to_point(self, point: Point2D) -> float:
        """Calculate the minimum distance from a point to the polyline."""
        if len(self.points) < 2:
            return float('inf')
        
        min_distance = float('inf')
        for segment in self.segments:
            distance = segment.distance_to_point(point)
            min_distance = min(min_distance, distance)
        
        return min_distance

    def closest_point_to(self, point: Point2D) -> Point2D:
        """Find the closest point on the polyline to the given point."""
        if len(self.points) < 2:
            return self.points[0] if self.points else Point2D(0, 0)
        
        min_distance = float('inf')
        closest_point = self.points[0]
        
        for segment in self.segments:
            segment_closest = segment.closest_point_to(point)
            distance = segment_closest.distance_to(point)
            if distance < min_distance:
                min_distance = distance
                closest_point = segment_closest
        
        return closest_point

    def contains_point(self, point: Point2D, tolerance: float = 1e-6) -> bool:
        """
        Check if a point is on the polyline within tolerance.
        This checks if the point is within tolerance of any segment.
        """
        return self.distance_to_point(point) <= tolerance

    def intersects_with(self, other: 'PolyLine2D', tolerance: float = 1e-6) -> List[Point2D]:
        """Find intersection points between this polyline and another."""
        intersections = []
        
        for segment1 in self.segments:
            for segment2 in other.segments:
                intersection = segment1.intersects_at(segment2)
                if intersection is not None:
                    # Check if this intersection is already found
                    is_duplicate = False
                    for existing in intersections:
                        if existing.distance_to(intersection) <= tolerance:
                            is_duplicate = True
                            break
                    if not is_duplicate:
                        intersections.append(intersection)
        
        return intersections

    def to_polygon(self) -> Optional['Polygon']:
        """Convert closed polyline to polygon. Returns None if not closed."""
        if not self.is_closed():
            return None
        
        # Remove the duplicate last point for polygon creation
        polygon_points = self.points[:-1]
        return Polygon(polygon_points)

    def offset(self, distance: float, join_type: str = 'round', end_type: str = 'closed_polygon') -> List['PolyLine2D']:
        """
        Create an offset of the polyline.
        
        Args:
            distance: Positive for outward offset, negative for inward
            join_type: 'round', 'square', or 'miter'
            end_type: 'closed_polygon', 'closed_line', or 'open_butt'
        
        Returns:
            List of offset polylines
        """
        try:
            import pyclipper
        except ImportError:
            raise ImportError("PyClipper is required for offset operations")
        
        # Convert polyline to PyClipper path format
        path = self._to_clipper_path()
        
        # Create PyClipperOffset object
        po = pyclipper.PyclipperOffset() # type: ignore
        
        # Determine join type
        if join_type == 'round':
            join_type_enum = pyclipper.JT_ROUND # type: ignore
        elif join_type == 'square':
            join_type_enum = pyclipper.JT_SQUARE # type: ignore
        elif join_type == 'miter':
            join_type_enum = pyclipper.JT_MITER # type: ignore
        else:
            raise ValueError("join_type must be 'round', 'square', or 'miter'")
        
        # Determine end type
        if end_type == 'closed_polygon':
            end_type_enum = pyclipper.ET_CLOSEDPOLYGON # type: ignore
        elif end_type == 'closed_line':
            end_type_enum = pyclipper.ET_CLOSEDLINE # type: ignore
        elif end_type == 'open_butt':
            end_type_enum = pyclipper.ET_OPENBUTT # type: ignore
        else:
            raise ValueError("end_type must be 'closed_polygon', 'closed_line', or 'open_butt'")
        
        # Add path and execute offset
        po.AddPath(path, join_type_enum, end_type_enum)
        result_paths = po.Execute(distance * Region.clipper_scale_factor)
        
        # Convert results back to PolyLine2D objects
        result_polylines = []
        for result_path in result_paths:
            if len(result_path) >= 2:  # Ensure valid polyline
                polyline = self._from_clipper_path(result_path)
                result_polylines.append(polyline)
        
        return result_polylines

    def _to_clipper_path(self) -> List[List[int]]:
        """Convert polyline points to PyClipper path format."""
        try:
            import pyclipper
        except ImportError:
            raise ImportError("PyClipper is required for boolean operations")
        
        # Convert Point2D to integer coordinates (PyClipper uses integers)
        # Scale to preserve precision
        scale_factor = Region.clipper_scale_factor
        path = []
        for point in self.points:
            x = int(point.x * scale_factor)
            y = int(point.y * scale_factor)
            path.append([x, y])
        return path

    @classmethod
    def _from_clipper_path(cls, path: List[List[int]]) -> 'PolyLine2D':
        """Convert PyClipper path format to PolyLine2D."""
        try:
            import pyclipper
        except ImportError:
            raise ImportError("PyClipper is required for boolean operations")
        
        # Convert back from integer coordinates
        scale_factor = Region.clipper_scale_factor
        points = []
        for point in path:
            x = point[0] / scale_factor
            y = point[1] / scale_factor
            points.append(Point2D(x, y))
        return cls(points)

    def add_vertex_at_point(self, point: Point2D, tolerance: float = 1e-6) -> int:
        """
        Add a vertex at a point that is almost exactly on the polyline.
        
        This method splits the line segment that contains the point and inserts
        a new vertex at that location. If the point is almost coincident with
        an existing vertex, no vertex is added. If the point is not on the
        polyline, an error is raised.
        
        Args:
            point: The point where to add the vertex
            tolerance: Distance tolerance for determining if point is on polyline
            
        Returns:
            The index of the newly added vertex (or existing vertex if coincident)
            
        Raises:
            ValueError: If the point is not on the polyline within tolerance
        """
        if len(self.points) < 2:
            raise ValueError("Cannot add vertex to polyline with fewer than 2 points")
        
        # First check if the point is already coincident with an existing vertex
        for i, existing_point in enumerate(self.points):
            if existing_point.distance_to(point) <= tolerance:
                return i  # Return existing vertex index
        
        # Find which segment contains the point
        segment_index = None
        closest_distance = float('inf')
        
        for i, segment in enumerate(self.segments):
            distance = segment.distance_to_point(point)
            if distance <= tolerance and distance < closest_distance:
                segment_index = i
                closest_distance = distance
        
        if segment_index is None:
            raise ValueError(f"Point {point} is not on the polyline within tolerance {tolerance}")
        
        # Insert the new vertex after the start point of the segment
        insert_index = segment_index + 1
        self.points.insert(insert_index, point)
        
        return insert_index

    def delete_vertex_at_point(self, point: Point2D, tolerance: float = 1e-6) -> bool:
        """
        Delete a vertex that is close to the given point.
        
        This method finds a vertex within tolerance of the given point and removes it.
        If no vertex is found within tolerance, no deletion occurs.
        
        Args:
            point: The point near which to delete a vertex
            tolerance: Distance tolerance for finding points to delete
            
        Returns:
            True if a vertex was deleted, False if no vertex was found within tolerance
            
        Raises:
            ValueError: If deletion would result in fewer than 2 points
        """
        if len(self.points) <= 2:
            raise ValueError("Cannot delete vertex: PolyLine2D must have at least 2 points")
        
        # Find the vertex closest to the point within tolerance
        closest_index = None
        closest_distance = float('inf')
        
        for i, vertex in enumerate(self.points):
            distance = vertex.distance_to(point)
            if distance <= tolerance and distance < closest_distance:
                closest_index = i
                closest_distance = distance
        
        if closest_index is None:
            return False  # No vertex found within tolerance
        
        # Remove the vertex
        del self.points[closest_index]
        return True

    def simplify(self, tolerance: float = 1e-6) -> int:
        """
        Simplify the polyline by removing redundant points.
        
        This method removes points that are:
        1. Coincident with adjacent points (within tolerance)
        2. Redundant collinear points (within tolerance)
        
        Args:
            tolerance: Distance and angle tolerance for simplification
            
        Returns:
            Number of points removed during simplification
        """
        if len(self.points) <= 2:
            return 0  # Cannot simplify polylines with 2 or fewer points
        
        original_count = len(self.points)
        i = 0
        
        while i < len(self.points) - 1:
            current = self.points[i]
            next_point = self.points[i + 1]
            
            # Check if current and next points are coincident
            if current.distance_to(next_point) <= tolerance:
                # Remove the next point (keep the current one)
                del self.points[i + 1]
                continue
            
            # Check if we have enough points to check collinearity
            if i > 0 and i < len(self.points) - 1:
                prev_point = self.points[i - 1]
                
                # Check if current point is collinear with adjacent points
                if self._is_collinear(prev_point, current, next_point, tolerance):
                    # Remove the current point
                    del self.points[i]
                    continue
            
            i += 1
        
        return original_count - len(self.points)

    def split_at_point(self, point: Point2D, tolerance: float = 1e-6) -> Tuple['PolyLine2D', 'PolyLine2D']:
        """
        Split the polyline at a given point.
        
        This method finds the segment that contains the given point and splits
        the polyline into two parts: one ending at the point, and one starting
        at the point.
        
        Args:
            point: The point where to split the polyline
            tolerance: Distance tolerance for finding the split point
            
        Returns:
            Tuple of two polylines: (before_point, after_point)
            
        Raises:
            ValueError: If the point is not on the polyline within tolerance
        """
        if len(self.points) < 2:
            raise ValueError("Cannot split polyline with fewer than 2 points")
        
        # First check if the point is coincident with an existing vertex
        for i, existing_point in enumerate(self.points):
            if existing_point.distance_to(point) <= tolerance:
                # Point is at an existing vertex, split there
                return self._split_at_vertex(i)
        
        # Find which segment contains the point
        segment_index = None
        closest_distance = float('inf')
        
        for i, segment in enumerate(self.segments):
            distance = segment.distance_to_point(point)
            if distance <= tolerance and distance < closest_distance:
                segment_index = i
                closest_distance = distance
        
        if segment_index is None:
            raise ValueError(f"Point {point} is not on the polyline within tolerance {tolerance}")
        
        # Split at the segment
        return self._split_at_segment(segment_index, point)

    def _split_at_vertex(self, vertex_index: int) -> Tuple['PolyLine2D', 'PolyLine2D']:
        """
        Split the polyline at an existing vertex.
        
        Args:
            vertex_index: Index of the vertex where to split
            
        Returns:
            Tuple of two polylines: (before_vertex, after_vertex)
        """
        # Handle special cases for first and last points
        if vertex_index == 0:
            # Split at first vertex: before has only the first point, after has all points
            before_points = [self.points[0]]
            after_points = self.points[:]
        elif vertex_index == len(self.points) - 1:
            # Split at last vertex: before has all points, after has only the last point
            before_points = self.points[:]
            after_points = [self.points[-1]]
        else:
            # Split at middle vertex: normal case
            before_points = self.points[:vertex_index + 1]
            after_points = self.points[vertex_index:]
        
        # Create polylines, handling the special cases where we might have only one point
        if len(before_points) == 1:
            # For single point, duplicate it to create a valid polyline
            before_polyline = PolyLine2D([before_points[0], before_points[0]])
        else:
            before_polyline = PolyLine2D(before_points)
        
        if len(after_points) == 1:
            # For single point, duplicate it to create a valid polyline
            after_polyline = PolyLine2D([after_points[0], after_points[0]])
        else:
            after_polyline = PolyLine2D(after_points)
        
        return before_polyline, after_polyline

    def _split_at_segment(self, segment_index: int, point: Point2D) -> Tuple['PolyLine2D', 'PolyLine2D']:
        """
        Split the polyline at a point on a segment.
        
        Args:
            segment_index: Index of the segment where to split
            point: The exact point where to split
            
        Returns:
            Tuple of two polylines: (before_point, after_point)
        """
        # Create the first polyline (up to the segment start, plus the split point)
        before_points = self.points[:segment_index + 1] + [point]
        before_polyline = PolyLine2D(before_points)
        
        # Create the second polyline (starting from the split point, plus the rest)
        after_points = [point] + self.points[segment_index + 1:]
        after_polyline = PolyLine2D(after_points)
        
        return before_polyline, after_polyline

    def reorient_start_point(self, new_start_index: int, tolerance: float = 1e-6) -> bool:
        """
        Reorient the polyline to start at a different vertex.
        
        This method is only applicable to closed polylines (where start and end points
        are coincident). It reorders the points so that the specified vertex becomes
        the new starting point.
        
        Args:
            new_start_index: Index of the vertex that should become the new start point
            tolerance: Distance tolerance for determining if polyline is closed
            
        Returns:
            True if reorientation was successful, False if polyline is not closed
            
        Raises:
            ValueError: If new_start_index is invalid
        """
        if len(self.points) < 3:
            return False  # Need at least 3 points for a closed polyline
        
        # Check if polyline is closed (start and end points are coincident)
        if self.points[0].distance_to(self.points[-1]) > tolerance:
            return False  # Polyline is not closed
        
        # Validate the new start index
        if new_start_index < 0 or new_start_index >= len(self.points):
            raise ValueError(f"Invalid start index {new_start_index}. Must be between 0 and {len(self.points) - 1}")
        
        # If the new start index is 0, no reorientation needed
        if new_start_index == 0:
            return True
        
        # Reorient the polyline by rotating the points
        # We need to handle the fact that the last point is the same as the first
        # So we rotate the points and ensure the last point matches the new first point
        
        # Create the reoriented points
        reoriented_points = []
        
        # Add points from new_start_index to the end (excluding the last point if it's the same as first)
        for i in range(new_start_index, len(self.points) - 1):
            reoriented_points.append(self.points[i])
        
        # Add points from beginning to new_start_index
        for i in range(new_start_index):
            reoriented_points.append(self.points[i])
        
        # Add the new start point as the last point to close the polyline
        reoriented_points.append(self.points[new_start_index])
        
        # Update the polyline points
        self.points = reoriented_points
        
        return True

    def _is_redundant_point(self, p1: Point2D, p2: Point2D, p3: Point2D, tolerance: float) -> bool:
        """
        Check if a point is redundant (can be removed without changing the shape).
        
        A point is redundant if:
        1. It's collinear with its adjacent points
        2. Removing it doesn't change the overall direction of the path
        
        Args:
            p1, p2, p3: Three consecutive points (p2 is the candidate for removal)
            tolerance: Distance and angle tolerance
            
        Returns:
            True if the point is redundant and can be removed
        """
        # Create vectors
        v1 = p2 - p1
        v2 = p3 - p2
        v3 = p3 - p1  # Direct vector from p1 to p3
        
        # Check if vectors are zero (coincident points)
        if v1.magnitude <= tolerance or v2.magnitude <= tolerance:
            return True
        
        # Check if the point is collinear
        angle = abs(v1.angle_between_vectors(v2))
        is_collinear = angle <= tolerance or abs(angle - np.pi) <= tolerance
        
        if not is_collinear:
            return False
        
        # For collinear points, check if removing p2 doesn't change the path direction
        # This is true if the direct vector p1->p3 has the same direction as the sum of p1->p2 + p2->p3
        if v3.magnitude <= tolerance:
            return True
        
        # Check if the direction is preserved
        # The angle between v1 and v3 should be small, and the angle between v2 and v3 should be small
        angle1 = abs(v1.angle_between_vectors(v3))
        angle2 = abs(v2.angle_between_vectors(v3))
        
        return angle1 <= tolerance and angle2 <= tolerance

    def _is_collinear(self, p1: Point2D, p2: Point2D, p3: Point2D, tolerance: float) -> bool:
        """
        Check if three points are collinear within tolerance.
        
        Args:
            p1, p2, p3: Three points to check
            tolerance: Angle tolerance in radians
            
        Returns:
            True if points are collinear within tolerance
        """
        # Create vectors
        v1 = p2 - p1
        v2 = p3 - p2
        
        # Check if vectors are zero (coincident points)
        if v1.magnitude <= tolerance or v2.magnitude <= tolerance:
            return True
        
        # Calculate angle between vectors
        angle = abs(v1.angle_between_vectors(v2))
        
        # Points are collinear if angle is close to 0 or π
        return angle <= tolerance or abs(angle - np.pi) <= tolerance

    @classmethod
    def from_polygon(cls, polygon: 'Polygon') -> 'PolyLine2D':
        """Create a polyline from a polygon."""
        points = polygon.points + [polygon.points[0]]  # Close the polyline
        return cls(points)

    @classmethod
    def rectangle(cls, center: Point2D, width: float, height: float) -> 'PolyLine2D':
        """Create a rectangular polyline."""
        half_w = width / 2
        half_h = height / 2

        points = [
            center + Point2D(-half_w, -half_h),
            center + Point2D(-half_w, half_h),
            center + Point2D(half_w, half_h),
            center + Point2D(half_w, -half_h),
            center + Point2D(-half_w, -half_h)  # Close the rectangle
        ]

        return cls(points)

    @classmethod
    def circle(cls, center: Point2D, radius: float, segments: int = 64) -> 'PolyLine2D':
        """Create a circular polyline."""
        angles = np.linspace(0, 2 * np.pi, segments + 1)
        points = [
            center + Point2D(radius * np.cos(angle), radius * np.sin(angle))
            for angle in angles
        ]
        return cls(points)

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get the bounds of the polyline as (min_x, min_y, max_x, max_y)."""
        if not self.points:
            return (0.0, 0.0, 0.0, 0.0)
        xs = [p.x for p in self.points]
        ys = [p.y for p in self.points]
        return (min(xs), min(ys), max(xs), max(ys))
