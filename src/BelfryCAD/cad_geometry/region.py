"""
Region Class for CAD Geometry

This module provides the Region class for representing complex 2D regions
with multiple polygons and holes.
"""

from typing import List, Optional, Tuple, Union, Iterator, TYPE_CHECKING
import numpy as np
import math
from .shapes import Shape2D, ShapeType
from .point import Point2D
from .line import Line2D
from .transform import Transform2D
from .polygon import Polygon

if TYPE_CHECKING:
    from .polyline import PolyLine2D
    from .bezier import BezierPath

EPSILON = 1e-10

class Region(Shape2D):
    """
    A region consisting of multiple polygons representing perimeters and holes.
    This class manages complex geometric shapes with multiple boundaries.
    """

    clipper_scale_factor = 10000

    def __init__(self, perimeters: Optional[List[Polygon]] = None, holes: Optional[List[Polygon]] = None):
        """
        Initialize a region with perimeters and holes.
        
        Args:
            perimeters: List of polygons representing the outer boundaries
            holes: List of polygons representing holes within the perimeters
        """
        self.perimeters = perimeters or []
        self.holes = holes or []
        
        # Validate that holes are contained within perimeters
        self._validate_holes()

    def decompose(self, into: List[ShapeType] = [], tolerance: float = 0.001) -> List['Shape2D']:
        if ShapeType.REGION in into:
            return [self]
        polys = [p for p in self.perimeters] + [h for h in self.holes]
        if ShapeType.POLYGON in into:
            return [p for p in polys]
        if ShapeType.POLYLINE in into:
            return [PolyLine2D(p.points) for p in polys]
        if ShapeType.LINE in into:
            return [p2 for p in polys for p2 in p.decompose([ShapeType.LINE])]
        raise ValueError(f"Cannot decompose region into any of {into}")

    def _validate_holes(self):
        """Validate that all holes are contained within at least one perimeter."""
        for hole in self.holes:
            hole_centroid = hole.centroid
            contained = False
            for perimeter in self.perimeters:
                if perimeter.contains_point(hole_centroid):
                    contained = True
                    break
            if not contained:
                # Only warn, don't raise error - holes might be valid in some cases
                print(f"Warning: Hole {hole} may not be contained within any perimeter")

    def __repr__(self) -> str:
        return f"Region({len(self.perimeters)} perimeters, {len(self.holes)} holes)"

    def __str__(self) -> str:
        return f"Region with {len(self.perimeters)} perimeters and {len(self.holes)} holes"

    def __len__(self) -> int:
        return len(self.perimeters) + len(self.holes)

    def __iter__(self) -> Iterator[Polygon]:
        """Iterate over all polygons (perimeters and holes)."""
        yield from self.perimeters
        yield from self.holes

    def __getitem__(self, index: int) -> Polygon:
        """Get polygon by index (perimeters first, then holes)."""
        if index < len(self.perimeters):
            return self.perimeters[index]
        else:
            return self.holes[index - len(self.perimeters)]

    @property
    def area(self) -> float:
        """Calculate total area of the region (perimeter areas minus hole areas)."""
        total_area = sum(poly.area for poly in self.perimeters)
        hole_area = sum(hole.area for hole in self.holes)
        return total_area - hole_area

    @property
    def perimeter(self) -> float:
        """Calculate total perimeter length."""
        perimeter_length = sum(poly.perimeter for poly in self.perimeters)
        hole_perimeter = sum(hole.perimeter for hole in self.holes)
        return perimeter_length + hole_perimeter

    @property
    def bounds(self) -> Tuple[Point2D, Point2D]:
        """Get bounding box of the entire region."""
        if not self.perimeters:
            return Point2D(0, 0), Point2D(0, 0)

        # Get bounds from all perimeters
        all_points = []
        for poly in self.perimeters:
            min_pt, max_pt = poly.bounds
            all_points.extend([min_pt, max_pt])

        # Find overall min and max
        min_x = min(pt.x for pt in all_points)
        max_x = max(pt.x for pt in all_points)
        min_y = min(pt.y for pt in all_points)
        max_y = max(pt.y for pt in all_points)

        return Point2D(min_x, min_y), Point2D(max_x, max_y)

    def contains_point(self, point: Point2D, tolerance: float = EPSILON) -> bool:
        """
        Check if point is inside the region.
        """
        # Count how many perimeters the point is inside
        inside_count = 0
        for perimeter in self.perimeters:
            if perimeter.contains_point(point, tolerance):
                inside_count += 1

        # Subtract how many holes the point is inside
        for hole in self.holes:
            if hole.contains_point(point, tolerance):
                inside_count -= 1

        return inside_count > 0

    def add_perimeter(self, polygon: Polygon):
        """Add a perimeter polygon to the region."""
        self.perimeters.append(polygon)
        self._validate_holes()

    def add_hole(self, polygon: Polygon):
        """Add a hole polygon to the region."""
        self.holes.append(polygon)
        self._validate_holes()

    def remove_perimeter(self, index: int):
        """Remove a perimeter polygon by index."""
        if 0 <= index < len(self.perimeters):
            del self.perimeters[index]

    def remove_hole(self, index: int):
        """Remove a hole polygon by index."""
        if 0 <= index < len(self.holes):
            del self.holes[index]

    def translate(self, vector) -> 'Region':
        """Make a new region, translated by vector."""
        return Region([poly.translate(vector) for poly in self.perimeters],
                      [hole.translate(vector) for hole in self.holes])

    def rotate(self, angle: float, center = None) -> 'Region':
        """Rotate all polygons in the region around a center point."""
        return Region([poly.rotate(angle, center) for poly in self.perimeters],
                      [hole.rotate(angle, center) for hole in self.holes])

    def scale(self, scale, center = None) -> 'Region':
        """Make a new region, scaled around a center point."""
        return Region([poly.scale(scale, center) for poly in self.perimeters],
                      [hole.scale(scale, center) for hole in self.holes])

    def transform(self, transform: Transform2D) -> 'Region':
        """Make a new region, transformed using a transformation matrix."""
        return Region([poly.transform(transform) for poly in self.perimeters],
                      [hole.transform(transform) for hole in self.holes])

    def _to_clipper_paths(self) -> Tuple[List[List[List[int]]], List[List[List[int]]]]:
        """Convert region to PyClipper format."""
        try:
            import pyclipper
        except ImportError:
            raise ImportError("PyClipper is required for boolean operations")

        # Convert perimeters to PyClipper format
        perimeter_paths = []
        for poly in self.perimeters:
            path = poly._to_clipper_path()
            perimeter_paths.append(path)

        # Convert holes to PyClipper format
        hole_paths = []
        for hole in self.holes:
            path = hole._to_clipper_path()
            hole_paths.append(path)

        return perimeter_paths, hole_paths

    @classmethod
    def _from_clipper_result(cls, result_paths: List[List[List[int]]]) -> 'Region':
        """Create Region from PyClipper result paths."""
        try:
            import pyclipper
        except ImportError:
            raise ImportError("PyClipper is required for boolean operations")

        perimeters = []
        holes = []

        for path in result_paths:
            if len(path) >= 3:  # Ensure valid polygon
                poly = Polygon._from_clipper_path(path)
                # Determine if it's a perimeter or hole based on orientation
                if poly.is_clockwise():
                    holes.append(poly)
                else:
                    perimeters.append(poly)

        return cls(perimeters, holes)

    def union(self, other: 'Region') -> 'Region':
        """
        Perform boolean union operation with another region.
        Returns a new Region representing the union.
        """
        try:
            import pyclipper
        except ImportError:
            raise ImportError("PyClipper is required for boolean operations")

        # Convert regions to PyClipper format
        perim1, holes1 = self._to_clipper_paths()
        perim2, holes2 = other._to_clipper_paths()

        # Create PyClipper object
        pc = pyclipper.Pyclipper() # type: ignore

        # Add all perimeters as subject paths
        for path in perim1:
            pc.AddPath(path, pyclipper.PT_SUBJECT, True) # type: ignore
        for path in perim2:
            pc.AddPath(path, pyclipper.PT_SUBJECT, True) # type: ignore

        # Add all holes as clip paths (they will be subtracted)
        for path in holes1:
            pc.AddPath(path, pyclipper.PT_CLIP, True) # type: ignore
        for path in holes2:
            pc.AddPath(path, pyclipper.PT_CLIP, True) # type: ignore

        # Execute union operation
        result_paths = pc.Execute(pyclipper.CT_UNION, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO) # type: ignore

        return self._from_clipper_result(result_paths)

    def difference(self, other: 'Region') -> 'Region':
        """
        Perform boolean difference operation (self - other).
        Returns a new Region representing the difference.
        """
        try:
            import pyclipper
        except ImportError:
            raise ImportError("PyClipper is required for boolean operations")

        # Convert regions to PyClipper format
        perim1, holes1 = self._to_clipper_paths()
        perim2, holes2 = other._to_clipper_paths()

        # Create PyClipper object
        pc = pyclipper.Pyclipper() # type: ignore

        # Add self perimeters as subject paths
        for path in perim1:
            pc.AddPath(path, pyclipper.PT_SUBJECT, True) # type: ignore

        # Add other perimeters and holes as clip paths
        for path in perim2:
            pc.AddPath(path, pyclipper.PT_CLIP, True) # type: ignore
        for path in holes2:
            pc.AddPath(path, pyclipper.PT_CLIP, True) # type: ignore

        # Add self holes as additional subject paths (they will be preserved)
        for path in holes1:
            pc.AddPath(path, pyclipper.PT_SUBJECT, True) # type: ignore

        # Execute difference operation
        result_paths = pc.Execute(pyclipper.CT_DIFFERENCE, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO) # type: ignore

        return self._from_clipper_result(result_paths)

    def intersection(self, other: 'Region') -> 'Region':
        """
        Perform boolean intersection operation with another region.
        Returns a new Region representing the intersection.
        """
        try:
            import pyclipper
        except ImportError:
            raise ImportError("PyClipper is required for boolean operations")

        # Convert regions to PyClipper format
        perim1, holes1 = self._to_clipper_paths()
        perim2, holes2 = other._to_clipper_paths()

        # Create PyClipper object
        pc = pyclipper.Pyclipper() # type: ignore

        # Add all perimeters as subject paths
        for path in perim1:
            pc.AddPath(path, pyclipper.PT_SUBJECT, True) # type: ignore
        for path in perim2:
            pc.AddPath(path, pyclipper.PT_SUBJECT, True) # type: ignore

        # Add all holes as clip paths
        for path in holes1:
            pc.AddPath(path, pyclipper.PT_CLIP, True) # type: ignore
        for path in holes2:
            pc.AddPath(path, pyclipper.PT_CLIP, True) # type: ignore

        # Execute intersection operation
        result_paths = pc.Execute(pyclipper.CT_INTERSECTION, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO) # type: ignore

        return self._from_clipper_result(result_paths)

    def xor(self, other: 'Region') -> 'Region':
        """
        Perform boolean XOR operation with another region.
        Returns a new Region representing the XOR result.
        """
        try:
            import pyclipper
        except ImportError:
            raise ImportError("PyClipper is required for boolean operations")

        # Convert regions to PyClipper format
        perim1, holes1 = self._to_clipper_paths()
        perim2, holes2 = other._to_clipper_paths()

        # Create PyClipper object
        pc = pyclipper.Pyclipper() # type: ignore

        # Add all perimeters as subject paths
        for path in perim1:
            pc.AddPath(path, pyclipper.PT_SUBJECT, True) # type: ignore
        for path in perim2:
            pc.AddPath(path, pyclipper.PT_SUBJECT, True) # type: ignore

        # Add all holes as clip paths
        for path in holes1:
            pc.AddPath(path, pyclipper.PT_CLIP, True) # type: ignore
        for path in holes2:
            pc.AddPath(path, pyclipper.PT_CLIP, True) # type: ignore

        # Execute XOR operation
        result_paths = pc.Execute(pyclipper.CT_XOR, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO) # type: ignore

        return self._from_clipper_result(result_paths)

    def offset(self, distance: float, join_type: str = 'round', end_type: str = 'closed_polygon') -> 'Region':
        """
        Create an offset (inset or outset) of the region.
        
        Args:
            distance: Positive for outset, negative for inset
            join_type: 'round', 'square', or 'miter'
            end_type: 'closed_polygon', 'closed_line', or 'open_butt'
        
        Returns:
            New Region with offset polygons
        """
        try:
            import pyclipper
        except ImportError:
            raise ImportError("PyClipper is required for offset operations")

        # Convert region to PyClipper format
        perim_paths, hole_paths = self._to_clipper_paths()

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

        # Add all paths and execute offset
        for path in perim_paths:
            po.AddPath(path, join_type_enum, end_type_enum)
        for path in hole_paths:
            po.AddPath(path, join_type_enum, end_type_enum)

        result_paths = po.Execute(distance * Region.clipper_scale_factor)  # Scale distance for integer precision

        return self._from_clipper_result(result_paths)

    @classmethod
    def from_polygons(cls, polygons: List[Polygon]) -> 'Region':
        """
        Create a region from a list of polygons.
        Polygons are automatically classified as perimeters or holes based on orientation.
        """
        perimeters = []
        holes = []

        for poly in polygons:
            if poly.is_clockwise():
                holes.append(poly)
            else:
                perimeters.append(poly)

        return cls(perimeters, holes)


    @classmethod
    def rectangle(cls, center: Point2D, width: float, height: float) -> 'Region':
        """Create a rectangular region."""
        rect = Polygon.rectangle(center, width, height)
        return cls([rect], [])

    @classmethod
    def circle(cls, center: Point2D, radius: float) -> 'Region':
        """Create a circular region."""
        circle_poly = Polygon.regular_polygon(center, radius, 64)  # 64-sided approximation
        return cls([circle_poly], [])

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get the bounds of the region as (min_x, min_y, max_x, max_y)."""
        min_pt, max_pt = self.bounds
        return (min_pt.x, min_pt.y, max_pt.x, max_pt.y)

    def minkowski_sum(self, other: 'Polygon') -> 'Region':
        """
        Compute the Minkowski sum of this region with another polygon.
        Applies the sum to all perimeters and holes, and returns a new Region.
        """
        perim_results = []
        for perim in self.perimeters:
            perim_results.extend(perim.minkowski_sum(other))
        hole_results = []
        for hole in self.holes:
            hole_results.extend(hole.minkowski_sum(other))
        return Region(perim_results, hole_results)

    def minkowski_diff(self, other: 'Polygon') -> 'Region':
        """
        Compute the Minkowski difference (erosion) of this region with a polygon.
        Applies the difference to all perimeters and holes, and returns a new Region.
        """
        perim_results = []
        for perim in self.perimeters:
            perim_results.extend(perim.minkowski_diff(other))
        hole_results = []
        for hole in self.holes:
            hole_results.extend(hole.minkowski_diff(other))
        return Region(perim_results, hole_results)


# Optimized utility functions using numpy and scipy
