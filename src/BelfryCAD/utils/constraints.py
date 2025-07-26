import math
import numpy as np
from scipy.optimize import least_squares
from typing import List, Tuple, Callable, Dict, Optional


# ========================
# ConstraintSolver Class
# ========================
class ConstraintSolver:
    def __init__(self):
        self.variables = []
        self.fixed_mask = []
        self.constraints = []
        self.soft_constraints = []
        self.constraint_labels = []
        self.points = []
        self.lines = []
        self.circles = []
        self.arcs = []
        self.beziers = []
        self.conflicting_constraints = []

    def add_variable(self, value: float, fixed: bool = False):
        """
        Adds a variable to the solver.
        The value is the initial value of the variable.
        The fixed flag indicates if the variable is fixed.
        """
        self.variables.append(value)
        self.fixed_mask.append(fixed)
        return len(self.variables) - 1

    def add_constraint(self, func: Callable, label: Optional[str] = None):
        """
        Adds a hard constraint to the solver.
        The constraint is a function that returns a list of residuals.
        The label is an optional string that identifies the constraint.
        """
        self.constraints.append(func)
        self.constraint_labels.append(label or f"constraint_{len(self.constraints)}")

    def add_soft_constraint(self, func: Callable, weight: float = 1.0):
        """
        Adds a soft constraint to the solver.
        The constraint is a function that returns a list of residuals.
        The weight is a multiplier for the residuals.
        """
        self.soft_constraints.append((func, weight))

    def solve(self):
        """
        Solves the constraints.
        Returns the result of the solve.
        The result is a dictionary with the following keys:
        - "x": the list of result variable values
        - "cost": Value of the cost function at the solution
        - "fun": the list of residuals at the solution
        - "success": whether the solve was successful
        - "status": the status of the solve
            * -2 : terminated because callback raised StopIteration.
            * -1 : improper input parameters status returned from MINPACK.
            *  0 : the maximum number of function evaluations is exceeded.
            *  1 : `gtol` termination condition is satisfied.
            *  2 : `ftol` termination condition is satisfied.
            *  3 : `xtol` termination condition is satisfied.
            *  4 : Both `ftol` and `xtol` termination conditions are satisfied.
        - "message": the message of the solve
        - "solver": the solver object
        """
        free_indices = [i for i, fixed in enumerate(self.fixed_mask) if not fixed]

        def masked_objective(free_vars):
            """
            Returns the masked objective function.
            The masked objective function is the sum of the residuals of the hard constraints and the soft constraints.
            The hard constraints are the constraints that are added to the solver.
            The soft constraints are the constraints that are added to the solver with a weight.
            """
            full_x = np.array(self.variables)
            for i, idx in enumerate(free_indices):
                full_x[idx] = free_vars[i]
            residuals = []
            for c in self.constraints:
                residuals.extend(c(full_x))
            for func, weight in self.soft_constraints:
                residuals.extend([r * weight for r in func(full_x)])
            return residuals

        if not free_indices:
            residuals = masked_objective([])
            self._detect_constraints_status()
            self._detect_conflicts(residuals)
            return None

        free_vars_init = [self.variables[i] for i in free_indices]
        result = least_squares(masked_objective, free_vars_init)

        for i, idx in enumerate(free_indices):
            self.variables[idx] = result.x[i]

        self._detect_constraints_status()
        self._detect_conflicts(result.fun)
        return result

    def _detect_constraints_status(self):
        num_vars_total = len(self.variables)
        num_vars_free = sum(not f for f in self.fixed_mask)
        num_constraints = sum(len(c(self.variables)) for c in self.constraints)
        self.under_constrained = num_constraints < num_vars_free
        self.over_constrained = num_constraints > num_vars_free
        self.constraint_info = {
            "total_variables": num_vars_total,
            "free_variables": num_vars_free,
            "num_constraints": num_constraints,
            "under_constrained": self.under_constrained,
            "over_constrained": self.over_constrained
        }

    def _detect_conflicts(self, residuals, tolerance=1e-3):
        self.conflicting_constraints = []
        i = 0
        for func, label in zip(self.constraints, self.constraint_labels):
            r_len = len(func(self.variables))
            subres = residuals[i:i + r_len]
            if any(abs(r) > tolerance for r in subres):
                self.conflicting_constraints.append(label)
            i += r_len

    def get_point_coords(self):
        return [pt.get(self.variables) for pt in self.points]


# ========================
# Geometry Classes
# ========================

class Point2D:
    def __init__(self, solver, pt, fixed=False):
        self.xi = solver.add_variable(pt[0], fixed=fixed)
        self.yi = solver.add_variable(pt[1], fixed=fixed)
        solver.points.append(self)

    def get(self, vars) -> Tuple[float, float]:
        return vars[self.xi], vars[self.yi]

    def distance_to(self, vars, p: 'Point2D') -> float:
        x, y = self.get(vars)
        px, py = p.get(vars)
        return math.hypot(x - px, y - py)

    def degrees_from_origin(self, vars) -> float:
        x, y = self.get(vars)
        return math.degrees(math.atan2(y, x))


class LineSegment:
    def __init__(
        self,
        solver,
        p1: Point2D,
        p2: Point2D
    ):
        self.p1 = p1
        self.p2 = p2
        solver.lines.append(self)

    def get(self, vars) -> Tuple[float, float, float, float]:
        x0, y0 = self.p1.get(vars)
        x1, y1 = self.p2.get(vars)
        return x0, y0, x1, y1

    def length(self, vars) -> float:
        x0, y0, x1, y1 = self.get(vars)
        return math.hypot(x1 - x0, y1 - y0)

    def closest_part(self, vars, p: Point2D) -> float:
        x0, y0, x1, y1 = self.get(vars)
        dx = x1 - x0
        dy = y1 - y0
        l_len = math.hypot(dx, dy)
        if l_len == 0:
            return 0.0
        px, py = p.get(vars)
        t = ((px - x0) * dx + (py - y0) * dy) / l_len**2
        if t < 0:
            return 0.0
        if t > 1:
            return 1.0
        return t

    def closest_point(self, vars, p: Point2D) -> Tuple[float, float]:
        t = self.closest_part(vars, p)
        x0, y0, x1, y1 = self.get(vars)
        return (
            x0 + t * (x1 - x0),
            y0 + t * (y1 - y0)
        )

    def distance_to(self, vars, p: Point2D) -> float:
        cx, cy = self.closest_point(vars, p)
        px, py = p.get(vars)
        return math.hypot(cx - px, cy - py)

    def angle(self, vars) -> float:
        x0, y0, x1, y1 = self.get(vars)
        return math.degrees(math.atan2(y1 - y0, x1 - x0))


class Circle:
    def __init__(
        self,
        solver,
        center: Point2D,
        radius: float,
        fixed_radius: bool = False
    ):
        self.center = center
        self.ri = solver.add_variable(radius, fixed=fixed_radius)
        solver.circles.append(self)

    def get(self, vars) -> Tuple[float, float, float]:
        cx, cy = self.center.get(vars)
        r = vars[self.ri]
        return cx, cy, r
    
    def closest_point_on_perimeter(
        self,
        vars,
        p: Point2D
    ) -> Optional[Tuple[float, float]]:
        cx, cy, r = self.get(vars)
        px, py = p.get(vars)
        dx = px - cx
        dy = py - cy
        d = math.hypot(dx, dy)
        if d == 0:
            return None
        t = r / d
        return (
            cx + t * dx,
            cy + t * dy
        )

    def distance_to_perimeter(self, vars, p: Point2D) -> float:
        closest_pt = self.closest_point_on_perimeter(vars, p)
        cx, cy, r = self.get(vars)
        px, py = p.get(vars)
        if closest_pt is None:
            return math.hypot(px - cx, py - cy)
        return math.hypot(closest_pt[0] - px, closest_pt[1] - py)


class Ellipse:
    def __init__(
        self,
        solver,
        center: Point2D,
        radius1: float,
        radius2: float,
        rotation_angle: float,
        fixed_radius1: bool = False,
        fixed_radius2: bool = False,
        fixed_rotation: bool = False
    ):
        self.center = center
        self.radius1_index = solver.add_variable(radius1, fixed=fixed_radius1)
        self.radius2_index = solver.add_variable(radius2, fixed=fixed_radius2)
        self.rotation_index = solver.add_variable(rotation_angle, fixed=fixed_rotation)
        solver.ellipses = getattr(solver, 'ellipses', [])
        solver.ellipses.append(self)

    def get(self, vars) -> Tuple[float, float, float, float, float]:
        cx, cy = self.center.get(vars)
        major_r = vars[self.radius1_index]
        minor_r = vars[self.radius2_index]
        rotation = vars[self.rotation_index]
        return cx, cy, major_r, minor_r, rotation

    def get_rotation_radians(self, vars) -> float:
        return math.radians(vars[self.rotation_index])

    def get_rotation_degrees(self, vars) -> float:
        return normalize_degrees(vars[self.rotation_index])

    def closest_point_on_perimeter(
        self,
        vars,
        p
    ) -> Optional[Tuple[float, float]]:
        """
        Finds the closest point on the ellipse perimeter to the given point.
        Uses numerical optimization to find the minimum distance.
        """
        cx, cy, major_r, minor_r, rotation = self.get(vars)
        px, py = p.get(vars)
        
        # Transform point to ellipse's coordinate system
        cos_rot = math.cos(math.radians(rotation))
        sin_rot = math.sin(math.radians(rotation))
        
        # Translate to origin
        dx = px - cx
        dy = py - cy
        
        # Rotate to ellipse's coordinate system
        x_rot = dx * cos_rot + dy * sin_rot
        y_rot = -dx * sin_rot + dy * cos_rot
        
        # Find closest point on ellipse using parametric approach
        def ellipse_point(t):
            return (
                major_r * math.cos(t),
                minor_r * math.sin(t)
            )
        
        def distance_to_point(t):
            ex, ey = ellipse_point(t)
            return math.hypot(x_rot - ex, y_rot - ey)
        
        # Find minimum distance using golden section search
        a, b = 0, 2 * math.pi
        gr = (math.sqrt(5) - 1) / 2  # golden ratio
        c = b - gr * (b - a)
        d = a + gr * (b - a)
        
        for _ in range(50):  # 50 iterations should be sufficient
            if distance_to_point(c) < distance_to_point(d):
                b = d
                d = c
                c = b - gr * (b - a)
            else:
                a = c
                c = d
                d = a + gr * (b - a)
        
        # Get the closest point in ellipse coordinates
        t = (a + b) / 2
        ex, ey = ellipse_point(t)
        
        # Transform back to world coordinates
        x_world = ex * cos_rot - ey * sin_rot + cx
        y_world = ex * sin_rot + ey * cos_rot + cy
        
        return (x_world, y_world)

    def distance_to_perimeter(self, vars, p) -> float:
        closest_pt = self.closest_point_on_perimeter(vars, p)
        px, py = p.get(vars)
        if closest_pt is None:
            return 0.0
        return math.hypot(closest_pt[0] - px, closest_pt[1] - py)

    def get_focus_points(self, vars) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Returns the two focus points of the ellipse.
        """
        cx, cy, major_r, minor_r, rotation = self.get(vars)
        
        # Calculate focal distance
        c = math.sqrt(major_r**2 - minor_r**2)
        
        # Focus points in ellipse's coordinate system
        f1_ellipse = (c, 0)
        f2_ellipse = (-c, 0)
        
        # Transform to world coordinates
        cos_rot = math.cos(math.radians(rotation))
        sin_rot = math.sin(math.radians(rotation))
        
        f1_world = (
            f1_ellipse[0] * cos_rot - f1_ellipse[1] * sin_rot + cx,
            f1_ellipse[0] * sin_rot + f1_ellipse[1] * cos_rot + cy
        )
        f2_world = (
            f2_ellipse[0] * cos_rot - f2_ellipse[1] * sin_rot + cx,
            f2_ellipse[0] * sin_rot + f2_ellipse[1] * cos_rot + cy
        )
        
        return f1_world, f2_world

    def eccentricity(self, vars) -> float:
        """
        Returns the eccentricity of the ellipse.
        """
        cx, cy, major_r, minor_r, rotation = self.get(vars)
        if major_r == 0:
            return 0.0
        return math.sqrt(1 - (minor_r**2 / major_r**2))


class Arc:
    def __init__(
        self,
        solver,
        center: Point2D,
        radius: float,
        start_angle: float,
        end_angle: float,
        fixed_radius=False,
        fixed_start_angle=False,
        fixed_end_angle=False
    ):
        self.center = center
        self.radius_index = solver.add_variable(radius, fixed=fixed_radius)
        self.start_angle_index = solver.add_variable(start_angle, fixed=fixed_start_angle)
        self.end_angle_index = solver.add_variable(end_angle, fixed=fixed_end_angle)
        solver.arcs.append(self)

    def get(self, vars) -> Tuple[float, float, float, float, float]:
        cx, cy = self.center.get(vars)
        r = vars[self.radius_index]
        theta1 = vars[self.start_angle_index]
        theta2 = vars[self.end_angle_index]
        return cx, cy, r, theta1, theta2

    def span_angle(self, vars) -> float:
        cx, cy, r, theta1, theta2 = self.get(vars)
        theta1 = normalize_degrees(theta1)
        theta2 = normalize_degrees(theta2)
        if theta1 > theta2:
            return theta2 - theta1 + 360
        return theta2 - theta1

    def start_angle(self, vars) -> float:
        return normalize_degrees(vars[self.start_angle_index])

    def end_angle(self, vars) -> float:
        return normalize_degrees(vars[self.end_angle_index])


class CubicBezierSegment:
    def __init__(
        self,
        solver,
        points: List[Point2D],
    ):
        self.points = points
        solver.beziers.append(self)

    def get(self, vars) -> List[Tuple[float, float]]:
        return [pt.get(vars) for pt in self.points]

    def get_segment(self, vars, i:int) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
        return (
            self.points[i*3].get(vars),
            self.points[i*3 + 1].get(vars),
            self.points[i*3 + 2].get(vars),
            self.points[i*3 + 3].get(vars)
        )

    def path_segment_point(self, vars, t: float, segment_index: int) -> Tuple[float, float]:
        p0, p1, p2, p3 = self.get_segment(vars, segment_index)
        return (
            (1 - t)**3 * p0[0] + 3 * (1 - t)**2 * t * p1[0] +
            3 * (1 - t) * t**2 * p2[0] + t**3 * p3[0],
            (1 - t)**3 * p0[1] + 3 * (1 - t)**2 * t * p1[1] +
            3 * (1 - t) * t**2 * p2[1] + t**3 * p3[1]
        )
    
    def path_point(self, vars, t: float) -> Tuple[float, float]:
        segs = (len(self.points)-1) // 3
        if t == 1.0:
            return self.path_segment_point(vars, 1.0, segs-1)
        t = t * segs
        seg = int(t)
        t = t - seg
        return self.path_segment_point(vars, t, seg)

    def path_segment_tangent(self, vars, t: float, segment_index: int) -> Tuple[float, float]:
        p0, p1, p2, p3 = self.get_segment(vars, segment_index)
        return (
            3 * (1 - t)**2 * (p1[0] - p0[0]) +
                6 * (1 - t) * t * (p2[0] - p1[0]) +
                3 * t**2 * (p3[0] - p2[0]),
            3 * (1 - t)**2 * (p1[1] - p0[1]) +
                6 * (1 - t) * t * (p2[1] - p1[1]) +
                3 * t**2 * (p3[1] - p2[1])
        )

    def path_tangent(self, vars, t: float) -> Tuple[float, float]:
        segs = (len(self.points)-1) // 3
        if t == 1.0:
            return self.path_segment_tangent(vars, 1.0, segs-1)
        t = t * segs
        seg = int(t)
        t = t - seg
        return self.path_segment_tangent(vars, t, seg)

    def closest_path_part(self, vars, p: Point2D) -> float:
        def dist(t: float) -> float:
            x, y = self.path_point(vars, t)
            px, py = p.get(vars)
            return math.hypot(x - px, y - py)
        
        segs = (len(self.points)-1) // 3
        t = 0.0
        d = dist(t)
        for tt in np.linspace(0.0, 1.0, 16*segs):
            dd = dist(tt)
            if dd < d:
                d = dd
                t = tt
        delta = 1.0/(16*segs)
        while delta > 1e-6:
            t1 = max(0.0, (t - delta))
            t2 = min(1.0, (t + delta))
            d1 = dist(t1)
            d = dist(t)
            d2 = dist(t2)
            if d > d1 or d > d2:
                if d1 < d2:
                    t = max(0.0, t - delta)
                else:
                    t = min(1.0, t + delta)
            delta *= 0.5
        return t

    def closest_path_point(self, vars, p: Point2D) -> Tuple[float, float]:
        t = self.closest_path_part(vars, p)
        return self.path_point(vars, t)


# ========================
# Helper Functions
# ========================

def normalize_degrees(angle: float) -> float:
    return ((angle % 360) + 360) % 360


def vector_angle(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    return math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))


def angle_from_arc_span(
    angle: float,
    start_angle: float,
    end_angle: float
) -> float:
    """
    Returns the angle between the given angle and the arc span.
    The arc span is defined by the start and end angles.
    The angle is normalized to the range of 0 to 360 degrees.
    The start and end angles are normalized to the range of 0 to 360 degrees.
    The angle is returned in degrees.
    If the angle is within the arc span, the angle is returned as 0.
    If the angle is outside the arc span, the angle is returned as the
    difference between the angle and the closest of the start or end angle.
    """
    angle = normalize_degrees(angle)
    start_angle = normalize_degrees(start_angle)
    end_angle = normalize_degrees(end_angle)
    delta_angle = 0.0
    if start_angle > end_angle:
        if angle < start_angle and angle > end_angle:
            delta_angle = min(start_angle - angle, angle - end_angle)
    elif angle < start_angle:
        delta_angle = start_angle - angle
    elif angle > end_angle:
        delta_angle = angle - end_angle
    else:
        delta_angle = 0.0
    return delta_angle


# ============================
# Point Constraint Functions
# ============================

def points_coincide(p1: Point2D, p2: Point2D):
    """
    Returns a constraint that ensures the points coincide.
    """
    def constraint(vars):
        p1x, p1y = p1.get(vars)
        p2x, p2y = p2.get(vars)
        return [p1x - p2x, p1y - p2y]
    return constraint


def points_aligned_vertically(p1: Point2D, p2: Point2D):
    """
    Returns a constraint that ensures the points are aligned vertically.
    """
    def constraint(vars):
        p1x, p1y = p1.get(vars)
        p2x, p2y = p2.get(vars)
        return [p1y - p2y]
    return constraint


def points_aligned_horizontally(p1: Point2D, p2: Point2D):
    """
    Returns a constraint that ensures the points are aligned horizontally.
    """
    def constraint(vars):
        p1x, p1y = p1.get(vars)
        p2x, p2y = p2.get(vars)
        return [p1x - p2x]
    return constraint


def point_on_line(p: Point2D, l: LineSegment):
    """
    Returns a constraint that ensures the point is on the line.
    """
    def constraint(vars):
        px, py = p.get(vars)
        p1x, p1y = l.p1.get(vars)
        p2x, p2y = l.p2.get(vars)
        return [(px - p1x) * (p2x - p1x) + (py - p1y) * (p2y - p1y)]
    return constraint


def point_on_arc(p: Point2D, a: Arc):
    """
    Returns a constraint that ensures the point is on the arc.
    """
    def constraint(vars):
        px, py = p.get(vars)
        cx, cy, r, theta1, theta2 = a.get(vars)
        return [
            math.hypot(px - cx, py - cy) - r,
            angle_from_arc_span(
                math.degrees(math.atan2(py - cy, px - cx)),
                theta1,
                theta2
            )
        ]
    return constraint


def point_on_circle(p: Point2D, c: Circle):
    """
    Returns a constraint that ensures the point is on the circle.
    """
    def constraint(vars):
        px, py = p.get(vars)
        cx, cy, r = c.get(vars)
        return [math.hypot(px - cx, py - cy) - r]
    return constraint


def point_on_bezier(p: Point2D, bezier: CubicBezierSegment):
    """
    Returns a constraint that ensures the point is on the bezier segment.
    """
    def constraint(vars):
        px, py = p.get(vars)
        t = bezier.closest_path_part(vars, p)
        pp = bezier.path_point(vars, t)
        return [pp[0] - px, pp[1] - py]
    return constraint


def point_coincides_with_arc_start(p: Point2D, arc: Arc):
    """
    Returns a constraint that ensures the point coincides with the arc start point.
    """
    def constraint(vars):
        cx, cy, r, theta1, theta2 = arc.get(vars)
        px, py = p.get(vars)
        spx = cx + r * np.cos(theta1)
        spy = cy + r * np.sin(theta1)
        return [
            math.hypot(px - spx, py - spy),
        ]
    return constraint


def point_coincides_with_arc_end(p: Point2D, arc: Arc):
    """
    Returns a constraint that ensures the point coincides with the arc start point.
    """
    def constraint(vars):
        cx, cy, r, theta1, theta2 = arc.get(vars)
        px, py = p.get(vars)
        epx = cx + r * np.cos(theta2)
        epy = cy + r * np.sin(theta2)
        return [
            math.hypot(px - epx, py - epy),
        ]
    return constraint


# ============================
# Line Constraint Functions
# ============================

def line_is_horizontal(l: LineSegment):
    """
    Returns a constraint that ensures the line is horizontal.
    """
    def constraint(vars):
        p1x, p1y = l.p1.get(vars)
        p2x, p2y = l.p2.get(vars)
        return [p1y - p2y]
    return constraint


def line_is_vertical(l: LineSegment):
    """
    Returns a constraint that ensures the line is vertical.
    """
    def constraint(vars):
        p1x, p1y = l.p1.get(vars)
        p2x, p2y = l.p2.get(vars)
        return [p1x - p2x]
    return constraint


def line_angle_is(l: LineSegment, angle: float):
    """
    Returns a constraint that ensures the line is at the given angle in degrees.
    """
    def constraint(vars):
        return [l.angle(vars) - angle]
    return constraint


def line_length_is(l: LineSegment, length: float):
    """
    Returns a constraint that ensures the line has the given length.
    """
    def constraint(vars):
        return [l.length(vars) - length]
    return constraint


def lines_are_equal_length(l1: LineSegment, l2: LineSegment):
    """
    Returns a constraint that ensures the lines have equal lengths.
    """
    def constraint(vars):
        return [l1.length(vars) - l2.length(vars)]
    return constraint


def lines_are_perpendicular(l1: LineSegment, l2: LineSegment):
    """
    Returns a constraint that ensures the lines are perpendicular.
    """
    def constraint(vars):
        p1x, p1y = l1.p1.get(vars)
        p2x, p2y = l1.p2.get(vars)
        p3x, p3y = l2.p1.get(vars)
        p4x, p4y = l2.p2.get(vars)
        return [(p2x - p1x) * (p4x - p3x) + (p2y - p1y) * (p4y - p3y)]
    return constraint


def lines_are_parallel(l1: LineSegment, l2: LineSegment):
    """
    Returns a constraint that ensures the lines are parallel.
    """
    def constraint(vars):
        p1x, p1y = l1.p1.get(vars)
        p2x, p2y = l1.p2.get(vars)
        p3x, p3y = l2.p1.get(vars)
        p4x, p4y = l2.p2.get(vars)
        return [(p2x - p1x) * (p4y - p3y) - (p2y - p1y) * (p4x - p3x)]
    return constraint


def line_is_tangent_to_arc(line: LineSegment, arc: Arc):
    """
    Returns a constraint that ensures the line is tangent to the arc.
    """
    def constraint(vars):
        clx, cly = line.closest_point(vars, arc.center)
        cx, cy, r, theta1, theta2 = arc.get(vars)
        dist = math.hypot(clx - cx, cly - cy)
        angle = math.degrees(math.atan2(cly - cy, clx - cx)) - theta1
        return [
            dist - r,
            angle_from_arc_span(angle, theta1, theta2)
        ]
    return constraint


def line_is_tangent_to_circle(line: LineSegment, circle: Circle):
    """
    Returns a constraint that ensures the line is tangent to the circle.
    """
    def constraint(vars):
        clx, cly = line.closest_point(vars, circle.center)
        cx, cy, r = circle.get(vars)
        dist = math.hypot(clx - cx, cly - cy)
        return [dist - r]
    return constraint


def line_is_tangent_to_bezier(
    line: LineSegment,
    bezier: CubicBezierSegment
):
    """
    Returns a constraint that ensures the line is tangent to the bezier segment.
    """
    def constraint(vars):
        lp1x, lp1y = line.p1.get(vars)
        lp2x, lp2y = line.p2.get(vars)
        t1 = bezier.closest_path_part(vars, line.p1)
        t2 = bezier.closest_path_part(vars, line.p2)
        cpt1 = bezier.path_point(vars, t1)
        cpt2 = bezier.path_point(vars, t2)
        dist1 = math.hypot(cpt1[0] - lp1x, cpt1[1] - lp1y)
        dist2 = math.hypot(cpt2[0] - lp2x, cpt2[1] - lp2y)
        if dist1 < dist2:
            t = t1
            cpt = cpt1
            dist = dist1
        else:
            t = t2
            cpt = cpt2
            dist = dist2
        vect = bezier.path_tangent(vars, t)
        vect_angle = vector_angle(vect, (lp2x - lp1x, lp2y - lp1y))
        return [
            abs(math.cos(math.radians(vect_angle))) - 1.0,
            dist
        ]
    return constraint


# ============================
# Arc Constraint Functions
# ============================

def arc_radius_is(arc: Arc, radius: float):
    """
    Returns a constraint that ensures the arc has the given radius.
    """
    def constraint(vars):
        cx, cy, r, theta1, theta2 = arc.get(vars)
        return [r - radius]
    return constraint


def arc_starts_at_angle(arc: Arc, angle: float):
    """
    Returns a constraint that ensures the arc starts at the given angle in degrees.
    """
    target_angle = normalize_degrees(angle)
    def constraint(vars):
        return [arc.start_angle(vars) - target_angle]
    return constraint

def arc_ends_at_angle(arc: Arc, angle: float):
    """
    Returns a constraint that ensures the arc ends at the given angle in degrees.
    """
    target_angle = normalize_degrees(angle)
    def constraint(vars):
        return [arc.end_angle(vars) - target_angle]
    return constraint


def arc_spans_angle(arc: Arc, angle: float):
    """
    Returns a constraint that ensures the arc spans the given angle in degrees.
    """
    target_angle = normalize_degrees(angle)
    def constraint(vars):
        return [arc.span_angle(vars) - target_angle]
    return constraint


def arc_is_tangent_to_arc(arc1: Arc, arc2: Arc):
    """
    Returns a constraint that ensures the arcs are tangent to each other.
    """
    def constraint(vars):
        cx1, cy1, r1, theta1, theta2 = arc1.get(vars)
        cx2, cy2, r2, theta3, theta4 = arc2.get(vars)
        dist = math.hypot(cx1 - cx2, cy1 - cy2)
        angle = math.degrees(math.atan2(cy2 - cy1, cx2 - cx1))
        return [
            dist - r1 - r2,
            angle_from_arc_span(angle, theta1, theta2) +
            angle_from_arc_span(angle, theta3, theta4)
        ]
    return constraint


def arc_is_tangent_to_circle(arc: Arc, circle: Circle): 
    """
    Returns a constraint that ensures the arc is tangent to the circle.
    """
    def constraint(vars):
        c1x, c1y, r1, theta1, theta2 = arc.get(vars)
        cx2, cy2, r2 = circle.get(vars)
        dist = math.hypot(c1x - cx2, c1y - cy2)
        angle = math.degrees(math.atan2(cy2 - c1y, cx2 - c1x))
        return [
            dist - r1 - r2,
            angle_from_arc_span(angle, theta1, theta2)
        ]
    return constraint


def arc_is_tangent_to_bezier(arc: Arc, bezier: CubicBezierSegment):
    """
    Returns a constraint that ensures the arc is tangent to the bezier segment.
    """
    def constraint(vars):
        cx, cy, r, theta1, theta2 = arc.get(vars)
        t = bezier.closest_path_part(vars, arc.center)
        cpt = bezier.path_point(vars, t)
        dist = math.hypot(cpt[0] - cx, cpt[1] - cy)
        return [
            dist - r,
            angle_from_arc_span(
                math.degrees(math.atan2(cpt[1] - cy, cpt[0] - cx)),
                theta1,
                theta2
            )
        ]
    return constraint


# ============================
# Circle Constraint Functions
# ============================

def circle_radius_is(circle: Circle, radius: float):
    """
    Returns a constraint that ensures the circle has the given radius.
    """
    def constraint(vars):
        cx, cy, r = circle.get(vars)
        return [r - radius]
    return constraint


def circle_is_tangent_to_circle(circle1: Circle, circle2: Circle):
    """
    Returns a constraint that ensures the circles are tangent to each other.
    """
    def constraint(vars):
        c1x, c1y, r1 = circle1.get(vars)
        c2x, c2y, r2 = circle2.get(vars)
        dist = math.hypot(c1x - c2x, c1y - c2y)
        return [dist - r1 - r2]
    return constraint


def circle_is_tangent_to_bezier(circle: Circle, bezier: CubicBezierSegment):
    """
    Returns a constraint that ensures the circle is tangent to the bezier segment.
    """
    def constraint(vars):
        cx, cy, r = circle.get(vars)
        t = bezier.closest_path_part(vars, circle.center)
        cpt = bezier.path_point(vars, t)
        dist = math.hypot(cpt[0] - cx, cpt[1] - cy)
        return [dist - r]
    return constraint


# ============================
# Ellipse Constraint Functions
# ============================

def ellipse_radius1_is(ellipse: Ellipse, radius: float):
    """
    Returns a constraint that ensures the ellipse has the given major radius.
    """
    def constraint(vars):
        cx, cy, major_r, minor_r, rotation = ellipse.get(vars)
        return [major_r - radius]
    return constraint


def ellipse_radius2_is(ellipse: Ellipse, radius: float):
    """
    Returns a constraint that ensures the ellipse has the given minor radius.
    """
    def constraint(vars):
        cx, cy, major_r, minor_r, rotation = ellipse.get(vars)
        return [minor_r - radius]
    return constraint


def ellipse_rotation_is(ellipse: Ellipse, angle: float):
    """
    Returns a constraint that ensures the ellipse has the given rotation angle in degrees.
    """
    target_angle = normalize_degrees(angle)
    def constraint(vars):
        return [ellipse.get_rotation_degrees(vars) - target_angle]
    return constraint


def ellipse_eccentricity_is(ellipse: Ellipse, eccentricity: float):
    """
    Returns a constraint that ensures the ellipse has the given eccentricity.
    """
    def constraint(vars):
        return [ellipse.eccentricity(vars) - eccentricity]
    return constraint


def point_on_ellipse(p: Point2D, ellipse: Ellipse):
    """
    Returns a constraint that ensures the point is on the ellipse perimeter.
    """
    def constraint(vars):
        return [ellipse.distance_to_perimeter(vars, p)]
    return constraint


def ellipse_is_centered_at_point(ellipse: Ellipse, point: Point2D):
    """
    Returns a constraint that ensures the ellipse is centered at the given point.
    """
    def constraint(vars):
        return points_coincide(ellipse.center, point)(vars)
    return constraint


def line_is_tangent_to_ellipse(line: LineSegment, ellipse: Ellipse):
    """
    Returns a constraint that ensures the line is tangent to the ellipse.
    """
    def constraint(vars):
        # Find closest point on ellipse to line
        lp1x, lp1y = line.p1.get(vars)
        lp2x, lp2y = line.p2.get(vars)
        
        # Use line midpoint as approximation for closest point
        mid_x = (lp1x + lp2x) / 2
        mid_y = (lp1y + lp2y) / 2
        
        # Create a temporary point for calculation (without solver)
        class TempPoint:
            def __init__(self, x, y):
                self.x = x
                self.y = y
            def get(self, vars):
                return self.x, self.y
        
        mid_point = TempPoint(mid_x, mid_y)
        
        closest_pt = ellipse.closest_point_on_perimeter(vars, mid_point)
        if closest_pt is None:
            return [1.0]  # Return non-zero residual if no closest point found
        
        # Calculate distance from line to closest point
        dist = line.distance_to(vars, mid_point)  # type: ignore
        
        # Calculate tangent angle at closest point
        cx, cy, major_r, minor_r, rotation = ellipse.get(vars)
        cos_rot = math.cos(math.radians(rotation))
        sin_rot = math.sin(math.radians(rotation))
        
        # Transform closest point to ellipse coordinates
        dx = closest_pt[0] - cx
        dy = closest_pt[1] - cy
        x_rot = dx * cos_rot + dy * sin_rot
        y_rot = -dx * sin_rot + dy * cos_rot
        
        # Calculate tangent angle in ellipse coordinates
        if abs(x_rot) < 1e-10 and abs(y_rot) < 1e-10:
            return [1.0]  # Point at center, no unique tangent
        
        # Parametric tangent calculation
        t = math.atan2(y_rot / minor_r, x_rot / major_r)
        tangent_x = -major_r * math.sin(t)
        tangent_y = minor_r * math.cos(t)
        
        # Transform tangent back to world coordinates
        world_tangent_x = tangent_x * cos_rot - tangent_y * sin_rot
        world_tangent_y = tangent_x * sin_rot + tangent_y * cos_rot
        
        # Calculate angle between line and tangent
        line_angle = math.atan2(lp2y - lp1y, lp2x - lp1x)
        tangent_angle = math.atan2(world_tangent_y, world_tangent_x)
        angle_diff = abs(line_angle - tangent_angle)
        
        return [
            dist,  # Distance should be zero for tangent
            abs(math.cos(angle_diff)) - 1.0  # Angles should be parallel or perpendicular
        ]
    return constraint


def ellipse_is_tangent_to_circle(ellipse: Ellipse, circle: Circle):
    """
    Returns a constraint that ensures the ellipse is tangent to the circle.
    """
    def constraint(vars):
        cx1, cy1, major_r, minor_r, rotation = ellipse.get(vars)
        cx2, cy2, r2 = circle.get(vars)
        
        # Calculate distance between centers
        center_dist = math.hypot(cx1 - cx2, cy1 - cy2)
        
        # For tangent ellipses, the distance should equal the sum of radii
        # However, for ellipses, this is more complex. We'll use an approximation
        # by finding the closest point on ellipse to circle center
        temp_point = Point2D(None, (cx2, cy2))
        closest_pt = ellipse.closest_point_on_perimeter(vars, temp_point)
        
        if closest_pt is None:
            return [1.0]
        
        # Distance from circle center to closest point on ellipse
        dist_to_ellipse = math.hypot(closest_pt[0] - cx2, closest_pt[1] - cy2)
        
        return [dist_to_ellipse - r2]
    return constraint


def ellipse_is_tangent_to_arc(ellipse: Ellipse, arc: Arc):
    """
    Returns a constraint that ensures the ellipse is tangent to the arc.
    """
    def constraint(vars):
        cx1, cy1, major_r, minor_r, rotation = ellipse.get(vars)
        cx2, cy2, r2, theta1, theta2 = arc.get(vars)
        
        # Find closest point on ellipse to arc center
        temp_point = Point2D(None, (cx2, cy2))
        closest_pt = ellipse.closest_point_on_perimeter(vars, temp_point)
        
        if closest_pt is None:
            return [1.0]
        
        # Distance from arc center to closest point on ellipse
        dist_to_ellipse = math.hypot(closest_pt[0] - cx2, closest_pt[1] - cy2)
        
        # Check if the closest point is within the arc span
        angle_to_point = math.degrees(math.atan2(closest_pt[1] - cy2, closest_pt[0] - cx2))
        span_check = angle_from_arc_span(angle_to_point, theta1, theta2)
        
        return [
            dist_to_ellipse - r2,  # Distance should equal arc radius
            span_check  # Point should be within arc span
        ]
    return constraint


def ellipse_is_tangent_to_bezier(ellipse: Ellipse, bezier: CubicBezierSegment):
    """
    Returns a constraint that ensures the ellipse is tangent to the bezier segment.
    """
    def constraint(vars):
        cx, cy, major_r, minor_r, rotation = ellipse.get(vars)
        
        # Find closest point on ellipse to bezier
        # Use bezier center approximation
        bezier_points = bezier.get(vars)
        if not bezier_points:
            return [1.0]
        
        # Calculate approximate center of bezier
        center_x = sum(p[0] for p in bezier_points) / len(bezier_points)
        center_y = sum(p[1] for p in bezier_points) / len(bezier_points)
        
        temp_point = Point2D(None, (center_x, center_y))
        closest_pt = ellipse.closest_point_on_perimeter(vars, temp_point)
        
        if closest_pt is None:
            return [1.0]
        
        # Find closest point on bezier to ellipse center
        t = bezier.closest_path_part(vars, ellipse.center)
        bezier_pt = bezier.path_point(vars, t)
        
        # Distance between closest points
        dist = math.hypot(closest_pt[0] - bezier_pt[0], closest_pt[1] - bezier_pt[1])
        
        return [dist]
    return constraint


def ellipses_are_concentric(ellipse1: Ellipse, ellipse2: Ellipse):
    """
    Returns a constraint that ensures the ellipses are concentric (same center).
    """
    def constraint(vars):
        return points_coincide(ellipse1.center, ellipse2.center)(vars)
    return constraint


# ============================
# Constraints Matrix
# ============================

constraints_matrix = {
    "point": {
        "": {
        },
        "scalar": {
        },
        "point": {
            "Point is at": points_coincide,
            "Point is vertical to": points_aligned_vertically,
            "Point is horizontal to": points_aligned_horizontally,
        },
        "line": {
            "Point is on line segment": point_on_line,
            "Line starts at point":
                lambda point, line: points_coincide(line.p1, point),
            "Line ends at point":
                lambda point, line: points_coincide(line.p2, point),
        },
        "arc": {
            "Point is on arc": point_on_arc,
            "Arc starts at point": point_coincides_with_arc_start,
            "Arc ends at point": point_coincides_with_arc_end,
            "Arc is centered at point":
                lambda point, arc:
                    points_coincide(arc.center, point),
        },
        "circle": {
            "Point is on circle perimeter": point_on_circle,
            "Circle is centered at point":
                lambda point, circle:
                    points_coincide(circle.center, point),
        },
        "bezier": {
            "Point is on bezier curve": point_on_bezier,
            "Bezier curve starts at point":
                lambda point, bezier:
                    points_coincide(bezier.points[0], point),
            "Bezier curve ends at point":
                lambda point, bezier:
                    points_coincide(bezier.points[-1], point),
        },
        "ellipse": {
            "Point is on ellipse perimeter": point_on_ellipse,
            "Ellipse is centered at point": ellipse_is_centered_at_point,
        }
    },
    "line": {
        "": {
            "Line is horizontal": line_is_horizontal,
            "Line is vertical": line_is_vertical,
        },
        "scalar": {
            "Line angle is": line_angle_is,
            "Line length is": line_length_is,
        },
        "point": {
            "Point is on line segment":
                lambda line, point:
                    point_on_line(point, line),
            "Line starts at point":
                lambda line, point:
                    points_coincide(point.p1, line),
            "Line ends at point":
                lambda line, point:
                    points_coincide(point.p2, line),
        },
        "line": {
            "Lines are equal length": lines_are_equal_length,
            "Lines are perpendicular": lines_are_perpendicular,
            "Lines are parallel": lines_are_parallel,
        },
        "arc": {
            "Line is tangential to arc": line_is_tangent_to_arc,
        },
        "circle": {
            "Line is tangential to circle": line_is_tangent_to_circle,
        },
        "bezier": {
            "Line is tangential to bezier curve": line_is_tangent_to_bezier,
        },
        "ellipse": {
            "Line is tangential to ellipse": line_is_tangent_to_ellipse,
        }
    },
    "arc": {
        "": {
        },
        "scalar": {
            "Arc start angle is": arc_starts_at_angle,
            "Arc end angle is": arc_ends_at_angle,
            "Arc span angle is": arc_spans_angle,
            "Arc radius is": arc_radius_is,
        },
        "point": {
            "Point is on arc":
                lambda arc, point:
                    point_on_arc(point, arc),
            "Arc is centered at point":
                lambda arc, point:
                    points_coincide(arc.center, point),
            "Arc starts at point":
                lambda arc, point:
                    point_coincides_with_arc_start(point, arc),
            "Arc ends at point":
                lambda arc, point:
                    point_coincides_with_arc_end(point, arc),
        },
        "line": {
            "Line is tangential to arc":
                lambda arc, line:
                    line_is_tangent_to_arc(line,arc),
        },
        "arc": {
            "Arcs are tangential": arc_is_tangent_to_arc,
            "Arcs are concentric":
                lambda arc, circle:
                    points_coincide(arc.center, circle.center),
        },
        "circle": {
            "Circle is tangential to arc": arc_is_tangent_to_circle,
            "Circle is concentric to arc":
                lambda arc, circle:
                    points_coincide(arc.center, circle.center),
        },
        "bezier": {
            "Arc is tangential to bezier curve": arc_is_tangent_to_bezier,
        },
        "ellipse": {
            "Arc is tangential to ellipse": ellipse_is_tangent_to_arc,
        }
    },
    "circle": {
        "": {
        },
        "scalar": {
            "Circle radius is": circle_radius_is,
        },
        "point": {
            "Point is on circle perimeter":
                lambda circle, point:
                    point_on_circle(point, circle),
            "Circle is centered at point":
                lambda circle, point:
                    points_coincide(circle.center, point),
        },
        "line": {
            "Line is tangential to circle":
                lambda circle, line:
                    line_is_tangent_to_circle(line, circle),
        },
        "arc": {
            "Circle is tangential to arc":
                lambda circle, arc:
                    arc_is_tangent_to_circle(arc, circle),
            "Circle is concentric to arc":
                lambda circle, arc:
                    points_coincide(circle.center, arc.center),
        },
        "circle": {
            "Circle is tangential to circle": circle_is_tangent_to_circle,
            "Circles are concentric":
                lambda circle1, circle2:
                    points_coincide(circle1.center,circle2.center),
        },
        "bezier": {
            "Circle is tangential to bezier": circle_is_tangent_to_bezier,
        },
        "ellipse": {
            "Circle is tangential to ellipse": ellipse_is_tangent_to_circle,
        }
    },
    "bezier": {
        "": {},
        "point": {
            "Point is on bezier curve":
                lambda bezier, point:
                    point_on_bezier(point, bezier),
            "Bezier curve starts at point":
                lambda bezier, point:
                    points_coincide(bezier.points[0], point),
            "Bezier curve ends at point":
                lambda bezier, point:
                    points_coincide(bezier.points[-1], point),
        },
        "line": {
            "Line is tangential to bezier curve":
                lambda bezier, line:
                    line_is_tangent_to_bezier(line,bezier),
        },
        "arc": {
            "Arc is tangential to bezier curve":
                lambda bezier, arc:
                    arc_is_tangent_to_bezier(arc,bezier),
        },
        "circle": {
            "Circle is tangential to bezier curve":
                lambda bezier, circle:
                    circle_is_tangent_to_bezier(circle,bezier),
        },
        "ellipse": {
            "Ellipse is tangential to bezier curve": ellipse_is_tangent_to_bezier,
        }
    },
    "ellipse": {
        "": {},
        "scalar": {
            "Ellipse radius1 is": ellipse_radius1_is,
            "Ellipse radius2 is": ellipse_radius2_is,
            "Ellipse rotation is": ellipse_rotation_is,
            "Ellipse eccentricity is": ellipse_eccentricity_is,
        },
        "point": {
            "Point is on ellipse perimeter": point_on_ellipse,
            "Ellipse is centered at point": ellipse_is_centered_at_point,
        },
        "line": {
            "Line is tangential to ellipse": line_is_tangent_to_ellipse,
        },
        "arc": {
            "Ellipse is tangential to arc": ellipse_is_tangent_to_arc,
        },
        "circle": {
            "Ellipse is tangential to circle": ellipse_is_tangent_to_circle,
        },
        "ellipse": {
            "Ellipses are concentric": ellipses_are_concentric,
        },
        "bezier": {
            "Ellipse is tangential to bezier curve": ellipse_is_tangent_to_bezier,
        }
    }
}


def get_objtype(obj):
    """
    Returns the type of the given object.
    """
    if isinstance(obj, float) or isinstance(obj, int):
        return "scalar"
    elif isinstance(obj, Point2D):
        return "point"
    elif isinstance(obj, LineSegment):
        return "line"
    elif isinstance(obj, Arc):
        return "arc"
    elif isinstance(obj, Circle):
        return "circle"
    elif isinstance(obj, CubicBezierSegment):
        return "bezier"
    elif isinstance(obj, Ellipse):
        return "ellipse"
    return ""


def get_available_constraints(obj1, obj2):
    """
    Returns a list of available constraints for the given objects.
    """
    objtype1 = get_objtype(obj1)
    objtype2 = get_objtype(obj2)
    if objtype1 == "":
        return []
    avail = constraints_matrix[objtype1][objtype2]
    return list(avail.keys())
    

def get_constraint(obj1, obj2, type):
    """
    Returns a constraint function for the given objects and type.
    """
    objtype1 = get_objtype(obj1)
    objtype2 = get_objtype(obj2)
    if objtype1 == "":
        return None
    avail = constraints_matrix[objtype1][objtype2]
    if type not in avail:
        return None
    call = avail[type]
    if objtype2 == "":
        return call(obj1)
    return call(obj1, obj2)

