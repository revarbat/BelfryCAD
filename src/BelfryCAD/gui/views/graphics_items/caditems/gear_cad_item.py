"""
PolylineCadItem - A polyline CAD item defined by a list of points.
"""

import math
from typing import List, Optional, Tuple, TYPE_CHECKING

from PySide6.QtCore import QPointF
from PySide6.QtGui import (
    QPen, QColor, QBrush,
    QPainterPath, QPainterPathStroker,
)

from ..cad_item import CadItem
from ..control_points import ControlPoint, SquareControlPoint, ControlDatum
from ..cad_rect import CadRect

if TYPE_CHECKING:
    from ....main_window import MainWindow


# Helper functions
def _involute(base_r: float, a: float) -> Tuple[float, float]:
    """Calculate a point on the involute curve, by angle in degrees."""
    b = a * math.pi / 180
    return (base_r * (math.cos(b) + b * math.sin(b)), 
            base_r * (math.sin(b) - b * math.cos(b)))

def xy_to_polar(xy: Tuple[float, float]) -> Tuple[float, float]:
    """Convert Cartesian to polar coordinates (r, theta_degrees)."""
    x, y = xy
    r = math.hypot(x, y)
    theta = math.degrees(math.atan2(y, x))
    return (r, theta)

def polar_to_xy(r: float, a: float) -> Tuple[float, float]:
    """Convert polar to Cartesian coordinates."""
    return (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))

def lookup(val: float, table: List[Tuple[float, float]]) -> float:
    """Lookup value in table with linear interpolation."""
    if not table:
        return 0
    if val <= table[0][0]:
        return table[0][1]
    if val >= table[-1][0]:
        return table[-1][1]
    
    for i in range(len(table) - 1):
        if table[i][0] <= val <= table[i+1][0]:
            t = (val - table[i][0]) / (table[i+1][0] - table[i][0])
            return table[i][1] + t * (table[i+1][1] - table[i][1])
    return table[-1][1]

def circular_pitch(pitch=None, circ_pitch=None, diam_pitch=None, mod=None):
    """Calculate circular pitch from various inputs."""
    if pitch is not None:
        return pitch
    elif circ_pitch is not None:
        return circ_pitch
    elif diam_pitch is not None:
        return math.pi / diam_pitch * 25.4  # Convert from inches to mm
    elif mod is not None:
        return mod * math.pi
    else:
        return 5  # Default

def module_value(circ_pitch):
    """Calculate module from circular pitch."""
    return circ_pitch / math.pi

def outer_radius(circ_pitch, teeth, helical=0.0, profile_shift=0.0, internal=False, shorten=0.0):
    """Calculate outer radius of gear."""
    mod = module_value(circ_pitch)
    prad = pitch_radius(circ_pitch, teeth, helical)
    if internal:
        return prad - mod * (1 - profile_shift) + shorten
    else:
        return prad + mod * (1 + profile_shift) - shorten

def pitch_radius(circ_pitch, teeth, helical=0.0):
    """Calculate pitch radius."""
    return teeth * circ_pitch / (2 * math.pi) / math.cos(math.radians(helical))

def _base_radius(circ_pitch, teeth, pressure_angle, helical=0.0):
    """Calculate base radius."""
    prad = pitch_radius(circ_pitch, teeth, helical)
    pa_radians = math.radians(pressure_angle)
    helical_radians = math.radians(helical)
    trans_pa = math.atan(math.tan(pa_radians)/math.cos(helical_radians))
    return prad * math.cos(trans_pa)

def _root_radius_basic(circ_pitch, teeth, clearance, helical=0.0, profile_shift=0.0, internal=False):
    """Calculate root radius."""
    mod = module_value(circ_pitch)
    prad = pitch_radius(circ_pitch, teeth, helical)
    if internal:
        return prad + mod * (1 + clearance/mod - profile_shift)
    else:
        return prad - mod * (1 + clearance/mod - profile_shift)

def ang_adj_to_opp(angle_deg, adj):
    """Calculate opposite side from angle and adjacent side."""
    return adj * math.tan(math.radians(angle_deg))

def line_intersection(line1, line2):
    """Find intersection of two lines, each defined by two points."""
    (x1, y1), (x2, y2) = line1
    (x3, y3), (x4, y4) = line2
    
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-10:
        return None
    
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    x = x1 + t * (x2 - x1)
    y = y1 + t * (y2 - y1)
    return (x, y)

def vector_angle(points):
    """Calculate angle between three points."""
    if len(points) != 3:
        return 0
    p1, p2, p3 = points
    u = (p1[0] - p2[0], p1[1] - p2[1])
    v = (p3[0] - p2[0], p3[1] - p2[1])
    dot_product = sum(i*j for i, j in zip(u, v))
    norm_u = math.sqrt(sum(i**2 for i in u))
    norm_v = math.sqrt(sum(i**2 for i in v))
    cos_theta = dot_product / (norm_u * norm_v)
    cos_theta = min(1, max(-1, cos_theta))
    angle_rad = math.acos(cos_theta)
    return math.degrees(angle_rad)

def corner_arc(n, r, corner):
    """Generate arc points for rounding a corner."""
    if len(corner) != 3:
        return []
    
    # Calculate the angle of the corner
    angle = vector_angle(corner)
    if abs(angle) < 1:
        return []
    
    # Find center of arc
    p1, p2, p3 = corner
    v1 = ((p1[0] - p2[0]), (p1[1] - p2[1]))
    v2 = ((p3[0] - p2[0]), (p3[1] - p2[1]))
    
    # Normalize vectors
    len1 = math.hypot(v1[0], v1[1])
    len2 = math.hypot(v2[0], v2[1])
    if len1 < 1e-10 or len2 < 1e-10:
        return []
    
    v1 = (v1[0]/len1, v1[1]/len2)
    v2 = (v2[0]/len2, v2[1]/len2)
    
    # Calculate bisector
    bisector = ((v1[0] + v2[0])/2, (v1[1] + v2[1])/2)
    bis_len = math.hypot(bisector[0], bisector[1])
    if bis_len < 1e-10:
        return []
    
    # Distance from corner to arc center
    half_angle = angle / 2
    dist = r / math.sin(math.radians(half_angle))
    
    # Arc center
    center = (p2[0] + bisector[0]/bis_len * dist,
                p2[1] + bisector[1]/bis_len * dist)
    
    # Generate arc points
    start_angle = math.atan2(p1[1] - center[1], p1[0] - center[0])
    end_angle = math.atan2(p3[1] - center[1], p3[0] - center[0])
    
    points = []
    for i in range(n + 1):
        t = i / n
        a = start_angle + t * (end_angle - start_angle)
        x = center[0] + r * math.cos(a)
        y = center[1] + r * math.sin(a)
        points.append((x, y))
    
    return points[1:-1]  # Exclude endpoints

def deduplicate(points, eps=1e-9):
    """Remove duplicate consecutive points."""
    if not points:
        return []
    result = [points[0]]
    for p in points[1:]:
        if abs(p[0] - result[-1][0]) > eps or abs(p[1] - result[-1][1]) > eps:
            result.append(p)
    return result

def path_merge_collinear(path, eps=1e-9):
    """Merge collinear segments in path."""
    if len(path) < 3:
        return path
    
    result = [path[0]]
    for i in range(1, len(path) - 1):
        # Check if three consecutive points are collinear
        p1, p2, p3 = result[-1], path[i], path[i+1]
        
        # Calculate cross product to check collinearity
        cross = (p2[0] - p1[0]) * (p3[1] - p1[1]) - (p2[1] - p1[1]) * (p3[0] - p1[0])
        
        if abs(cross) > eps:
            result.append(p2)
    
    result.append(path[-1])
    return result

def strip_left(path, i, undercut_max):
    """Strip "jaggies" if found"""
    if i >= len(path):
        return []
    
    if undercut_max == 0 or math.hypot(path[i][0], path[i][1]) >= undercut_max:
        return path[i:]
    
    # Find next point beyond undercut
    best_j = i + 1
    min_angle = float('inf')
    
    for j in range(i + 1, len(path)):
        r = math.hypot(path[j][0], path[j][1])
        if r >= undercut_max:
            break
        
        # Calculate angle
        dx = path[j][0] - path[i][0]
        dy = path[j][1] - path[i][1]
        if dx != 0 or dy != 0:
            angle = math.atan2(dy, dx)
            if angle < min_angle:
                min_angle = angle
                best_j = j
    
    return [path[i]] + strip_left(path, best_j, undercut_max)

def lerp(a, b, u):
    return a + (b - a) * u

def zrot(angle, pt):
    ang_rad = math.radians(angle)
    return (
        pt[0] * math.cos(ang_rad) - pt[1] * math.sin(ang_rad),
        pt[0] * math.sin(ang_rad) + pt[1] * math.cos(ang_rad)
    )

def _gear_tooth_profile(
        circ_pitch: Optional[float] = None,
        teeth: int = 20,
        pressure_angle: float = 20,
        clearance: Optional[float] = None,
        backlash: float = 0.0,
        helical: float = 0,
        internal: bool = False,
        profile_shift: float = 0.0,
        shorten: float = 0,
        mod: Optional[float] = None,
        diam_pitch: Optional[float] = None,
        pitch: Optional[float] = None,
        center: bool = False,
        gear_steps: int = 16
) -> List[Tuple[float, float]]:
    """
    Generate the 2D profile path for an individual gear tooth.
    Faithful translation of OpenSCAD BOSL2 _gear_tooth_profile function.
    
    Args:
        circ_pitch: The circular pitch, the distance between teeth centers around the pitch circle.
        teeth: Total number of teeth on the spur gear that this is a tooth for.
        pressure_angle: Pressure Angle in degrees. Controls how straight or bulged the tooth sides are.
        clearance: Gap between top of a tooth on one gear and bottom of valley on a meshing gear (in millimeters)
        backlash: Gap between two meshing teeth, in the direction along the circumference of the pitch circle
        internal: If true, create a mask for difference()ing from something else.
        profile_shift: Profile shift factor
        shorten: Amount to shorten gear
        mod: The module of the gear (pitch diameter / teeth)
        diam_pitch: The diametral pitch, or number of teeth per inch of pitch diameter.
        pitch: Deprecated parameter for circular pitch
        center: If true, centers the pitch circle of the tooth profile at the origin.
        gear_steps: Number of steps to use in generating curves (default 16)
    
    Returns:
        List of (x, y) points forming the tooth profile
    """
    
    # Main calculation
    num_steps = gear_steps
    circ_pitch = circular_pitch(pitch=pitch, circ_pitch=circ_pitch, diam_pitch=diam_pitch, mod=mod)
    module = module_value(circ_pitch)
    clearance_value = clearance if clearance is not None else 0.25 * module
    
    # Calculate the important circle radii
    addendum_radius = outer_radius(circ_pitch, teeth, helical=helical, profile_shift=profile_shift, internal=internal, shorten=shorten)
    pitch_radius_value = pitch_radius(circ_pitch, teeth, helical=helical)
    base_radius = _base_radius(circ_pitch, teeth, pressure_angle, helical=helical)
    root_radius = _root_radius_basic(circ_pitch, teeth, clearance_value, helical=helical, profile_shift=profile_shift, internal=internal)
    safety_radius = max(root_radius, base_radius)

    tooth_thickness = circ_pitch/math.pi / math.cos(math.radians(helical)) * (math.pi/2 + 2*profile_shift * math.tan(math.radians(pressure_angle))) + (backlash if internal else -backlash)

    tooth_angle = tooth_thickness / pitch_radius_value / 2 * 180 / math.pi
    
    # Generate a lookup table for the involute curve angles, by radius
    involute_lookup = []
    for i in range(0, int(addendum_radius/math.pi/base_radius*360), 5):
        xy = _involute(base_radius, i)
        rad,ang = xy_to_polar(xy)
        if rad <= addendum_radius * 1.1:
            involute_lookup.append((rad, 90 - ang))

    # Generate reverse lookup table for involute radii, by angle
    involute_reverse_lookup = [(y, x) for x, y in reversed(involute_lookup)]  # Swap columns
    
    addendum_angle = lookup(addendum_radius, involute_lookup)
    pitch_angle = lookup(pitch_radius_value, involute_lookup)
    base_angle = lookup(base_radius, involute_lookup)
    root_angle = lookup(root_radius, involute_lookup)
    safety_angle = lookup(safety_radius, involute_lookup)
    angle_offset = tooth_angle + (base_angle - pitch_angle)

    #ma_rad = min(arad, lookup(90-soff+0.05*360/teeth/2, involute_rlup)),
    max_addendum_radius = min(addendum_radius, lookup(90 - angle_offset + 0.05*360/teeth/2, involute_reverse_lookup))
    max_addendum_angle = lookup(max_addendum_radius, involute_lookup)
    cap_steps = max(1, math.ceil((max_addendum_angle + angle_offset - 90) / 5))
    cap_step = (max_addendum_angle + angle_offset - 90) / cap_steps
    
    rack_offset = circ_pitch/4 - ang_adj_to_opp(pressure_angle, circ_pitch/math.pi)
    
    # Calculate the undercut a meshing rack might carve out of this tooth
    undercut = []
    for a in range(int(math.degrees(math.atan2(rack_offset, root_radius))), -91, -1):
        bx = -a/360 * 2*math.pi*pitch_radius_value
        x = bx + rack_offset
        y = pitch_radius_value - circ_pitch/math.pi + profile_shift*circ_pitch/math.pi
        rad, ang = xy_to_polar((x, y))
        if rad < addendum_radius*1.05:
            undercut.append((rad, ang - a + 180/teeth))
    
    # Find minimum index for undercut
    if undercut:
        uc_min = min(range(len(undercut)), key=lambda i: undercut[i][0])
        undercut_lookup = undercut[uc_min:]
    else:
        undercut_lookup = []
    
    # The u values to use when generating the tooth
    us = [i/num_steps/2 for i in range(num_steps*2 + 1)]
    
    # Find top of undercut
    undercut_max = 0
    for u in us:
        r = lerp(root_radius, max_addendum_radius, u)
        a1 = lookup(r, involute_lookup) + angle_offset
        if undercut_lookup and r >= undercut_lookup[0][0]:
            a2 = lookup(r, undercut_lookup)
            a = a1 if internal else min(a1, a2)
            b = False if internal else a1 > a2
            if a < 90 + 180/teeth and b:
                undercut_max = max(undercut_max, r)
        
    # Generate the left half of the tooth
    tooth_half_raw = []
    
    # Main tooth profile
    for u in us:
        r = lerp(root_radius, max_addendum_radius, u)  # lerp
        a1 = lookup(r, involute_lookup) + angle_offset
        if undercut_lookup and r >= undercut_lookup[0][0] and not internal:
            a2 = lookup(r, undercut_lookup)
            a = min(a1, a2)
        else:
            a = a1
  
        if internal or r > root_radius + clearance_value:
            if not internal or r < max_addendum_radius - clearance_value:
                if a < 90 + 180/teeth:
                    tooth_half_raw.append(polar_to_xy(r, a))

    # Add cap for external gears
    if not internal:
        for i in range(cap_steps):
            a = max_addendum_angle + angle_offset - i * (cap_step - 1)
            tooth_half_raw.append(polar_to_xy(max_addendum_radius, a))
    
    tooth_half_raw = deduplicate(tooth_half_raw)
    
    # Round out the clearance valley
    rcircum = 2 * math.pi * (max_addendum_radius if internal else root_radius)
    rpart = (180/teeth - tooth_angle) / 360
    
    if internal:
        line1 = [tooth_half_raw[-2], tooth_half_raw[-1]]
        line2 = [(0, max_addendum_radius), (-1, max_addendum_radius)]
    else:
        line1 = [tooth_half_raw[0], tooth_half_raw[1]]
        line2 = [  # Rotate line2 by half a tooth.
            zrot(180/teeth, (0, root_radius)), 
            zrot(180/teeth, (1, root_radius))
        ]
    
    isect_pt = line_intersection(line1, line2)
    if isect_pt is None:
        isect_pt = line1[0]
    
    if internal:
        rcorner = [line1[-1], isect_pt, line2[0]]
    else:
        rcorner = [line2[0], isect_pt, line1[0]]
    
    # Calculate max radius for rounding
    if len(rcorner) == 3 and rcorner[0] != rcorner[1]:
        vang = vector_angle(rcorner)
        maxr = math.hypot(
            rcorner[0][0] - rcorner[1][0], 
            rcorner[0][1] - rcorner[1][1]
        ) * math.tan(math.radians(abs(vang)/2))
    else:
        maxr = 0
    
    round_r = min(maxr, clearance_value, rcircum * rpart) if maxr > 0 else 0
    # Build rounded tooth half
    rounded_tooth_half = []
    
    if not internal:
        if round_r > 0:
            rounded_tooth_half.extend(corner_arc(n=8, r=round_r, corner=rcorner))
        else:
            rounded_tooth_half.append(isect_pt)
    
    rounded_tooth_half.extend(tooth_half_raw)
    
    if internal:
        if round_r > 0:
            rounded_tooth_half.extend(corner_arc(n=8, r=round_r, corner=rcorner))
        else:
            rounded_tooth_half.append(isect_pt)
    
    rounded_tooth_half = deduplicate(rounded_tooth_half)
        
    tooth_half = rounded_tooth_half if undercut_max == 0 else strip_left(rounded_tooth_half, 0, undercut_max)

    # Look for self-intersections in the gear profile
    invalid = []
    for i, pt in enumerate(tooth_half):
        angle = math.degrees(math.atan2(pt[1], pt[0]))
        if angle > 90 + 180/teeth:
            invalid.append(i)
    
    if invalid:
        ind = invalid[-1]
        # Find intersection with radial line at 90 + 180/teeth degrees
        angle_rad = math.radians(90 + 180/teeth)
        radial_line = [(0, 0), (math.cos(angle_rad), math.sin(angle_rad))]
        
        if ind < len(tooth_half) - 1:
            segment = [tooth_half[ind], tooth_half[ind + 1]]
            ipt = line_intersection(radial_line, segment)
            if ipt:
                clipped = [ipt] + tooth_half[ind + 1:]
            else:
                clipped = tooth_half[ind + 1:]
        else:
            clipped = tooth_half
    else:
        clipped = tooth_half

    trimmed = []
    for x,y in clipped:
        r,a = xy_to_polar((x, y))
        if r < root_radius:
            trimmed.append(polar_to_xy(root_radius, a))
        else:
            trimmed.append((x, y))

    # Mirror the tooth to complete it
    full_tooth = []
    full_tooth.extend(trimmed)
    # Add mirrored points (flip x coordinate)
    for pt in reversed(trimmed):
        full_tooth.append((-pt[0], pt[1]))
    
    full_tooth = deduplicate(full_tooth)
    
    # Reduce number of vertices
    tooth = path_merge_collinear(full_tooth)
    
    # Center if requested
    if center:
        tooth = [(x, y - pitch_radius_value) for x, y in tooth]
    
    return tooth


def _generate_gear_path(
        num_teeth: int,
        mod: Optional[float] = None,
        diametral_pitch: Optional[float] = None,
        pressure_angle: float = 20.0,
        profile_shift: float = 0.0,
        backlash: float = 0.0,
        clearance: Optional[float] = None,
        internal: bool = False,
        points_per_involute: int = 30
) -> List[Tuple[float, float]]:
    """
    Returns a list of (x, y) points forming the 2D outline of an involute spur gear.
    Based on OpenSCAD BOSL2 gears.scad _gear_tooth_profile() implementation.
    
    Args:
        num_teeth: Number of teeth on the gear
        mod: Module (pitch diameter / teeth) - specify either mod or diametral_pitch
        diametral_pitch: Diametral pitch (teeth per inch) - specify either mod or diametral_pitch
        pressure_angle: Pressure angle in degrees (default: 20)
        profile_shift: Profile shift factor x (default: 0)
        backlash: Gap between meshing teeth (default: 0)
        clearance: Gap between tooth tip and valley (default: module/4)
        internal: If True, creates internal gear (default: False)
        points_per_involute: Number of points to sample involute curve (default: 30)
    
    Returns:
        List of (x, y) points forming the gear outline
    """
    # Validate input parameters
    if (mod is None) == (diametral_pitch is None):
        raise ValueError("Specify exactly one of module or diametral_pitch.")
    
    # Calculate module from diametral pitch if needed
    m = mod if mod is not None else 25.4 / diametral_pitch  # type: ignore
    
    # Set default clearance if not specified
    if clearance is None:
        clearance = 0.25 * m
    
    # Generate complete gear by rotating and duplicating tooth profiles
    points = []
    
    for i in range(num_teeth):
        tooth_rotation = -2 * math.pi * i / num_teeth
        
        # Get single tooth profile
        tooth_profile = _gear_tooth_profile(
            teeth=num_teeth,
            mod=mod,
            pressure_angle=pressure_angle,
            profile_shift=profile_shift,
            backlash=backlash,
            clearance=clearance,
            internal=internal,
            gear_steps=points_per_involute
        )
        
        # Rotate tooth to correct position
        rotated_tooth = []
        for x, y in tooth_profile:
            # Rotate point
            cos_rot = math.cos(tooth_rotation)
            sin_rot = math.sin(tooth_rotation)
            new_x = x * cos_rot - y * sin_rot
            new_y = x * sin_rot + y * cos_rot
            rotated_tooth.append((new_x, new_y))
        
        points.extend(rotated_tooth)
        
    return points


class GearCadItem(CadItem):
    """A gear CAD item defined by center, pitch radius point, tooth count, and module."""

    def __init__(
            self,
            main_window: 'MainWindow',
            center: QPointF = QPointF(0, 0),
            pitch_radius_point: QPointF = QPointF(1, 0),
            tooth_count: int = 12,
            pressure_angle: float = 20,
            color: QColor = QColor(0, 0, 0),
            line_width: Optional[float] = 0.05
    ):
        super().__init__(main_window, color, line_width)
        self._center = QPointF(center)
        self._pitch_radius_point = QPointF(pitch_radius_point)
        self._tooth_count = int(tooth_count)
        self._pressure_angle = pressure_angle
        self._center_cp = None
        self._radius_cp = None
        self._tooth_count_datum = None
        self._pitch_diameter_datum = None
        self._pressure_angle_datum = None
        self._gear_path = None
        self.setZValue(1)
        self.setPos(self._center)
        self.createControls()
        self._update_gear_path()

    def _update_gear_path(self):
        # Compute scale and rotation from center and pitch_radius_point
        if self._gear_path is not None:
            return
        
        v = self._pitch_radius_point - self._center
        pitch_radius = math.hypot(v.x(), v.y())
        mod = pitch_radius*2/self._tooth_count
        angle = math.degrees(math.atan2(v.y(), v.x()))
        
        # Generate gear at origin with fewer points for better performance
        points = _generate_gear_path(
            num_teeth=self._tooth_count,
            mod=mod,
            pressure_angle=self._pressure_angle,
            points_per_involute=20  # Reduced for better performance
        )
        
        # Convert points to QPointF and apply transformation
        if points:
            # Convert to QPointF and apply rotation and translation
            cos_a = math.cos(math.radians(angle))
            sin_a = math.sin(math.radians(angle))
            
            # Create QPainterPath from points
            self._gear_path = QPainterPath()
            
            # Start at the first point
            x, y = points[0]
            # Apply rotation and scale
            x_rot = x * cos_a - y * sin_a
            y_rot = x * sin_a + y * cos_a
            self._gear_path.moveTo(QPointF(x_rot, y_rot))
            
            # Add all other points
            for x, y in points[1:]:
                # Apply rotation and scale
                x_rot = x * cos_a - y * sin_a
                y_rot = x * sin_a + y * cos_a
                self._gear_path.lineTo(QPointF(x_rot, y_rot))
            
            # Close the path
            self._gear_path.closeSubpath()

        self.prepareGeometryChange()
        self.update()

    def boundingRect(self):
        if self._gear_path is not None:
            rect = self._gear_path.boundingRect()
            padding = max(self.line_width / 2, 0.1)
            rect.adjust(-padding, -padding, padding, padding)
            return rect
        return CadRect(-1, -1, 2, 2)

    def shape(self):
        if self._gear_path is not None:
            stroker = QPainterPathStroker()
            stroker.setWidth(max(self.line_width, 0.1))
            return stroker.createStroke(self._gear_path)
        return QPainterPath()

    def paint_item_with_color(self, painter, option, widget=None, color: Optional[QColor] = None):
        if self._gear_path is None:
            self._update_gear_path()
        if self._gear_path is None:
            return
        painter.save()
        line_color = color if color is not None else self.color
        pen = QPen(line_color, self.line_width)
        if self._line_width is None:
            pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(QBrush())
        painter.drawPath(self._gear_path)

        # Draw dashed pitch radius circle if selected
        if self._is_singly_selected():
            v = self._pitch_radius_point - self._center
            pitch_radius = math.hypot(v.x(), v.y())
            self.draw_construction_circle(painter, QPointF(0,0), pitch_radius)
            self.draw_center_cross(painter, QPointF(0,0))
            self.draw_diameter_arrow(painter, QPointF(0,0), 45, pitch_radius*2, 0.05)

        painter.restore()

    def paint_item(self, painter, option, widget=None):
        self.paint_item_with_color(painter, option, widget, self._color)

    def _create_controls_impl(self):
        self._center_cp = SquareControlPoint(
            cad_item=self,
            setter=self._set_center
        )
        self._radius_cp = ControlPoint(
            cad_item=self,
            setter=self._set_pitch_radius_point
        )
        self._pitch_diameter_datum = ControlDatum(
            setter=self._set_pitch_diameter,
            prefix="D",
            cad_item=self,
            label="Pitch Circle Diameter",
            angle=45,
            pixel_offset=10
        )
        self._pressure_angle_datum = ControlDatum(
            setter=self._set_pressure_angle,
            prefix="PA: ",
            suffix="°",
            cad_item=self,
            label="Pressure Angle",
            precision_override=1,
            angle=135,
            pixel_offset=10,
            is_length=False
        )
        self._tooth_count_datum = ControlDatum(
            setter=self._set_tooth_count,
            prefix="T: ",
            cad_item=self,
            label="Tooth Count",
            precision_override=0,
            angle=-45,
            pixel_offset=10,
            is_length=False,
            min_value=5
        )
        
        # Create both datums but set visibility based on metric setting
        if self.is_metric():
            self._pitch_datum = ControlDatum(
                setter=self._set_module,
                prefix="m: ",
                cad_item=self,
                label="Gear Module",
                angle=-135,
                pixel_offset=10,
                is_length=False
            )
        else:
            self._pitch_datum = ControlDatum(
                setter=self._set_diametral_pitch,
                prefix="DP: ",
                cad_item=self,
                label="Diametral Gear Pitch",
                angle=-135,
                pixel_offset=10,
                is_length=False
            )
        
        self.updateControls()
        
        # Return both datums (visibility controls which one is shown)
        control_points = [
            self._center_cp,
            self._radius_cp,
            self._tooth_count_datum,
            self._pitch_diameter_datum,
            self._pressure_angle_datum,
            self._pitch_datum
        ]
        
        return control_points

    def updateControls(self):
        if self._center_cp:
            self._center_cp.setPos(self._center)
        if self._radius_cp:
            self._radius_cp.setPos(self._pitch_radius_point)
        if self._pitch_diameter_datum:
            pos = self._center + QPointF(
                self.pitch_radius * math.cos(math.radians(45)),
                self.pitch_radius * math.sin(math.radians(45))
            )
            self._pitch_diameter_datum.update_datum(self.pitch_radius*2, pos)
        if self._pressure_angle_datum:
            pos = self._center
            self._pressure_angle_datum.update_datum(self._pressure_angle, pos)
        if self._tooth_count_datum:
            pos = self._center
            self._tooth_count_datum.update_datum(self._tooth_count, pos)
        
        # Update the appropriate datum based on metric setting
        if self._pitch_datum:
            pos = self._center
            if self.is_metric():
                self._pitch_datum.prefix = "m: "
                self._pitch_datum.label = "Gear Module"
                self._pitch_datum.setter = self._set_module
                self._pitch_datum.update_datum(self.module, pos)
            else:
                self._pitch_datum.prefix = "DP: "
                self._pitch_datum.label = "Gear Diametral Pitch"
                self._pitch_datum.setter = self._set_diametral_pitch
                self._pitch_datum.update_datum(self.diametral_pitch, pos)

    def _get_control_point_objects(self):
        cps = []
        if self._center_cp:
            cps.append(self._center_cp)
        if self._radius_cp:
            cps.append(self._radius_cp)
        return cps

    def getControlPoints(self, exclude_cps=None):
        out = []
        if self._center_cp and (exclude_cps is None or self._center_cp not in exclude_cps):
            out.append(self._center)
        if self._radius_cp and (exclude_cps is None or self._radius_cp not in exclude_cps):
            out.append(self._pitch_radius_point)
        return out

    def _set_center(self, new_pos):
        delta = new_pos - self._center
        self._center = QPointF(new_pos)
        self._pitch_radius_point += delta
        self.setPos(self._center)
        self.updateControls()

    def _set_pitch_radius_point(self, new_pos):
        if new_pos != self._pitch_radius_point:
            self._gear_path = None
        self._pitch_radius_point = QPointF(new_pos)
        self._update_gear_path()
        self.updateControls()

    def _set_tooth_count(self, value):
        if value != self._tooth_count:
            self._gear_path = None
        try:
            value = int(round(float(value)))
            if value < 3:
                value = 3
        except Exception:
            value = 12
        self._tooth_count = value
        self._update_gear_path()
        self.updateControls()

    def _set_pitch_diameter(self, value):
        try:
            value = float(value)
            if value <= 0:
                value = 1.0
        except Exception:
            value = 1.0
        self.pitch_radius = value / 2

    @property
    def pitch_radius(self):
        return math.hypot(
            self._pitch_radius_point.x() - self._center.x(),
            self._pitch_radius_point.y() - self._center.y()
        )

    @pitch_radius.setter
    def pitch_radius(self, value):
        if value != self.pitch_radius:
            self._gear_path = None
        r,a = xy_to_polar((
            self._pitch_radius_point.x() - self._center.x(),
            self._pitch_radius_point.y() - self._center.y()
        ))
        newxy = polar_to_xy(value, a)
        self._pitch_radius_point = self._center + QPointF(newxy[0], newxy[1])
        self._update_gear_path()
        self.updateControls()

    @property
    def module(self):
        return self.pitch_radius * 2 * 25.4 / self._tooth_count

    @module.setter
    def module(self, value):
        if value != self.module:
            self._gear_path = None
        self.pitch_radius = value * self._tooth_count / 25.4 / 2
        self._update_gear_path()
        self.updateControls()

    @property
    def pressure_angle(self):
        return self._pressure_angle

    @pressure_angle.setter
    def pressure_angle(self, value):
        if value != self._pressure_angle:
            self._gear_path = None
        self._pressure_angle = value
        self._update_gear_path()
        self.updateControls()

    def _set_pressure_angle(self, value):
        self.pressure_angle = value

    def _set_module(self, value):
        self.module = value

    def _set_diametral_pitch(self, value):
        self.diametral_pitch = value

    def _set_circular_pitch(self, value):
        self.circular_pitch = value

    def refresh_control_datums_for_units(self):
        """Refresh control datums when grid units change."""
        self.updateControls()

    @property
    def diametral_pitch(self):
        return self._tooth_count / (self.pitch_radius * 2)

    @diametral_pitch.setter
    def diametral_pitch(self, value):
        if value != self.diametral_pitch:
            self._gear_path = None
        self.pitch_radius = self._tooth_count / (value * 2)
        self._update_gear_path()
        self.updateControls()

    @property
    def circular_pitch(self):
        return self.pitch_radius*2*math.pi/self._tooth_count

    @circular_pitch.setter
    def circular_pitch(self, value):
        if value != self.circular_pitch:
            self._gear_path = None
        self.pitch_radius = value * self._tooth_count / (2*math.pi)
        self._update_gear_path()
        self.updateControls()

    def moveBy(self, dx, dy):
        if dx == 0 and dy == 0:
            return
        self.prepareGeometryChange()
        self._center += QPointF(dx, dy)
        self._pitch_radius_point += QPointF(dx, dy)
        self._update_gear_path()
        self.updateControls()

    def get_original_gear_points(self):
        """Get the original gear points before Bezier optimization for debugging."""
        v = self._pitch_radius_point - self._center
        pitch_radius = math.hypot(v.x(), v.y())
        mod = pitch_radius*2/self._tooth_count
        
        return _generate_gear_path(
            num_teeth=self._tooth_count,
            mod=mod,
            pressure_angle=self._pressure_angle,
            points_per_involute=5
        )

