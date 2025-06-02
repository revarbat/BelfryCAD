"""
Geometry utility functions for pyTkCAD.

This module provides geometric computation functions including:
- Point and path operations
- Line and polygon intersections
- Boolean operations on polygons
- Circle and arc operations
- Bounding box calculations

Translated from geometry.tcl
"""

import math
from typing import List, Tuple, Optional
import pyclipper


# Constants
PI = math.pi
DEG_TO_RAD = PI / 180.0
RAD_TO_DEG = 180.0 / PI
EPSILON = 1e-6


def sign(x: float) -> int:
    """Return the sign of a number."""
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0


def frac(x: float) -> float:
    """Return the fractional part of a number."""
    return x - math.floor(x)


def normang(angle: float) -> float:
    """Normalize angle to range [0, 2*pi)."""
    while angle >= 2 * PI:
        angle -= 2 * PI
    while angle < 0:
        angle += 2 * PI
    return angle


def geometry_path_is_closed(path: List[float]) -> bool:
    """Check if a path is closed (first and last points are the same)."""
    if len(path) < 4:
        return False

    return (abs(path[0] - path[-2]) < EPSILON and
            abs(path[1] - path[-1]) < EPSILON)


def geometry_points_are_collinear(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    x3: float,
    y3: float,
    tol: float = EPSILON
) -> bool:
    """Test if three points are collinear within tolerance."""
    # Calculate cross product to test collinearity
    cross_product = abs((x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1))
    return cross_product < tol


def geometry_points_are_in_box(x1: float, y1: float, x2: float, y2: float,
                               points: List[float]) -> bool:
    """Check if points are within the bounding box defined by corners."""
    minx = min(x1, x2)
    maxx = max(x1, x2)
    miny = min(y1, y2)
    maxy = max(y1, y2)

    for i in range(0, len(points), 2):
        x, y = points[i], points[i + 1]
        if not (minx <= x <= maxx and miny <= y <= maxy):
            return False
    return True


def geometry_boxes_intersect(x1: float, y1: float, x2: float, y2: float,
                             x3: float, y3: float, x4: float,
                             y4: float) -> bool:
    """Test if two bounding boxes intersect."""
    minx1, maxx1 = min(x1, x2), max(x1, x2)
    miny1, maxy1 = min(y1, y2), max(y1, y2)
    minx2, maxx2 = min(x3, x4), max(x3, x4)
    miny2, maxy2 = min(y3, y4), max(y3, y4)

    return not (maxx1 < minx2 or maxx2 < minx1 or
                maxy1 < miny2 or maxy2 < miny1)


def geometry_points_are_on_line_segment(x1: float, y1: float, x2: float,
                                        y2: float, points: List[float],
                                        tol: float = EPSILON) -> bool:
    """Check if points lie on a line segment within tolerance."""
    for i in range(0, len(points), 2):
        x, y = points[i], points[i + 1]

        # Check if point is collinear with line segment
        if not geometry_points_are_collinear(x1, y1, x2, y2, x, y, tol):
            return False

        # Check if point is within the line segment bounds
        if not geometry_points_are_in_box(x1, y1, x2, y2, [x, y]):
            return False

    return True


def geometry_polyline_add_vertex(polyline: List[float], x: float, y: float,
                                 tol: float = EPSILON) -> List[float]:
    """Add a vertex to a polyline, avoiding duplicates within tolerance."""
    if len(polyline) >= 2:
        last_x, last_y = polyline[-2], polyline[-1]
        if abs(x - last_x) < tol and abs(y - last_y) < tol:
            return polyline[:]  # Don't add duplicate point

    result = polyline[:]
    result.extend([x, y])
    return result


def geometry_find_polyline_line_segment_intersections(
    polyline: List[float],
    x1: float, y1: float,
    x2: float, y2: float
) -> List[float]:
    """Find intersections between a polyline and a line segment."""
    intersections = []

    if len(polyline) < 4:
        return intersections

    for i in range(0, len(polyline) - 2, 2):
        px1, py1 = polyline[i], polyline[i + 1]
        px2, py2 = polyline[i + 2], polyline[i + 3]

        # Find intersection between line segments
        intersection = _line_segment_intersection(px1, py1, px2, py2,
                                                  x1, y1, x2, y2)
        if intersection:
            intersections.extend(intersection)

    return intersections


def _line_segment_intersection(x1: float, y1: float, x2: float, y2: float,
                               x3: float, y3: float, x4: float,
                               y4: float) -> Optional[List[float]]:
    """Find intersection point between two line segments."""
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

    if abs(denom) < EPSILON:
        return None  # Lines are parallel

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

    if 0 <= t <= 1 and 0 <= u <= 1:
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        return [x, y]

    return None


def geometry_polyline_strip_duplicates(polyline: List[float],
                                       tol: float = EPSILON) -> List[float]:
    """Remove duplicate consecutive points from a polyline."""
    if len(polyline) < 4:
        return polyline[:]

    result = [polyline[0], polyline[1]]

    for i in range(2, len(polyline), 2):
        x, y = polyline[i], polyline[i + 1]
        last_x, last_y = result[-2], result[-1]

        if abs(x - last_x) >= tol or abs(y - last_y) >= tol:
            result.extend([x, y])

    return result


def geometry_find_polylines_intersections(polyline1: List[float],
                                          polyline2: List[float]
                                          ) -> List[float]:
    """Find all intersections between two polylines."""
    intersections = []

    if len(polyline1) < 4 or len(polyline2) < 4:
        return intersections

    for i in range(0, len(polyline1) - 2, 2):
        x1, y1 = polyline1[i], polyline1[i + 1]
        x2, y2 = polyline1[i + 2], polyline1[i + 3]

        for j in range(0, len(polyline2) - 2, 2):
            x3, y3 = polyline2[j], polyline2[j + 1]
            x4, y4 = polyline2[j + 2], polyline2[j + 3]

            intersection = _line_segment_intersection(x1, y1, x2, y2,
                                                      x3, y3, x4, y4)
            if intersection:
                intersections.extend(intersection)

    return intersections


def geometry_closest_point_on_arc(cx: float, cy: float, radius: float,
                                  start_angle: float, end_angle: float,
                                  px: float, py: float) -> Tuple[float, float]:
    """Find the closest point on an arc to a given point."""
    # Convert point to polar coordinates relative to arc center
    dx = px - cx
    dy = py - cy
    distance = math.sqrt(dx * dx + dy * dy)

    if distance < EPSILON:
        # Point is at center, return any point on arc
        return (cx + radius * math.cos(start_angle),
                cy + radius * math.sin(start_angle))

    angle = math.atan2(dy, dx)
    angle = normang(angle)
    start_angle = normang(start_angle)
    end_angle = normang(end_angle)

    # Check if angle is within arc range
    if start_angle <= end_angle:
        if start_angle <= angle <= end_angle:
            closest_angle = angle
        else:
            # Choose closer endpoint
            d1 = abs(angle - start_angle)
            d2 = abs(angle - end_angle)
            closest_angle = start_angle if d1 < d2 else end_angle
    else:
        # Arc crosses 0 angle
        if angle >= start_angle or angle <= end_angle:
            closest_angle = angle
        else:
            d1 = abs(angle - start_angle)
            d2 = abs(angle - end_angle)
            closest_angle = start_angle if d1 < d2 else end_angle

    return (cx + radius * math.cos(closest_angle),
            cy + radius * math.sin(closest_angle))


def geometry_join_polylines(polylines: List[List[float]],
                            tol: float = EPSILON) -> List[List[float]]:
    """Join polylines that share endpoints within tolerance."""
    if not polylines:
        return []

    result = []
    remaining = [p[:] for p in polylines]  # Copy all polylines

    while remaining:
        current = remaining.pop(0)
        changed = True

        while changed:
            changed = False
            for i, candidate in enumerate(remaining):
                # Check if we can join at the end of current
                if (abs(current[-2] - candidate[0]) < tol and
                        abs(current[-1] - candidate[1]) < tol):
                    current.extend(candidate[2:])
                    remaining.pop(i)
                    changed = True
                    break
                # Check if we can join at the beginning of current
                elif (abs(current[0] - candidate[-2]) < tol and
                      abs(current[1] - candidate[-1]) < tol):
                    current = candidate[:-2] + current
                    remaining.pop(i)
                    changed = True
                    break
                # Check reverse connections
                elif (abs(current[-2] - candidate[-2]) < tol and
                      abs(current[-1] - candidate[-1]) < tol):
                    # Reverse candidate and join
                    reversed_candidate = []
                    for j in range(len(candidate) - 2, -1, -2):
                        reversed_candidate.extend([candidate[j],
                                                  candidate[j + 1]])
                    current.extend(reversed_candidate[2:])
                    remaining.pop(i)
                    changed = True
                    break
                elif (abs(current[0] - candidate[0]) < tol and
                      abs(current[1] - candidate[1]) < tol):
                    # Reverse candidate and join at beginning
                    reversed_candidate = []
                    for j in range(len(candidate) - 2, -1, -2):
                        reversed_candidate.extend([candidate[j],
                                                  candidate[j + 1]])
                    current = reversed_candidate[:-2] + current
                    remaining.pop(i)
                    changed = True
                    break

        result.append(current)

    return result


def geometry_polygon_circumscribed_by_polygon(inner_polygon: List[float],
                                              outer_polygon: List[float]
                                              ) -> bool:
    """Test if one polygon is completely contained within another."""
    if len(inner_polygon) < 6 or len(outer_polygon) < 6:
        return False

    # Check if all vertices of inner polygon are inside outer polygon
    for i in range(0, len(inner_polygon), 2):
        x, y = inner_polygon[i], inner_polygon[i + 1]
        if not _point_in_polygon(x, y, outer_polygon):
            return False

    return True


def _point_in_polygon(x: float, y: float, polygon: List[float]) -> bool:
    """Test if a point is inside a polygon using ray casting algorithm."""
    if len(polygon) < 6:
        return False

    inside = False
    j = len(polygon) - 2

    for i in range(0, len(polygon), 2):
        xi, yi = polygon[i], polygon[i + 1]
        xj, yj = polygon[j], polygon[j + 1]

        if (((yi > y) != (yj > y)) and
                (x < (xj - xi) * (y - yi) / (yj - yi) + xi)):
            inside = not inside

        j = i

    return inside


def coords_to_points(coords):
    """Convert flat coordinate list to list of point tuples."""
    return [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]


def points_to_coords(points):
    """Convert list of point tuples to flat coordinate list."""
    coords = []
    for point in points:
        coords.extend([point[0], point[1]])
    return coords


def geometry_polygons_union(poly1: List[float],
                            poly2: List[float]) -> List[List[float]]:
    """Compute the union of two polygons using pyclipper."""
    # Convert input polygons
    subject = [coords_to_points(poly1)]
    clip = [coords_to_points(poly2)]

    # Perform union operation
    pc = pyclipper.Pyclipper()
    pc.AddPaths(subject, pyclipper.PT_SUBJECT, True)
    pc.AddPaths(clip, pyclipper.PT_CLIP, True)

    solution = pc.Execute(pyclipper.CT_UNION, pyclipper.PFT_EVENODD,
                          pyclipper.PFT_EVENODD)

    # Convert result back to flat coordinate lists
    result = []
    for polygon in solution:
        if len(polygon) >= 3:  # Valid polygon needs at least 3 points
            result.append(points_to_coords(polygon))

    return result


def geometry_polygons_diff(poly1: List[float],
                           poly2: List[float]) -> List[List[float]]:
    """Compute the difference of two polygons (poly1 - poly2)."""
    # Convert input polygons
    subject = [coords_to_points(poly1)]
    clip = [coords_to_points(poly2)]

    # Perform difference operation
    pc = pyclipper.Pyclipper()
    pc.AddPaths(subject, pyclipper.PT_SUBJECT, True)
    pc.AddPaths(clip, pyclipper.PT_CLIP, True)

    solution = pc.Execute(pyclipper.CT_DIFFERENCE, pyclipper.PFT_EVENODD,
                          pyclipper.PFT_EVENODD)

    # Convert result back to flat coordinate lists
    result = []
    for polygon in solution:
        if len(polygon) >= 3:  # Valid polygon needs at least 3 points
            result.append(points_to_coords(polygon))

    return result


def geometry_polygons_intersection(poly1: List[float],
                                   poly2: List[float]) -> List[List[float]]:
    """Compute the intersection of two polygons using pyclipper."""
    # Convert input polygons
    subject = [coords_to_points(poly1)]
    clip = [coords_to_points(poly2)]

    # Perform intersection operation
    pc = pyclipper.Pyclipper()
    pc.AddPaths(subject, pyclipper.PT_SUBJECT, True)
    pc.AddPaths(clip, pyclipper.PT_CLIP, True)

    solution = pc.Execute(pyclipper.CT_INTERSECTION, pyclipper.PFT_EVENODD,
                          pyclipper.PFT_EVENODD)

    # Convert result back to flat coordinate lists
    result = []
    for polygon in solution:
        if len(polygon) >= 3:  # Valid polygon needs at least 3 points
            result.append(points_to_coords(polygon))

    return result


def geometry_find_closest_point_in_list(x: float, y: float,
                                        points: List[float]
                                        ) -> Tuple[int, float]:
    """Find the index and distance of the closest point in a list."""
    if len(points) < 2:
        return -1, float('inf')

    min_dist = float('inf')
    min_index = -1

    for i in range(0, len(points), 2):
        px, py = points[i], points[i + 1]
        dist = math.sqrt((x - px) ** 2 + (y - py) ** 2)

        if dist < min_dist:
            min_dist = dist
            min_index = i // 2

    return min_index, min_dist


def geometry_find_circles_intersections(cx1: float, cy1: float, r1: float,
                                        cx2: float, cy2: float,
                                        r2: float) -> List[float]:
    """Find intersection points between two circles."""
    # Distance between centers
    d = math.sqrt((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2)

    # Check for no intersection cases
    if d > r1 + r2 or d < abs(r1 - r2) or d == 0:
        return []

    # Check for single intersection (circles are tangent)
    if (abs(d - (r1 + r2)) < EPSILON or
            abs(d - abs(r1 - r2)) < EPSILON):
        # Single intersection point
        a = r1
        x = cx1 + a * (cx2 - cx1) / d
        y = cy1 + a * (cy2 - cy1) / d
        return [x, y]

    # Two intersection points
    a = (r1 * r1 - r2 * r2 + d * d) / (2 * d)
    h = math.sqrt(r1 * r1 - a * a)

    # Point on line between centers
    px = cx1 + a * (cx2 - cx1) / d
    py = cy1 + a * (cy2 - cy1) / d

    # Two intersection points
    x1 = px + h * (cy2 - cy1) / d
    y1 = py - h * (cx2 - cx1) / d
    x2 = px - h * (cy2 - cy1) / d
    y2 = py + h * (cx2 - cx1) / d

    return [x1, y1, x2, y2]


def geometry_find_circle_polyline_intersections(cx: float, cy: float,
                                                radius: float,
                                                polyline: List[float]
                                                ) -> List[float]:
    """Find intersections between a circle and a polyline."""
    intersections = []

    if len(polyline) < 4:
        return intersections

    for i in range(0, len(polyline) - 2, 2):
        x0, y0 = polyline[i], polyline[i + 1]
        x1, y1 = polyline[i + 2], polyline[i + 3]

        points = geometry_find_circle_lineseg_intersections(cx, cy, radius,
                                                            x0, y0, x1, y1)
        intersections.extend(points)

    return intersections


def geometry_find_circle_lineseg_intersections(cx: float, cy: float,
                                               radius: float, x0: float,
                                               y0: float, x1: float,
                                               y1: float) -> List[float]:
    """Find intersections between a circle and a line segment."""
    intersections = []

    # Handle vertical line case
    if abs(x1 - x0) < EPSILON:
        if abs(cx - x0) > radius:
            return intersections
        elif abs(cx - x0) == radius:
            if geometry_points_are_in_box(x0, y0, x1, y1, [x0, cy]):
                intersections.extend([x0, cy])
            return intersections

        # Two intersections for vertical line
        a = x0 - cx
        b = math.sqrt(radius * radius - a * a)
        ny0 = cy + b
        ny1 = cy - b

        if geometry_points_are_in_box(x0, y0, x1, y1, [x0, ny0]):
            intersections.extend([x0, ny0])
        if geometry_points_are_in_box(x0, y0, x1, y1, [x0, ny1]):
            intersections.extend([x0, ny1])

        return intersections

    # Non-vertical line
    dx = x1 - x0
    dy = y1 - y0
    dr = math.sqrt(dx * dx + dy * dy)

    # Translate line to origin
    lx0 = x0 - cx
    ly0 = y0 - cy
    lx1 = x1 - cx
    ly1 = y1 - cy

    d = lx0 * ly1 - lx1 * ly0
    sgn = -1 if dy < 0 else 1

    h = radius * radius * dr * dr - d * d

    if h < 0:
        return intersections

    sqrt_h = math.sqrt(h)
    dr_sq = dr * dr

    nx0 = cx + (d * dy + sgn * dx * sqrt_h) / dr_sq
    ny0 = cy + (-d * dx + abs(dy) * sqrt_h) / dr_sq
    nx1 = cx + (d * dy - sgn * dx * sqrt_h) / dr_sq
    ny1 = cy + (-d * dx - abs(dy) * sqrt_h) / dr_sq

    if geometry_points_are_in_box(x0, y0, x1, y1, [nx0, ny0]):
        intersections.extend([nx0, ny0])
    if h > 0 and geometry_points_are_in_box(x0, y0, x1, y1, [nx1, ny1]):
        intersections.extend([nx1, ny1])

    return intersections


def geometry_pointlist_bbox(points: List[float]) -> List[float]:
    """Calculate bounding box of a list of points."""
    if len(points) < 2:
        return [0, 0, 0, 0]

    minx = maxx = points[0]
    miny = maxy = points[1]

    for i in range(2, len(points), 2):
        x, y = points[i], points[i + 1]
        minx = min(minx, x)
        maxx = max(maxx, x)
        miny = min(miny, y)
        maxy = max(maxy, y)

    return [minx, miny, maxx, maxy]


def geometry_line_offset(x0: float, y0: float, x1: float, y1: float,
                         offset: float) -> List[float]:
    """Offset a line segment. Positive offset is to the left."""
    angle = math.atan2(y1 - y0, x1 - x0)
    perp_angle = angle + PI / 2.0

    nx0 = x0 + offset * math.cos(perp_angle)
    ny0 = y0 + offset * math.sin(perp_angle)
    nx1 = x1 + offset * math.cos(perp_angle)
    ny1 = y1 + offset * math.sin(perp_angle)

    return [nx0, ny0, nx1, ny1]


def geometry_line_rot_point(x0: float, y0: float, x1: float, y1: float,
                            radius: float, offset_angle: float) -> List[float]:
    """Get point at radius distance from (x0,y0) in direction offset."""
    angle = math.atan2(y1 - y0, x1 - x0)
    x2 = radius * math.cos(angle + offset_angle * DEG_TO_RAD) + x0
    y2 = radius * math.sin(angle + offset_angle * DEG_TO_RAD) + y0

    return [x2, y2]


# Utility functions for compatibility with CAD operations
def distance_point_to_point(x1: float, y1: float, x2: float,
                            y2: float) -> float:
    """Calculate distance between two points."""
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def distance_point_to_line(px: float, py: float, x1: float, y1: float,
                           x2: float, y2: float) -> float:
    """Calculate distance from a point to a line."""
    # Line equation: ax + by + c = 0
    a = y2 - y1
    b = x1 - x2
    c = x2 * y1 - x1 * y2

    # Distance formula
    return abs(a * px + b * py + c) / math.sqrt(a * a + b * b)


def angle_between_points(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate angle from point 1 to point 2 in radians."""
    return math.atan2(y2 - y1, x2 - x1)


def rotate_point(x: float, y: float, cx: float, cy: float,
                 angle: float) -> Tuple[float, float]:
    """Rotate a point around a center point by angle (in radians)."""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    # Translate to origin
    dx = x - cx
    dy = y - cy

    # Rotate
    new_x = dx * cos_a - dy * sin_a
    new_y = dx * sin_a + dy * cos_a

    # Translate back
    return (new_x + cx, new_y + cy)
