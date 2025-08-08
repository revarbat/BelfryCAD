"""
BezierPath Class for CAD Geometry

This module provides the BezierPath class for representing 2D Bezier curves
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
    from .polyline import PolyLine2D
    from .region import Region

class BezierPath(Shape2D):
    """
    A multi-segment cubic Bezier path defined by a list of control points.
    
    Each Bezier segment requires 3 points (start, control1, control2) plus an end point.
    If the number of points doesn't match len(points)%3==1, the path is padded with
    copies of the last point to form complete segments.
    """
    
    def __init__(self, points: Optional[List[Point2D]] = None):
        """
        Initialize a Bezier path with control points.
        
        Args:
            points: List of Point2D control points. Each segment needs 4 points:
                   start, control1, control2, end. If len(points)%3!=1, the path
                   is padded with copies of the last point.
        """
        self._points = points or []
    
    def __repr__(self) -> str:
        return f"BezierPath({len(self._points)} points, {len(self._get_segments_from_points())} segments)"
    
    def __str__(self) -> str:
        segments = self._get_segments_from_points()
        return f"BezierPath with {len(self._points)} points, {len(segments)} segments"
    
    def decompose(self, into: List[ShapeType] = [], tolerance: float = 0.001) -> List['Shape2D']:
        if ShapeType.BEZIER in into:
            return [self]
        points = self.to_polyline(tolerance=tolerance).points
        if ShapeType.POLYGON in into:
            return [Polygon(points)]
        if ShapeType.REGION in into:
            return [Region(perimeters=[Polygon(self._points)], holes=[])]
        if ShapeType.POLYLINE in into:
            return [PolyLine2D(points)]
        if ShapeType.LINE in into:
            return [
                Line2D(points[i], points[i + 1])
                for i in range(len(points) - 1)
            ]
        raise ValueError(f"Cannot decompose bezier path into any of {into}")
    
    def __len__(self) -> int:
        return len(self._get_segments_from_points())
    
    def __iter__(self):
        """Iterate over segments."""
        return iter(self._get_segments_from_points())
    
    def __getitem__(self, index: int) -> Tuple[Point2D, Point2D, Point2D, Point2D]:
        """Get segment by index."""
        segments = self._get_segments_from_points()
        return segments[index]
    
    def _get_segments_from_points(self) -> List[Tuple[Point2D, Point2D, Point2D, Point2D]]:
        """Convert the points list to Bezier segments, padding with last point if needed."""
        if len(self._points) < 4:
            return []
        
        segments = []
        # Each segment needs 4 points: start, control1, control2, end
        # We need len(points) % 3 == 1 for complete segments
        required_points = len(self._points)
        if required_points % 3 != 1:
            # Pad with copies of the last point
            padding_needed = 3 - (required_points % 3)
            padded_points = self._points + [self._points[-1]] * padding_needed
        else:
            padded_points = self._points
        
        # Create segments from groups of 4 points
        for i in range(0, len(padded_points) - 3, 3):
            start = padded_points[i]
            control1 = padded_points[i + 1]
            control2 = padded_points[i + 2]
            end = padded_points[i + 3]
            segments.append((start, control1, control2, end))
        
        return segments
    
    @property
    def start_point(self) -> Optional[Point2D]:
        """Get the start point of the first segment."""
        segments = self._get_segments_from_points()
        if segments:
            return segments[0][0]
        return None
    
    @property
    def end_point(self) -> Optional[Point2D]:
        """Get the end point of the last segment."""
        segments = self._get_segments_from_points()
        if segments:
            return segments[-1][3]
        return None
    
    @property
    def is_closed(self) -> bool:
        """Check if the path is closed (start and end points are the same)."""
        start_pt = self.start_point
        end_pt = self.end_point
        if start_pt is None or end_pt is None:
            return False
        return start_pt.distance_to(end_pt) < 1e-6
    
    @property
    def points(self) -> List[Point2D]:
        """Get all control points as a list."""
        return self._points.copy()
    
    @points.setter
    def points(self, value: List[Point2D]):
        """Set all control points from a list."""
        self._points = [Point2D(p) for p in value]
    
    def add_point(self, point: Point2D):
        """Add a new control point to the end of the list."""
        self._points.append(Point2D(point))
    
    def insert_point(self, index: int, point: Point2D):
        """Insert a control point at the specified index."""
        self._points.insert(index, Point2D(point))
    
    def remove_point(self, index: int):
        """Remove a control point at the specified index."""
        if 0 <= index < len(self._points):
            del self._points[index]
    
    def get_point(self, index: int) -> Point2D:
        """Get a specific control point by index."""
        if 0 <= index < len(self._points):
            return self._points[index]
        raise IndexError(f"Point index {index} out of range")
    
    def set_point(self, index: int, point: Point2D):
        """Set a specific control point by index."""
        if 0 <= index < len(self._points):
            self._points[index] = Point2D(point)
        else:
            raise IndexError(f"Point index {index} out of range")
    
    def add_segment(self, start: Point2D, control1: Point2D, control2: Point2D, end: Point2D):
        """Add a new segment to the path."""
        # If this is not the first segment, we need to ensure continuity
        if self._points and len(self._points) % 3 == 1:
            # We have complete segments, so we can add the new segment
            self._points.extend([Point2D(control1), Point2D(control2), Point2D(end)])
        else:
            # We need to add all four points
            self._points.extend([Point2D(start), Point2D(control1), Point2D(control2), Point2D(end)])
    
    def insert_segment(self, index: int, start: Point2D, control1: Point2D, control2: Point2D, end: Point2D):
        """Insert a segment at the specified index."""
        segments = self._get_segments_from_points()
        if index > len(segments):
            raise IndexError(f"Segment index {index} out of range")
        
        # Convert segments back to points for insertion
        all_points = []
        for i, (s, c1, c2, e) in enumerate(segments):
            if i == index:
                # Insert the new segment
                all_points.extend([Point2D(start), Point2D(control1), Point2D(control2), Point2D(end)])
            all_points.extend([s, c1, c2, e])
        
        if index == len(segments):
            # Insert at the end
            all_points.extend([Point2D(start), Point2D(control1), Point2D(control2), Point2D(end)])
        
        self._points = all_points
    
    def remove_segment(self, index: int):
        """Remove a segment at the specified index."""
        segments = self._get_segments_from_points()
        if 0 <= index < len(segments):
            # Rebuild points list without the specified segment
            all_points = []
            for i, (start, control1, control2, end) in enumerate(segments):
                if i != index:
                    all_points.extend([start, control1, control2, end])
            self._points = all_points
    
    def point_at_parameter(self, t: float) -> Optional[Point2D]:
        """
        Get the point at parameter t along the entire path.
        
        Args:
            t: Parameter value between 0 and 1
            
        Returns:
            Point at parameter t, or None if no segments
        """
        segments = self._get_segments_from_points()
        if not segments:
            return None
        
        # Handle edge cases
        if t <= 0:
            start, control1, control2, end = segments[0]
            return start
        elif t >= 1:
            start, control1, control2, end = segments[-1]
            return end
        
        # Normalize t to the number of segments
        segment_count = len(segments)
        segment_index = int(t * segment_count)
        segment_t = (t * segment_count) - segment_index
        
        # Clamp segment_index to valid range
        segment_index = max(0, min(segment_index, segment_count - 1))
        
        # Get the segment
        start, control1, control2, end = segments[segment_index]
        
        # Calculate point on this segment
        return self._cubic_bezier_point(start, control1, control2, end, segment_t)
    
    def _cubic_bezier_point(self, p0: Point2D, p1: Point2D, p2: Point2D, p3: Point2D, t: float) -> Point2D:
        """Calculate point on cubic Bezier curve."""
        # Cubic Bezier formula: B(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
        one_minus_t = 1 - t
        one_minus_t_squared = one_minus_t * one_minus_t
        one_minus_t_cubed = one_minus_t_squared * one_minus_t
        t_squared = t * t
        t_cubed = t_squared * t
        
        return (one_minus_t_cubed * p0 + 
                3 * one_minus_t_squared * t * p1 + 
                3 * one_minus_t * t_squared * p2 + 
                t_cubed * p3)
    
    def tangent_at_parameter(self, t: float) -> Optional[Point2D]:
        """
        Get the tangent vector at parameter t.
        
        Args:
            t: Parameter value between 0 and 1
            
        Returns:
            Tangent vector at parameter t, or None if no segments
        """
        segments = self._get_segments_from_points()
        if not segments:
            return None
        
        # Handle edge cases
        if t <= 0:
            start, control1, control2, end = segments[0]
            return self._cubic_bezier_tangent(start, control1, control2, end, 0)
        elif t >= 1:
            start, control1, control2, end = segments[-1]
            return self._cubic_bezier_tangent(start, control1, control2, end, 1)
        
        # Normalize t to the number of segments
        segment_count = len(segments)
        segment_index = int(t * segment_count)
        segment_t = (t * segment_count) - segment_index
        
        # Clamp segment_index to valid range
        segment_index = max(0, min(segment_index, segment_count - 1))
        
        # Get the segment
        start, control1, control2, end = segments[segment_index]
        
        # Calculate tangent on this segment
        return self._cubic_bezier_tangent(start, control1, control2, end, segment_t)
    
    def _cubic_bezier_tangent(self, p0: Point2D, p1: Point2D, p2: Point2D, p3: Point2D, t: float) -> Point2D:
        """Calculate tangent vector of cubic Bezier curve."""
        # Derivative of cubic Bezier: B'(t) = 3(1-t)²(P₁-P₀) + 6(1-t)t(P₂-P₁) + 3t²(P₃-P₂)
        one_minus_t = 1 - t
        one_minus_t_squared = one_minus_t * one_minus_t
        t_squared = t * t
        
        return (3 * one_minus_t_squared * (p1 - p0) + 
                6 * one_minus_t * t * (p2 - p1) + 
                3 * t_squared * (p3 - p2))
    
    def to_polyline(self, segments_per_curve: int = 16, tolerance: float = 0.001) -> 'PolyLine2D':
        """
        Convert the Bezier path to a polyline using adaptive subdivision.
        
        Args:
            segments_per_curve: Number of line segments to approximate each Bezier curve (fallback)
            tolerance: Maximum deviation from the true curve
            
        Returns:
            PolyLine2D approximation of the Bezier path
        """
        segments = self._get_segments_from_points()
        if not segments:
            # Return a polyline with two identical points for empty path
            return PolyLine2D([Point2D(0, 0), Point2D(0, 0)])
        
        points = []
        
        for i, (start, control1, control2, end) in enumerate(segments):
            # Use adaptive subdivision if tolerance is provided
            if tolerance > 0:
                segment_points = self._adaptive_subdivide_curve(start, control1, control2, end, tolerance)
            else:
                # Fallback to fixed segments
                segment_points = []
                for j in range(segments_per_curve + 1):
                    t = j / segments_per_curve
                    point = self._cubic_bezier_point(start, control1, control2, end, t)
                    segment_points.append(point)
            
            # Add points (skip first point if not the first segment to avoid duplicates)
            if i == 0:
                points.extend(segment_points)
            else:
                points.extend(segment_points[1:])
        
        return PolyLine2D(points)
    
    def _adaptive_subdivide_curve(self, start: Point2D, control1: Point2D, control2: Point2D, end: Point2D, tolerance: float) -> List[Point2D]:
        """
        Adaptively subdivide a cubic Bezier curve based on tolerance.
        Uses the flatness test to determine where to add more points.
        """
        points = [start]
        
        def subdivide_recursive(p0: Point2D, p1: Point2D, p2: Point2D, p3: Point2D, t0: float, t3: float):
            # Check if the curve is flat enough
            if self._is_curve_flat_enough(p0, p1, p2, p3, tolerance):
                points.append(p3)
                return
            
            # Split the curve at the midpoint
            t_mid = (t0 + t3) / 2
            mid_point = self._cubic_bezier_point(p0, p1, p2, p3, 0.5)
            
            # Calculate control points for the two halves
            # First half: p0, (p0 + p1)/2, (p0 + 2*p1 + p2)/4, mid_point
            # Second half: mid_point, (p1 + 2*p2 + p3)/4, (p2 + p3)/2, p3
            p1_first = (p0 + p1) / 2
            p2_first = (p0 + 2*p1 + p2) / 4
            p1_second = (p1 + 2*p2 + p3) / 4
            p2_second = (p2 + p3) / 2
            
            # Recursively subdivide both halves
            subdivide_recursive(p0, p1_first, p2_first, mid_point, t0, t_mid)
            subdivide_recursive(mid_point, p1_second, p2_second, p3, t_mid, t3)
        
        # Start recursive subdivision
        subdivide_recursive(start, control1, control2, end, 0.0, 1.0)
        
        return points
    
    def _is_curve_flat_enough(self, p0: Point2D, p1: Point2D, p2: Point2D, p3: Point2D, tolerance: float) -> bool:
        """
        Check if a cubic Bezier curve is flat enough to be approximated by a line segment.
        Uses the distance from control points to the line segment p0-p3.
        """
        # Calculate the line from start to end
        line_vector = p3 - p0
        line_length = line_vector.magnitude
        
        if line_length < tolerance:
            return True
        
        # Calculate distances from control points to the line
        # Project control points onto the line and find the maximum deviation
        max_deviation = 0
        
        for control_point in [p1, p2]:
            # Vector from p0 to control point
            to_control = control_point - p0
            
            # Project onto line vector
            if line_length > 0:
                projection = to_control.dot(line_vector) / line_length
                # Clamp projection to line segment
                projection = max(0, min(line_length, projection))
                
                # Calculate the point on the line
                point_on_line = p0 + (line_vector / line_length) * projection
                
                # Distance from control point to line
                deviation = control_point.distance_to(point_on_line)
                max_deviation = max(max_deviation, deviation)
        
        return max_deviation <= tolerance
    
    def _estimate_curve_length(self, start: Point2D, control1: Point2D, control2: Point2D, end: Point2D) -> float:
        """Estimate the length of a Bezier curve segment."""
        # Simple estimation using control polygon length
        return (start.distance_to(control1) + 
                control1.distance_to(control2) + 
                control2.distance_to(end))
    
    def length(self, segments_per_curve: int = 100) -> float:
        """
        Calculate the approximate length of the Bezier path.
        
        Args:
            segments_per_curve: Number of segments to use for length calculation
            
        Returns:
            Approximate length of the path
        """
        polyline = self.to_polyline(segments_per_curve)
        return polyline.length
    
    @property
    def bounds(self) -> Tuple[Point2D, Point2D]:
        """Get bounding box of the Bezier path."""
        if not self._points:
            return Point2D(0, 0), Point2D(0, 0)
        
        # Find min and max coordinates of all points
        min_x = min(pt.x for pt in self._points)
        max_x = max(pt.x for pt in self._points)
        min_y = min(pt.y for pt in self._points)
        max_y = max(pt.y for pt in self._points)
        
        return Point2D(min_x, min_y), Point2D(max_x, max_y)
    
    def translate(self, vector) -> 'BezierPath':
        """Make a new Bezier path, translated by the given vector."""
        return BezierPath([point.translate(vector) for point in self._points])
        
    def rotate(self, angle: float, center = None) -> 'BezierPath':
        """Make a new Bezier path, rotated around the given center."""
        return BezierPath([point.rotate(angle, center) for point in self._points])
        
    def scale(self, scale, center = None) -> 'BezierPath':
        """Make a new Bezier path, scaled around the given center."""
        return BezierPath([point.scale(scale, center) for point in self._points])
        
    def transform(self, transform: Transform2D) -> 'BezierPath':
        """Make a new Bezier path, transformed using a transformation matrix."""
        return BezierPath([point.transform(transform) for point in self._points])
        
    def reverse(self) -> 'BezierPath':
        """Make a new Bezier path, reversed."""
        return BezierPath(list(reversed(self._points)))
    
    def close(self):
        """Close the path by connecting the last point to the first point."""
        segments = self._get_segments_from_points()
        if len(segments) < 2:
            return
        
        # Get the end point of the last segment and start point of the first segment
        last_end = segments[-1][3]
        first_start = segments[0][0]
        
        # If they're not already the same, add a closing segment
        if last_end.distance_to(first_start) > 1e-6:
            # Create a smooth closing segment
            last_control2 = segments[-1][2]
            first_control1 = segments[0][1]
            
            # Calculate control points for smooth closure
            # Use reflection of the existing control points
            closing_control1 = last_end + (last_end - last_control2)
            closing_control2 = first_start + (first_start - first_control1)
            
            self.add_segment(last_end, closing_control1, closing_control2, first_start)
    
    @classmethod
    def from_polyline(cls, polyline: 'PolyLine2D', smoothness: float = 0.5) -> 'BezierPath':
        """
        Create a Bezier path from a polyline using curve fitting.
        
        Args:
            polyline: The polyline to convert
            smoothness: Smoothness factor (0 = sharp corners, 1 = very smooth)
            
        Returns:
            BezierPath approximating the polyline
        """
        if len(polyline.points) < 2:
            return cls([])
        
        points = []
        polyline_points = polyline.points
        
        for i in range(len(polyline_points) - 1):
            start = polyline_points[i]
            end = polyline_points[i + 1]
            
            # Calculate control points based on adjacent segments
            if i == 0:
                # First segment
                if len(polyline_points) > 2:
                    next_point = polyline_points[i + 2]
                    direction = (next_point - start).unit_vector
                    control1 = start + direction * (end - start).magnitude * smoothness
                else:
                    control1 = start + (end - start) * 0.25
            else:
                # Use previous segment's end control point
                prev_end = polyline_points[i - 1]
                direction = (end - prev_end).unit_vector
                control1 = start + direction * (end - start).magnitude * smoothness
            
            if i == len(polyline_points) - 2:
                # Last segment
                if len(polyline_points) > 2:
                    prev_point = polyline_points[i - 1]
                    direction = (end - prev_point).unit_vector
                    control2 = end - direction * (end - start).magnitude * smoothness
                else:
                    control2 = end - (end - start) * 0.25
            else:
                # Use next segment's start control point
                next_point = polyline_points[i + 2]
                direction = (next_point - start).unit_vector
                control2 = end - direction * (end - start).magnitude * smoothness
            
            # Add points for this segment
            if i == 0:
                points.extend([start, control1, control2, end])
            else:
                points.extend([control1, control2, end])
        
        return cls(points)
    
    @classmethod
    def circle(cls, center: Point2D, radius: float) -> 'BezierPath':
        """Create a circular Bezier path using four cubic Bezier curves."""
        # Circle approximation using four cubic Bezier curves
        # Each curve covers 90 degrees
        
        # Control point distance for circle approximation
        # For a perfect circle, this should be 4 * (sqrt(2) - 1) / 3 ≈ 0.552
        control_distance = radius * 0.552
        
        points = []
        
        # Four quadrants
        for i in range(4):
            angle = i * np.pi / 2
            next_angle = (i + 1) * np.pi / 2
            
            # Start and end points
            start = center + Point2D(radius * np.cos(angle), radius * np.sin(angle))
            end = center + Point2D(radius * np.cos(next_angle), radius * np.sin(next_angle))
            
            # Control points
            control1 = start + Point2D(-control_distance * np.sin(angle), control_distance * np.cos(angle))
            control2 = end + Point2D(control_distance * np.sin(next_angle), -control_distance * np.cos(next_angle))
            
            # Add points for this segment
            if i == 0:
                points.extend([start, control1, control2, end])
            else:
                points.extend([control1, control2, end])
        
        return cls(points)

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get the bounds of the Bezier path as (min_x, min_y, max_x, max_y)."""
        min_pt, max_pt = self.bounds
        return (min_pt.x, min_pt.y, max_pt.x, max_pt.y)

    def closest_point_to(self, point: Point2D) -> Point2D:
        """
        Find the closest point on the Bezier path to the given point.
        
        Args:
            point: The point to find the closest point to
            
        Returns:
            The closest point on the Bezier path
        """
        segments = self._get_segments_from_points()
        if not segments:
            return point  # Return the input point if no segments
        
        closest_point = None
        min_distance = float('inf')
        
        # Check each segment
        for start, control1, control2, end in segments:
            segment_closest = self._closest_point_on_bezier_segment(
                point, start, control1, control2, end
            )
            distance = point.distance_to(segment_closest)
            
            if distance < min_distance:
                min_distance = distance
                closest_point = segment_closest
        
        return closest_point  # type: ignore
    
    def _closest_point_on_bezier_segment(
            self,
            point: Point2D,
            p0: Point2D,
            p1: Point2D,
            p2: Point2D,
            p3: Point2D
    ) -> Point2D:
        """
        Find the closest point on a single Bezier curve segment to the given point.
        Uses Newton's method to find the parameter t that minimizes the distance.
        
        Args:
            point: The point to find the closest point to
            p0, p1, p2, p3: The control points of the Bezier curve
            
        Returns:
            The closest point on the curve
        """
        # Initial guess: try several points along the curve
        best_t = 0.5
        min_distance = float('inf')
        
        # Try a few initial guesses
        for t_guess in np.linspace(0, 1, 16):
            curve_point = self._cubic_bezier_point(p0, p1, p2, p3, t_guess)
            distance = point.distance_to(curve_point)
            if distance < min_distance:
                min_distance = distance
                best_t = t_guess
        
        # Use Newton's method to refine the solution
        t = best_t
        for _ in range(20):  # Maximum iteration count
            # Current point on curve
            curve_point = self._cubic_bezier_point(p0, p1, p2, p3, t)
            
            # Tangent at current point
            tangent = self._cubic_bezier_tangent(p0, p1, p2, p3, t)
            
            # Vector from curve point to target point
            to_point = point - curve_point
            
            # Project to_point onto tangent to find parameter update
            if tangent.magnitude_squared > 1e-12:
                # Dot product gives us the projection
                projection = to_point.dot(tangent) / tangent.magnitude_squared
                
                # Update parameter
                t_new = t + projection
                
                # Clamp to [0, 1]
                t_new = max(0.0, min(1.0, t_new))
                
                # Check for convergence
                if abs(t_new - t) < 1e-6:
                    break
                
                t = t_new
            else:
                break
        
        return self._cubic_bezier_point(p0, p1, p2, p3, t)
