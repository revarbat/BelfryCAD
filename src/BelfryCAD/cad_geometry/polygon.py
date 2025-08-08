"""
Polygon Class for CAD Geometry

This module provides the Polygon class for representing 2D polygons
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
    from .polyline import PolyLine2D
    from .region import Region

EPSILON = 1e-10

class Polygon(Shape2D):
    """Polygon with geometric operations - optimized with numpy."""

    def __init__(self, points: List[Point2D]):
        """Initialize a polygon from points."""
        if len(points) < 3:
            raise ValueError("Polygon must have at least 3 points")
        self.points = points[:]

    def __repr__(self) -> str:
        return f"Polygon({len(self.points)} points)"

    def __str__(self) -> str:
        return f"Polygon with {len(self.points)} points"

    def decompose(self, into: List[ShapeType] = [], tolerance: float = 0.001) -> List['Shape2D']:
        if ShapeType.POLYGON in into:
            return [self]
        if ShapeType.REGION in into:
            return [Region(perimeters=[self], holes=[])]
        if ShapeType.POLYLINE in into:
            return [PolyLine2D(self.points)]
        if ShapeType.LINE in into:
            return [Line2D(self.points[i], self.points[i + 1]) for i in range(len(self.points) - 1)]
        raise ValueError(f"Cannot decompose polygon into any of {into}")

    def __len__(self) -> int:
        return len(self.points)

    def __iter__(self) -> Iterator[Point2D]:
        return iter(self.points)

    def __getitem__(self, index: int) -> Point2D:
        return self.points[index]

    @property
    def edges(self) -> List[Line2D]:
        """Get polygon edges as line segments."""
        edges = []
        for i in range(len(self.points)):
            start = self.points[i]
            end = self.points[(i + 1) % len(self.points)]
            edges.append(Line2D(start, end))
        return edges

    @property
    def area(self) -> float:
        """Calculate polygon area using shoelace formula - optimized with numpy."""
        if len(self.points) < 3:
            return 0.0

        # Convert to numpy arrays for faster computation
        vertices_array = np.array([[v.x, v.y] for v in self.points])
        
        # Use numpy for efficient area calculation
        x_coords = vertices_array[:, 0]
        y_coords = vertices_array[:, 1]
        
        # Calculate area using shoelace formula with numpy
        x_shifted = np.roll(x_coords, -1)
        y_shifted = np.roll(y_coords, -1)
        
        area = np.sum(x_coords * y_shifted - x_shifted * y_coords)
        return np.abs(area) / 2.0

    @property
    def perimeter(self) -> float:
        """Calculate polygon perimeter - optimized."""
        if len(self.points) < 2:
            return 0.0
        
        # Use numpy for vectorized distance calculation
        vertices_array = np.array([[v.x, v.y] for v in self.points])
        # Create array of consecutive pairs
        pairs = np.column_stack([vertices_array, np.roll(vertices_array, -1, axis=0)])
        
        # Calculate distances between consecutive points
        distances = np.sqrt(np.sum((pairs[:, :2] - pairs[:, 2:]) ** 2, axis=1))
        
        return np.sum(distances)

    @property
    def centroid(self) -> Point2D:
        """Calculate polygon centroid - optimized with numpy."""
        if len(self.points) < 3:
            return Point2D(0, 0)

        area = self.area
        if area == 0:
            # Degenerate polygon, return average of points
            vertices_array = np.array([[v.x, v.y] for v in self.points])
            centroid_coords = np.mean(vertices_array, axis=0)
            return Point2D(centroid_coords[0], centroid_coords[1])

        # Use numpy for efficient centroid calculation
        vertices_array = np.array([[v.x, v.y] for v in self.points])
        
        # Calculate centroid using area-weighted method
        x_coords = vertices_array[:, 0]
        y_coords = vertices_array[:, 1]
        
        # Shift arrays for cross product calculation
        x_shifted = np.roll(x_coords, -1)
        y_shifted = np.roll(y_coords, -1)
        
        # Calculate cross products
        cross_products = x_coords * y_shifted - x_shifted * y_coords
        
        # Calculate centroid coordinates
        cx = np.sum((x_coords + x_shifted) * cross_products) / (6.0 * area)
        cy = np.sum((y_coords + y_shifted) * cross_products) / (6.0 * area)
        
        return Point2D(cx, cy)

    @property
    def bounds(self) -> Tuple[Point2D, Point2D]:
        """Get bounding box as (min_point, max_point) - optimized with numpy."""
        if not self.points:
            return Point2D(0, 0), Point2D(0, 0)

        # Use numpy for efficient min/max calculation
        vertices_array = np.array([[v.x, v.y] for v in self.points])
        min_coords = np.min(vertices_array, axis=0)
        max_coords = np.max(vertices_array, axis=0)

        return Point2D(min_coords[0], min_coords[1]), Point2D(max_coords[0], max_coords[1])

    def is_clockwise(self) -> bool:
        """Check if polygon points are ordered clockwise - optimized."""
        if len(self.points) < 3:
            return False

        # Use numpy for efficient signed area calculation
        vertices_array = np.array([[v.x, v.y] for v in self.points])
        
        # Calculate signed area using shoelace formula
        x_coords = vertices_array[:, 0]
        y_coords = vertices_array[:, 1]
        
        # Shift arrays for cross product calculation
        x_shifted = np.roll(x_coords, -1)
        y_shifted = np.roll(y_coords, -1)
        
        # Calculate signed area
        signed_area = np.sum((x_shifted - x_coords) * (y_shifted + y_coords))
        
        return signed_area > 0

    def is_convex(self) -> bool:
        """Check if polygon is convex - optimized with numpy."""
        if len(self.points) < 3:
            return False

        if len(self.points) == 3:
            return True

        # Use numpy for efficient cross product calculation
        points_array = np.array([[v.x, v.y] for v in self.points])
        
        # Create vectors between consecutive points
        vectors = np.diff(points_array, axis=0)
        # Add the vector from last to first vertex
        vectors = np.vstack([vectors, points_array[0] - points_array[-1]])
        
        # Calculate cross products
        cross_products = np.cross(vectors[:-1], vectors[1:])
        
        # Filter out near-zero cross products
        significant_crosses = cross_products[np.abs(cross_products) > EPSILON]
        
        if len(significant_crosses) == 0:
            return False
        
        # All cross products should have the same sign
        first_sign = significant_crosses[0] > 0
        return bool(np.all((significant_crosses > 0) == first_sign))

    def contains_point(self, point: Point2D, tolerance: float = EPSILON) -> bool:
        """Check if point is inside polygon using ray casting algorithm - optimized."""
        if len(self.points) < 3:
            return False

        # Use numpy for efficient ray casting
        points_array = np.array([[v.x, v.y] for v in self.points])
        px, py = point.x, point.y
        
        # Extract x and y coordinates
        x_coords = points_array[:, 0]
        y_coords = points_array[:, 1]
        
        # Shift arrays for edge calculation
        x_shifted = np.roll(x_coords, -1)
        y_shifted = np.roll(y_coords, -1)
        
        # Calculate ray casting conditions
        # Check if ray crosses edge
        # Avoid division by zero
        denominator = y_shifted - y_coords
        valid_edges = np.abs(denominator) > tolerance
        crosses = ((y_coords > py) != (y_shifted > py)) & valid_edges & \
                 (px < (x_shifted - x_coords) * (py - y_coords) / denominator + x_coords)
        
        return bool(np.sum(crosses) % 2 == 1)

    def translate(self, vector) -> 'Polygon':
        """Translate polygon by vector."""
        return Polygon([point.translate(vector) for point in self.points])

    def rotate(self, angle: float, center = None) -> 'Polygon':
        """Rotate polygon around a center point."""
        return Polygon([point.rotate(angle, center) for point in self.points])

    def scale(self, scale, center = None) -> 'Polygon':
        """Scale polygon around a center point."""
        return Polygon([point.scale(scale, center) for point in self.points])
        
    def transform(self, transform: Transform2D) -> 'Polygon':
        """Transform polygon using a transformation matrix."""
        return Polygon([point.transform(transform) for point in self.points])

    @classmethod
    def rectangle(cls, center: Point2D, width: float, height: float) -> 'Polygon':
        """Create a rectangle polygon."""
        half_w = width / 2
        half_h = height / 2

        points = [
            center + Point2D(-half_w, -half_h),
            center + Point2D(-half_w, half_h),
            center + Point2D(half_w, half_h),
            center + Point2D(half_w, -half_h)
        ]

        return cls(points)

    @classmethod
    def regular_polygon(cls, center: Point2D, radius: float, sides: int) -> 'Polygon':
        """Create a regular polygon - optimized with numpy."""
        if sides < 3:
            raise ValueError("Regular polygon must have at least 3 sides")
        
        # Use numpy for efficient angle calculation
        angles = np.linspace(0, 2 * np.pi, sides + 1)[:-1]  # Exclude last angle to avoid duplicate
        points = [
            center + Point2D(radius * np.cos(angle), radius * np.sin(angle))
            for angle in angles
        ]
        return cls(points)

    def _to_clipper_path(self) -> List[List[int]]:
        """Convert polygon points to PyClipper path format."""
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
    def _from_clipper_path(cls, path: List[List[int]]) -> 'Polygon':
        """Convert PyClipper path format to Polygon."""
        # Convert back from integer coordinates
        scale_factor = Region.clipper_scale_factor
        points = []
        for point in path:
            x = point[0] / scale_factor
            y = point[1] / scale_factor
            points.append(Point2D(x, y))
        return cls(points)

    def union(self, other: 'Polygon') -> List['Polygon']:
        """
        Perform boolean union operation with another polygon.
        Returns a list of polygons (usually one, but can be multiple for complex cases).
        """
        # Create regions from polygons
        region1 = Region([self], [])
        region2 = Region([other], [])
        
        # Perform union using Region class
        result_region = region1.union(region2)
        
        # Return perimeters as polygons
        return result_region.perimeters

    def difference(self, other: 'Polygon') -> List['Polygon']:
        """
        Perform boolean difference operation (self - other).
        Returns a list of polygons representing the difference.
        """
        # Create regions from polygons
        region1 = Region([self], [])
        region2 = Region([other], [])
        
        # Perform difference using Region class
        result_region = region1.difference(region2)
        
        # Return perimeters as polygons
        return result_region.perimeters

    def intersection(self, other: 'Polygon') -> List['Polygon']:
        """
        Perform boolean intersection operation with another polygon.
        Returns a list of polygons representing the intersection.
        """
        # Create regions from polygons
        region1 = Region([self], [])
        region2 = Region([other], [])
        
        # Perform intersection using Region class
        result_region = region1.intersection(region2)
        
        # Return perimeters as polygons
        return result_region.perimeters

    def offset(self, distance: float, join_type: str = 'round', end_type: str = 'closed_polygon') -> List['Polygon']:
        """
        Create an offset (inset or outset) of the polygon.
        
        Args:
            distance: Positive for outset, negative for inset
            join_type: 'round', 'square', or 'miter'
            end_type: 'closed_polygon', 'closed_line', or 'open_butt'
        
        Returns:
            List of offset polygons
        """
        # Create region from polygon
        region = Region([self], [])
        
        # Perform offset using Region class
        result_region = region.offset(distance, join_type, end_type)
        
        # Return perimeters as polygons
        return result_region.perimeters

    def xor(self, other: 'Polygon') -> List['Polygon']:
        """
        Perform boolean XOR operation with another polygon.
        Returns a list of polygons representing the XOR result.
        """
        # Create regions from polygons
        region1 = Region([self], [])
        region2 = Region([other], [])
        
        # Perform XOR using Region class
        result_region = region1.xor(region2)
        
        # Return perimeters as polygons
        return result_region.perimeters

    def add_vertex_at_point(self, point: Point2D, tolerance: float = 1e-6) -> int:
        """
        Add a vertex at a point that is almost exactly on the polygon perimeter.
        
        This method splits the edge that contains the point and inserts
        a new vertex at that location. If the point is almost coincident with
        an existing vertex, no vertex is added. If the point is not on the
        polygon perimeter, an error is raised.
        
        Args:
            point: The point where to add the vertex
            tolerance: Distance tolerance for determining if point is on polygon perimeter
            
        Returns:
            The index of the newly added vertex (or existing vertex if coincident)
            
        Raises:
            ValueError: If the point is not on the polygon perimeter within tolerance
        """
        if len(self.points) < 3:
            raise ValueError("Cannot add vertex to polygon with fewer than 3 points")
        
        # First check if the point is already coincident with an existing vertex
        for i, existing_point in enumerate(self.points):
            if existing_point.distance_to(point) <= tolerance:
                return i  # Return existing vertex index
        
        # Find which edge contains the point
        edge_index = None
        closest_distance = float('inf')
        
        for i, edge in enumerate(self.edges):
            distance = edge.distance_to_point(point)
            if distance <= tolerance and distance < closest_distance:
                edge_index = i
                closest_distance = distance
        
        if edge_index is None:
            raise ValueError(f"Point {point} is not on the polygon perimeter within tolerance {tolerance}")
        
        # Insert the new vertex after the start vertex of the edge
        # For polygons, the edge index corresponds to the start vertex index
        insert_index = edge_index + 1
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
            ValueError: If deletion would result in fewer than 3 points
        """
        if len(self.points) <= 3:
            raise ValueError("Cannot delete vertex: Polygon must have at least 3 points")
        
        # Find the vertex closest to the point within tolerance
        closest_index = None
        closest_distance = float('inf')
        
        for i, point in enumerate(self.points):
            distance = point.distance_to(point)
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
        Simplify the polygon by removing redundant points.
        
        This method removes points that are:
        1. Coincident with adjacent points (within tolerance)
        2. Redundant collinear points (within tolerance)
        
        Args:
            tolerance: Distance and angle tolerance for simplification
            
        Returns:
            Number of points removed during simplification
        """
        if len(self.points) <= 3:
            return 0  # Cannot simplify polygons with 3 or fewer points
        
        original_count = len(self.points)
        i = 0
        
        while i < len(self.points):
            current = self.points[i]
            next_vertex = self.points[(i + 1) % len(self.points)]
            
            # Check if current and next points are coincident
            if current.distance_to(next_vertex) <= tolerance:
                # Remove the next vertex (keep the current one)
                del self.points[(i + 1) % len(self.points)]
                continue
            
            # Check if we have enough points to check collinearity
            if len(self.points) > 3:
                prev_vertex = self.points[(i - 1) % len(self.points)]
                
                # Check if current vertex is collinear with adjacent points
                if self._is_collinear(prev_vertex, current, next_vertex, tolerance):
                    # Remove the current vertex
                    del self.points[i]
                    continue
            
            i += 1
            
            # Prevent infinite loop if we've gone through all points
            if i >= len(self.points):
                break
        
        return original_count - len(self.points)

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
        return p1.is_collinear_to([p2, p3], tolerance)

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get the bounds of the polygon as (min_x, min_y, max_x, max_y)."""
        if not self.points:
            return (0.0, 0.0, 0.0, 0.0)
        xs = [p.x for p in self.points]
        ys = [p.y for p in self.points]
        return (min(xs), min(ys), max(xs), max(ys))

    def minkowski_sum(self, other: 'Polygon') -> List['Polygon']:
        """
        Compute the Minkowski sum of this polygon with another polygon.
        Returns a list of resulting polygons (may be multiple if the result is disjoint).
        Uses pyclipper for robust computation.
        """
        try:
            import pyclipper
        except ImportError:
            raise ImportError("pyclipper is required for Minkowski operations")
        # Convert polygons to pyclipper format
        subj = [[int(p.x * 1e6), int(p.y * 1e6)] for p in self.points]
        clip = [[int(p.x * 1e6), int(p.y * 1e6)] for p in other.points]
        # pyclipper expects lists of polygons
        result_paths = pyclipper.MinkowskiSum2(subj, clip, True)  # type: ignore
        # Convert back to Polygon objects
        result = []
        for path in result_paths:
            pts = [Point2D(x / 1e6, y / 1e6) for x, y in path]
            if len(pts) >= 3:
                result.append(Polygon(pts))
        return result

    def minkowski_diff(self, other: 'Polygon') -> List['Polygon']:
        """
        Compute the Minkowski difference (erosion) of this polygon with another polygon.
        Returns a list of resulting polygons (may be multiple if the result is disjoint).
        Uses pyclipper for robust computation.
        """
        try:
            import pyclipper
        except ImportError:
            raise ImportError("pyclipper is required for Minkowski operations")
        subj = [[int(p.x * 1e6), int(p.y * 1e6)] for p in self.points]
        clip = [[int(p.x * 1e6), int(p.y * 1e6)] for p in other.points]
        result_paths = pyclipper.MinkowskiDiff(subj, clip, True)  # type: ignore
        result = []
        for path in result_paths:
            pts = [Point2D(x / 1e6, y / 1e6) for x, y in path]
            if len(pts) >= 3:
                result.append(Polygon(pts))
        return result
