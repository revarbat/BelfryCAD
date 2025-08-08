"""
Spur gear geometry class for calculating gear profiles and properties.

This module provides the SpurGear class for generating spur gear tooth profiles,
calculating gear dimensions, and managing gear geometry.
"""

import math
from typing import List, Tuple, Optional

from .geometry import ShapeType, Shape2D, Point2D, EPSILON, Polygon, PolyLine2D


class SpurGear(Shape2D):
    """
    Spur gear geometry class for calculating gear profiles and properties.
    
    This class provides methods for generating spur gear tooth profiles,
    calculating gear dimensions, and managing gear geometry.
    """
    
    def __init__(self, 
                 num_teeth: int = 20,
                 pitch_diameter: float = 1.0,
                 pressure_angle: float = 20.0,
                 clearance: Optional[float] = None,
                 backlash: float = 0.0,
                 profile_shift: float = 0.0,
                 shorten: float = 0.0):
        """
        Initialize spur gear parameters.
        
        Args:
            num_teeth: Number of teeth on the gear
            pitch_diameter: Pitch circle diameter
            pressure_angle: Pressure angle in degrees
            clearance: Gap between tooth tip and root of meshing gear
            backlash: Gap between meshing teeth along pitch circle
            profile_shift: Profile shift factor
            shorten: Amount to shorten gear
        """
        self.num_teeth = num_teeth
        self.pitch_diameter = pitch_diameter
        self.pressure_angle = pressure_angle
        self.backlash = backlash
        self.profile_shift = profile_shift
        self.shorten = shorten
        
        # Calculate derived properties
        self.pitch_radius = pitch_diameter / 2.0
        self.circular_pitch = math.pi * pitch_diameter / num_teeth
        self.module = pitch_diameter / num_teeth
        self.diametral_pitch = num_teeth / pitch_diameter
        
        # Set clearance if not provided
        if clearance is None:
            self.clearance = 0.25 * self.module
        else:
            self.clearance = clearance
    
    def decompose(self, into: List[ShapeType] = [], tolerance: float = 5.0) -> List[Shape2D]:
        """Decompose the gear into simpler objects."""
        if ShapeType.SPUR_GEAR in into:
            return [self]
        points = self._to_points(tolerance)
        if ShapeType.POLYGON in into:
            return [Polygon(points)]
        if ShapeType.POLYLINE in into:
            return [PolyLine2D(points)]
        raise ValueError(f"Cannot decompose gear into any of {into}")
    
    @property
    def addendum_radius(self) -> float:
        """Get addendum (outer) radius."""
        return self._outer_radius()
    
    @property
    def base_radius(self) -> float:
        """Get base circle radius."""
        return self._base_radius()
    
    @property
    def root_radius(self) -> float:
        """Get root (inner) radius."""
        return self._root_radius_basic()
    
    @property
    def safety_radius(self) -> float:
        """Get safety radius (max of root and base)."""
        return max(self.root_radius, self.base_radius)
    
    def _outer_radius(self) -> float:
        """Calculate outer radius."""
        return (self.pitch_diameter / 2.0 + 
                self.module * (1.0 + self.profile_shift) - 
                self.shorten)
    
    def _base_radius(self) -> float:
        """Calculate base circle radius."""
        return (self.pitch_radius * 
                math.cos(math.radians(self.pressure_angle)))
    
    def _root_radius_basic(self) -> float:
        """Calculate root circle radius."""
        return (self.pitch_radius - 
                self.module * (1.25 - self.profile_shift) - 
                self.clearance)
    
    def _involute(self, base_r: float, a: float) -> Tuple[float, float]:
        """Calculate involute curve point."""
        x = base_r * (math.cos(a) + a * math.sin(a))
        y = base_r * (math.sin(a) - a * math.cos(a))
        return (x, y)
    
    def _xy_to_polar(self, xy: Tuple[float, float]) -> Tuple[float, float]:
        """Convert Cartesian to polar coordinates."""
        x, y = xy
        r = math.sqrt(x * x + y * y)
        a = math.degrees(math.atan2(y, x))
        return (r, a)
    
    def _polar_to_xy(self, r: float, a: float) -> Tuple[float, float]:
        """Convert polar to Cartesian coordinates."""
        x = r * math.cos(math.radians(a))
        y = r * math.sin(math.radians(a))
        return (x, y)
    
    def _lookup(self, val: float, table: List[Tuple[float, float]]) -> float:
        """Lookup value in table using linear interpolation."""
        if not table:
            return 0.0
        
        # Find the two closest values
        for i in range(len(table) - 1):
            if table[i][0] <= val <= table[i + 1][0]:
                x1, y1 = table[i]
                x2, y2 = table[i + 1]
                if x2 == x1:
                    return y1
                return y1 + (y2 - y1) * (val - x1) / (x2 - x1)
        
        # Extrapolate if value is outside table range
        if val <= table[0][0]:
            return table[0][1]
        else:
            return table[-1][1]
    
    def _ang_adj_to_opp(self, angle_deg: float, adj: float) -> float:
        """Convert adjacent to opposite using angle."""
        return adj * math.tan(math.radians(angle_deg))
    
    def _line_intersection(self, line1: Tuple[Point2D, Point2D], 
                          line2: Tuple[Point2D, Point2D]) -> Optional[Point2D]:
        """Find intersection of two lines."""
        p1, p2 = line1
        p3, p4 = line2
        
        x1, y1 = p1.x, p1.y
        x2, y2 = p2.x, p2.y
        x3, y3 = p3.x, p3.y
        x4, y4 = p4.x, p4.y
        
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < EPSILON:
            return None
        
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        
        return Point2D(x, y)
    
    def _vector_angle(self, points: List[Point2D]) -> float:
        """Calculate angle of vector from points."""
        if len(points) < 2:
            return 0.0
        
        dx = points[-1].x - points[0].x
        dy = points[-1].y - points[0].y
        
        return math.degrees(math.atan2(dy, dx))
    
    def _corner_arc(self, n: int, r: float, corner: List[Point2D]) -> List[Point2D]:
        """Generate arc for corner."""
        if len(corner) < 3:
            return corner
        
        p1, p2, p3 = corner[0], corner[1], corner[2]
        
        # Calculate vectors
        v1 = Point2D(p2.x - p1.x, p2.y - p1.y)
        v2 = Point2D(p3.x - p2.x, p3.y - p2.y)
        
        # Normalize vectors
        len1 = math.sqrt(v1.x * v1.x + v1.y * v1.y)
        len2 = math.sqrt(v2.x * v2.x + v2.y * v2.y)
        
        if len1 < EPSILON or len2 < EPSILON:
            return corner
        
        v1 = v1 / len1
        v2 = v2 / len2
        
        # Calculate angle between vectors
        dot = v1.x * v2.x + v1.y * v2.y
        dot = max(-1.0, min(1.0, dot))  # Clamp to [-1, 1]
        angle = math.acos(dot)
        
        if angle < EPSILON:
            return corner
        
        # Calculate arc parameters
        tan_dist = r / math.tan(angle / 2.0)
        
        # Calculate arc points
        arc_points = []
        steps = max(1, int(n * angle / (2 * math.pi)))
        
        for i in range(steps + 1):
            t = i / steps
            arc_angle = t * angle
            
            # Rotate v1 by arc_angle
            cos_a = math.cos(arc_angle)
            sin_a = math.sin(arc_angle)
            
            v_rot = Point2D(
                v1.x * cos_a - v1.y * sin_a,
                v1.x * sin_a + v1.y * cos_a
            )
            
            # Calculate arc point
            arc_point = p2 + v_rot * tan_dist
            arc_points.append(arc_point)
        
        return arc_points
    
    def _deduplicate(self, points: List[Point2D], eps: float = 1e-9) -> List[Point2D]:
        """Remove duplicate points."""
        if not points:
            return []
        
        result = [points[0]]
        for point in points[1:]:
            if point.distance_to(result[-1]) > eps:
                result.append(point)
        
        return result
    
    def _path_merge_collinear(self, path: List[Point2D], eps: float = 1e-9) -> List[Point2D]:
        """Merge collinear segments in path."""
        if len(path) < 3:
            return path
        
        result = [path[0]]
        
        for i in range(1, len(path) - 1):
            p1, p2, p3 = path[i-1], path[i], path[i+1]
            
            # Check if p2 is collinear with p1-p3
            v1 = Point2D(p2.x - p1.x, p2.y - p1.y)
            v2 = Point2D(p3.x - p2.x, p3.y - p2.y)
            
            # Calculate cross product
            cross = v1.x * v2.y - v1.y * v2.x
            
            if abs(cross) > eps:
                result.append(p2)
        
        result.append(path[-1])
        return result
    
    def _strip_left(self, path: List[Point2D], i: int, undercut_max: float) -> List[Point2D]:
        """Strip left side of path."""
        if i >= len(path):
            return path
        
        result = path[:i]
        
        for j in range(i, len(path)):
            if path[j].x >= undercut_max:
                result.append(path[j])
        
        return result
    
    def _lerp(self, a: float, b: float, u: float) -> float:
        """Linear interpolation."""
        return a + u * (b - a)
    
    def _zrot(self, angle: float, pt: Point2D) -> Point2D:
        """Rotate point around Z axis."""
        cos_a = math.cos(math.radians(angle))
        sin_a = math.sin(math.radians(angle))
        
        return Point2D(
            pt[0] * cos_a - pt[1] * sin_a,
            pt[0] * sin_a + pt[1] * cos_a
        )
    
    def generate_tooth_profile(self, tolerance: float = 0.001) -> List[Point2D]:
        """
        Generate the 2D profile path for an individual gear tooth.
        
        Args:
            tolerance: Maximum deviation from the true curve
            
        Returns:
            List of points forming the tooth profile
        """
        # Calculate number of steps based on tolerance
        # For gear curves, we need more points for smaller tolerances
        # Use a more effective calculation based on the gear size and tolerance
        # The gear radius affects how many points we need for a given tolerance
        gear_radius = self.addendum_radius
        if tolerance <= 0:
            gear_steps = 100  # Default fallback
        else:
            # Calculate steps based on the circumference and desired tolerance
            # For a circle, the maximum deviation is approximately r * (1 - cos(π/n))
            # Setting this equal to tolerance: r * (1 - cos(π/n)) = tolerance
            # Solving for n: n = π / arccos(1 - tolerance/r)
            if tolerance >= gear_radius:
                gear_steps = 8  # Minimum steps
            else:
                gear_steps = max(8, int(math.pi / math.acos(1 - tolerance / gear_radius)))
        num_steps = gear_steps
        
        # Calculate the important circle radii
        addendum_radius = self.addendum_radius
        pitch_radius_value = self.pitch_radius
        base_radius = self.base_radius
        root_radius = self.root_radius
        safety_radius = self.safety_radius
        
        tooth_thickness = (self.circular_pitch / math.pi * 
                          (math.pi / 2 + 2 * self.profile_shift * 
                           math.tan(math.radians(self.pressure_angle))) + 
                          (self.backlash if False else -self.backlash))  # internal=False
        
        tooth_angle = tooth_thickness / pitch_radius_value / 2 * 180 / math.pi
        
        # Generate a lookup table for the involute curve angles, by radius
        involute_lookup = []
        for i in range(0, int(addendum_radius / math.pi / base_radius * 360), 5):
            xy = self._involute(base_radius, i)
            rad, ang = self._xy_to_polar(xy)
            if rad <= addendum_radius * 1.1:
                involute_lookup.append((rad, 90 - ang))
        
        # Generate reverse lookup table for involute radii, by angle
        involute_reverse_lookup = [(y, x) for x, y in reversed(involute_lookup)]
        
        addendum_angle = self._lookup(addendum_radius, involute_lookup)
        pitch_angle = self._lookup(pitch_radius_value, involute_lookup)
        base_angle = self._lookup(base_radius, involute_lookup)
        root_angle = self._lookup(root_radius, involute_lookup)
        safety_angle = self._lookup(safety_radius, involute_lookup)
        angle_offset = tooth_angle + (base_angle - pitch_angle)
        
        max_addendum_radius = min(addendum_radius, 
                                 self._lookup(90 - angle_offset + 0.05 * 360 / self.num_teeth / 2, 
                                             involute_reverse_lookup))
        max_addendum_angle = self._lookup(max_addendum_radius, involute_lookup)
        cap_steps = max(1, math.ceil((max_addendum_angle + angle_offset - 90) / 5))
        cap_step = (max_addendum_angle + angle_offset - 90) / cap_steps
        
        rack_offset = self.circular_pitch / 4 - self._ang_adj_to_opp(self.pressure_angle, self.circular_pitch / math.pi)
        
        # Calculate the undercut a meshing rack might carve out of this tooth
        undercut = []
        for a in range(int(math.degrees(math.atan2(rack_offset, root_radius))), -91, -1):
            bx = -a / 360 * 2 * math.pi * pitch_radius_value
            x = bx + rack_offset
            y = pitch_radius_value - self.circular_pitch / math.pi + self.profile_shift * self.circular_pitch / math.pi
            rad, ang = self._xy_to_polar((x, y))
            if rad < addendum_radius * 1.05:
                undercut.append((rad, ang - a + 180 / self.num_teeth))
        
        # Find minimum index for undercut
        if undercut:
            uc_min = min(range(len(undercut)), key=lambda i: undercut[i][0])
            undercut_lookup = undercut[uc_min:]
        else:
            undercut_lookup = []
        
        # Generate the tooth profile
        profile = []
        
        # Start from root radius
        if root_radius > safety_radius:
            # Add root circle arc
            for i in range(num_steps + 1):
                angle = 90 - angle_offset + i * tooth_angle / num_steps
                x, y = self._polar_to_xy(root_radius, angle)
                profile.append(Point2D(x, y))
        else:
            # Start from safety radius
            safety_angle_val = self._lookup(safety_radius, involute_lookup)
            for i in range(num_steps + 1):
                angle = safety_angle_val + i * (base_angle - safety_angle_val) / num_steps
                x, y = self._polar_to_xy(safety_radius, angle)
                profile.append(Point2D(x, y))
        
        # Add involute curve
        for i in range(num_steps + 1):
            angle = base_angle + i * (addendum_angle - base_angle) / num_steps
            x, y = self._polar_to_xy(addendum_radius, angle)
            profile.append(Point2D(x, y))
        
        # Add cap
        for i in range(cap_steps + 1):
            angle = addendum_angle + i * cap_step
            x, y = self._polar_to_xy(addendum_radius, angle)
            profile.append(Point2D(x, y))
        
        # Add undercut if present
        if undercut_lookup:
            for rad, ang in undercut_lookup:
                x, y = self._polar_to_xy(rad, ang)
                profile.append(Point2D(x, y))
        
        # Clean up profile
        profile = self._deduplicate(profile)
        profile = self._path_merge_collinear(profile)
        
        return profile
    
    def _to_points(self, tolerance: float = 0.001) -> List[Point2D]:
        """
        Generate complete gear path.
        
        Args:
            tolerance: Maximum deviation from the true curve
            
        Returns:
            List of points forming the complete gear profile
        """
        # Generate single tooth profile
        tooth_profile = self.generate_tooth_profile(tolerance)
        
        # Generate complete gear by rotating tooth profile
        gear_points = []
        
        for tooth in range(self.num_teeth):
            angle = 360.0 * tooth / self.num_teeth
            
            for point in tooth_profile:
                rotated_point = self._zrot(angle, point)
                gear_points.append(rotated_point)
        
        # Close the gear
        if gear_points:
            gear_points.append(gear_points[0])
        
        return gear_points
    
    def generate_gear_path(self, tolerance: float = 0.001) -> List[Point2D]:
        """Generate the complete gear path as a list of points.
        
        Args:
            tolerance: Maximum deviation allowed when approximating curves.
        
        Returns:
            List of points forming the closed gear profile path.
        """
        return self._to_points(tolerance)
    
    def get_pitch_circle_points(self, num_points: int = 64) -> List[Point2D]:
        """
        Get points for pitch circle.
        
        Args:
            num_points: Number of points to generate
            
        Returns:
            List of points forming the pitch circle
        """
        points = []
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            x = self.pitch_radius * math.cos(angle)
            y = self.pitch_radius * math.sin(angle)
            points.append(Point2D(x, y))
        
        return points 