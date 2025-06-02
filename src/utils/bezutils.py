"""
Bezier curve utility functions for pyTkCAD.

This module provides comprehensive Bezier curve operations including:
- Cubic and quadratic Bezier curve operations
- Curve splitting, merging, and simplification
- Arc to Bezier conversion
- Point projection and distance calculations
- Curve breaking and nearest point finding

Translated from bezutils.tcl
"""

import math
from typing import List, Tuple, Optional
from .geometry import (
    geometry_points_are_collinear,
    PI, EPSILON
)


def bezutil_append_bezier_arc(coords: List[float], cx: float, cy: float,
                              radiusx: float, radiusy: float,
                              start: float, extent: float) -> None:
    """
    Append a Bezier approximation of an elliptical arc to coordinates list.

    Args:
        coords: List to append bezier coordinates to
        cx, cy: Center of the ellipse
        radiusx, radiusy: Radii of the ellipse
        start: Start angle in degrees
        extent: Angular extent in degrees
    """
    arcsliceangle = 15.0

    start = float(start)
    extent = float(extent)

    if extent == 0.0:
        return

    arcslice = extent / math.ceil(abs(extent / arcsliceangle))
    arcrdn = 0.5 * arcslice * PI / 180.0

    # Formula for calculating the "magic number" bezier distance
    # for approximating an elliptical curve closely:
    bezmagic = abs((4.0/3.0) * ((1.0 - math.cos(arcrdn)) /
                                math.sin(arcrdn)))

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


def bezutil_append_line_arc(coords: List[float], cx: float, cy: float,
                            radiusx: float, radiusy: float,
                            start: float, extent: float) -> None:
    """
    Append a line approximation of an elliptical arc to coordinates list.

    Args:
        coords: List to append line coordinates to
        cx, cy: Center of the ellipse
        radiusx, radiusy: Radii of the ellipse
        start: Start angle in degrees
        extent: Angular extent in degrees
    """
    arcsliceangle = 0.5

    start = float(start)
    extent = float(extent)

    if extent == 0.0:
        return

    arcslice = extent / math.ceil(abs(extent / arcsliceangle))

    done = False
    i = start

    while not done:
        radians = i * PI / 180.0
        tx = cx + radiusx * math.cos(radians)
        ty = cy + radiusy * math.sin(radians)
        coords.extend([tx, ty])

        if abs(i - (start + extent)) < 1e-6:
            done = True

        i += arcslice


def bezutil_segment_is_collinear(x0: float, y0: float, x1: float, y1: float,
                                 x2: float, y2: float,
                                 tolerance: float = 1e-4) -> bool:
    """Check if three points forming a segment are collinear."""
    return geometry_points_are_collinear(x0, y0, x1, y1, x2, y2, tolerance)


def bezutil_bezier_split_long_segments(path: List[float],
                                       maxlen: float) -> List[float]:
    """Split long Bezier segments recursively until shorter than maxlen."""
    if len(path) < 8:
        return path[:]

    nupath = []
    x0, y0 = path[0], path[1]
    nupath.extend([x0, y0])

    for i in range(2, len(path), 6):
        if i + 5 >= len(path):
            break
        x1, y1, x2, y2, x3, y3 = path[i:i+6]

        if math.hypot(x3 - x0, y3 - y0) <= maxlen:
            nupath.extend([x1, y1, x2, y2, x3, y3])
        else:
            nusegs = bezutil_bezier_segment_split(0.5, x0, y0, x1, y1,
                                                  x2, y2, x3, y3)
            nusegs = bezutil_bezier_split_long_segments(nusegs, maxlen)
            nupath.extend(nusegs[2:])

        x0, y0 = x3, y3

    return nupath


def bezutil_bezier_segment_split(t: float, x0: float, y0: float,
                                 x1: float, y1: float, x2: float, y2: float,
                                 x3: float, y3: float) -> List[float]:
    """Split a cubic Bezier segment at parameter t."""
    u = 1.0 - t

    mx01 = u * x0 + t * x1
    my01 = u * y0 + t * y1
    mx12 = u * x1 + t * x2
    my12 = u * y1 + t * y2
    mx23 = u * x2 + t * x3
    my23 = u * y2 + t * y3
    mx012 = u * mx01 + t * mx12
    my012 = u * my01 + t * my12
    mx123 = u * mx12 + t * mx23
    my123 = u * my12 + t * my23
    mx0123 = u * mx012 + t * mx123
    my0123 = u * my012 + t * my123

    return [x0, y0, mx01, my01, mx012, my012, mx0123, my0123,
            mx123, my123, mx23, my23, x3, y3]


def bezutil_bezier_segment_length(x0: float, y0: float, x1: float, y1: float,
                                  x2: float, y2: float,
                                  x3: float, y3: float) -> float:
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


def bezutil_bezier_length(coords: List[float]) -> float:
    """Calculate approximate length of a cubic Bezier curve."""
    if len(coords) < 8:
        return 0.0

    length = 0.0
    x0, y0 = coords[0], coords[1]

    for i in range(2, len(coords), 6):
        if i + 5 >= len(coords):
            break
        x1, y1, x2, y2, x3, y3 = coords[i:i+6]
        seglen = bezutil_bezier_segment_length(x0, y0, x1, y1, x2, y2, x3, y3)
        length += seglen
        x0, y0 = x3, y3

    return length


def bezutil_bezier_segment_point(t: float, x0: float, y0: float,
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


def bezutil_bezier_segment_partial_pos(x0: float, y0: float, x1: float,
                                       y1: float, x2: float, y2: float,
                                       x3: float, y3: float, part: float,
                                       tolerance: float = 1e-3
                                       ) -> Tuple[float, float, float]:
    """Find position at a given partial distance along a Bezier segment."""
    inc = 1.0 / 20.0

    # Convert to standard form
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
        seglen = math.hypot(my - oy, mx - ox)

        if length + seglen >= part:
            if inc < tolerance:
                break
            t -= inc
            inc /= 2.0
            continue

        length += seglen
        ox, oy = mx, my
        t += inc

    angle = math.atan2(my - oy, mx - ox)
    return (ox, oy, angle)


def bezutil_bezier_segment_mindist_pos(px: float, py: float, x0: float,
                                       y0: float, x1: float, y1: float,
                                       x2: float, y2: float, x3: float,
                                       y3: float, closeenough: float = 1e-2,
                                       tolerance: float = 1e-3
                                       ) -> Optional[float]:
    """Find the t parameter of closest point on Bezier segment to point."""
    # Convert to standard form
    xc = 3.0 * (x1 - x0)
    xb = 3.0 * (x2 - x1) - xc
    xa = x3 - x0 - xc - xb

    yc = 3.0 * (y1 - y0)
    yb = 3.0 * (y2 - y1) - yc
    ya = y3 - y0 - yc - yb

    inc = 0.05
    stepmult = 10.0
    allminima = [0.5]

    while True:
        minima = []
        minimadists = []

        for min_val in allminima:
            start = max(0.0, min_val - inc * stepmult)
            end = min(1.0, min_val + inc * stepmult)

            trend = -1
            prevdist = 1e17
            t = start
            prevmx = prevmy = 0

            while True:
                mx = ((xa * t + xb) * t + xc) * t + x0
                my = ((ya * t + yb) * t + yc) * t + y0
                dist = math.hypot(my - py, mx - px)

                if dist > prevdist:
                    if trend == -1:
                        minima.append(t - inc)
                        minimadists.append(dist)
                    trend = 1
                else:
                    trend = -1

                if abs(t - end) < 1e-10:
                    if dist < prevdist:
                        minima.append(t)
                        minimadists.append(dist)
                    break

                prevdist = dist
                prevmx, prevmy = mx, my
                t += inc

        allminima = minima
        stepmult = 2.0
        inc /= 2.0

        if (len(minima) > 0 and
                math.hypot(my - prevmy, mx - prevmx) < tolerance):
            break

    closest = None
    mindist = closeenough

    for min_val, dist in zip(minima, minimadists):
        if dist < mindist:
            closest = min_val
            mindist = dist

    return closest


def bezutil_bezier_mindist_segpos(px: float, py: float, bezpath: List[float],
                                  closeenough: float = 1e-2,
                                  tolerance: float = 1e-4
                                  ) -> Optional[Tuple[int, float]]:
    """Find segment index and t parameter of closest point on Bezier curve."""
    if len(bezpath) < 8:
        return None

    seg = 0
    x0, y0 = bezpath[0], bezpath[1]

    for i in range(2, len(bezpath), 6):
        if i + 5 >= len(bezpath):
            break
        x1, y1, x2, y2, x3, y3 = bezpath[i:i+6]

        closest = bezutil_bezier_segment_mindist_pos(
            px, py, x0, y0, x1, y1, x2, y2, x3, y3, closeenough, tolerance
        )
        if closest is not None:
            return (seg, closest)

        x0, y0 = x3, y3
        seg += 1

    return None


def bezutil_bezier_segment_nearest_point(px: float, py: float, x0: float,
                                         y0: float, x1: float, y1: float,
                                         x2: float, y2: float, x3: float,
                                         y3: float, closeenough: float = 1e-2,
                                         tolerance: float = 1e-4
                                         ) -> Optional[Tuple[float, float]]:
    """Find the nearest point on a Bezier segment to a given point."""
    t = bezutil_bezier_segment_mindist_pos(
        px, py, x0, y0, x1, y1, x2, y2, x3, y3, closeenough, tolerance
    )
    if t is None:
        return None

    return bezutil_bezier_segment_point(t, x0, y0, x1, y1, x2, y2, x3, y3)


def bezutil_bezier_nearest_point(px: float, py: float, coords: List[float],
                                 closeenough: float = 1e-2,
                                 tolerance: float = 1e-4
                                 ) -> Optional[Tuple[float, float]]:
    """Find the nearest point on a Bezier curve to a given point."""
    ret = bezutil_bezier_mindist_segpos(px, py, coords, closeenough, tolerance)
    if ret is None:
        return None

    seg, t = ret
    pos1 = seg * 6
    pos2 = pos1 + 8

    if pos2 > len(coords):
        return None

    x0, y0, x1, y1, x2, y2, x3, y3 = coords[pos1:pos2]
    return bezutil_bezier_segment_point(t, x0, y0, x1, y1, x2, y2, x3, y3)


def bezutil_bezier_segment_split_near(px: float, py: float, x0: float,
                                      y0: float, x1: float, y1: float,
                                      x2: float, y2: float, x3: float,
                                      y3: float, closeenough: float = 1e-2,
                                      tolerance: float = 1e-3) -> List[float]:
    """Split a Bezier segment at the point closest to a given point."""
    closest = bezutil_bezier_segment_mindist_pos(
        px, py, x0, y0, x1, y1, x2, y2, x3, y3, closeenough, tolerance
    )
    if closest is not None:
        return bezutil_bezier_segment_split(closest, x0, y0, x1, y1,
                                            x2, y2, x3, y3)

    return [x0, y0, x1, y1, x2, y2, x3, y3]


def bezutil_bezier_split_near(px: float, py: float, coords: List[float],
                              closeenough: float = 1e-2,
                              tolerance: float = 1e-3) -> List[float]:
    """Split a Bezier curve at the point closest to a given point."""
    if len(coords) < 8:
        return coords[:]

    outcoords = []
    x0, y0 = coords[0], coords[1]
    outcoords.extend([x0, y0])

    for i in range(2, len(coords), 6):
        if i + 5 >= len(coords):
            break
        x1, y1, x2, y2, x3, y3 = coords[i:i+6]

        if abs(x3 - px) + abs(y3 - py) <= tolerance:
            outcoords.extend([x1, y1, x2, y2, x3, y3])
        else:
            split_result = bezutil_bezier_segment_split_near(
                px, py, x0, y0, x1, y1, x2, y2, x3, y3, closeenough,
                tolerance
            )
            outcoords.extend(split_result[2:])

        x0, y0 = x3, y3

    return outcoords


def bezutil_bezier_segment_break_near(px: float, py: float, x0: float,
                                      y0: float, x1: float, y1: float,
                                      x2: float, y2: float, x3: float,
                                      y3: float, closeenough: float = 1e-2,
                                      tolerance: float = 1e-3
                                      ) -> List[List[float]]:
    """Break a Bezier segment at the point closest to a given point."""
    closest = bezutil_bezier_segment_mindist_pos(
        px, py, x0, y0, x1, y1, x2, y2, x3, y3, closeenough, tolerance
    )
    if closest is not None:
        points = bezutil_bezier_segment_split(closest, x0, y0, x1, y1,
                                              x2, y2, x3, y3)
        # points = [x0, y0, x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, x6, y6]
        bez1 = points[0:8]   # First segment
        bez2 = points[6:14]  # Second segment
        return [bez1, bez2]

    bez1 = [x0, y0, x1, y1, x2, y2, x3, y3]
    return [bez1]


def bezutil_bezier_break_near(px: float, py: float, coords: List[float],
                              closeenough: float = 1e-2,
                              tolerance: float = 1e-3) -> List[List[float]]:
    """Break a Bezier curve at the point closest to a given point."""
    if len(coords) < 8:
        return [coords[:]] if len(coords) >= 2 else []

    outbezs = []
    outcoords = []
    x0, y0 = coords[0], coords[1]
    outcoords.extend([x0, y0])

    for i in range(2, len(coords), 6):
        if i + 5 >= len(coords):
            break
        x1, y1, x2, y2, x3, y3 = coords[i:i+6]

        if abs(x3 - px) + abs(y3 - py) <= tolerance:
            outcoords.extend([x1, y1, x2, y2, x3, y3])
            outbezs.append(outcoords[:])
            outcoords = [x3, y3]
        else:
            bezs = bezutil_bezier_segment_break_near(
                px, py, x0, y0, x1, y1, x2, y2, x3, y3, closeenough,
                tolerance
            )

            if len(bezs) > 0:
                first_bez = bezs[0]
                bx0, by0, bx1, by1, bx2, by2, bx3, by3 = first_bez

                if (abs(bx3 - bx0) + abs(by3 - by0) + abs(bx2 - bx0) +
                    abs(by2 - by0) + abs(bx1 - bx0) + abs(by1 - by0) >
                        tolerance):
                    outcoords.extend([bx1, by1, bx2, by2, bx3, by3])

                if len(bezs) > 1:
                    second_bez = bezs[1]
                    sx0, sy0, sx1, sy1, sx2, sy2, sx3, sy3 = second_bez

                    if (abs(sx3 - sx0) + abs(sy3 - sy0) + abs(sx2 - sx0) +
                        abs(sy2 - sy0) + abs(sx1 - sx0) + abs(sy1 - sy0) >
                            tolerance):
                        if len(outcoords) > 2:
                            outbezs.append(outcoords[:])
                        outcoords = second_bez[:]
                    else:
                        if len(outcoords) > 2:
                            outcoords = outcoords[:-2]
                            outcoords.extend([sx3, sy3])
                            outbezs.append(outcoords[:])
                        outcoords = [sx3, sy3]

        x0, y0 = x3, y3

    if len(outcoords) > 2:
        outbezs.append(outcoords)

    return outbezs


def bezutil_bezier_smooth(coords: List[float],
                          tolerance: float = 1e-2) -> List[float]:
    """Smooth out nearly straight control point triplets to smooth curves."""
    if len(coords) < 14:  # Need at least two segments
        return coords[:]

    tolerance *= 2.0
    outcoords = []

    # Get first segment
    x0, y0, x1, y1, x2, y2, x3, y3 = coords[0:8]
    outcoords.extend([x0, y0])

    # Process remaining segments
    for i in range(8, len(coords), 6):
        if i + 5 >= len(coords):
            break
        x4, y4, x5, y5, x6, y6 = coords[i:i+6]

        if bezutil_segment_is_collinear(x2, y2, x3, y3, x4, y4, tolerance):
            dx1 = x3 - x2
            dy1 = y3 - y2
            dx2 = x4 - x3
            dy2 = y4 - y3
            ang1 = math.atan2(dy1, dx1)
            ang2 = math.atan2(dy2, dx2)
            dang = ang2 - ang1

            # Normalize angle difference
            if dang > PI:
                dang -= 2 * PI
            elif dang < -PI:
                dang += 2 * PI

            if abs(dang) < PI / 4:  # Less than 45 degrees
                # Straighten it out
                mx1 = (x2 + x3) / 2.0
                my1 = (y2 + y3) / 2.0
                mx2 = (x3 + x4) / 2.0
                my2 = (y3 + y4) / 2.0

                d1 = math.hypot(dy1, dx1)
                d2 = math.hypot(dy2, dx2)

                if d1 + d2 > 1e-9:
                    dx = mx2 - mx1
                    dy = my2 - my1

                    x3 = mx1 + dx * (d1 / (d1 + d2))
                    y3 = my1 + dy * (d1 / (d1 + d2))
                    x2 = x3 + 2.0 * (mx1 - x3)
                    y2 = y3 + 2.0 * (my1 - y3)
                    x4 = x3 + 2.0 * (mx2 - x3)
                    y4 = y3 + 2.0 * (my2 - y3)

        outcoords.extend([x1, y1, x2, y2, x3, y3])
        x0, y0, x1, y1, x2, y2, x3, y3 = x3, y3, x4, y4, x5, y5, x6, y6

    outcoords.extend([x1, y1, x2, y2, x3, y3])
    return outcoords


def bezutil_bezier_simplify(coords: List[float],
                            tolerance: float = 1e-3) -> List[float]:
    """Merge adjacent bezier curves represented closely by one curve."""
    if len(coords) < 14:  # Need at least two segments
        return coords[:]

    outcoords = []
    x0, y0, x1, y1, x2, y2, x3, y3 = coords[0:8]
    outcoords.extend([x0, y0])

    for i in range(8, len(coords), 6):
        if i + 5 >= len(coords):
            break
        x4, y4, x5, y5, x6, y6 = coords[i:i+6]

        # Check for tiny bezier curves and clean them up
        if (math.hypot(x3 - x6, y3 - y6) < tolerance * 2 and
            math.hypot(x4 - x3, y4 - y3) < tolerance and
                math.hypot(x5 - x6, y5 - y6) < tolerance):
            # Second bezier is too tiny, skip it
            x3, y3 = x6, y6
            continue
        elif (math.hypot(x3 - x6, y3 - y6) < tolerance * 8 and
              math.hypot(x4 - x3, y4 - y3) < tolerance * 4 and
              math.hypot(x5 - x6, y5 - y6) < tolerance * 4):
            # Second bezier is small, clean it up into a straight line
            dx = x6 - x3
            dy = y6 - y3
            x4 = x3 + dx * 0.333
            y4 = y3 + dy * 0.333
            x5 = x6 - dx * 0.333
            y5 = y6 - dy * 0.333
        elif (math.hypot(x4 - x3, y4 - y3) < tolerance and
              math.hypot(x5 - x6, y5 - y6) < tolerance):
            # Control lines are really short, clean up into straight line
            dx = x6 - x3
            dy = y6 - y3
            x4 = x3 + dx * 0.333
            y4 = y3 + dy * 0.333
            x5 = x6 - dx * 0.333
            y5 = y6 - dy * 0.333

        # Check if control points are collinear for potential merging
        if bezutil_segment_is_collinear(x2, y2, x3, y3, x4, y4, tolerance):
            dx1 = x3 - x2
            dy1 = y3 - y2
            dx2 = x4 - x2
            dy2 = y4 - y2
            dist1 = math.hypot(dy1, dx1)
            dist2 = math.hypot(dy2, dx2)
            ang1 = math.atan2(dy1, dx1)
            ang2 = math.atan2(y4 - y3, x4 - x3)
            dang = ang2 - ang1

            # Normalize angle
            if dang > PI:
                dang -= 2 * PI
            elif dang < -PI:
                dang += 2 * PI

            if (dist1 > 1e-5 and dist2 > 1e-5 and dist2 > dist1 and
                    abs(dang) < PI / 4):
                t = dist1 / dist2
                u = 1.0 - t

                # Calculate new control points
                dx = x1 - x0
                dy = y1 - y0
                mx1 = x0 + dx / t
                my1 = y0 + dy / t

                dx = x2 - x1
                dy = y2 - y1
                mx2 = x1 + dx / t
                my2 = y1 + dy / t

                dx = x5 - x6
                dy = y5 - y6
                mx3 = x6 + dx / u
                my3 = y6 + dy / u

                mx2b = u * mx1 + t * mx3
                my2b = u * my1 + t * my3

                # Check if midpoint predictions agree
                if math.hypot(my2 - my2b, mx2 - mx2b) <= tolerance * 2:
                    x1, y1, x2, y2, x3, y3 = mx1, my1, mx3, my3, x6, y6
                    continue

        outcoords.extend([x1, y1, x2, y2, x3, y3])
        x0, y0, x1, y1, x2, y2, x3, y3 = x3, y3, x4, y4, x5, y5, x6, y6

    outcoords.extend([x1, y1, x2, y2, x3, y3])
    return outcoords


def bezutil_bezier_split(coords: List[float],
                         tolerance: float = 1e-2) -> List[float]:
    """Split Bezier curves recursively for better approximation."""
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
        if (bezutil_segment_is_collinear(x0, y0, x1, y1, x2, y2, tolerance) and
                bezutil_segment_is_collinear(x1, y1, x2, y2, x3, y3,
                                             tolerance)):
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
            bezsplit1 = bezutil_bezier_split([x0, y0, mx01, my01, mx012,
                                              my012, mx0123, my0123],
                                             tolerance)
            bezsplit2 = bezutil_bezier_split([mx0123, my0123, mx123, my123,
                                              mx23, my23, x3, y3], tolerance)

            outcoords.extend(bezsplit1[2:])
            outcoords.extend(bezsplit2[2:])

        x0, y0 = x3, y3

    return outcoords


def bezutil_append_line_from_bezier(coords: List[float],
                                    bezcoords: List[float]) -> None:
    """Convert a Bezier curve to line segments and append to coords."""
    bezpath = bezutil_bezier_split(bezcoords, 5e-4)
    if len(bezpath) < 2:
        return

    x0, y0 = bezpath[0], bezpath[1]
    coords.extend([x0, y0])

    for i in range(2, len(bezpath), 6):
        if i + 5 >= len(bezpath):
            break
        x1, y1, x2, y2, x3, y3 = bezpath[i:i+6]
        coords.extend([x3, y3])


def bezutil_bezier_from_line(linecoords: List[float]) -> List[float]:
    """Convert line segments to Bezier curves."""
    if len(linecoords) < 4:
        return linecoords[:]

    out = []
    onethird = 1.0 / 3.0
    twothirds = 2.0 / 3.0

    x0, y0 = linecoords[0], linecoords[1]
    out.extend([x0, y0])

    for i in range(2, len(linecoords), 2):
        x3, y3 = linecoords[i], linecoords[i + 1]
        dx = x3 - x0
        dy = y3 - y0
        x1 = x0 + dx * onethird
        y1 = y0 + dy * onethird
        x2 = x0 + dx * twothirds
        y2 = y0 + dy * twothirds
        out.extend([x1, y1, x2, y2, x3, y3])
        x0, y0 = x3, y3

    return out


# Quadratic Bezier functions

def bezutil_quadbezier_split(coords: List[float],
                             tolerance: float = 1e-2) -> List[float]:
    """Split quadratic Bezier curves recursively for approximation."""
    if len(coords) < 6:
        return coords[:]

    outcoords = []
    x0, y0 = coords[0], coords[1]
    outcoords.extend([x0, y0])

    for i in range(2, len(coords), 4):
        if i + 3 >= len(coords):
            break
        x1, y1, x2, y2 = coords[i:i+4]

        if bezutil_segment_is_collinear(x0, y0, x1, y1, x2, y2, tolerance):
            # Co-linear, don't split
            outcoords.extend([x1, y1, x2, y2])
        else:
            # Split at midpoint
            mx01 = (x0 + x1) / 2.0
            my01 = (y0 + y1) / 2.0
            mx12 = (x1 + x2) / 2.0
            my12 = (y1 + y2) / 2.0
            mx012 = (mx01 + mx12) / 2.0
            my012 = (my01 + my12) / 2.0

            # Recursively split both halves
            bezsplit1 = bezutil_quadbezier_split([x0, y0, mx01, my01,
                                                  mx012, my012], tolerance)
            bezsplit2 = bezutil_quadbezier_split([mx012, my012, mx12, my12,
                                                  x2, y2], tolerance)

            outcoords.extend(bezsplit1[2:])
            outcoords.extend(bezsplit2[2:])

        x0, y0 = x2, y2

    return outcoords


def bezutil_quadbezier_segment_split(t: float, x0: float, y0: float,
                                     x1: float, y1: float,
                                     x2: float, y2: float) -> List[float]:
    """Split a quadratic Bezier segment at parameter t."""
    u = 1.0 - t
    mx01 = u * x0 + t * x1
    my01 = u * y0 + t * y1
    mx12 = u * x1 + t * x2
    my12 = u * y1 + t * y2
    mx012 = u * mx01 + t * mx12
    my012 = u * my01 + t * my12

    return [x0, y0, mx01, my01, mx012, my012, mx12, my12, x2, y2]


def bezutil_quadbezier_segment_length(x0: float, y0: float, x1: float,
                                      y1: float, x2: float,
                                      y2: float) -> float:
    """Calculate approximate length of a quadratic Bezier segment."""
    inc = 1.0 / 20.0
    length = 0.0

    t = 0.0
    u = 1.0 - t
    ox = x2 * t * t + x1 * 2.0 * t * u + x0 * u * u
    oy = y2 * t * t + y1 * 2.0 * t * u + y0 * u * u

    t = inc
    while t <= 1.0:
        u = 1.0 - t
        mx = x2 * t * t + x1 * 2.0 * t * u + x0 * u * u
        my = y2 * t * t + y1 * 2.0 * t * u + y0 * u * u
        length += math.hypot(my - oy, mx - ox)
        ox, oy = mx, my
        t += inc

    return length


def bezutil_quadbezier_length(coords: List[float]) -> float:
    """Calculate approximate length of a quadratic Bezier curve."""
    if len(coords) < 6:
        return 0.0

    length = 0.0
    x0, y0 = coords[0], coords[1]

    for i in range(2, len(coords), 4):
        if i + 3 >= len(coords):
            break
        x1, y1, x2, y2 = coords[i:i+4]
        seglen = bezutil_quadbezier_segment_length(x0, y0, x1, y1, x2, y2)
        length += seglen
        x0, y0 = x2, y2

    return length


def bezutil_quadbezier_segment_point(t: float, x0: float, y0: float,
                                     x1: float, y1: float,
                                     x2: float, y2: float
                                     ) -> Tuple[float, float]:
    """Calculate a point on a quadratic Bezier segment at parameter t."""
    u = 1.0 - t
    mx = x2 * t * t + x1 * 2.0 * t * u + x0 * u * u
    my = y2 * t * t + y1 * 2.0 * t * u + y0 * u * u
    return (mx, my)


def bezutil_append_line_from_quadbezier(coords: List[float],
                                        bezcoords: List[float]) -> None:
    """Convert quadratic Bezier curve to line segments and append."""
    qbezpath = bezutil_quadbezier_split(bezcoords, 5e-4)
    if len(qbezpath) < 2:
        return

    x0, y0 = qbezpath[0], qbezpath[1]
    coords.extend([x0, y0])

    for i in range(2, len(qbezpath), 4):
        if i + 3 >= len(qbezpath):
            break
        x1, y1, x2, y2 = qbezpath[i:i+4]
        coords.extend([x2, y2])


def bezutil_polyline_break_near(px: float, py: float, coords: List[float],
                                closeenough: float = 1e-2
                                ) -> List[List[float]]:
    """Break a polyline at the point closest to a given point."""
    if len(coords) < 4:
        return [coords[:]]

    min_d = 1e99
    min_seg = -1
    seg = 0

    # Find closest line segment
    x0, y0 = coords[0], coords[1]
    for i in range(2, len(coords), 2):
        x1, y1 = coords[i], coords[i + 1]

        # Calculate distance from point to line segment
        # Using basic point-to-line distance calculation
        A = px - x0
        B = py - y0
        C = x1 - x0
        D = y1 - y0

        dot = A * C + B * D
        len_sq = C * C + D * D

        if len_sq < EPSILON:
            # Degenerate segment
            d = math.hypot(A, B)
        else:
            param = dot / len_sq
            if param < 0:
                xx, yy = x0, y0
            elif param > 1:
                xx, yy = x1, y1
            else:
                xx = x0 + param * C
                yy = y0 + param * D

            d = math.hypot(px - xx, py - yy)

        if d < min_d:
            min_d = d
            min_seg = seg

        x0, y0 = x1, y1
        seg += 1

    if min_d > closeenough:
        return [coords[:]]

    # Calculate the closest point on the line segment
    x0, y0 = coords[min_seg * 2], coords[min_seg * 2 + 1]
    x1, y1 = coords[min_seg * 2 + 2], coords[min_seg * 2 + 3]

    A = px - x0
    B = py - y0
    C = x1 - x0
    D = y1 - y0

    dot = A * C + B * D
    len_sq = C * C + D * D

    if len_sq < EPSILON:
        nupt = [x0, y0]
    else:
        param = max(0, min(1, dot / len_sq))
        nupt = [x0 + param * C, y0 + param * D]

    # Split the polyline
    coords1 = coords[0:min_seg * 2 + 2]
    coords2 = coords[min_seg * 2 + 2:]

    if abs(coords1[-2] - nupt[0]) + abs(coords1[-1] - nupt[1]) > 1e-4:
        coords1.extend(nupt)

    if abs(coords2[0] - nupt[0]) + abs(coords2[1] - nupt[1]) > 1e-4:
        coords2 = nupt + coords2

    # Return non-trivial segments
    result = []
    if len(coords1) > 2:
        result.append(coords1)
    if len(coords2) > 2:
        result.append(coords2)

    return result if result else [coords[:]]
