"""
Bezier curve utility functions and classes for BelfryCAD.

This module provides comprehensive Bezier curve operations including:
- BezierPath class for object-oriented curve manipulation
- Cubic and quadratic Bezier curve operations
- Curve splitting, merging, and simplification
- Arc to Bezier conversion
- Point projection and distance calculations
- Curve breaking and nearest point finding

Translated from bezutils.tcl
"""

import math
from typing import List, Tuple, Optional, Iterator
from dataclasses import dataclass
from .geometry import geometry_points_are_collinear


# Constants
PI = math.pi
EPSILON = 1e-10


@dataclass
class BezierSegment:
    """Represents a single cubic Bezier curve segment."""
    x0: float
    y0: float
    x1: float
    y1: float
    x2: float
    y2: float
    x3: float
    y3: float

    def to_coords(self) -> List[float]:
        """Convert to flat coordinate list."""
        return [self.x0, self.y0, self.x1, self.y1, self.x2, self.y2, self.x3, self.y3]

    @classmethod
    def from_coords(cls, coords: List[float]) -> 'BezierSegment':
        """Create from flat coordinate list."""
        if len(coords) < 8:
            raise ValueError("Need at least 8 coordinates for cubic Bezier segment")
        return cls(*coords[:8])

    def start_point(self) -> Tuple[float, float]:
        """Get the start point of the segment."""
        return (self.x0, self.y0)

    def end_point(self) -> Tuple[float, float]:
        """Get the end point of the segment."""
        return (self.x3, self.y3)

    def control_points(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Get the control points."""
        return ((self.x1, self.y1), (self.x2, self.y2))


class BezierPath:
    """
    A class representing a path composed of cubic Bezier curve segments.

    This class provides an object-oriented interface for manipulating
    Bezier curves with methods for splitting, merging, simplification,
    and geometric operations.
    """

    def __init__(self, coords: Optional[List[float]] = None):
        """
        Initialize a BezierPath.

        Args:
            coords: Flat list of coordinates [x0, y0, x1, y1, x2, y2, x3, y3, ...]
                   where each segment is defined by 8 coordinates (start point + 3 control points)
        """
        self._coords: List[float] = coords[:] if coords else []
        self._validate_coords()

    def _validate_coords(self) -> None:
        """Validate that coordinates form valid Bezier segments."""
        if len(self._coords) > 0 and (len(self._coords) - 2) % 6 != 0:
            raise ValueError("Invalid coordinate count for Bezier path")

    @property
    def coords(self) -> List[float]:
        """Get a copy of the coordinate list."""
        return self._coords[:]

    @coords.setter
    def coords(self, value: List[float]) -> None:
        """Set the coordinate list."""
        self._coords = value[:]
        self._validate_coords()

    def __len__(self) -> int:
        """Return the number of segments in the path."""
        return max(0, (len(self._coords) - 2) // 6)

    def __iter__(self) -> Iterator[BezierSegment]:
        """Iterate over segments in the path."""
        if len(self._coords) < 8:
            return iter([])

        x0, y0 = self._coords[0], self._coords[1]
        for i in range(2, len(self._coords), 6):
            if i + 5 >= len(self._coords):
                break
            x1, y1, x2, y2, x3, y3 = self._coords[i:i+6]
            yield BezierSegment(x0, y0, x1, y1, x2, y2, x3, y3)
            x0, y0 = x3, y3

    def __getitem__(self, index: int) -> BezierSegment:
        """Get a specific segment by index."""
        segments = list(self)
        return segments[index]

    def is_empty(self) -> bool:
        """Check if the path is empty."""
        return len(self._coords) < 8

    def start_point(self) -> Optional[Tuple[float, float]]:
        """Get the start point of the path."""
        if len(self._coords) < 2:
            return None
        return (self._coords[0], self._coords[1])

    def end_point(self) -> Optional[Tuple[float, float]]:
        """Get the end point of the path."""
        if len(self._coords) < 8:
            return None
        return (self._coords[-2], self._coords[-1])

    def append_segment(self, segment: BezierSegment) -> None:
        """Append a Bezier segment to the path."""
        if self.is_empty():
            self._coords.extend(segment.to_coords())
        else:
            # Skip the start point as it should connect to the end of the current path
            self._coords.extend(segment.to_coords()[2:])

    def length(self) -> float:
        """Calculate the approximate length of the entire path."""
        if len(self._coords) < 8:
            return 0.0

        length = 0.0
        x0, y0 = self._coords[0], self._coords[1]

        for i in range(2, len(self._coords), 6):
            if i + 5 >= len(self._coords):
                break
            x1, y1, x2, y2, x3, y3 = self._coords[i:i+6]
            seglen = self._bezier_segment_length(x0, y0, x1, y1, x2, y2, x3, y3)
            length += seglen
            x0, y0 = x3, y3

        return length

    def _bezier_segment_length(self, x0: float, y0: float, x1: float, y1: float,
                              x2: float, y2: float, x3: float, y3: float) -> float:
        """Calculate approximate length of a cubic Bezier segment."""
        inc = 1.0 / 20.0

        # Convert to standard form: P(t) = at^3 + bt^2 + ct + d
        xc = 3.0 * (x1 - x0)
        xb = 3.0 * (x2 - x1) - xc
        xa = x3 - x0 - xc - xb

        yc = 3.0 * (y1 - y0)
        yb = 3.0 * (y2 - y1) - yc
        ya = y3 - y0 - yc - yb

        length = 0.0
        t = 0.0
        ox = ((xa * t + xb) * t + xc) * t + x0
        oy = ((ya * t + yb) * t + yc) * t + y0

        t = inc
        while t <= 1.0:
            mx = ((xa * t + xb) * t + xc) * t + x0
            my = ((ya * t + yb) * t + yc) * t + y0
            length += math.hypot(my - oy, mx - ox)
            ox, oy = mx, my
            t += inc

        return length

    def point_at_parameter(self, segment_index: int, t: float) -> Optional[Tuple[float, float]]:
        """Get a point at parameter t on a specific segment."""
        try:
            segment = self[segment_index]
            return self._bezier_segment_point(
                t, segment.x0, segment.y0, segment.x1, segment.y1,
                segment.x2, segment.y2, segment.x3, segment.y3
            )
        except (IndexError, ValueError):
            return None

    def _bezier_segment_point(self, t: float, x0: float, y0: float,
                             x1: float, y1: float, x2: float, y2: float,
                             x3: float, y3: float) -> Tuple[float, float]:
        """Calculate a point on a cubic Bezier segment at parameter t."""
        # Convert to standard form
        xc = 3.0 * (x1 - x0)
        xb = 3.0 * (x2 - x1) - xc
        xa = x3 - x0 - xc - xb

        yc = 3.0 * (y1 - y0)
        yb = 3.0 * (y2 - y1) - yc
        ya = y3 - y0 - yc - yb

        x = ((xa * t + xb) * t + xc) * t + x0
        y = ((ya * t + yb) * t + yc) * t + y0

        return (x, y)

    def translate(self, dx: float, dy: float) -> 'BezierPath':
        """Translate the path by the given offset."""
        new_coords = []
        for i in range(0, len(self._coords), 2):
            new_coords.extend([self._coords[i] + dx, self._coords[i+1] + dy])
        return BezierPath(new_coords)

    def scale(self, sx: float, sy: float, cx: float = 0, cy: float = 0) -> 'BezierPath':
        """Scale the path around a center point."""
        new_coords = []
        for i in range(0, len(self._coords), 2):
            x = (self._coords[i] - cx) * sx + cx
            y = (self._coords[i+1] - cy) * sy + cy
            new_coords.extend([x, y])
        return BezierPath(new_coords)

    def rotate(self, angle: float, cx: float = 0, cy: float = 0) -> 'BezierPath':
        """Rotate the path around a center point."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        new_coords = []

        for i in range(0, len(self._coords), 2):
            x = self._coords[i] - cx
            y = self._coords[i+1] - cy
            new_x = x * cos_a - y * sin_a + cx
            new_y = x * sin_a + y * cos_a + cy
            new_coords.extend([new_x, new_y])

        return BezierPath(new_coords)

    def bounds(self) -> Optional[Tuple[float, float, float, float]]:
        """Get the bounding box of the path (minx, miny, maxx, maxy)."""
        if self.is_empty():
            return None

        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')

        for i in range(0, len(self._coords), 2):
            x, y = self._coords[i], self._coords[i+1]
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)

        return (min_x, min_y, max_x, max_y)

    def copy(self) -> 'BezierPath':
        """Create a copy of this path."""
        return BezierPath(self._coords)

    def reverse(self) -> 'BezierPath':
        """Reverse the direction of the path."""
        if self.is_empty():
            return BezierPath()

        # Reverse the order of segments and flip control points
        reversed_coords = []
        segments = list(self)

        if not segments:
            return BezierPath()

        # Start with the end point of the last segment
        last_seg = segments[-1]
        reversed_coords.extend([last_seg.x3, last_seg.y3])

        # Process segments in reverse order
        for segment in reversed(segments):
            # Reverse control points: (x0,y0,x1,y1,x2,y2,x3,y3) -> (x3,y3,x2,y2,x1,y1,x0,y0)
            reversed_coords.extend([segment.x2, segment.y2, segment.x1, segment.y1, segment.x0, segment.y0])

        return BezierPath(reversed_coords)

    @classmethod
    def from_line_segments(cls, points: List[Tuple[float, float]]) -> 'BezierPath':
        """Create a Bezier path from line segments."""
        if len(points) < 2:
            return cls()

        out = []
        onethird = 1.0 / 3.0
        twothirds = 2.0 / 3.0

        x0, y0 = points[0]
        out.extend([x0, y0])

        for i in range(1, len(points)):
            x3, y3 = points[i]
            dx = x3 - x0
            dy = y3 - y0
            x1 = x0 + dx * onethird
            y1 = y0 + dy * onethird
            x2 = x0 + dx * twothirds
            y2 = y0 + dy * twothirds
            out.extend([x1, y1, x2, y2, x3, y3])
            x0, y0 = x3, y3

        return cls(out)

    @classmethod
    def from_arc(cls, cx: float, cy: float, radiusx: float, radiusy: float,
                start: float, extent: float) -> 'BezierPath':
        """Create a Bezier path approximating an elliptical arc."""
        coords = []
        cls._append_bezier_arc(coords, cx, cy, radiusx, radiusy, start, extent)
        return cls(coords)

    @staticmethod
    def _append_bezier_arc(coords: List[float], cx: float, cy: float,
                          radiusx: float, radiusy: float,
                          start: float, extent: float) -> None:
        """Append a Bezier approximation of an elliptical arc to coordinates list."""
        arcsliceangle = 15.0

        start = float(start)
        extent = float(extent)

        if extent == 0.0:
            return

        arcslice = extent / math.ceil(abs(extent / arcsliceangle))
        arcrdn = 0.5 * arcslice * PI / 180.0

        # Formula for calculating the "magic number" bezier distance
        # for approximating an elliptical curve closely:
        bezmagic = abs((4.0/3.0) * ((1.0 - math.cos(arcrdn)) / math.sin(arcrdn)))

        tmpcoords = []
        done = False
        i = start

        while not done:
            radians = i * PI / 180.0
            tx = math.cos(radians)
            ty = math.sin(radians)
            tx1 = math.cos(radians - 1e-4)
            ty1 = math.sin(radians - 1e-4)
            tx2 = math.cos(radians + 1e-4)
            ty2 = math.sin(radians + 1e-4)
            curang = math.atan2(ty2 - ty1, tx2 - tx1)

            prad = bezmagic if extent >= 0.0 else -bezmagic

            if i == start:
                coordlen = len(coords)
                if coordlen > 0 and coordlen % 6 == 2:
                    tmpcoords.extend([tx, ty, tx, ty])
            else:
                cpx1 = tx - prad * math.cos(curang)
                cpy1 = ty - prad * math.sin(curang)
                tmpcoords.extend([cpx1, cpy1])

            tmpcoords.extend([tx, ty])

            if abs(i - (start + extent)) < 1e-6:
                done = True
            else:
                cpx2 = tx + prad * math.cos(curang)
                cpy2 = ty + prad * math.sin(curang)
                tmpcoords.extend([cpx2, cpy2])

            i += arcslice

        # Apply transformation matrix (translate and scale)
        for i in range(0, len(tmpcoords), 2):
            x = tmpcoords[i] * radiusx + cx
            y = tmpcoords[i + 1] * radiusy + cy
            coords.extend([x, y])

    def add_line_to(self, x: float, y: float) -> None:
        """Add a straight line segment to the path."""
        if self.is_empty():
            # Start new path
            self._coords = [0.0, 0.0]

        current_end = self.end_point() or (0.0, 0.0)
        x0, y0 = current_end

        # Create a linear Bezier segment (control points on the line)
        dx = x - x0
        dy = y - y0
        x1 = x0 + dx / 3.0
        y1 = y0 + dy / 3.0
        x2 = x0 + 2.0 * dx / 3.0
        y2 = y0 + 2.0 * dy / 3.0

        self._coords.extend([x1, y1, x2, y2, x, y])

    def add_curve_to(self, x1: float, y1: float, x2: float, y2: float,
                     x3: float, y3: float) -> None:
        """Add a cubic Bezier curve segment to the path."""
        if self.is_empty():
            # Start new path at origin if empty
            self._coords = [0.0, 0.0]

        self._coords.extend([x1, y1, x2, y2, x3, y3])

    def close_path(self) -> None:
        """Close the path by adding a line back to the start point."""
        start = self.start_point()
        end = self.end_point()

        if start and end and (abs(start[0] - end[0]) > 1e-6 or abs(start[1] - end[1]) > 1e-6):
            self.add_line_to(start[0], start[1])

    @property
    def is_closed(self) -> bool:
        """Check if the path is closed (start and end points are the same)."""
        start = self.start_point()
        end = self.end_point()

        if not start or not end:
            return False

        return abs(start[0] - end[0]) < 1e-6 and abs(start[1] - end[1]) < 1e-6

    def to_line_segments(self, tolerance: float = 5e-4) -> List[Tuple[float, float]]:
        """Convert the Bezier path to line segments."""
        coords = []
        bezpath = self._split_for_lines(self._coords, tolerance)
        if len(bezpath) < 2:
            return []

        x0, y0 = bezpath[0], bezpath[1]
        coords.append((x0, y0))

        for i in range(2, len(bezpath), 6):
            if i + 5 >= len(bezpath):
                break
            x1, y1, x2, y2, x3, y3 = bezpath[i:i+6]
            coords.append((x3, y3))

        return coords

    def _split_for_lines(self, coords: List[float], tolerance: float) -> List[float]:
        """Split Bezier curves recursively for better line approximation."""
        if len(coords) < 8:
            return coords[:]

        outcoords = []
        x0, y0 = coords[0], coords[1]
        outcoords.extend([x0, y0])

        for i in range(2, len(coords), 6):
            if i + 5 >= len(coords):
                break
            x1, y1, x2, y2, x3, y3 = coords[i:i+6]

            # Check if segment is already linear enough
            if (geometry_points_are_collinear(x0, y0, x1, y1, x2, y2, tolerance) and
                    geometry_points_are_collinear(x1, y1, x2, y2, x3, y3, tolerance)):
                # Co-linear, don't split
                outcoords.extend([x1, y1, x2, y2, x3, y3])
            else:
                # Split at midpoint
                mx01 = (x0 + x1) / 2.0
                my01 = (y0 + y1) / 2.0
                mx12 = (x1 + x2) / 2.0
                my12 = (y1 + y2) / 2.0
                mx23 = (x2 + x3) / 2.0
                my23 = (y2 + y3) / 2.0
                mx012 = (mx01 + mx12) / 2.0
                my012 = (my01 + my12) / 2.0
                mx123 = (mx12 + mx23) / 2.0
                my123 = (my12 + my23) / 2.0
                mx0123 = (mx012 + mx123) / 2.0
                my0123 = (my012 + my123) / 2.0

                # Recursively split both halves
                bezsplit1 = self._split_for_lines([x0, y0, mx01, my01, mx012,
                                                  my012, mx0123, my0123], tolerance)
                bezsplit2 = self._split_for_lines([mx0123, my0123, mx123, my123,
                                                  mx23, my23, x3, y3], tolerance)

                outcoords.extend(bezsplit1[2:])
                outcoords.extend(bezsplit2[2:])

            x0, y0 = x3, y3

        return outcoords

    def __str__(self) -> str:
        """String representation of the path."""
        return f"BezierPath({len(self)} segments, {len(self._coords)} coords)"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"BezierPath(coords={self._coords})"


# Legacy utility functions for backward compatibility

def bezutil_bezier_length(coords: List[float]) -> float:
    """Calculate approximate length of a cubic Bezier curve."""
    path = BezierPath(coords)
    return path.length()


def bezutil_bezier_segment_point(t: float, x0: float, y0: float,
                                 x1: float, y1: float, x2: float, y2: float,
                                 x3: float, y3: float) -> Tuple[float, float]:
    """Calculate a point on a cubic Bezier segment at parameter t."""
    path = BezierPath()
    return path._bezier_segment_point(t, x0, y0, x1, y1, x2, y2, x3, y3)


def bezutil_append_line_from_bezier(coords: List[float], bezcoords: List[float]) -> None:
    """Convert a Bezier curve to line segments and append to coords."""
    path = BezierPath(bezcoords)
    line_segments = path.to_line_segments()
    for x, y in line_segments:
        coords.extend([x, y])


def bezutil_bezier_from_line(linecoords: List[float]) -> List[float]:
    """Convert line segments to Bezier curves."""
    if len(linecoords) < 4:
        return linecoords[:]

    points = [(linecoords[i], linecoords[i+1]) for i in range(0, len(linecoords), 2)]
    path = BezierPath.from_line_segments(points)
    return path.coords


def bezutil_append_bezier_arc(coords: List[float], cx: float, cy: float,
                              radiusx: float, radiusy: float,
                              start: float, extent: float) -> None:
    """Append a Bezier approximation of an elliptical arc to coordinates list."""
    BezierPath._append_bezier_arc(coords, cx, cy, radiusx, radiusy, start, extent)
