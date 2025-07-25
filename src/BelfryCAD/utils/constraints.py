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


def point_coincides_with_line_endpoint(p: Point2D, l: LineSegment):
    """
    Returns a constraint that ensures the point coincides with the line endpoint.
    """
    def constraint(vars):
        dist1 = p.distance_to(vars, l.p1)
        dist2 = p.distance_to(vars, l.p2)
        return [min(dist1, dist2)]
    return constraint


def point_coincides_with_arc_endpoint(p: Point2D, arc: Arc):
    """
    Returns a constraint that ensures the point coincides with the arc endpoint.
    """
    def constraint(vars):
        cx, cy, r, theta1, theta2 = arc.get(vars)
        px, py = p.get(vars)
        spx = cx + r * np.cos(theta1)
        spy = cy + r * np.sin(theta1)
        epx = cx + r * np.cos(theta2)
        epy = cy + r * np.sin(theta2)
        return [
            min(
                math.hypot(px - spx, py - spy),
                math.hypot(px - epx, py - epy)
            )
        ]
    return constraint


def point_coincides_with_bezier_endpoint(p: Point2D, bezier: CubicBezierSegment):
    """
    Returns a constraint that ensures the point coincides with the bezier segment endpoint.
    """
    def constraint(vars):
        dist1 = p.distance_to(vars, bezier.points[0])
        dist2 = p.distance_to(vars, bezier.points[-1])
        return [min(dist1, dist2)]
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

def circle_is_tangent_to_line(circle: Circle, line: LineSegment):
    """
    Returns a constraint that ensures the circle is tangent to the line.
    """
    return line_is_tangent_to_circle(line, circle)


def circle_is_tangent_to_arc(circle: Circle, arc: Arc):
    """
    Returns a constraint that ensures the circle is tangent to the arc.
    """
    return arc_is_tangent_to_circle(arc, circle)


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
# Constraints Matrix
# ============================

constraints_matrix = {
    "point": {
        "": {},
        "point": {
            "on": points_coincide,
            "vertical": points_aligned_vertically,
            "horizontal": points_aligned_horizontally,
        },
        "line": {
            "on": point_on_line,
            "endpoint": point_coincides_with_line_endpoint,
        },
        "arc": {
            "on": point_on_arc,
            "endpoint": point_coincides_with_arc_endpoint,
        },
        "circle": {
            "on": point_on_circle,
        },
        "bezier": {
            "on": point_on_bezier,
            "endpoint": point_coincides_with_bezier_endpoint,
        }
    },
    "line": {
        "": {
            "horizontal": line_is_horizontal,
            "vertical": line_is_vertical,
        },
        "point": {
            "on":
                lambda line, point:
                    point_on_line(point, line),
            "endpoint":
                lambda line, point:
                    point_coincides_with_line_endpoint(point, line),
        },
        "line": {
            "equal": lines_are_equal_length,
            "perpendicular": lines_are_perpendicular,
            "lparallel": lines_are_parallel,
        },
        "arc": {
            "tangent": line_is_tangent_to_arc,
        },
        "circle": {
            "tangent": line_is_tangent_to_circle,
        },
        "bezier": {
            "tangent": line_is_tangent_to_bezier,
        }
    },
    "arc": {
        "": {},
        "point": {
            "on": point_on_arc,
            "endpoint": point_coincides_with_arc_endpoint,
        },
        "line": {
            "tangent":
                lambda arc, line:
                    line_is_tangent_to_arc(line,arc),
        },
        "arc": {
            "tangent": arc_is_tangent_to_arc,
        },
        "circle": {
            "tangent": arc_is_tangent_to_circle,
        },
        "bezier": {
            "tangent": arc_is_tangent_to_bezier,
        }
    },
    "circle": {
        "": {},
        "point": {
            "on":
                lambda circle, point:
                    point_on_circle(point, circle),
        },
        "line": {
            "tangent": circle_is_tangent_to_line,
        },
        "arc": {
            "tangent": circle_is_tangent_to_arc,
        },
        "circle": {
            "tangent": circle_is_tangent_to_circle,
            "concentric":
                lambda circle1, circle2:
                    points_coincide(circle1.center,circle2.center),
        },
        "bezier": {
            "tangent": circle_is_tangent_to_bezier,
        }
    },
    "bezier": {
        "": {},
        "point": {
            "on":
                lambda bezier, point:
                    point_on_bezier(point, bezier),
            "endpoint":
                lambda bezier, point:
                    point_coincides_with_bezier_endpoint(point, bezier),
        },
        "line": {
            "tangent":
                lambda bezier, line:
                    line_is_tangent_to_bezier(line,bezier),
        },
        "arc": {
            "tangent":
                lambda bezier, arc:
                    arc_is_tangent_to_bezier(arc,bezier),
        },
        "circle": {
            "tangent":
                lambda bezier, circle:
                    circle_is_tangent_to_bezier(circle,bezier),
        }
    }
}


def get_objtype(obj):
    """
    Returns the type of the given object.
    """
    if isinstance(obj, Point2D):
        return "point"
    elif isinstance(obj, LineSegment):
        return "line"
    elif isinstance(obj, Arc):
        return "arc"
    elif isinstance(obj, Circle):
        return "circle"
    elif isinstance(obj, CubicBezierSegment):
        return "bezier"
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

