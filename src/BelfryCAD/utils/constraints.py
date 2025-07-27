import math
import numpy as np
from scipy.optimize import least_squares
from typing import List, Tuple, Callable, Dict, Optional


import numpy as np

# =========================
# Constraint base class
# =========================
class Constraint:
    """Base class for constraints with analytic Jacobians."""
    def residual(self, x):
        raise NotImplementedError
    def jacobian(self, x):
        raise NotImplementedError


# =========================
# ConstraintSolver
# =========================
class ConstraintSolver:
    def __init__(self):
        self.variables = []
        self.fixed_mask = []
        self.constraints = []
        self.soft_constraints = []
        self.constraint_labels = []
        # Geometry entities
        self.points = []
        self.lines = []
        self.circles = []
        self.arcs = []
        self.bezier_curves = []
        self.conflicting_constraints = []

    # -------------------------
    # Variable management
    # -------------------------
    def add_variable(self, value, fixed=False):
        self.variables.append(value)
        self.fixed_mask.append(fixed)
        return len(self.variables) - 1

    # -------------------------
    # Constraints
    # -------------------------
    def add_constraint(self, func, label=None):
        """Adds either a callable constraint or an analytic Constraint object."""
        self.constraints.append(func)
        self.constraint_labels.append(label or f"constraint_{len(self.constraints)}")

    def add_soft_constraint(self, func, weight=1.0):
        """
        Adds a soft constraint. Soft constraints are constraints that are not
        enforced strictly, but are used to guide the solver towards a solution.
        The weight parameter controls the strength of the constraint.
        """
        self.soft_constraints.append((func, weight))

    # -------------------------
    # Numerical Jacobian (fallback)
    # -------------------------
    @staticmethod
    def _numerical_jacobian(func, x, eps=1e-6):
        f0 = np.array(func(x))
        m = len(f0)
        n = len(x)
        J = np.zeros((m, n))
        for j in range(n):
            x1 = x.copy()
            x1[j] += eps
            J[:, j] = (np.array(func(x1)) - f0) / eps
        return J

    # -------------------------
    # Custom Gauss-Newton solver
    # -------------------------
    def gauss_newton_solve(self, max_iter=50, tol=1e-8, damping=1e-6):
        """Custom Gauss-Newton/LM solver with hybrid analytic/numeric Jacobians."""
        free_indices = [i for i, fixed in enumerate(self.fixed_mask) if not fixed]
        full_x = np.array(self.variables, dtype=float)

        def unpack(free_x):
            x = full_x.copy()
            for i, idx in enumerate(free_indices):
                x[idx] = free_x[i]
            return x

        def residuals_and_jacobian(free_x):
            x = unpack(free_x)
            res_list = []
            jac_list = []
            # Collect residuals/J for all constraints
            for c in self.constraints:
                if hasattr(c, "jacobian") and hasattr(c, "residual"):
                    # Analytic constraint object
                    res = c.residual(x)
                    J_full = c.jacobian(x)
                else:
                    # Callable function: use numerical derivative
                    res = np.array(c(x))
                    J_full = ConstraintSolver._numerical_jacobian(c, x)
                res_list.append(res)
                jac_list.append(J_full)

            # Stack all
            R = np.concatenate(res_list)
            J = np.vstack(jac_list)[:, free_indices]

            # Soft constraints
            for func, weight in self.soft_constraints:
                res_soft = np.array(func(x)) * weight
                R = np.concatenate([R, res_soft])
                J_soft = ConstraintSolver._numerical_jacobian(func, x)[:, free_indices] * weight
                J = np.vstack([J, J_soft])

            return R, J

        # Initial free variable vector
        x_free = np.array([self.variables[i] for i in free_indices])

        for it in range(max_iter):
            R, J = residuals_and_jacobian(x_free)
            if np.linalg.norm(R) < tol:
                break
            A = J.T @ J + damping * np.eye(len(x_free))
            g = J.T @ R
            delta = np.linalg.solve(A, g)
            x_free -= delta

        # Write results back
        for i, idx in enumerate(free_indices):
            self.variables[idx] = x_free[i]

        self._detect_constraints_status()
        return self.variables

    # -------------------------
    # SciPy least_squares solver (alternative)
    # -------------------------
    def solve(self):
        from scipy.optimize import least_squares
        free_indices = [i for i, fixed in enumerate(self.fixed_mask) if not fixed]

        def masked_objective(free_vars):
            full_x = np.array(self.variables)
            for i, idx in enumerate(free_indices):
                full_x[idx] = free_vars[i]
            residuals = []
            for c in self.constraints:
                if callable(c):
                    residuals.extend(c(full_x))  # type: ignore
                else:
                    residuals.extend(c.residual(full_x))
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

    # -------------------------
    # Diagnostics
    # -------------------------
    def _detect_constraints_status(self):
        num_vars_total = len(self.variables)
        num_vars_free = sum(not f for f in self.fixed_mask)
        num_constraints = sum(len(c.residual(self.variables) if hasattr(c, "residual") else c(self.variables))
                              for c in self.constraints)
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
        for c, label in zip(self.constraints, self.constraint_labels):
            count = len(c.residual(self.variables) if hasattr(c, "residual") else c(self.variables))
            subres = residuals[i:i+count]
            if any(abs(r) > tolerance for r in subres):
                self.conflicting_constraints.append(label)
            i += count

    def get_point_coords(self):
        return [pt.get(self.variables) for pt in self.points]


# ========================
# Helper Functions
# ========================

def normalize_degrees(angle: float) -> float:
    return ((angle % 360) + 360) % 360

def vector_angle(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    return math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))


# ======================
# Geometry Classes
# ======================

class Point2D(object):
    def __init__(self, solver, pt, fixed=False):
        self.xi = solver.add_variable(pt[0], fixed=fixed)
        self.yi = solver.add_variable(pt[1], fixed=fixed)
        solver.points.append(self)

    def get(self, vars) -> Tuple[float, float]:
        return vars[self.xi], vars[self.yi]

    def distance_to(self, vars, px: float, py: float) -> float:
        x, y = self.get(vars)
        return math.hypot(x - px, y - py)

    def degrees_from_origin(self, vars) -> float:
        x, y = self.get(vars)
        return math.degrees(math.atan2(y, x))


class LineSegment(object):
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

    def closest_part(self, vars, px: float, py: float) -> float:
        x0, y0, x1, y1 = self.get(vars)
        dx = x1 - x0
        dy = y1 - y0
        l_len = math.hypot(dx, dy)
        if l_len == 0:
            return 0.0
        t = ((px - x0) * dx + (py - y0) * dy) / l_len**2
        if t < 0:
            return 0.0
        if t > 1:
            return 1.0
        return t

    def closest_point(self, vars, px: float, py: float) -> Tuple[float, float]:
        t = self.closest_part(vars, px, py)
        x0, y0, x1, y1 = self.get(vars)
        return (
            x0 + t * (x1 - x0),
            y0 + t * (y1 - y0)
        )

    def distance_to(self, vars, px: float, py: float) -> float:
        cx, cy = self.closest_point(vars, px, py)
        return math.hypot(cx - px, cy - py)

    def angle(self, vars) -> float:
        x0, y0, x1, y1 = self.get(vars)
        return math.degrees(math.atan2(y1 - y0, x1 - x0))


class Circle(object):
    def __init__(
        self,
        solver,
        center: Point2D,
        radius: float,
        fixed_radius: bool = False
    ):
        self.center = center
        self.radius_index = solver.add_variable(radius, fixed=fixed_radius)
        solver.circles.append(self)

    def get(self, vars) -> Tuple[float, float, float]:
        cx, cy = self.center.get(vars)
        r = vars[self.radius_index]
        return cx, cy, r
    
    def closest_point_on_perimeter(
        self,
        vars,
        px: float,
        py: float
    ) -> Optional[Tuple[float, float]]:
        cx, cy, r = self.get(vars)
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

    def distance_to_perimeter(self, vars, px: float, py: float) -> float:
        closest_pt = self.closest_point_on_perimeter(vars, px, py)
        cx, cy, r = self.get(vars)
        if closest_pt is None:
            return math.hypot(px - cx, py - cy)
        return math.hypot(closest_pt[0] - px, closest_pt[1] - py)


class Ellipse(object):
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
        px: float,
        py: float
    ) -> Optional[Tuple[float, float]]:
        """
        Finds the closest point on the ellipse perimeter to the given point.
        Uses numerical optimization to find the minimum distance.
        """
        cx, cy, major_r, minor_r, rotation = self.get(vars)
        
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

    def distance_to_perimeter(self, vars, px: float, py: float) -> float:
        closest_pt = self.closest_point_on_perimeter(vars, px, py)
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


class Arc(object):
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

    def angle_from_arc_span(self, vars, angle: float) -> float:
        """
        Returns the angle between the given angle and the arc span.
        If the angle is within the arc span, the angle is returned as 0.
        If the angle is outside the arc span, the angle is returned as the
        difference between the angle and the closest of the start or end angle.
        """
        angle = normalize_degrees(angle)
        start_angle = self.start_angle(vars)
        end_angle = self.end_angle(vars)
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


class BezierPath(object):
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

    def closest_path_part(self, vars, px: float, py: float) -> float:
        def dist(t: float) -> float:
            x, y = self.path_point(vars, t)
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

    def closest_path_point(self, vars, px: float, py: float) -> Tuple[float, float]:
        t = self.closest_path_part(vars, px, py)
        return self.path_point(vars, t)


# ============================
# Point Constraint Functions
# ============================

class CoincidentConstraint(Constraint):
    def __init__(self, p1: Point2D, p2: Point2D):
        self.p1, self.p2 = p1, p2

    def residual(self, x):
        return np.array([
            x[self.p1.xi] - x[self.p2.xi],
            x[self.p1.yi] - x[self.p2.yi]
        ])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((2, n))
        J[0, self.p1.xi] = 1
        J[0, self.p2.xi] = -1
        J[1, self.p1.yi] = 1
        J[1, self.p2.yi] = -1
        return J


class HorizontalConstraint(Constraint):
    def __init__(self, p1, p2):
        self.p1, self.p2 = p1, p2

    def residual(self, x):
        return np.array([x[self.p1.yi] - x[self.p2.yi]])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((1, n))
        # d(Δy)/d(y1) = 1, d(Δy)/d(y2) = -1
        J[0, self.p1.yi] = 1
        J[0, self.p2.yi] = -1
        return J


class VerticalConstraint(Constraint):
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2

    def residual(self, x):
        # Vertical means Δx = 0
        return np.array([x[self.p1.xi] - x[self.p2.xi]])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((1, n))
        # d(Δx)/d(x1) = 1, d(Δx)/d(x2) = -1
        J[0, self.p1.xi] = 1
        J[0, self.p2.xi] = -1
        return J


class PointIsOnLineSegmentConstraint(Constraint):
    def __init__(self, point: Point2D, line: LineSegment):
        self.point = point
        self.line = line

    def residual(self, x):
        # Point is on line if the cross product of vectors is zero
        # (px - lx1) * (ly2 - ly1) - (py - ly1) * (lx2 - lx1) = 0
        px, py = x[self.point.xi], x[self.point.yi]
        lx1, ly1 = x[self.line.p1.xi], x[self.line.p1.yi]
        lx2, ly2 = x[self.line.p2.xi], x[self.line.p2.yi]
        
        # First constraint: point is on the infinite line
        on_line = (px - lx1) * (ly2 - ly1) - (py - ly1) * (lx2 - lx1)
        
        # Second constraint: point is within segment bounds (0 <= t <= 1)
        # Calculate parameter t where point = p1 + t * (p2 - p1)
        dx = lx2 - lx1
        dy = ly2 - ly1
        if abs(dx) > abs(dy):
            # Use x-coordinate for parameter calculation
            t = (px - lx1) / dx if dx != 0 else 0
        else:
            # Use y-coordinate for parameter calculation
            t = (py - ly1) / dy if dy != 0 else 0
        
        # Constrain t to be between 0 and 1
        # We use soft constraints to keep t in bounds
        t_min = max(0, t - 1)  # t should be >= 0, so t_min should be <= 0
        t_max = min(0, t - 1)  # t should be <= 1, so t_max should be <= 0
        
        return np.array([on_line, t_min, t_max])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((3, n))
        
        px, py = x[self.point.xi], x[self.point.yi]
        lx1, ly1 = x[self.line.p1.xi], x[self.line.p1.yi]
        lx2, ly2 = x[self.line.p2.xi], x[self.line.p2.yi]
        
        dx = lx2 - lx1
        dy = ly2 - ly1
        
        # First row: on_line constraint
        # Residual: (px - lx1) * (ly2 - ly1) - (py - ly1) * (lx2 - lx1)
        J[0, self.point.xi] = dy  # d/dpx
        J[0, self.point.yi] = -dx  # d/dpy
        J[0, self.line.p1.xi] = -dy + (py - ly1)  # d/dlx1
        J[0, self.line.p1.yi] = (px - lx1) + dx  # d/dly1
        J[0, self.line.p2.xi] = (py - ly1)  # d/dlx2
        J[0, self.line.p2.yi] = -(px - lx1)  # d/dly2
        
        # Calculate parameter t
        if abs(dx) > abs(dy):
            t = (px - lx1) / dx if dx != 0 else 0
            dt_dpx = 1.0 / dx if dx != 0 else 0
            dt_dpy = 0
            dt_dlx1 = -1.0 / dx if dx != 0 else 0
            dt_dly1 = 0
            dt_dlx2 = 0
            dt_dly2 = 0
        else:
            t = (py - ly1) / dy if dy != 0 else 0
            dt_dpx = 0
            dt_dpy = 1.0 / dy if dy != 0 else 0
            dt_dlx1 = 0
            dt_dly1 = -1.0 / dy if dy != 0 else 0
            dt_dlx2 = 0
            dt_dly2 = 0
        
        # Second row: t >= 0 constraint (t_min = max(0, t - 1))
        if t > 1:
            J[1, self.point.xi] = dt_dpx
            J[1, self.point.yi] = dt_dpy
            J[1, self.line.p1.xi] = dt_dlx1
            J[1, self.line.p1.yi] = dt_dly1
            J[1, self.line.p2.xi] = dt_dlx2
            J[1, self.line.p2.yi] = dt_dly2
        
        # Third row: t <= 1 constraint (t_max = min(0, t - 1))
        if t < 0:
            J[2, self.point.xi] = dt_dpx
            J[2, self.point.yi] = dt_dpy
            J[2, self.line.p1.xi] = dt_dlx1
            J[2, self.line.p1.yi] = dt_dly1
            J[2, self.line.p2.xi] = dt_dlx2
            J[2, self.line.p2.yi] = dt_dly2
        
        return J


class PointIsOnArcConstraint(Constraint):
    def __init__(self, point: Point2D, arc: Arc):
        self.point = point
        self.arc = arc

    def residual(self, x):
        px, py = x[self.point.xi], x[self.point.yi]
        cx, cy, r, theta1, theta2 = x[self.arc.center.xi], x[self.arc.center.yi], x[self.arc.radius_index], x[self.arc.start_angle_index], x[self.arc.end_angle_index]
        
        # First constraint: point is at the arc radius
        radius_constraint = math.hypot(px - cx, py - cy) - r
        
        # Second constraint: point angle is within arc span
        point_angle = math.degrees(math.atan2(py - cy, px - cx))
        angle_constraint = self.arc.angle_from_arc_span(x, point_angle)
        
        return np.array([radius_constraint, angle_constraint])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((2, n))
        
        px, py = x[self.point.xi], x[self.point.yi]
        cx, cy, r, theta1, theta2 = x[self.arc.center.xi], x[self.arc.center.yi], x[self.arc.radius_index], x[self.arc.start_angle_index], x[self.arc.end_angle_index]
        
        # Calculate distances and angles
        dx = px - cx
        dy = py - cy
        dist = math.hypot(dx, dy)
        point_angle = math.degrees(math.atan2(dy, dx))
        
        # First row: radius constraint (distance from center = radius)
        if dist > 0:
            J[0, self.point.xi] = dx / dist  # d/dpx
            J[0, self.point.yi] = dy / dist  # d/dpy
            J[0, self.arc.center.xi] = -dx / dist  # d/dcx
            J[0, self.arc.center.yi] = -dy / dist  # d/dcy
            J[0, self.arc.radius_index] = -1  # d/dr
        else:
            # Handle case where point is at center
            J[0, self.point.xi] = 1
            J[0, self.point.yi] = 1
            J[0, self.arc.center.xi] = -1
            J[0, self.arc.center.yi] = -1
            J[0, self.arc.radius_index] = -1
        
        # Second row: angle constraint (point angle within arc span)
        # This uses the arc's angle_from_arc_span method
        # We need to calculate the derivative of angle_from_arc_span
        if dist > 0:
            # Derivative of atan2(dy, dx) with respect to point coordinates
            J[1, self.point.xi] = -dy / (dist**2)  # d/dpx of angle
            J[1, self.point.yi] = dx / (dist**2)   # d/dpy of angle
            J[1, self.arc.center.xi] = dy / (dist**2)  # d/dcx of angle
            J[1, self.arc.center.yi] = -dx / (dist**2)  # d/dcy of angle
        
        # Derivatives with respect to arc angles depend on the specific implementation
        # of angle_from_arc_span. For now, we'll use a simplified approach
        # that assumes the angle constraint is active when point is outside span
        if dist > 0:
            # Calculate angle difference from start and end angles
            start_angle = normalize_degrees(theta1)
            end_angle = normalize_degrees(theta2)
            point_angle_norm = normalize_degrees(point_angle)
            
            # Determine if point is outside the arc span
            if start_angle > end_angle:
                # Arc crosses 0 degrees
                if point_angle_norm < start_angle and point_angle_norm > end_angle:
                    # Point is outside span, need to move towards closest boundary
                    if abs(point_angle_norm - start_angle) < abs(point_angle_norm - end_angle):
                        # Closer to start angle
                        J[1, self.arc.start_angle_index] = 1
                    else:
                        # Closer to end angle
                        J[1, self.arc.end_angle_index] = -1
            else:
                # Normal arc span
                if point_angle_norm < start_angle:
                    J[1, self.arc.start_angle_index] = 1
                elif point_angle_norm > end_angle:
                    J[1, self.arc.end_angle_index] = -1
        
        return J


class PointCoincidentWithArcStartConstraint(Constraint):
    def __init__(self, point: Point2D, arc: Arc):
        self.point = point
        self.arc = arc

    def residual(self, x):
        px, py = x[self.point.xi], x[self.point.yi]
        cx, cy, r, theta1, theta2 = x[self.arc.center.xi], x[self.arc.center.yi], x[self.arc.radius_index], x[self.arc.start_angle_index], x[self.arc.end_angle_index]
        
        # Calculate arc start point coordinates
        start_x = cx + r * math.cos(math.radians(theta1))
        start_y = cy + r * math.sin(math.radians(theta1))
        
        # Constraint: point should coincide with arc start point
        return np.array([
            start_x - px,  # x-coordinate difference
            start_y - py   # y-coordinate difference
        ])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((2, n))
        
        cx, cy, r, theta1, theta2 = x[self.arc.center.xi], x[self.arc.center.yi], x[self.arc.radius_index], x[self.arc.start_angle_index], x[self.arc.end_angle_index]
        
        # Arc start point: (cx + r*cos(θ1), cy + r*sin(θ1))
        # Derivatives with respect to arc parameters:
        
        # Derivatives with respect to point coordinates
        J[0, self.point.xi] = -1  # d/dpx of (start_x - px)
        J[1, self.point.yi] = -1  # d/dpy of (start_y - py)
        
        # Derivatives with respect to arc center
        J[0, self.arc.center.xi] = 1  # d/dcx of start_x
        J[1, self.arc.center.yi] = 1  # d/dcy of start_y
        
        # Derivatives with respect to radius
        J[0, self.arc.radius_index] = math.cos(math.radians(theta1))  # d/dr of start_x
        J[1, self.arc.radius_index] = math.sin(math.radians(theta1))  # d/dr of start_y
        
        # Derivatives with respect to start angle
        J[0, self.arc.start_angle_index] = -r * math.sin(math.radians(theta1)) * math.radians(1)  # d/dθ1 of start_x
        J[1, self.arc.start_angle_index] = r * math.cos(math.radians(theta1)) * math.radians(1)   # d/dθ1 of start_y
        
        return J


class PointCoincidentWithArcEndConstraint(Constraint):
    def __init__(self, point: Point2D, arc: Arc):
        self.point = point
        self.arc = arc

    def residual(self, x):
        px, py = x[self.point.xi], x[self.point.yi]
        cx, cy, r, theta1, theta2 = x[self.arc.center.xi], x[self.arc.center.yi], x[self.arc.radius_index], x[self.arc.start_angle_index], x[self.arc.end_angle_index]
        
        # Calculate arc end point coordinates
        end_x = cx + r * math.cos(math.radians(theta2))
        end_y = cy + r * math.sin(math.radians(theta2))
        
        # Constraint: point should coincide with arc end point
        return np.array([
            end_x - px,  # x-coordinate difference
            end_y - py   # y-coordinate difference
        ])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((2, n))
        
        cx, cy, r, theta1, theta2 = x[self.arc.center.xi], x[self.arc.center.yi], x[self.arc.radius_index], x[self.arc.start_angle_index], x[self.arc.end_angle_index]
        
        # Arc end point: (cx + r*cos(θ2), cy + r*sin(θ2))
        # Derivatives with respect to arc parameters:
        
        # Derivatives with respect to point coordinates
        J[0, self.point.xi] = -1  # d/dpx of (end_x - px)
        J[1, self.point.yi] = -1  # d/dpy of (end_y - py)
        
        # Derivatives with respect to arc center
        J[0, self.arc.center.xi] = 1  # d/dcx of end_x
        J[1, self.arc.center.yi] = 1  # d/dcy of end_y
        
        # Derivatives with respect to radius
        J[0, self.arc.radius_index] = math.cos(math.radians(theta2))  # d/dr of end_x
        J[1, self.arc.radius_index] = math.sin(math.radians(theta2))  # d/dr of end_y
        
        # Derivatives with respect to end angle
        J[0, self.arc.end_angle_index] = -r * math.sin(math.radians(theta2)) * math.radians(1)  # d/dθ2 of end_x
        J[1, self.arc.end_angle_index] = r * math.cos(math.radians(theta2)) * math.radians(1)   # d/dθ2 of end_y
        
        return J


class PointIsOnCircleConstraint(Constraint):
    def __init__(self, point: Point2D, circle: Circle):
        self.point = point
        self.circle = circle

    def residual(self, x):
        px, py = x[self.point.xi], x[self.point.yi]
        cx, cy, r = x[self.circle.center.xi], x[self.circle.center.yi], x[self.circle.radius_index]
        
        # Constraint: distance from point to center equals radius
        distance = math.hypot(px - cx, py - cy)
        return np.array([distance - r])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((1, n))
        
        px, py = x[self.point.xi], x[self.point.yi]
        cx, cy, r = x[self.circle.center.xi], x[self.circle.center.yi], x[self.circle.radius_index]
        
        # Calculate distance
        dx = px - cx
        dy = py - cy
        distance = math.hypot(dx, dy)
        
        if distance > 0:
            # Derivatives of distance = sqrt((px-cx)² + (py-cy)²)
            J[0, self.point.xi] = dx / distance  # d/dpx
            J[0, self.point.yi] = dy / distance  # d/dpy
            J[0, self.circle.center.xi] = -dx / distance  # d/dcx
            J[0, self.circle.center.yi] = -dy / distance  # d/dcy
            J[0, self.circle.radius_index] = -1  # d/dr
        else:
            # Handle case where point is at center (distance = 0)
            J[0, self.point.xi] = 1
            J[0, self.point.yi] = 1
            J[0, self.circle.center.xi] = -1
            J[0, self.circle.center.yi] = -1
            J[0, self.circle.radius_index] = -1
        
        return J


class PointIsOnEllipseConstraint(Constraint):
    def __init__(self, point: Point2D, ellipse: Ellipse):
        self.point = point
        self.ellipse = ellipse

    def residual(self, x):
        # Calculate the distance from point to ellipse perimeter
        px, py = self.point.get(x)
        closest_pt = self.ellipse.closest_point_on_perimeter(x, px, py)
        
        if closest_pt is None:
            return np.array([1.0])  # Return non-zero residual if no closest point found
        
        # Distance from point to closest point on ellipse
        dist = np.sqrt((px - closest_pt[0])**2 + (py - closest_pt[1])**2)
        return np.array([dist])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((1, n))
        
        px, py = self.point.get(x)
        closest_pt = self.ellipse.closest_point_on_perimeter(x, px, py)
        
        if closest_pt is not None:
            dist = np.sqrt((px - closest_pt[0])**2 + (py - closest_pt[1])**2)
            
            if dist > 1e-10:
                # Derivatives with respect to point coordinates
                J[0, self.point.xi] = (px - closest_pt[0]) / dist
                J[0, self.point.yi] = (py - closest_pt[1]) / dist
                
                # Derivatives with respect to ellipse center
                J[0, self.ellipse.center.xi] = -(px - closest_pt[0]) / dist
                J[0, self.ellipse.center.yi] = -(py - closest_pt[1]) / dist
                
                # Derivatives with respect to ellipse radii and rotation
                # These are complex and would require numerical differentiation
                # For now, we'll use numerical differentiation for these parameters
                eps = 1e-6
                for i in [self.ellipse.radius1_index, self.ellipse.radius2_index, self.ellipse.rotation_index]:
                    x_plus = x.copy()
                    x_plus[i] += eps
                    closest_pt_plus = self.ellipse.closest_point_on_perimeter(x_plus, px, py)
                    if closest_pt_plus is not None:
                        dist_plus = np.sqrt((px - closest_pt_plus[0])**2 + (py - closest_pt_plus[1])**2)
                        J[0, i] = (dist_plus - dist) / eps
                    else:
                        J[0, i] = 0
            else:
                # Point is at ellipse center, derivatives are zero
                J[0, self.ellipse.radius1_index] = 0
                J[0, self.ellipse.radius2_index] = 0
                J[0, self.ellipse.rotation_index] = 0
        else:
            # Handle case where point is exactly on perimeter
            J[0, self.point.xi] = 1
            J[0, self.point.yi] = 1
            J[0, self.ellipse.center.xi] = -1
            J[0, self.ellipse.center.yi] = -1
        
        return J


class PointIsOnBezierPathConstraint(Constraint):
    def __init__(self, point: Point2D, bezier: BezierPath):
        self.point = point
        self.bezier = bezier

    def residual(self, x):
        px, py = x[self.point.xi], x[self.point.yi]
        
        # Find the closest point on the bezier path
        t = self.bezier.closest_path_part(x, px, py)
        bezier_point = self.bezier.path_point(x, t)
        
        # Constraint: point should coincide with the closest point on bezier
        return np.array([
            bezier_point[0] - px,  # x-coordinate difference
            bezier_point[1] - py   # y-coordinate difference
        ])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((2, n))
        
        px, py = x[self.point.xi], x[self.point.yi]
        
        # Find the closest point and parameter t
        t = self.bezier.closest_path_part(x, px, py)
        bezier_point = self.bezier.path_point(x, t)
        
        # Derivatives with respect to point coordinates
        J[0, self.point.xi] = -1  # d/dpx of (bezier_x - px)
        J[1, self.point.yi] = -1  # d/dpy of (bezier_y - py)
        
        # Derivatives with respect to bezier control points
        # We need to account for both:
        # 1. Direct effect: how bezier_point changes with control points (at fixed t)
        # 2. Indirect effect: how t changes with control points, affecting bezier_point
        
        # Calculate derivatives of bezier_point with respect to control points
        # This depends on the specific bezier segment where t lies
        segs = (len(self.bezier.points) - 1) // 3
        if t == 1.0:
            seg = segs - 1
            t_seg = 1.0
        else:
            t_scaled = t * segs
            seg = int(t_scaled)
            t_seg = t_scaled - seg
        
        # Get the control points for this segment
        p0_idx = seg * 3
        p1_idx = p0_idx + 1
        p2_idx = p0_idx + 2
        p3_idx = p0_idx + 3
        
        # Bezier point calculation: B(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
        # Direct derivatives with respect to control points:
        # ∂B/∂P₀ = (1-t)³, ∂B/∂P₁ = 3(1-t)²t, ∂B/∂P₂ = 3(1-t)t², ∂B/∂P₃ = t³
        
        # Direct derivatives for x-coordinate
        J[0, self.bezier.points[p0_idx].xi] = (1 - t_seg)**3
        J[0, self.bezier.points[p1_idx].xi] = 3 * (1 - t_seg)**2 * t_seg
        J[0, self.bezier.points[p2_idx].xi] = 3 * (1 - t_seg) * t_seg**2
        J[0, self.bezier.points[p3_idx].xi] = t_seg**3
        
        # Direct derivatives for y-coordinate
        J[1, self.bezier.points[p0_idx].yi] = (1 - t_seg)**3
        J[1, self.bezier.points[p1_idx].yi] = 3 * (1 - t_seg)**2 * t_seg
        J[1, self.bezier.points[p2_idx].yi] = 3 * (1 - t_seg) * t_seg**2
        J[1, self.bezier.points[p3_idx].yi] = t_seg**3
        
        # Now we need to account for the indirect effect: how t changes with control points
        # The closest point condition implies that the tangent at t is perpendicular to (point - bezier_point)
        # This gives us a relationship between dt and the control points
        
        # Calculate the tangent vector at t
        # Tangent: B'(t) = -3(1-t)²P₀ + 3(1-t)²P₁ - 6(1-t)tP₁ + 6(1-t)tP₂ - 3t²P₂ + 3t²P₃
        # Simplified: B'(t) = 3(1-t)²(P₁-P₀) + 6(1-t)t(P₂-P₁) + 3t²(P₃-P₂)
        
        # Get control point coordinates for this segment
        p0x, p0y = x[self.bezier.points[p0_idx].xi], x[self.bezier.points[p0_idx].yi]
        p1x, p1y = x[self.bezier.points[p1_idx].xi], x[self.bezier.points[p1_idx].yi]
        p2x, p2y = x[self.bezier.points[p2_idx].xi], x[self.bezier.points[p2_idx].yi]
        p3x, p3y = x[self.bezier.points[p3_idx].xi], x[self.bezier.points[p3_idx].yi]
        
        # Calculate tangent vector components
        tangent_x = 3 * (1 - t_seg)**2 * (p1x - p0x) + 6 * (1 - t_seg) * t_seg * (p2x - p1x) + 3 * t_seg**2 * (p3x - p2x)
        tangent_y = 3 * (1 - t_seg)**2 * (p1y - p0y) + 6 * (1 - t_seg) * t_seg * (p2y - p1y) + 3 * t_seg**2 * (p3y - p2y)
        
        # Calculate the vector from bezier point to the target point
        dx = px - bezier_point[0]
        dy = py - bezier_point[1]
        
        # The closest point condition: tangent ⊥ (point - bezier_point)
        # This means: tangent_x * dx + tangent_y * dy = 0
        # Taking derivatives with respect to control points gives us dt/dP
        
        # Calculate the second derivative of the bezier curve (needed for dt/dP)
        # B''(t) = 6(1-t)(P₂-2P₁+P₀) + 6t(P₃-2P₂+P₁)
        d2x = 6 * (1 - t_seg) * (p2x - 2*p1x + p0x) + 6 * t_seg * (p3x - 2*p2x + p1x)
        d2y = 6 * (1 - t_seg) * (p2y - 2*p1y + p0y) + 6 * t_seg * (p3y - 2*p2y + p1y)
        
        # The condition for closest point: d/dt(|point - B(t)|²) = 0
        # This gives: tangent_x * dx + tangent_y * dy = 0
        # Taking derivatives with respect to control points:
        # ∂tangent_x/∂P * dx + tangent_x * ∂dx/∂P + ∂tangent_y/∂P * dy + tangent_y * ∂dy/∂P = 0
        
        # Calculate the denominator for dt/dP (from implicit differentiation)
        # This is the derivative of the closest point condition with respect to t
        denominator = tangent_x * tangent_x + tangent_y * tangent_y + dx * d2x + dy * d2y
        
        if abs(denominator) > 1e-10:
            # Calculate dt/dP for each control point
            # We need to calculate how the tangent changes with each control point
            
            # Derivatives of tangent with respect to control points
            # ∂tangent_x/∂P₀ = -3(1-t)², ∂tangent_x/∂P₁ = 3(1-t)² - 6(1-t)t, etc.
            dt_dp0x = (-3 * (1 - t_seg)**2 * dx - 3 * (1 - t_seg)**2 * dy) / denominator
            dt_dp1x = ((3 * (1 - t_seg)**2 - 6 * (1 - t_seg) * t_seg) * dx + 
                       (3 * (1 - t_seg)**2 - 6 * (1 - t_seg) * t_seg) * dy) / denominator
            dt_dp2x = ((6 * (1 - t_seg) * t_seg - 3 * t_seg**2) * dx + 
                       (6 * (1 - t_seg) * t_seg - 3 * t_seg**2) * dy) / denominator
            dt_dp3x = (3 * t_seg**2 * dx + 3 * t_seg**2 * dy) / denominator
            
            # Similar for y-coordinates
            dt_dp0y = (-3 * (1 - t_seg)**2 * dx - 3 * (1 - t_seg)**2 * dy) / denominator
            dt_dp1y = ((3 * (1 - t_seg)**2 - 6 * (1 - t_seg) * t_seg) * dx + 
                       (3 * (1 - t_seg)**2 - 6 * (1 - t_seg) * t_seg) * dy) / denominator
            dt_dp2y = ((6 * (1 - t_seg) * t_seg - 3 * t_seg**2) * dx + 
                       (6 * (1 - t_seg) * t_seg - 3 * t_seg**2) * dy) / denominator
            dt_dp3y = (3 * t_seg**2 * dx + 3 * t_seg**2 * dy) / denominator
            
            # Now add the indirect effect: ∂B/∂t * dt/dP
            # ∂B/∂t = tangent vector
            # Add this to the direct derivatives
            J[0, self.bezier.points[p0_idx].xi] += tangent_x * dt_dp0x
            J[0, self.bezier.points[p1_idx].xi] += tangent_x * dt_dp1x
            J[0, self.bezier.points[p2_idx].xi] += tangent_x * dt_dp2x
            J[0, self.bezier.points[p3_idx].xi] += tangent_x * dt_dp3x
            
            J[1, self.bezier.points[p0_idx].yi] += tangent_y * dt_dp0y
            J[1, self.bezier.points[p1_idx].yi] += tangent_y * dt_dp1y
            J[1, self.bezier.points[p2_idx].yi] += tangent_y * dt_dp2y
            J[1, self.bezier.points[p3_idx].yi] += tangent_y * dt_dp3y
        
        return J


# ============================
# Line Constraint Functions
# ============================

class LineAngleConstraint(Constraint):
    def __init__(self, line: LineSegment, angle: float):
        self.line = line
        self.angle = angle

    def residual(self, x):
        # Calculate the current line angle
        x0, y0 = x[self.line.p1.xi], x[self.line.p1.yi]
        x1, y1 = x[self.line.p2.xi], x[self.line.p2.yi]
        
        # Calculate current angle in degrees
        current_angle = math.degrees(math.atan2(y1 - y0, x1 - x0))
        
        # Constraint: line angle should equal target angle
        return np.array([current_angle - self.angle])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((1, n))
        
        x0, y0 = x[self.line.p1.xi], x[self.line.p1.yi]
        x1, y1 = x[self.line.p2.xi], x[self.line.p2.yi]
        
        # Calculate line direction vector
        dx = x1 - x0
        dy = y1 - y0
        length_squared = dx*dx + dy*dy
        
        if length_squared > 0:
            # Angle is atan2(dy, dx)
            # Derivatives of atan2(dy, dx):
            # ∂angle/∂x0 = -dy / (dx² + dy²)
            # ∂angle/∂y0 = dx / (dx² + dy²)
            # ∂angle/∂x1 = dy / (dx² + dy²)
            # ∂angle/∂y1 = -dx / (dx² + dy²)
            
            J[0, self.line.p1.xi] = -dy / length_squared  # d/dx0
            J[0, self.line.p1.yi] = dx / length_squared   # d/dy0
            J[0, self.line.p2.xi] = dy / length_squared   # d/dx1
            J[0, self.line.p2.yi] = -dx / length_squared  # d/dy1
        else:
            # Handle case where line has zero length
            # In this case, angle is undefined, so we set derivatives to zero
            pass
        
        return J


class LineLengthConstraint(Constraint):
    def __init__(self, line: LineSegment, length: float):
        self.line = line
        self.length = length

    def residual(self, x):
        # Calculate the current line length
        x0, y0 = x[self.line.p1.xi], x[self.line.p1.yi]
        x1, y1 = x[self.line.p2.xi], x[self.line.p2.yi]
        
        # Calculate current length
        dx = x1 - x0
        dy = y1 - y0
        current_length = math.hypot(dx, dy)
        
        # Constraint: line length should equal target length
        return np.array([current_length - self.length])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((1, n))
        
        x0, y0 = x[self.line.p1.xi], x[self.line.p1.yi]
        x1, y1 = x[self.line.p2.xi], x[self.line.p2.yi]
        
        # Calculate line direction vector and length
        dx = x1 - x0
        dy = y1 - y0
        current_length = math.hypot(dx, dy)
        
        if current_length > 0:
            # Length is sqrt(dx² + dy²)
            # Derivatives:
            # ∂length/∂x0 = -dx / length
            # ∂length/∂y0 = -dy / length
            # ∂length/∂x1 = dx / length
            # ∂length/∂y1 = dy / length
            
            J[0, self.line.p1.xi] = -dx / current_length  # d/dx0
            J[0, self.line.p1.yi] = -dy / current_length  # d/dy0
            J[0, self.line.p2.xi] = dx / current_length   # d/dx1
            J[0, self.line.p2.yi] = dy / current_length   # d/dy1
        else:
            # Handle case where line has zero length
            # In this case, derivatives are undefined, so we set them to zero
            pass
        
        return J


class LinesEqualLengthConstraint(Constraint):
    def __init__(self, l1: LineSegment, l2: LineSegment):
        self.l1 = l1
        self.l2 = l2

    def residual(self, x):
        def sqdist(line):
            return (x[line.p2.xi] - x[line.p1.xi])**2 + (x[line.p2.yi] - x[line.p1.yi])**2
        return np.array([sqdist(self.l1) - sqdist(self.l2)])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((1, n))

        # Line1 derivatives
        dx1 = x[self.l1.p2.xi] - x[self.l1.p1.xi]
        dy1 = x[self.l1.p2.yi] - x[self.l1.p1.yi]
        J[0, self.l1.p1.xi] += -2 * dx1
        J[0, self.l1.p1.yi] += -2 * dy1
        J[0, self.l1.p2.xi] += 2 * dx1
        J[0, self.l1.p2.yi] += 2 * dy1

        # Line2 derivatives (subtract)
        dx2 = x[self.l2.p2.xi] - x[self.l2.p1.xi]
        dy2 = x[self.l2.p2.yi] - x[self.l2.p1.yi]
        J[0, self.l2.p1.xi] += 2 * dx2
        J[0, self.l2.p1.yi] += 2 * dy2
        J[0, self.l2.p2.xi] += -2 * dx2
        J[0, self.l2.p2.yi] += -2 * dy2

        return J


class LinesPerpendicularConstraint(Constraint):
    def __init__(self, l1: LineSegment, l2: LineSegment):
        self.l1 = l1
        self.l2 = l2

    def residual(self, x):
        dx1 = x[self.l1.p2.xi] - x[self.l1.p1.xi]
        dy1 = x[self.l1.p2.yi] - x[self.l1.p1.yi]
        dx2 = x[self.l2.p2.xi] - x[self.l2.p1.xi]
        dy2 = x[self.l2.p2.yi] - x[self.l2.p1.yi]
        return np.array([dx1 * dx2 + dy1 * dy2])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((1, n))

        dx1 = x[self.l1.p2.xi] - x[self.l1.p1.xi]
        dy1 = x[self.l1.p2.yi] - x[self.l1.p1.yi]
        dx2 = x[self.l2.p2.xi] - x[self.l2.p1.xi]
        dy2 = x[self.l2.p2.yi] - x[self.l2.p1.yi]

        J[0, self.l1.p1.xi] = -dx2
        J[0, self.l1.p1.yi] = -dy2
        J[0, self.l1.p2.xi] = dx2
        J[0, self.l1.p2.yi] = dy2

        J[0, self.l2.p1.xi] = -dx1
        J[0, self.l2.p1.yi] = -dy1
        J[0, self.l2.p2.xi] = dx1
        J[0, self.l2.p2.yi] = dy1

        return J


class LinesParallelConstraint(Constraint):
    """
    Ensures that two line segments are parallel.
    Uses the cross product: dx1*dy2 - dy1*dx2 = 0
    """
    def __init__(self, l1: LineSegment, l2: LineSegment):
        self.l1 = l1
        self.l2 = l2

    def residual(self, x):
        dx1 = x[self.l1.p2.xi] - x[self.l1.p1.xi]
        dy1 = x[self.l1.p2.yi] - x[self.l1.p1.yi]
        dx2 = x[self.l2.p2.xi] - x[self.l2.p1.xi]
        dy2 = x[self.l2.p2.yi] - x[self.l2.p1.yi]
        return np.array([dx1 * dy2 - dy1 * dx2])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((1, n))

        # Line directions
        dx1 = x[self.l1.p2.xi] - x[self.l1.p1.xi]
        dy1 = x[self.l1.p2.yi] - x[self.l1.p1.yi]
        dx2 = x[self.l2.p2.xi] - x[self.l2.p1.xi]
        dy2 = x[self.l2.p2.yi] - x[self.l2.p1.yi]

        # Partial derivatives:
        # r = dx1*dy2 - dy1*dx2
        # For line1
        J[0, self.l1.p1.xi] = -dy2
        J[0, self.l1.p1.yi] =  dx2
        J[0, self.l1.p2.xi] =  dy2
        J[0, self.l1.p2.yi] = -dx2

        # For line2
        J[0, self.l2.p1.xi] =  dy1
        J[0, self.l2.p1.yi] = -dx1
        J[0, self.l2.p2.xi] = -dy1
        J[0, self.l2.p2.yi] =  dx1

        return J


class LineTangentToArcConstraint(Constraint):
    def __init__(self, line: LineSegment, arc: Arc, at_start: bool = True):
        self.arc = arc
        self.line = line
        self.at_start = at_start

    def residual(self, x):
        theta = x[self.arc.start_angle_index if self.at_start else self.arc.end_angle_index]
        tx = -np.sin(theta)
        ty =  np.cos(theta)
        p1x, p1y = x[self.line.p1.xi], x[self.line.p1.yi]
        p2x, p2y = x[self.line.p2.xi], x[self.line.p2.yi]
        dx = p2x - p1x
        dy = p2y - p1y
        return np.array([dx * ty - dy * tx])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((1, n))

        angle_index = self.arc.start_angle_index if self.at_start else self.arc.end_angle_index
        theta = x[angle_index]
        tx = -np.sin(theta)
        ty =  np.cos(theta)
        p1x, p1y = x[self.line.p1.xi], x[self.line.p1.yi]
        p2x, p2y = x[self.line.p2.xi], x[self.line.p2.yi]
        dx = p2x - p1x
        dy = p2y - p1y

        # Partial derivatives
        J[0, angle_index] = -dx * np.sin(theta) - dy * np.cos(theta)
        J[0, self.line.p2.xi] = ty
        J[0, self.line.p2.yi] = -tx
        J[0, self.line.p1.xi] = -ty
        J[0, self.line.p1.yi] = tx

        return J


class LineTangentToCircleConstraint(Constraint):
    def __init__(self, line: LineSegment, circle: Circle):
        self.line = line
        self.circle = circle

    def residual(self, x):
        # Find the closest point on the line to the circle center
        cx, cy = x[self.circle.center.xi], x[self.circle.center.yi]
        clx, cly = self.line.closest_point(x, cx, cy)
        r = x[self.circle.radius_index]
        
        # Calculate distance from circle center to closest point on line
        dist = math.hypot(clx - cx, cly - cy)
        
        # Constraint: distance should equal circle radius (tangent condition)
        return np.array([dist - r])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((1, n))
        
        # Get line and circle parameters
        x0, y0 = x[self.line.p1.xi], x[self.line.p1.yi]
        x1, y1 = x[self.line.p2.xi], x[self.line.p2.yi]
        cx, cy, r = x[self.circle.center.xi], x[self.circle.center.yi], x[self.circle.radius_index]
        
        # Calculate line direction and length
        dx = x1 - x0
        dy = y1 - y0
        line_length_squared = dx*dx + dy*dy
        
        if line_length_squared > 0:
            # Find closest point on line to circle center
            # Parameter t where closest point is: t = ((cx-x0)*dx + (cy-y0)*dy) / (dx² + dy²)
            t = ((cx - x0) * dx + (cy - y0) * dy) / line_length_squared
            t = max(0, min(1, t))  # Clamp to line segment
            
            # Closest point coordinates
            clx = x0 + t * dx
            cly = y0 + t * dy
            
            # Distance from circle center to closest point
            dist = math.hypot(clx - cx, cly - cy)
            
            if dist > 0:
                # Derivatives of distance with respect to variables
                # ∂dist/∂clx = (clx - cx) / dist
                # ∂dist/∂cly = (cly - cy) / dist
                # ∂dist/∂cx = -(clx - cx) / dist
                # ∂dist/∂cy = -(cly - cy) / dist
                # ∂dist/∂r = -1
                
                # Derivatives of closest point with respect to line endpoints
                # ∂clx/∂x0 = 1 - t * dx/dx = 1 - t
                # ∂clx/∂y0 = 0
                # ∂clx/∂x1 = t
                # ∂clx/∂y1 = 0
                # ∂cly/∂x0 = 0
                # ∂cly/∂y0 = 1 - t
                # ∂cly/∂x1 = 0
                # ∂cly/∂y1 = t
                
                # Derivatives of closest point with respect to circle center
                # ∂clx/∂cx = 0 (closest point doesn't depend on circle center)
                # ∂cly/∂cy = 0
                
                # Derivatives of t with respect to line endpoints
                # ∂t/∂x0 = -dx / line_length_squared
                # ∂t/∂y0 = -dy / line_length_squared
                # ∂t/∂x1 = dx / line_length_squared
                # ∂t/∂y1 = dy / line_length_squared
                
                # Combined derivatives
                dt_dx0 = -dx / line_length_squared
                dt_dx1 = dx / line_length_squared
                dt_dy0 = -dy / line_length_squared
                dt_dy1 = dy / line_length_squared
                
                # Derivatives of distance with respect to line endpoints
                J[0, self.line.p1.xi] = ((clx - cx) / dist) * (1 - t) + ((cly - cy) / dist) * 0 + \
                                        ((clx - cx) * dx + (cly - cy) * dy) / dist * dt_dx0
                J[0, self.line.p1.yi] = ((clx - cx) / dist) * 0 + ((cly - cy) / dist) * (1 - t) + \
                                        ((clx - cx) * dx + (cly - cy) * dy) / dist * dt_dy0
                J[0, self.line.p2.xi] = ((clx - cx) / dist) * t + ((cly - cy) / dist) * 0 + \
                                        ((clx - cx) * dx + (cly - cy) * dy) / dist * dt_dx1
                J[0, self.line.p2.yi] = ((clx - cx) / dist) * 0 + ((cly - cy) / dist) * t + \
                                        ((clx - cx) * dx + (cly - cy) * dy) / dist * dt_dy1
                
                # Derivatives with respect to circle parameters
                J[0, self.circle.center.xi] = -(clx - cx) / dist
                J[0, self.circle.center.yi] = -(cly - cy) / dist
                J[0, self.circle.radius_index] = -1
            else:
                # Handle case where closest point is at circle center
                J[0, self.circle.center.xi] = 1
                J[0, self.circle.center.yi] = 1
                J[0, self.circle.radius_index] = -1
        else:
            # Handle case where line has zero length
            # In this case, derivatives are undefined
            pass
        
        return J


class LineTangentToEllipseConstraint(Constraint):
    def __init__(self, line: LineSegment, ellipse: Ellipse):
        self.line = line
        self.ellipse = ellipse

    def residual(self, x):
        # Get line endpoints
        lx1, ly1 = self.line.p1.get(x)
        lx2, ly2 = self.line.p2.get(x)
        
        # Get ellipse parameters
        cx, cy, r1, r2, rotation = self.ellipse.get(x)
        
        # Find the closest point on the ellipse to the line
        # Use line midpoint as initial approximation
        mid_x = (lx1 + lx2) / 2
        mid_y = (ly1 + ly2) / 2
        
        closest_pt = self.ellipse.closest_point_on_perimeter(x, mid_x, mid_y)
        if closest_pt is None:
            return np.array([1.0, 1.0])  # Return non-zero residuals if no closest point found
        
        # Calculate distance from line to closest point
        dist = self.line.distance_to(x, closest_pt[0], closest_pt[1])
        
        # Calculate tangent angle at closest point
        # For ellipse: tangent angle = angle to point + 90 degrees
        angle_to_point = np.arctan2(closest_pt[1] - cy, closest_pt[0] - cx)
        
        # Calculate ellipse tangent angle (perpendicular to radius)
        # This is a simplified approximation - in practice, we'd need to calculate
        # the actual ellipse tangent at the closest point
        ellipse_tangent_angle = angle_to_point + np.pi/2
        
        # Calculate line angle
        line_angle = np.arctan2(ly2 - ly1, lx2 - lx1)
        
        # Tangency constraint: line should be parallel to ellipse tangent
        # We use the difference in angles (should be 0 or π)
        angle_diff = abs(line_angle - ellipse_tangent_angle)
        angle_diff = min(angle_diff, abs(angle_diff - np.pi))
        
        return np.array([dist, angle_diff])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((2, n))
        
        # Get line endpoints
        lx1, ly1 = self.line.p1.get(x)
        lx2, ly2 = self.line.p2.get(x)
        
        # Get ellipse parameters
        cx, cy, r1, r2, rotation = self.ellipse.get(x)
        
        # Find the closest point on the ellipse to the line
        mid_x = (lx1 + lx2) / 2
        mid_y = (ly1 + ly2) / 2
        
        closest_pt = self.ellipse.closest_point_on_perimeter(x, mid_x, mid_y)
        if closest_pt is None:
            return J
        
        # Calculate distance from line to closest point
        dist = self.line.distance_to(x, closest_pt[0], closest_pt[1])
        
        if dist > 1e-10:
            # Derivatives for distance constraint (first row)
            # Line endpoint derivatives
            line_length = np.sqrt((lx2 - lx1)**2 + (ly2 - ly1)**2)
            if line_length > 1e-10:
                # Distance from point to line: |(p2-p1) × (p-closest_pt)| / |p2-p1|
                cross_product = (lx2 - lx1) * (closest_pt[1] - ly1) - (ly2 - ly1) * (closest_pt[0] - lx1)
                
                # Derivatives with respect to line endpoints
                J[0, self.line.p1.xi] = -(ly2 - ly1) * cross_product / (line_length**3)
                J[0, self.line.p1.yi] = (lx2 - lx1) * cross_product / (line_length**3)
                J[0, self.line.p2.xi] = (ly2 - ly1) * cross_product / (line_length**3)
                J[0, self.line.p2.yi] = -(lx2 - lx1) * cross_product / (line_length**3)
            
            # Derivatives with respect to ellipse center (numerical)
            eps = 1e-6
            for i in [self.ellipse.center.xi, self.ellipse.center.yi]:
                x_plus = x.copy()
                x_plus[i] += eps
                closest_pt_plus = self.ellipse.closest_point_on_perimeter(x_plus, mid_x, mid_y)
                if closest_pt_plus is not None:
                    dist_plus = self.line.distance_to(x_plus, closest_pt_plus[0], closest_pt_plus[1])
                    J[0, i] = (dist_plus - dist) / eps
                else:
                    J[0, i] = 0
            
            # Derivatives with respect to ellipse radii and rotation (numerical)
            for i in [self.ellipse.radius1_index, self.ellipse.radius2_index, self.ellipse.rotation_index]:
                x_plus = x.copy()
                x_plus[i] += eps
                closest_pt_plus = self.ellipse.closest_point_on_perimeter(x_plus, mid_x, mid_y)
                if closest_pt_plus is not None:
                    dist_plus = self.line.distance_to(x_plus, closest_pt_plus[0], closest_pt_plus[1])
                    J[0, i] = (dist_plus - dist) / eps
                else:
                    J[0, i] = 0
            
            # Derivatives for angle constraint (second row)
            # Line angle derivatives
            line_angle = np.arctan2(ly2 - ly1, lx2 - lx1)
            angle_to_point = np.arctan2(closest_pt[1] - cy, closest_pt[0] - cx)
            ellipse_tangent_angle = angle_to_point + np.pi/2
            
            angle_diff = abs(line_angle - ellipse_tangent_angle)
            angle_diff = min(angle_diff, abs(angle_diff - np.pi))
            
            if abs(angle_diff) > 1e-10:
                # Derivatives with respect to line endpoints
                line_length_sq = (lx2 - lx1)**2 + (ly2 - ly1)**2
                if line_length_sq > 1e-10:
                    J[1, self.line.p1.xi] = (ly2 - ly1) / line_length_sq
                    J[1, self.line.p1.yi] = -(lx2 - lx1) / line_length_sq
                    J[1, self.line.p2.xi] = -(ly2 - ly1) / line_length_sq
                    J[1, self.line.p2.yi] = (lx2 - lx1) / line_length_sq
                
                # Derivatives with respect to ellipse parameters (numerical)
                for i in [self.ellipse.center.xi, self.ellipse.center.yi, 
                         self.ellipse.radius1_index, self.ellipse.radius2_index, self.ellipse.rotation_index]:
                    x_plus = x.copy()
                    x_plus[i] += eps
                    closest_pt_plus = self.ellipse.closest_point_on_perimeter(x_plus, mid_x, mid_y)
                    if closest_pt_plus is not None:
                        angle_to_point_plus = np.arctan2(closest_pt_plus[1] - cy, closest_pt_plus[0] - cx)
                        ellipse_tangent_angle_plus = angle_to_point_plus + np.pi/2
                        angle_diff_plus = abs(line_angle - ellipse_tangent_angle_plus)
                        angle_diff_plus = min(angle_diff_plus, abs(angle_diff_plus - np.pi))
                        J[1, i] = (angle_diff_plus - angle_diff) / eps
                    else:
                        J[1, i] = 0
        
        return J


class LineTangentToBezierConstraint(Constraint):
    def __init__(self, line: LineSegment, bezier: BezierPath):
        self.line = line
        self.bezier = bezier

    def residual(self, x):
        # Get line endpoints
        lp1x, lp1y = x[self.line.p1.xi], x[self.line.p1.yi]
        lp2x, lp2y = x[self.line.p2.xi], x[self.line.p2.yi]
        
        # Find closest points on bezier to line endpoints
        t1 = self.bezier.closest_path_part(x, lp1x, lp1y)
        t2 = self.bezier.closest_path_part(x, lp2x, lp2y)
        
        # Get closest points on bezier
        cpt1 = self.bezier.path_point(x, t1)
        cpt2 = self.bezier.path_point(x, t2)
        
        # Calculate distances
        dist1 = math.hypot(cpt1[0] - lp1x, cpt1[1] - lp1y)
        dist2 = math.hypot(cpt2[0] - lp2x, cpt2[1] - lp2y)
        
        # Choose the closer endpoint for tangent calculation
        if dist1 < dist2:
            t = t1
            cpt = cpt1
            dist = dist1
        else:
            t = t2
            cpt = cpt2
            dist = dist2
        
        # Get bezier tangent at the closest point
        bezier_tangent = self.bezier.path_tangent(x, t)
        
        # Calculate line direction
        line_direction = (lp2x - lp1x, lp2y - lp1y)
        
        # Calculate angle between bezier tangent and line direction
        vect_angle = vector_angle(bezier_tangent, line_direction)
        
        # Two constraints:
        # 1. Line should be parallel to bezier tangent (angle difference should be 0° or 180°)
        # 2. Distance from line to bezier should be zero
        return np.array([
            abs(math.cos(math.radians(vect_angle))) - 1.0,  # Parallel constraint
            dist  # Distance constraint
        ])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((2, n))
        
        # Get line endpoints
        lp1x, lp1y = x[self.line.p1.xi], x[self.line.p1.yi]
        lp2x, lp2y = x[self.line.p2.xi], x[self.line.p2.yi]
        
        # Find closest points and determine which endpoint to use
        t1 = self.bezier.closest_path_part(x, lp1x, lp1y)
        t2 = self.bezier.closest_path_part(x, lp2x, lp2y)
        
        cpt1 = self.bezier.path_point(x, t1)
        cpt2 = self.bezier.path_point(x, t2)
        
        dist1 = math.hypot(cpt1[0] - lp1x, cpt1[1] - lp1y)
        dist2 = math.hypot(cpt2[0] - lp2x, cpt2[1] - lp2y)
        
        if dist1 < dist2:
            t = t1
            cpt = cpt1
            dist = dist1
            use_p1 = True
        else:
            t = t2
            cpt = cpt2
            dist = dist2
            use_p1 = False
        
        # Get bezier tangent and line direction
        bezier_tangent = self.bezier.path_tangent(x, t)
        line_direction = (lp2x - lp1x, lp2y - lp1y)
        
        # Calculate angle between vectors
        vect_angle = vector_angle(bezier_tangent, line_direction)
        
        # Derivatives for distance constraint (second row)
        if dist > 0:
            # Distance derivatives with respect to line endpoints
            J[1, self.line.p1.xi] = (cpt[0] - lp1x) / dist if use_p1 else 0
            J[1, self.line.p1.yi] = (cpt[1] - lp1y) / dist if use_p1 else 0
            J[1, self.line.p2.xi] = (cpt[0] - lp2x) / dist if not use_p1 else 0
            J[1, self.line.p2.yi] = (cpt[1] - lp2y) / dist if not use_p1 else 0
            
            # Derivatives with respect to bezier control points for distance constraint
            # We need to account for both direct and indirect effects
            segs = (len(self.bezier.points) - 1) // 3
            if t == 1.0:
                seg = segs - 1
                t_seg = 1.0
            else:
                t_scaled = t * segs
                seg = int(t_scaled)
                t_seg = t_scaled - seg
            
            # Get control points for this segment
            p0_idx = seg * 3
            p1_idx = p0_idx + 1
            p2_idx = p0_idx + 2
            p3_idx = p0_idx + 3
            
            # Get control point coordinates
            p0x, p0y = x[self.bezier.points[p0_idx].xi], x[self.bezier.points[p0_idx].yi]
            p1x, p1y = x[self.bezier.points[p1_idx].xi], x[self.bezier.points[p1_idx].yi]
            p2x, p2y = x[self.bezier.points[p2_idx].xi], x[self.bezier.points[p2_idx].yi]
            p3x, p3y = x[self.bezier.points[p3_idx].xi], x[self.bezier.points[p3_idx].yi]
            
            # Calculate tangent vector components
            tangent_x = 3 * (1 - t_seg)**2 * (p1x - p0x) + 6 * (1 - t_seg) * t_seg * (p2x - p1x) + 3 * t_seg**2 * (p3x - p2x)
            tangent_y = 3 * (1 - t_seg)**2 * (p1y - p0y) + 6 * (1 - t_seg) * t_seg * (p2y - p1y) + 3 * t_seg**2 * (p3y - p2y)
            
            # Calculate the vector from bezier point to the line endpoint
            dx = (lp1x if use_p1 else lp2x) - cpt[0]
            dy = (lp1y if use_p1 else lp1y) - cpt[1]
            
            # Calculate second derivative for dt/dP calculation
            d2x = 6 * (1 - t_seg) * (p2x - 2*p1x + p0x) + 6 * t_seg * (p3x - 2*p2x + p1x)
            d2y = 6 * (1 - t_seg) * (p2y - 2*p1y + p0y) + 6 * t_seg * (p3y - 2*p2y + p1y)
            
            # Denominator for dt/dP
            denominator = tangent_x * tangent_x + tangent_y * tangent_y + dx * d2x + dy * d2y
            
            if abs(denominator) > 1e-10:
                # Calculate dt/dP for each control point
                dt_dp0x = (-3 * (1 - t_seg)**2 * dx - 3 * (1 - t_seg)**2 * dy) / denominator
                dt_dp1x = ((3 * (1 - t_seg)**2 - 6 * (1 - t_seg) * t_seg) * dx + 
                           (3 * (1 - t_seg)**2 - 6 * (1 - t_seg) * t_seg) * dy) / denominator
                dt_dp2x = ((6 * (1 - t_seg) * t_seg - 3 * t_seg**2) * dx + 
                           (6 * (1 - t_seg) * t_seg - 3 * t_seg**2) * dy) / denominator
                dt_dp3x = (3 * t_seg**2 * dx + 3 * t_seg**2 * dy) / denominator
                
                # Similar for y-coordinates
                dt_dp0y = (-3 * (1 - t_seg)**2 * dx - 3 * (1 - t_seg)**2 * dy) / denominator
                dt_dp1y = ((3 * (1 - t_seg)**2 - 6 * (1 - t_seg) * t_seg) * dx + 
                           (3 * (1 - t_seg)**2 - 6 * (1 - t_seg) * t_seg) * dy) / denominator
                dt_dp2y = ((6 * (1 - t_seg) * t_seg - 3 * t_seg**2) * dx + 
                           (6 * (1 - t_seg) * t_seg - 3 * t_seg**2) * dy) / denominator
                dt_dp3y = (3 * t_seg**2 * dx + 3 * t_seg**2 * dy) / denominator
                
                # Direct derivatives for bezier control points
                J[1, self.bezier.points[p0_idx].xi] = (1 - t_seg)**3 / dist if use_p1 else 0
                J[1, self.bezier.points[p1_idx].xi] = 3 * (1 - t_seg)**2 * t_seg / dist if use_p1 else 0
                J[1, self.bezier.points[p2_idx].xi] = 3 * (1 - t_seg) * t_seg**2 / dist if use_p1 else 0
                J[1, self.bezier.points[p3_idx].xi] = t_seg**3 / dist if use_p1 else 0
                
                J[1, self.bezier.points[p0_idx].yi] = (1 - t_seg)**3 / dist if use_p1 else 0
                J[1, self.bezier.points[p1_idx].yi] = 3 * (1 - t_seg)**2 * t_seg / dist if use_p1 else 0
                J[1, self.bezier.points[p2_idx].yi] = 3 * (1 - t_seg) * t_seg**2 / dist if use_p1 else 0
                J[1, self.bezier.points[p3_idx].yi] = t_seg**3 / dist if use_p1 else 0
                
                # Add indirect effect: ∂B/∂t * dt/dP
                J[1, self.bezier.points[p0_idx].xi] += tangent_x * dt_dp0x / dist if use_p1 else 0
                J[1, self.bezier.points[p1_idx].xi] += tangent_x * dt_dp1x / dist if use_p1 else 0
                J[1, self.bezier.points[p2_idx].xi] += tangent_x * dt_dp2x / dist if use_p1 else 0
                J[1, self.bezier.points[p3_idx].xi] += tangent_x * dt_dp3x / dist if use_p1 else 0
                
                J[1, self.bezier.points[p0_idx].yi] += tangent_y * dt_dp0y / dist if use_p1 else 0
                J[1, self.bezier.points[p1_idx].yi] += tangent_y * dt_dp1y / dist if use_p1 else 0
                J[1, self.bezier.points[p2_idx].yi] += tangent_y * dt_dp2y / dist if use_p1 else 0
                J[1, self.bezier.points[p3_idx].yi] += tangent_y * dt_dp3y / dist if use_p1 else 0
        
        # Derivatives for parallel constraint (first row)
        # The parallel constraint is: |cos(angle)| - 1 = 0
        # We need to calculate how the angle changes with respect to all variables
        
        # Calculate unit vectors
        line_length = math.hypot(line_direction[0], line_direction[1])
        tangent_length = math.hypot(bezier_tangent[0], bezier_tangent[1])
        
        if line_length > 1e-10 and tangent_length > 1e-10:
            # Unit vectors
            line_unit = (line_direction[0] / line_length, line_direction[1] / line_length)
            tangent_unit = (bezier_tangent[0] / tangent_length, bezier_tangent[1] / tangent_length)
            
            # Dot product: cos(angle) = line_unit · tangent_unit
            cos_angle = line_unit[0] * tangent_unit[0] + line_unit[1] * tangent_unit[1]
            
            # The constraint is |cos_angle| - 1 = 0
            # Derivative: sign(cos_angle) * d(cos_angle)/d(variable)
            sign_cos = 1 if cos_angle >= 0 else -1
            
            # Derivatives of cos_angle with respect to line endpoints
            # ∂cos_angle/∂line = ∂(line_unit · tangent_unit)/∂line
            # This involves the derivative of line_unit with respect to line endpoints
            
            # Derivatives of line_unit with respect to line endpoints
            line_length_cubed = line_length**3
            dline_unit_dx1 = (line_direction[1]**2 / line_length_cubed, -line_direction[0] * line_direction[1] / line_length_cubed)
            dline_unit_dy1 = (-line_direction[0] * line_direction[1] / line_length_cubed, line_direction[0]**2 / line_length_cubed)
            dline_unit_dx2 = (-line_direction[1]**2 / line_length_cubed, line_direction[0] * line_direction[1] / line_length_cubed)
            dline_unit_dy2 = (line_direction[0] * line_direction[1] / line_length_cubed, -line_direction[0]**2 / line_length_cubed)
            
            # Derivatives of cos_angle with respect to line endpoints
            J[0, self.line.p1.xi] = sign_cos * (dline_unit_dx1[0] * tangent_unit[0] + dline_unit_dx1[1] * tangent_unit[1])
            J[0, self.line.p1.yi] = sign_cos * (dline_unit_dy1[0] * tangent_unit[0] + dline_unit_dy1[1] * tangent_unit[1])
            J[0, self.line.p2.xi] = sign_cos * (dline_unit_dx2[0] * tangent_unit[0] + dline_unit_dx2[1] * tangent_unit[1])
            J[0, self.line.p2.yi] = sign_cos * (dline_unit_dy2[0] * tangent_unit[0] + dline_unit_dy2[1] * tangent_unit[1])
            
            # Derivatives with respect to bezier control points
            # This is more complex because the tangent depends on the bezier control points
            # and the parameter t also changes with control points
            
            # Calculate t_seg for this section
            segs = (len(self.bezier.points) - 1) // 3
            if t == 1.0:
                seg = segs - 1
                t_seg = 1.0
            else:
                t_scaled = t * segs
                seg = int(t_scaled)
                t_seg = t_scaled - seg
            
            # Get control points for this segment
            p0_idx = seg * 3
            p1_idx = p0_idx + 1
            p2_idx = p0_idx + 2
            p3_idx = p0_idx + 3
            
            # Direct derivatives of tangent with respect to control points
            # ∂tangent/∂P₀ = -3(1-t)², ∂tangent/∂P₁ = 3(1-t)² - 6(1-t)t, etc.
            dtangent_dp0x = -3 * (1 - t_seg)**2
            dtangent_dp1x = 3 * (1 - t_seg)**2 - 6 * (1 - t_seg) * t_seg
            dtangent_dp2x = 6 * (1 - t_seg) * t_seg - 3 * t_seg**2
            dtangent_dp3x = 3 * t_seg**2
            
            dtangent_dp0y = -3 * (1 - t_seg)**2
            dtangent_dp1y = 3 * (1 - t_seg)**2 - 6 * (1 - t_seg) * t_seg
            dtangent_dp2y = 6 * (1 - t_seg) * t_seg - 3 * t_seg**2
            dtangent_dp3y = 3 * t_seg**2
            
            # Derivatives of tangent_unit with respect to tangent components
            # ∂tangent_unit/∂tangent_x = (1 - tangent_x²/tangent_length²) / tangent_length
            # ∂tangent_unit/∂tangent_y = -tangent_x * tangent_y / (tangent_length³)
            tangent_length_cubed = tangent_length**3
            dtangent_unit_dx = (tangent_length**2 - bezier_tangent[0]**2) / tangent_length_cubed
            dtangent_unit_dy = -bezier_tangent[0] * bezier_tangent[1] / tangent_length_cubed
            
            # Combined derivatives for bezier control points
            J[0, self.bezier.points[p0_idx].xi] = sign_cos * (line_unit[0] * dtangent_unit_dx * dtangent_dp0x + 
                                                              line_unit[1] * dtangent_unit_dy * dtangent_dp0x)
            J[0, self.bezier.points[p1_idx].xi] = sign_cos * (line_unit[0] * dtangent_unit_dx * dtangent_dp1x + 
                                                              line_unit[1] * dtangent_unit_dy * dtangent_dp1x)
            J[0, self.bezier.points[p2_idx].xi] = sign_cos * (line_unit[0] * dtangent_unit_dx * dtangent_dp2x + 
                                                              line_unit[1] * dtangent_unit_dy * dtangent_dp2x)
            J[0, self.bezier.points[p3_idx].xi] = sign_cos * (line_unit[0] * dtangent_unit_dx * dtangent_dp3x + 
                                                              line_unit[1] * dtangent_unit_dy * dtangent_dp3x)
            
            J[0, self.bezier.points[p0_idx].yi] = sign_cos * (line_unit[0] * dtangent_unit_dy * dtangent_dp0y + 
                                                              line_unit[1] * dtangent_unit_dx * dtangent_dp0y)
            J[0, self.bezier.points[p1_idx].yi] = sign_cos * (line_unit[0] * dtangent_unit_dy * dtangent_dp1y + 
                                                              line_unit[1] * dtangent_unit_dx * dtangent_dp1y)
            J[0, self.bezier.points[p2_idx].yi] = sign_cos * (line_unit[0] * dtangent_unit_dy * dtangent_dp2y + 
                                                              line_unit[1] * dtangent_unit_dx * dtangent_dp2y)
            J[0, self.bezier.points[p3_idx].yi] = sign_cos * (line_unit[0] * dtangent_unit_dy * dtangent_dp3y + 
                                                              line_unit[1] * dtangent_unit_dx * dtangent_dp3y)
        
        return J


# ============================
# Arc Constraint Functions
# ============================

class ArcRadiusConstraint(Constraint):
    def __init__(self, arc: Arc, radius: float):
        self.arc = arc
        self.radius = radius

    def residual(self, x):
        # Get the current arc radius
        r = x[self.arc.radius_index]
        
        # Constraint: arc radius should equal target radius
        return np.array([r - self.radius])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((1, n))
        
        # Derivative with respect to radius
        J[0, self.arc.radius_index] = 1.0
        
        return J


class ArcStartAngleConstraint(Constraint):
    def __init__(self, arc: Arc, angle: float):
        self.arc = arc
        self.angle = normalize_degrees(angle)

    def residual(self, x):
        # Get the current arc start angle
        start_angle = normalize_degrees(x[self.arc.start_angle_index])
        
        # Constraint: arc start angle should equal target angle
        return np.array([start_angle - self.angle])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((1, n))
        
        # Derivative with respect to start angle
        J[0, self.arc.start_angle_index] = 1.0
        
        return J


class ArcEndAngleConstraint(Constraint):
    def __init__(self, arc: Arc, angle: float):
        self.arc = arc
        self.angle = normalize_degrees(angle)

    def residual(self, x):
        # Get the current arc end angle
        end_angle = normalize_degrees(x[self.arc.end_angle_index])
        
        # Constraint: arc end angle should equal target angle
        return np.array([end_angle - self.angle])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((1, n))
        
        # Derivative with respect to arc end angle
        # Since we're using normalize_degrees, the derivative is 1
        J[0, self.arc.end_angle_index] = 1  # d/dθ2 of (θ2 - target_angle)
        
        return J


class ArcSpanAngleConstraint(Constraint):
    def __init__(self, arc: Arc, angle: float):
        self.arc = arc
        self.angle = normalize_degrees(angle)

    def residual(self, x):
        # Get the current arc span angle
        start_angle = normalize_degrees(x[self.arc.start_angle_index])
        end_angle = normalize_degrees(x[self.arc.end_angle_index])
        
        # Calculate current span angle
        if start_angle > end_angle:
            current_span = end_angle - start_angle + 360
        else:
            current_span = end_angle - start_angle
        
        # Constraint: arc span angle should equal target angle
        return np.array([current_span - self.angle])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((1, n))
        
        # Get current angles
        start_angle = normalize_degrees(x[self.arc.start_angle_index])
        end_angle = normalize_degrees(x[self.arc.end_angle_index])
        
        # Calculate span angle
        if start_angle > end_angle:
            current_span = end_angle - start_angle + 360
        else:
            current_span = end_angle - start_angle
        
        # Derivatives with respect to start and end angles
        # ∂span/∂start_angle = -1 (increasing start angle decreases span)
        # ∂span/∂end_angle = 1 (increasing end angle increases span)
        J[0, self.arc.start_angle_index] = -1  # d/dθ1 of span
        J[0, self.arc.end_angle_index] = 1     # d/dθ2 of span
        
        return J


class ArcTangentToArcConstraint(Constraint):
    def __init__(self, arc1: Arc, arc2: Arc):
        self.arc1 = arc1
        self.arc2 = arc2

    def residual(self, x):
        # Get arc parameters
        cx1, cy1, r1, start1, end1 = self.arc1.get(x)
        cx2, cy2, r2, start2, end2 = self.arc2.get(x)
        
        # Calculate arc centers and radii
        center1 = np.array([cx1, cy1])
        center2 = np.array([cx2, cy2])
        
        # Calculate distance between centers
        dist = np.linalg.norm(center2 - center1)

        # angle between arc centers
        angle = math.degrees(math.atan2(cy2 - cy1, cx2 - cx1))
        
        # For arcs to be tangent, the distance between centers should equal the sum or difference of radii
        # We'll use the sum of radii as the constraint
        target_dist = r1 + r2
        
        # Two constraints for tangency:
        # 1. Distance between centers equals sum of radii
        # 2. The tangent point is within both arc spans
        return np.array([
            dist - target_dist,  # Distance constraint
            self.arc1.angle_from_arc_span(x, angle) +  # Span constraint for arc1
            self.arc2.angle_from_arc_span(x, angle + 180)  # Span constraint for arc2
        ])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((1, n))
        
        # Get arc parameters
        cx1, cy1, r1, start1, end1 = self.arc1.get(x)
        cx2, cy2, r2, start2, end2 = self.arc2.get(x)
        
        center1 = np.array([cx1, cy1])
        center2 = np.array([cx2, cy2])
        center_dist = np.linalg.norm(center2 - center1)
        
        if center_dist > 1e-10:  # Avoid division by zero
            # Derivatives with respect to arc1 center
            J[0, self.arc1.center.xi] = (center1[0] - center2[0]) / center_dist
            J[0, self.arc1.center.yi] = (center1[1] - center2[1]) / center_dist
            
            # Derivatives with respect to arc2 center
            J[0, self.arc2.center.xi] = (center2[0] - center1[0]) / center_dist
            J[0, self.arc2.center.yi] = (center2[1] - center1[1]) / center_dist
            
            # Derivatives with respect to radii
            J[0, self.arc1.radius_index] = 1.0
            J[0, self.arc2.radius_index] = 1.0
        
        return J


class ArcTangentToCircleConstraint(Constraint):
    def __init__(self, arc: Arc, circle: Circle):
        self.arc = arc
        self.circle = circle

    def residual(self, x):
        # Get arc and circle parameters
        cx1, cy1, r1, start1, end1 = self.arc.get(x)
        cx2, cy2, r2 = self.circle.get(x)
        
        # Calculate centers
        center1 = np.array([cx1, cy1])
        center2 = np.array([cx2, cy2])
        
        # Calculate distance between centers
        center_dist = np.linalg.norm(center2 - center1)
        
        # For arc and circle to be tangent, the distance between centers should equal the sum or difference of radii
        # We'll use the sum of radii as the constraint
        target_dist = r1 + r2
        
        return np.array([center_dist - target_dist])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((1, n))
        
        # Get arc and circle parameters
        cx1, cy1, r1, start1, end1 = self.arc.get(x)
        cx2, cy2, r2 = self.circle.get(x)
        
        center1 = np.array([cx1, cy1])
        center2 = np.array([cx2, cy2])
        center_dist = np.linalg.norm(center2 - center1)
        
        if center_dist > 1e-10:  # Avoid division by zero
            # Derivatives with respect to arc center
            J[0, self.arc.center.xi] = (center1[0] - center2[0]) / center_dist
            J[0, self.arc.center.yi] = (center1[1] - center2[1]) / center_dist
            
            # Derivatives with respect to circle center
            J[0, self.circle.center.xi] = (center2[0] - center1[0]) / center_dist
            J[0, self.circle.center.yi] = (center2[1] - center1[1]) / center_dist
            
            # Derivatives with respect to radii
            J[0, self.arc.radius_index] = 1.0
            J[0, self.circle.radius_index] = 1.0
        
        return J


class ArcTangentToEllipseConstraint(Constraint):
    def __init__(self, arc: Arc, ellipse: Ellipse):
        self.arc = arc
        self.ellipse = ellipse

    def residual(self, x):
        # Get arc and ellipse parameters
        cx1, cy1, r1, start_angle, end_angle = self.arc.get(x)
        cx2, cy2, r2, r3, rotation = self.ellipse.get(x)
        
        # Find the closest point on the ellipse to the arc center
        closest_pt = self.ellipse.closest_point_on_perimeter(x, cx1, cy1)
        if closest_pt is None:
            return np.array([1.0, 1.0, 1.0])  # Return non-zero residuals if no closest point found
        
        # Calculate distance from arc center to closest point on ellipse
        dist_to_ellipse = np.sqrt((closest_pt[0] - cx1)**2 + (closest_pt[1] - cy1)**2)
        
        # Distance constraint: distance should equal arc radius
        distance_constraint = dist_to_ellipse - r1
        
        # Check if the closest point is within the arc span
        angle_to_point = np.degrees(np.arctan2(closest_pt[1] - cy1, closest_pt[0] - cx1))
        span_check = self.arc.angle_from_arc_span(x, angle_to_point)
        
        # Tangency constraint: calculate tangent angles
        # Ellipse tangent angle at closest point
        ellipse_angle_to_point = np.arctan2(closest_pt[1] - cy2, closest_pt[0] - cx2)
        ellipse_tangent_angle = ellipse_angle_to_point + np.pi/2
        
        # Arc tangent angle (perpendicular to radius)
        arc_tangent_angle = np.radians(angle_to_point) + np.pi/2
        
        # Tangency constraint: angles should be parallel or perpendicular
        angle_diff = abs(ellipse_tangent_angle - arc_tangent_angle)
        angle_diff = min(angle_diff, abs(angle_diff - np.pi))
        
        return np.array([distance_constraint, span_check, angle_diff])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((3, n))
        
        # Get arc and ellipse parameters
        cx1, cy1, r1, start_angle, end_angle = self.arc.get(x)
        cx2, cy2, r2, r3, rotation = self.ellipse.get(x)
        
        # Find the closest point on the ellipse to the arc center
        closest_pt = self.ellipse.closest_point_on_perimeter(x, cx1, cy1)
        if closest_pt is None:
            return J
        
        # Calculate distance from arc center to closest point on ellipse
        dist_to_ellipse = np.sqrt((closest_pt[0] - cx1)**2 + (closest_pt[1] - cy1)**2)
        
        if dist_to_ellipse > 1e-10:
            # Derivatives for distance constraint (first row)
            # Derivatives with respect to arc center
            J[0, self.arc.center.xi] = (cx1 - closest_pt[0]) / dist_to_ellipse
            J[0, self.arc.center.yi] = (cy1 - closest_pt[1]) / dist_to_ellipse
            
            # Derivatives with respect to arc radius
            J[0, self.arc.radius_index] = -1.0
            
            # Derivatives with respect to ellipse parameters (numerical)
            eps = 1e-6
            for i in [self.ellipse.center.xi, self.ellipse.center.yi, 
                     self.ellipse.radius1_index, self.ellipse.radius2_index, self.ellipse.rotation_index]:
                x_plus = x.copy()
                x_plus[i] += eps
                closest_pt_plus = self.ellipse.closest_point_on_perimeter(x_plus, cx1, cy1)
                if closest_pt_plus is not None:
                    dist_plus = np.sqrt((closest_pt_plus[0] - cx1)**2 + (closest_pt_plus[1] - cy1)**2)
                    J[0, i] = (dist_plus - dist_to_ellipse) / eps
                else:
                    J[0, i] = 0
            
            # Derivatives for span constraint (second row)
            angle_to_point = np.degrees(np.arctan2(closest_pt[1] - cy1, closest_pt[0] - cx1))
            span_check = self.arc.angle_from_arc_span(x, angle_to_point)
            
            # Derivatives with respect to arc parameters (numerical)
            for i in [self.arc.start_angle_index, self.arc.end_angle_index]:
                x_plus = x.copy()
                x_plus[i] += eps
                span_check_plus = self.arc.angle_from_arc_span(x_plus, angle_to_point)
                J[1, i] = (span_check_plus - span_check) / eps
            
            # Derivatives with respect to ellipse parameters (numerical)
            for i in [self.ellipse.center.xi, self.ellipse.center.yi, 
                     self.ellipse.radius1_index, self.ellipse.radius2_index, self.ellipse.rotation_index]:
                x_plus = x.copy()
                x_plus[i] += eps
                closest_pt_plus = self.ellipse.closest_point_on_perimeter(x_plus, cx1, cy1)
                if closest_pt_plus is not None:
                    angle_to_point_plus = np.degrees(np.arctan2(closest_pt_plus[1] - cy1, closest_pt_plus[0] - cx1))
                    span_check_plus = self.arc.angle_from_arc_span(x_plus, angle_to_point_plus)
                    J[1, i] = (span_check_plus - span_check) / eps
                else:
                    J[1, i] = 0
            
            # Derivatives for angle constraint (third row)
            ellipse_angle_to_point = np.arctan2(closest_pt[1] - cy2, closest_pt[0] - cx2)
            ellipse_tangent_angle = ellipse_angle_to_point + np.pi/2
            arc_tangent_angle = np.radians(angle_to_point) + np.pi/2
            
            angle_diff = abs(ellipse_tangent_angle - arc_tangent_angle)
            angle_diff = min(angle_diff, abs(angle_diff - np.pi))
            
            if abs(angle_diff) > 1e-10:
                # Derivatives with respect to ellipse parameters (numerical)
                for i in [self.ellipse.center.xi, self.ellipse.center.yi, 
                         self.ellipse.radius1_index, self.ellipse.radius2_index, self.ellipse.rotation_index]:
                    x_plus = x.copy()
                    x_plus[i] += eps
                    closest_pt_plus = self.ellipse.closest_point_on_perimeter(x_plus, cx1, cy1)
                    if closest_pt_plus is not None:
                        ellipse_angle_to_point_plus = np.arctan2(closest_pt_plus[1] - cy2, closest_pt_plus[0] - cx2)
                        ellipse_tangent_angle_plus = ellipse_angle_to_point_plus + np.pi/2
                        angle_diff_plus = abs(ellipse_tangent_angle_plus - arc_tangent_angle)
                        angle_diff_plus = min(angle_diff_plus, abs(angle_diff_plus - np.pi))
                        J[2, i] = (angle_diff_plus - angle_diff) / eps
                    else:
                        J[2, i] = 0
        
        return J


class ArcTangentToBezierConstraint(Constraint):
    def __init__(self, arc: Arc, bezier: BezierPath):
        self.arc = arc
        self.bezier = bezier

    def residual(self, x):
        # Get arc parameters
        cx1, cy1, r1, start_angle, end_angle = self.arc.get(x)
        
        # Find the closest point on the bezier path to the arc center
        closest_t = self.bezier.closest_path_part(x, cx1, cy1)
        
        # Get the point on bezier at parameter t
        bezier_point = self.bezier.path_point(x, closest_t)
        bezier_point = np.array(bezier_point)
        
        # Get the tangent at that point
        bezier_tangent = self.bezier.path_tangent(x, closest_t)
        bezier_tangent = np.array(bezier_tangent)
        
        # Normalize tangent
        tangent_norm = np.linalg.norm(bezier_tangent)
        if tangent_norm > 1e-10:
            bezier_tangent = bezier_tangent / tangent_norm
        else:
            return np.array([1.0, 1.0])  # Return non-zero residuals if tangent is zero
        
        # Calculate distance from arc center to bezier point
        dist = np.sqrt((bezier_point[0] - cx1)**2 + (bezier_point[1] - cy1)**2)
        
        # Distance constraint: distance should equal arc radius
        distance_constraint = dist - r1
        
        # Tangency constraint: bezier tangent should be perpendicular to radius vector
        # Radius vector from arc center to bezier point
        radius_vector = bezier_point - np.array([cx1, cy1])
        radius_norm = np.linalg.norm(radius_vector)
        if radius_norm > 1e-10:
            radius_vector = radius_vector / radius_norm
        else:
            return np.array([1.0, 1.0])  # Return non-zero residuals if radius is zero
        
        # Dot product should be zero for tangency
        tangency_constraint = np.dot(bezier_tangent, radius_vector)
        
        return np.array([distance_constraint, tangency_constraint])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((2, n))
        
        # Get arc parameters
        cx1, cy1, r1, start_angle, end_angle = self.arc.get(x)
        
        # Find the closest point on the bezier path to the arc center
        closest_t = self.bezier.closest_path_part(x, cx1, cy1)
        
        # Get the point on bezier at parameter t
        bezier_point = self.bezier.path_point(x, closest_t)
        bezier_point = np.array(bezier_point)
        
        # Get the tangent at that point
        bezier_tangent = self.bezier.path_tangent(x, closest_t)
        bezier_tangent = np.array(bezier_tangent)
        
        # Normalize tangent
        tangent_norm = np.linalg.norm(bezier_tangent)
        if tangent_norm > 1e-10:
            bezier_tangent = bezier_tangent / tangent_norm
        else:
            return J
        
        # Calculate distance from arc center to bezier point
        dist = np.sqrt((bezier_point[0] - cx1)**2 + (bezier_point[1] - cy1)**2)
        
        if dist > 1e-10:
            # Derivatives for distance constraint (first row)
            # Derivatives with respect to arc center
            J[0, self.arc.center.xi] = (cx1 - bezier_point[0]) / dist
            J[0, self.arc.center.yi] = (cy1 - bezier_point[1]) / dist
            
            # Derivatives with respect to arc radius
            J[0, self.arc.radius_index] = -1.0
            
            # Derivatives with respect to bezier control points (numerical)
            eps = 1e-6
            for i in range(len(self.bezier.points) * 2):  # Each point has x and y coordinates
                x_plus = x.copy()
                x_plus[i] += eps
                closest_t_plus = self.bezier.closest_path_part(x_plus, cx1, cy1)
                bezier_point_plus = self.bezier.path_point(x_plus, closest_t_plus)
                bezier_point_plus = np.array(bezier_point_plus)
                dist_plus = np.sqrt((bezier_point_plus[0] - cx1)**2 + (bezier_point_plus[1] - cy1)**2)
                J[0, i] = (dist_plus - dist) / eps
            
            # Derivatives for tangency constraint (second row)
            # Radius vector from arc center to bezier point
            radius_vector = bezier_point - np.array([cx1, cy1])
            radius_norm = np.linalg.norm(radius_vector)
            if radius_norm > 1e-10:
                radius_vector = radius_vector / radius_norm
                
                # Tangency constraint: dot product should be zero
                tangency_constraint = np.dot(bezier_tangent, radius_vector)
                
                if abs(tangency_constraint) > 1e-10:
                    # Derivatives with respect to arc parameters (numerical)
                    for i in [self.arc.center.xi, self.arc.center.yi, self.arc.radius_index]:
                        x_plus = x.copy()
                        x_plus[i] += eps
                        closest_t_plus = self.bezier.closest_path_part(x_plus, cx1, cy1)
                        bezier_point_plus = self.bezier.path_point(x_plus, closest_t_plus)
                        bezier_tangent_plus = self.bezier.path_tangent(x_plus, closest_t_plus)
                        bezier_point_plus = np.array(bezier_point_plus)
                        bezier_tangent_plus = np.array(bezier_tangent_plus)
                        
                        # Normalize tangent
                        tangent_norm_plus = np.linalg.norm(bezier_tangent_plus)
                        if tangent_norm_plus > 1e-10:
                            bezier_tangent_plus = bezier_tangent_plus / tangent_norm_plus
                            
                            # Radius vector
                            radius_vector_plus = bezier_point_plus - np.array([cx1, cy1])
                            radius_norm_plus = np.linalg.norm(radius_vector_plus)
                            if radius_norm_plus > 1e-10:
                                radius_vector_plus = radius_vector_plus / radius_norm_plus
                                tangency_constraint_plus = np.dot(bezier_tangent_plus, radius_vector_plus)
                                J[1, i] = (tangency_constraint_plus - tangency_constraint) / eps
                            else:
                                J[1, i] = 0
                        else:
                            J[1, i] = 0
                    
                    # Derivatives with respect to bezier control points (numerical)
                    for i in range(len(self.bezier.points) * 2):
                        x_plus = x.copy()
                        x_plus[i] += eps
                        closest_t_plus = self.bezier.closest_path_part(x_plus, cx1, cy1)
                        bezier_point_plus = self.bezier.path_point(x_plus, closest_t_plus)
                        bezier_tangent_plus = self.bezier.path_tangent(x_plus, closest_t_plus)
                        bezier_point_plus = np.array(bezier_point_plus)
                        bezier_tangent_plus = np.array(bezier_tangent_plus)
                        
                        # Normalize tangent
                        tangent_norm_plus = np.linalg.norm(bezier_tangent_plus)
                        if tangent_norm_plus > 1e-10:
                            bezier_tangent_plus = bezier_tangent_plus / tangent_norm_plus
                            
                            # Radius vector
                            radius_vector_plus = bezier_point_plus - np.array([cx1, cy1])
                            radius_norm_plus = np.linalg.norm(radius_vector_plus)
                            if radius_norm_plus > 1e-10:
                                radius_vector_plus = radius_vector_plus / radius_norm_plus
                                tangency_constraint_plus = np.dot(bezier_tangent_plus, radius_vector_plus)
                                J[1, i] = (tangency_constraint_plus - tangency_constraint) / eps
                            else:
                                J[1, i] = 0
                        else:
                            J[1, i] = 0
        
        return J


# ============================
# Circle Constraint Functions
# ============================

class CircleRadiusConstraint(Constraint):
    def __init__(self, circle: Circle, radius: float):
        self.circle = circle
        self.radius = radius

    def residual(self, x):
        # Get the current circle radius
        r = x[self.circle.radius_index]
        
        # Constraint: circle radius should equal target radius
        return np.array([r - self.radius])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((1, n))
        
        # Derivative with respect to circle radius
        J[0, self.circle.radius_index] = 1  # d/dr of (r - target_radius)
        
        return J


class CircleTangentToCircleConstraint(Constraint):
    def __init__(self, circle1: Circle, circle2: Circle):
        self.circle1 = circle1
        self.circle2 = circle2

    def residual(self, x):
        # Get circle parameters
        c1x, c1y, r1 = x[self.circle1.center.xi], x[self.circle1.center.yi], x[self.circle1.radius_index]
        c2x, c2y, r2 = x[self.circle2.center.xi], x[self.circle2.center.yi], x[self.circle2.radius_index]
        
        # Calculate distance between centers
        dist = math.hypot(c1x - c2x, c1y - c2y)
        
        # Constraint: distance should equal sum of radii (tangent condition)
        return np.array([dist - r1 - r2])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((1, n))
        
        # Get circle parameters
        c1x, c1y, r1 = x[self.circle1.center.xi], x[self.circle1.center.yi], x[self.circle1.radius_index]
        c2x, c2y, r2 = x[self.circle2.center.xi], x[self.circle2.center.yi], x[self.circle2.radius_index]
        
        # Calculate distance
        dx = c1x - c2x
        dy = c1y - c2y
        dist = math.hypot(dx, dy)
        
        if dist > 0:
            # Derivatives of distance = sqrt((c1x-c2x)² + (c1y-c2y)²)
            # Derivatives with respect to circle1 parameters
            J[0, self.circle1.center.xi] = dx / dist  # d/dc1x
            J[0, self.circle1.center.yi] = dy / dist  # d/dc1y
            J[0, self.circle1.radius_index] = -1                # d/dr1
            
            # Derivatives with respect to circle2 parameters
            J[0, self.circle2.center.xi] = -dx / dist  # d/dc2x
            J[0, self.circle2.center.yi] = -dy / dist  # d/dc2y
            J[0, self.circle2.radius_index] = -1                 # d/dr2
        else:
            # Handle case where centers coincide
            J[0, self.circle1.center.xi] = 1
            J[0, self.circle1.center.yi] = 1
            J[0, self.circle1.radius_index] = -1
            J[0, self.circle2.center.xi] = -1
            J[0, self.circle2.center.yi] = -1
            J[0, self.circle2.radius_index] = -1
        
        return J


class CircleTangentToEllipseConstraint(Constraint):
    def __init__(self, circle: Circle, ellipse: Ellipse):
        self.circle = circle
        self.ellipse = ellipse

    def residual(self, x):
        # Get ellipse and circle parameters
        cx1, cy1, major_r, minor_r, rotation = x[self.ellipse.center.xi], x[self.ellipse.center.yi], x[self.ellipse.radius1_index], x[self.ellipse.radius2_index], x[self.ellipse.rotation_index]
        cx2, cy2, r2 = x[self.circle.center.xi], x[self.circle.center.yi], x[self.circle.radius_index]
        
        # Find the closest point on ellipse to circle center
        closest_pt = self.ellipse.closest_point_on_perimeter(x, cx2, cy2)
        
        if closest_pt is None:
            return np.array([1.0, 1.0])  # Return non-zero residuals if no closest point found
        
        # Calculate distance from circle center to closest point on ellipse
        dist_to_ellipse = np.sqrt((closest_pt[0] - cx2)**2 + (closest_pt[1] - cy2)**2)
        
        # Distance constraint: distance should equal circle radius
        distance_constraint = dist_to_ellipse - r2
        
        # Tangency constraint: calculate tangent angles
        # Ellipse tangent angle at closest point
        angle_to_point = np.arctan2(closest_pt[1] - cy1, closest_pt[0] - cx1)
        ellipse_tangent_angle = angle_to_point + np.pi/2
        
        # Circle tangent angle (perpendicular to radius)
        circle_tangent_angle = angle_to_point + np.pi/2
        
        # Tangency constraint: angles should be parallel or perpendicular
        angle_diff = abs(ellipse_tangent_angle - circle_tangent_angle)
        angle_diff = min(angle_diff, abs(angle_diff - np.pi))
        
        return np.array([distance_constraint, angle_diff])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((2, n))
        
        # Get ellipse and circle parameters
        cx1, cy1, major_r, minor_r, rotation = x[self.ellipse.center.xi], x[self.ellipse.center.yi], x[self.ellipse.radius1_index], x[self.ellipse.radius2_index], x[self.ellipse.rotation_index]
        cx2, cy2, r2 = x[self.circle.center.xi], x[self.circle.center.yi], x[self.circle.radius_index]
        
        # Find the closest point on ellipse to circle center
        closest_pt = self.ellipse.closest_point_on_perimeter(x, cx2, cy2)
        
        if closest_pt is None:
            return J
        
        # Calculate distance from circle center to closest point on ellipse
        dist_to_ellipse = np.sqrt((closest_pt[0] - cx2)**2 + (closest_pt[1] - cy2)**2)
        
        if dist_to_ellipse > 1e-10:
            # Derivatives for distance constraint (first row)
            # Derivatives with respect to circle center
            J[0, self.circle.center.xi] = (cx2 - closest_pt[0]) / dist_to_ellipse
            J[0, self.circle.center.yi] = (cy2 - closest_pt[1]) / dist_to_ellipse
            
            # Derivatives with respect to circle radius
            J[0, self.circle.radius_index] = -1.0
            
            # Derivatives with respect to ellipse parameters (numerical)
            eps = 1e-6
            for i in [self.ellipse.center.xi, self.ellipse.center.yi, 
                     self.ellipse.radius1_index, self.ellipse.radius2_index, self.ellipse.rotation_index]:
                x_plus = x.copy()
                x_plus[i] += eps
                closest_pt_plus = self.ellipse.closest_point_on_perimeter(x_plus, cx2, cy2)
                if closest_pt_plus is not None:
                    dist_plus = np.sqrt((closest_pt_plus[0] - cx2)**2 + (closest_pt_plus[1] - cy2)**2)
                    J[0, i] = (dist_plus - dist_to_ellipse) / eps
                else:
                    J[0, i] = 0
            
            # Derivatives for angle constraint (second row)
            angle_to_point = np.arctan2(closest_pt[1] - cy1, closest_pt[0] - cx1)
            ellipse_tangent_angle = angle_to_point + np.pi/2
            circle_tangent_angle = angle_to_point + np.pi/2
            
            angle_diff = abs(ellipse_tangent_angle - circle_tangent_angle)
            angle_diff = min(angle_diff, abs(angle_diff - np.pi))
            
            if abs(angle_diff) > 1e-10:
                # Derivatives with respect to ellipse parameters (numerical)
                for i in [self.ellipse.center.xi, self.ellipse.center.yi, 
                         self.ellipse.radius1_index, self.ellipse.radius2_index, self.ellipse.rotation_index]:
                    x_plus = x.copy()
                    x_plus[i] += eps
                    closest_pt_plus = self.ellipse.closest_point_on_perimeter(x_plus, cx2, cy2)
                    if closest_pt_plus is not None:
                        angle_to_point_plus = np.arctan2(closest_pt_plus[1] - cy1, closest_pt_plus[0] - cx1)
                        ellipse_tangent_angle_plus = angle_to_point_plus + np.pi/2
                        angle_diff_plus = abs(ellipse_tangent_angle_plus - circle_tangent_angle)
                        angle_diff_plus = min(angle_diff_plus, abs(angle_diff_plus - np.pi))
                        J[1, i] = (angle_diff_plus - angle_diff) / eps
                    else:
                        J[1, i] = 0
        
        return J


class CircleTangentToBezierConstraint(Constraint):
    def __init__(self, circle: Circle, bezier: BezierPath):
        self.circle = circle
        self.bezier = bezier

    def residual(self, x):
        # Get circle parameters
        cx, cy, r = self.circle.get(x)
        circle_center = np.array([cx, cy])
        
        # Find the closest point on the bezier path to the circle center
        closest_t = self.bezier.closest_path_part(x, cx, cy)
        
        # Get the point on bezier at parameter t
        bezier_point = self.bezier.path_point(x, closest_t)
        bezier_point = np.array(bezier_point)
        
        # Get the tangent at that point
        bezier_tangent = self.bezier.path_tangent(x, closest_t)
        bezier_tangent = np.array(bezier_tangent)
        
        # Normalize tangent
        tangent_norm = np.linalg.norm(bezier_tangent)
        if tangent_norm > 1e-10:
            bezier_tangent = bezier_tangent / tangent_norm
        
        # Calculate vector from bezier point to circle center
        to_center = circle_center - bezier_point
        to_center_norm = np.linalg.norm(to_center)
        
        if to_center_norm > 1e-10:
            to_center = to_center / to_center_norm
        
        # For tangency, the distance from bezier point to circle center should equal the circle radius
        # and the tangent should be perpendicular to the radius vector
        distance_constraint = to_center_norm - r
        tangency_constraint = np.dot(bezier_tangent, to_center)
        
        return np.array([distance_constraint, tangency_constraint])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((2, n))
        
        # Get circle parameters
        cx, cy, r = self.circle.get(x)
        circle_center = np.array([cx, cy])
        
        # Find the closest point on the bezier path to the circle center
        closest_t = self.bezier.closest_path_part(x, cx, cy)
        
        # Get the point on bezier at parameter t
        bezier_point = self.bezier.path_point(x, closest_t)
        bezier_point = np.array(bezier_point)
        
        # Get the tangent at that point
        bezier_tangent = self.bezier.path_tangent(x, closest_t)
        bezier_tangent = np.array(bezier_tangent)
        
        # Normalize tangent
        tangent_norm = np.linalg.norm(bezier_tangent)
        if tangent_norm > 1e-10:
            bezier_tangent = bezier_tangent / tangent_norm
        
        # Calculate vector from bezier point to circle center
        to_center = circle_center - bezier_point
        to_center_norm = np.linalg.norm(to_center)
        
        if to_center_norm > 1e-10:
            to_center = to_center / to_center_norm
        
        # Derivatives for distance constraint (row 0)
        if to_center_norm > 1e-10:
            # Derivatives with respect to circle center
            J[0, self.circle.center.xi] = to_center[0]
            J[0, self.circle.center.yi] = to_center[1]
            
            # Derivatives with respect to circle radius
            J[0, self.circle.radius_index] = -1.0
            
            # Derivatives with respect to bezier control points
            # We need to compute how the closest point changes with respect to control points
            # This is complex, so we'll use numerical differentiation for the bezier derivatives
            eps = 1e-6
            for i, point in enumerate(self.bezier.points):
                # Derivative with respect to x coordinate
                x_plus = x.copy()
                x_plus[point.xi] += eps
                closest_t_plus = self.bezier.closest_path_part(x_plus, cx, cy)
                bezier_point_plus = self.bezier.path_point(x_plus, closest_t_plus)
                bezier_point_plus = np.array(bezier_point_plus)
                to_center_plus = circle_center - bezier_point_plus
                to_center_norm_plus = np.linalg.norm(to_center_plus)
                
                if to_center_norm_plus > 1e-10:
                    to_center_plus = to_center_plus / to_center_norm_plus
                    J[0, point.xi] = (to_center_norm_plus - to_center_norm) / eps
                
                # Derivative with respect to y coordinate
                y_plus = x.copy()
                y_plus[point.yi] += eps
                closest_t_plus = self.bezier.closest_path_part(y_plus, cx, cy)
                bezier_point_plus = self.bezier.path_point(y_plus, closest_t_plus)
                bezier_point_plus = np.array(bezier_point_plus)
                to_center_plus = circle_center - bezier_point_plus
                to_center_norm_plus = np.linalg.norm(to_center_plus)
                
                if to_center_norm_plus > 1e-10:
                    to_center_plus = to_center_plus / to_center_norm_plus
                    J[0, point.yi] = (to_center_norm_plus - to_center_norm) / eps
        
        # Derivatives for tangency constraint (row 1)
        if tangent_norm > 1e-10 and to_center_norm > 1e-10:
            # Derivatives with respect to circle center
            # The tangent doesn't depend on circle center, so these are zero
            J[1, self.circle.center.xi] = 0.0
            J[1, self.circle.center.yi] = 0.0
            
            # Derivatives with respect to circle radius
            # The tangent constraint doesn't depend on radius
            J[1, self.circle.radius_index] = 0.0
            
            # Derivatives with respect to bezier control points
            # This is complex, so we'll use numerical differentiation
            eps = 1e-6
            for i, point in enumerate(self.bezier.points):
                # Derivative with respect to x coordinate
                x_plus = x.copy()
                x_plus[point.xi] += eps
                closest_t_plus = self.bezier.closest_path_part(x_plus, cx, cy)
                bezier_tangent_plus = self.bezier.path_tangent(x_plus, closest_t_plus)
                bezier_tangent_plus = np.array(bezier_tangent_plus)
                tangent_norm_plus = np.linalg.norm(bezier_tangent_plus)
                
                if tangent_norm_plus > 1e-10:
                    bezier_tangent_plus = bezier_tangent_plus / tangent_norm_plus
                    bezier_point_plus = self.bezier.path_point(x_plus, closest_t_plus)
                    bezier_point_plus = np.array(bezier_point_plus)
                    to_center_plus = circle_center - bezier_point_plus
                    to_center_norm_plus = np.linalg.norm(to_center_plus)
                    
                    if to_center_norm_plus > 1e-10:
                        to_center_plus = to_center_plus / to_center_norm_plus
                        tangency_plus = np.dot(bezier_tangent_plus, to_center_plus)
                        J[1, point.xi] = (tangency_plus - np.dot(bezier_tangent, to_center)) / eps
                
                # Derivative with respect to y coordinate
                y_plus = x.copy()
                y_plus[point.yi] += eps
                closest_t_plus = self.bezier.closest_path_part(y_plus, cx, cy)
                bezier_tangent_plus = self.bezier.path_tangent(y_plus, closest_t_plus)
                bezier_tangent_plus = np.array(bezier_tangent_plus)
                tangent_norm_plus = np.linalg.norm(bezier_tangent_plus)
                
                if tangent_norm_plus > 1e-10:
                    bezier_tangent_plus = bezier_tangent_plus / tangent_norm_plus
                    bezier_point_plus = self.bezier.path_point(y_plus, closest_t_plus)
                    bezier_point_plus = np.array(bezier_point_plus)
                    to_center_plus = circle_center - bezier_point_plus
                    to_center_norm_plus = np.linalg.norm(to_center_plus)
                    
                    if to_center_norm_plus > 1e-10:
                        to_center_plus = to_center_plus / to_center_norm_plus
                        tangency_plus = np.dot(bezier_tangent_plus, to_center_plus)
                        J[1, point.yi] = (tangency_plus - np.dot(bezier_tangent, to_center)) / eps
        
        return J


# ============================
# Ellipse Constraint Functions
# ============================

class EllipseMajorRadiusConstraint(Constraint):
    def __init__(self, ellipse: Ellipse, radius: float):
        self.ellipse = ellipse
        self.radius = radius

    def residual(self, x):
        # Get the current ellipse major radius
        major_r = x[self.ellipse.radius1_index]
        
        # Constraint: ellipse major radius should equal target radius
        return np.array([major_r - self.radius])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((1, n))
        
        # Derivative with respect to ellipse major radius
        J[0, self.ellipse.radius1_index] = 1  # d/dmajor_r of (major_r - target_radius)
        
        return J


class EllipseMinorRadiusConstraint(Constraint):
    def __init__(self, ellipse: Ellipse, radius: float):
        self.ellipse = ellipse
        self.radius = radius

    def residual(self, x):
        # Get the current ellipse minor radius
        minor_r = x[self.ellipse.radius2_index]
        
        # Constraint: ellipse minor radius should equal target radius
        return np.array([minor_r - self.radius])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((1, n))
        
        # Derivative with respect to ellipse minor radius
        J[0, self.ellipse.radius2_index] = 1  # d/dminor_r of (minor_r - target_radius)
        
        return J


class EllipseRotationConstraint(Constraint):
    def __init__(self, ellipse: Ellipse, angle: float):
        self.ellipse = ellipse
        self.angle = normalize_degrees(angle)

    def residual(self, x):
        # Get the current ellipse rotation angle
        rotation_angle = normalize_degrees(x[self.ellipse.rotation_index])
        
        # Constraint: ellipse rotation should equal target angle
        return np.array([rotation_angle - self.angle])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((1, n))
        
        # Derivative with respect to ellipse rotation angle
        # Since we're using normalize_degrees, the derivative is 1
        J[0, self.ellipse.rotation_index] = 1  # d/drotation of (rotation - target_angle)
        
        return J


class EllipseEccentricityConstraint(Constraint):
    def __init__(self, ellipse: Ellipse, eccentricity: float):
        self.ellipse = ellipse
        self.eccentricity = eccentricity

    def residual(self, x):
        # Get the current ellipse eccentricity
        current_eccentricity = self.ellipse.eccentricity(x)
        
        # Constraint: ellipse eccentricity should equal target eccentricity
        return np.array([current_eccentricity - self.eccentricity])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((1, n))
        
        # Get ellipse parameters
        major_r = x[self.ellipse.radius1_index]
        minor_r = x[self.ellipse.radius2_index]
        
        # Eccentricity is defined as: e = sqrt(1 - (b/a)^2) where a > b
        # So de/da = (b^2/a^3) / sqrt(1 - (b/a)^2)
        # And de/db = -(b/a^2) / sqrt(1 - (b/a)^2)
        
        if major_r > minor_r and major_r > 0:
            ratio = minor_r / major_r
            ratio_sq = ratio * ratio
            
            if ratio_sq < 1:  # Valid eccentricity
                sqrt_term = math.sqrt(1 - ratio_sq)
                
                # Derivatives with respect to major and minor radii
                J[0, self.ellipse.radius1_index] = (ratio_sq / major_r) / sqrt_term  # de/da
                J[0, self.ellipse.radius2_index] = -(ratio / major_r) / sqrt_term     # de/db
            else:
                # Invalid eccentricity (ratio >= 1)
                J[0, self.ellipse.radius1_index] = 0
                J[0, self.ellipse.radius2_index] = 0
        else:
            # Invalid case (major_r <= minor_r or major_r <= 0)
            J[0, self.ellipse.radius1_index] = 0
            J[0, self.ellipse.radius2_index] = 0
        
        return J


class EllipseTangentToEllipseConstraint(Constraint):
    def __init__(self, ellipse1: Ellipse, ellipse2: Ellipse):
        self.ellipse1 = ellipse1
        self.ellipse2 = ellipse2

    def residual(self, x):
        # Get ellipse parameters
        cx1, cy1, r1, r2, rotation1 = self.ellipse1.get(x)
        cx2, cy2, r3, r4, rotation2 = self.ellipse2.get(x)
        
        # Find the closest point on ellipse2 to ellipse1 center
        closest_pt2 = self.ellipse2.closest_point_on_perimeter(x, cx1, cy1)
        if closest_pt2 is None:
            return np.array([1.0, 1.0])  # Return non-zero residuals if no closest point found
        
        # Find the closest point on ellipse1 to ellipse2 center
        closest_pt1 = self.ellipse1.closest_point_on_perimeter(x, cx2, cy2)
        if closest_pt1 is None:
            return np.array([1.0, 1.0])  # Return non-zero residuals if no closest point found
        
        # Calculate distance from ellipse1 center to closest point on ellipse2
        dist1_to_2 = np.sqrt((closest_pt2[0] - cx1)**2 + (closest_pt2[1] - cy1)**2)
        
        # Calculate distance from ellipse2 center to closest point on ellipse1
        dist2_to_1 = np.sqrt((closest_pt1[0] - cx2)**2 + (closest_pt1[1] - cy2)**2)
        
        # Distance constraint: the distances should be equal (both ellipses should be at the same distance)
        distance_constraint = dist1_to_2 - dist2_to_1
        
        # Tangency constraint: calculate tangent angles
        # Ellipse1 tangent angle at closest point
        ellipse1_angle_to_point = np.arctan2(closest_pt1[1] - cy1, closest_pt1[0] - cx1)
        ellipse1_tangent_angle = ellipse1_angle_to_point + np.pi/2
        
        # Ellipse2 tangent angle at closest point
        ellipse2_angle_to_point = np.arctan2(closest_pt2[1] - cy2, closest_pt2[0] - cx2)
        ellipse2_tangent_angle = ellipse2_angle_to_point + np.pi/2
        
        # Tangency constraint: angles should be parallel or perpendicular
        angle_diff = abs(ellipse1_tangent_angle - ellipse2_tangent_angle)
        angle_diff = min(angle_diff, abs(angle_diff - np.pi))
        
        return np.array([distance_constraint, angle_diff])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((2, n))
        
        # Get ellipse parameters
        cx1, cy1, r1, r2, rotation1 = self.ellipse1.get(x)
        cx2, cy2, r3, r4, rotation2 = self.ellipse2.get(x)
        
        # Find the closest point on ellipse2 to ellipse1 center
        closest_pt2 = self.ellipse2.closest_point_on_perimeter(x, cx1, cy1)
        if closest_pt2 is None:
            return J
        
        # Find the closest point on ellipse1 to ellipse2 center
        closest_pt1 = self.ellipse1.closest_point_on_perimeter(x, cx2, cy2)
        if closest_pt1 is None:
            return J
        
        # Calculate distances
        dist1_to_2 = np.sqrt((closest_pt2[0] - cx1)**2 + (closest_pt2[1] - cy1)**2)
        dist2_to_1 = np.sqrt((closest_pt1[0] - cx2)**2 + (closest_pt1[1] - cy2)**2)
        
        if dist1_to_2 > 1e-10 and dist2_to_1 > 1e-10:
            # Derivatives for distance constraint (first row)
            # Derivatives with respect to ellipse1 parameters (numerical)
            eps = 1e-6
            for i in [self.ellipse1.center.xi, self.ellipse1.center.yi, 
                     self.ellipse1.radius1_index, self.ellipse1.radius2_index, self.ellipse1.rotation_index]:
                x_plus = x.copy()
                x_plus[i] += eps
                closest_pt2_plus = self.ellipse2.closest_point_on_perimeter(x_plus, cx1, cy1)
                closest_pt1_plus = self.ellipse1.closest_point_on_perimeter(x_plus, cx2, cy2)
                if closest_pt2_plus is not None and closest_pt1_plus is not None:
                    dist1_to_2_plus = np.sqrt((closest_pt2_plus[0] - cx1)**2 + (closest_pt2_plus[1] - cy1)**2)
                    dist2_to_1_plus = np.sqrt((closest_pt1_plus[0] - cx2)**2 + (closest_pt1_plus[1] - cy2)**2)
                    J[0, i] = ((dist1_to_2_plus - dist2_to_1_plus) - (dist1_to_2 - dist2_to_1)) / eps
                else:
                    J[0, i] = 0
            
            # Derivatives with respect to ellipse2 parameters (numerical)
            for i in [self.ellipse2.center.xi, self.ellipse2.center.yi, 
                     self.ellipse2.radius1_index, self.ellipse2.radius2_index, self.ellipse2.rotation_index]:
                x_plus = x.copy()
                x_plus[i] += eps
                closest_pt2_plus = self.ellipse2.closest_point_on_perimeter(x_plus, cx1, cy1)
                closest_pt1_plus = self.ellipse1.closest_point_on_perimeter(x_plus, cx2, cy2)
                if closest_pt2_plus is not None and closest_pt1_plus is not None:
                    dist1_to_2_plus = np.sqrt((closest_pt2_plus[0] - cx1)**2 + (closest_pt2_plus[1] - cy1)**2)
                    dist2_to_1_plus = np.sqrt((closest_pt1_plus[0] - cx2)**2 + (closest_pt1_plus[1] - cy2)**2)
                    J[0, i] = ((dist1_to_2_plus - dist2_to_1_plus) - (dist1_to_2 - dist2_to_1)) / eps
                else:
                    J[0, i] = 0
            
            # Derivatives for angle constraint (second row)
            ellipse1_angle_to_point = np.arctan2(closest_pt1[1] - cy1, closest_pt1[0] - cx1)
            ellipse1_tangent_angle = ellipse1_angle_to_point + np.pi/2
            ellipse2_angle_to_point = np.arctan2(closest_pt2[1] - cy2, closest_pt2[0] - cx2)
            ellipse2_tangent_angle = ellipse2_angle_to_point + np.pi/2
            
            angle_diff = abs(ellipse1_tangent_angle - ellipse2_tangent_angle)
            angle_diff = min(angle_diff, abs(angle_diff - np.pi))
            
            if abs(angle_diff) > 1e-10:
                # Derivatives with respect to ellipse1 parameters (numerical)
                for i in [self.ellipse1.center.xi, self.ellipse1.center.yi, 
                         self.ellipse1.radius1_index, self.ellipse1.radius2_index, self.ellipse1.rotation_index]:
                    x_plus = x.copy()
                    x_plus[i] += eps
                    closest_pt1_plus = self.ellipse1.closest_point_on_perimeter(x_plus, cx2, cy2)
                    if closest_pt1_plus is not None:
                        ellipse1_angle_to_point_plus = np.arctan2(closest_pt1_plus[1] - cy1, closest_pt1_plus[0] - cx1)
                        ellipse1_tangent_angle_plus = ellipse1_angle_to_point_plus + np.pi/2
                        angle_diff_plus = abs(ellipse1_tangent_angle_plus - ellipse2_tangent_angle)
                        angle_diff_plus = min(angle_diff_plus, abs(angle_diff_plus - np.pi))
                        J[1, i] = (angle_diff_plus - angle_diff) / eps
                    else:
                        J[1, i] = 0
                
                # Derivatives with respect to ellipse2 parameters (numerical)
                for i in [self.ellipse2.center.xi, self.ellipse2.center.yi, 
                         self.ellipse2.radius1_index, self.ellipse2.radius2_index, self.ellipse2.rotation_index]:
                    x_plus = x.copy()
                    x_plus[i] += eps
                    closest_pt2_plus = self.ellipse2.closest_point_on_perimeter(x_plus, cx1, cy1)
                    if closest_pt2_plus is not None:
                        ellipse2_angle_to_point_plus = np.arctan2(closest_pt2_plus[1] - cy2, closest_pt2_plus[0] - cx2)
                        ellipse2_tangent_angle_plus = ellipse2_angle_to_point_plus + np.pi/2
                        angle_diff_plus = abs(ellipse1_tangent_angle - ellipse2_tangent_angle_plus)
                        angle_diff_plus = min(angle_diff_plus, abs(angle_diff_plus - np.pi))
                        J[1, i] = (angle_diff_plus - angle_diff) / eps
                    else:
                        J[1, i] = 0
        
        return J


class EllipseTangentToBezierConstraint(Constraint):
    def __init__(self, ellipse: Ellipse, bezier: BezierPath):
        self.ellipse = ellipse
        self.bezier = bezier

    def residual(self, x):
        # Get ellipse parameters
        cx, cy, r1, r2, rotation = self.ellipse.get(x)
        
        # Find the closest point on the bezier path to the ellipse center
        closest_t = self.bezier.closest_path_part(x, cx, cy)
        
        # Get the point on bezier at parameter t
        bezier_point = self.bezier.path_point(x, closest_t)
        bezier_point = np.array(bezier_point)
        
        # Get the tangent at that point
        bezier_tangent = self.bezier.path_tangent(x, closest_t)
        bezier_tangent = np.array(bezier_tangent)
        
        # Normalize tangent
        tangent_norm = np.linalg.norm(bezier_tangent)
        if tangent_norm > 1e-10:
            bezier_tangent = bezier_tangent / tangent_norm
        else:
            return np.array([1.0, 1.0])  # Return non-zero residuals if tangent is zero
        
        # Find the closest point on the ellipse to the bezier point
        closest_pt = self.ellipse.closest_point_on_perimeter(x, bezier_point[0], bezier_point[1])
        if closest_pt is None:
            return np.array([1.0, 1.0])  # Return non-zero residuals if no closest point found
        
        # Calculate distance from bezier point to closest point on ellipse
        dist = np.sqrt((bezier_point[0] - closest_pt[0])**2 + (bezier_point[1] - closest_pt[1])**2)
        
        # Distance constraint: distance should be zero for tangency
        distance_constraint = dist
        
        # Tangency constraint: bezier tangent should be parallel to ellipse tangent
        # Calculate ellipse tangent angle at closest point
        ellipse_angle_to_point = np.arctan2(closest_pt[1] - cy, closest_pt[0] - cx)
        ellipse_tangent_angle = ellipse_angle_to_point + np.pi/2
        
        # Calculate bezier tangent angle
        bezier_tangent_angle = np.arctan2(bezier_tangent[1], bezier_tangent[0])
        
        # Tangency constraint: angles should be parallel or perpendicular
        angle_diff = abs(ellipse_tangent_angle - bezier_tangent_angle)
        angle_diff = min(angle_diff, abs(angle_diff - np.pi))
        
        return np.array([distance_constraint, angle_diff])

    def jacobian(self, x):
        n = len(x)
        J = np.zeros((2, n))
        
        # Get ellipse parameters
        cx, cy, r1, r2, rotation = self.ellipse.get(x)
        
        # Find the closest point on the bezier path to the ellipse center
        closest_t = self.bezier.closest_path_part(x, cx, cy)
        
        # Get the point on bezier at parameter t
        bezier_point = self.bezier.path_point(x, closest_t)
        bezier_point = np.array(bezier_point)
        
        # Get the tangent at that point
        bezier_tangent = self.bezier.path_tangent(x, closest_t)
        bezier_tangent = np.array(bezier_tangent)
        
        # Normalize tangent
        tangent_norm = np.linalg.norm(bezier_tangent)
        if tangent_norm > 1e-10:
            bezier_tangent = bezier_tangent / tangent_norm
        else:
            return J
        
        # Find the closest point on the ellipse to the bezier point
        closest_pt = self.ellipse.closest_point_on_perimeter(x, bezier_point[0], bezier_point[1])
        if closest_pt is None:
            return J
        
        # Calculate distance from bezier point to closest point on ellipse
        dist = np.sqrt((bezier_point[0] - closest_pt[0])**2 + (bezier_point[1] - closest_pt[1])**2)
        
        if dist > 1e-10:
            # Derivatives for distance constraint (first row)
            # Derivatives with respect to ellipse parameters (numerical)
            eps = 1e-6
            for i in [self.ellipse.center.xi, self.ellipse.center.yi, 
                     self.ellipse.radius1_index, self.ellipse.radius2_index, self.ellipse.rotation_index]:
                x_plus = x.copy()
                x_plus[i] += eps
                closest_pt_plus = self.ellipse.closest_point_on_perimeter(x_plus, bezier_point[0], bezier_point[1])
                if closest_pt_plus is not None:
                    dist_plus = np.sqrt((bezier_point[0] - closest_pt_plus[0])**2 + (bezier_point[1] - closest_pt_plus[1])**2)
                    J[0, i] = (dist_plus - dist) / eps
                else:
                    J[0, i] = 0
            
            # Derivatives with respect to bezier control points (numerical)
            for i in range(len(self.bezier.points) * 2):  # Each point has x and y coordinates
                x_plus = x.copy()
                x_plus[i] += eps
                closest_t_plus = self.bezier.closest_path_part(x_plus, cx, cy)
                bezier_point_plus = self.bezier.path_point(x_plus, closest_t_plus)
                bezier_point_plus = np.array(bezier_point_plus)
                closest_pt_plus = self.ellipse.closest_point_on_perimeter(x_plus, bezier_point_plus[0], bezier_point_plus[1])
                if closest_pt_plus is not None:
                    dist_plus = np.sqrt((bezier_point_plus[0] - closest_pt_plus[0])**2 + (bezier_point_plus[1] - closest_pt_plus[1])**2)
                    J[0, i] = (dist_plus - dist) / eps
                else:
                    J[0, i] = 0
            
            # Derivatives for angle constraint (second row)
            ellipse_angle_to_point = np.arctan2(closest_pt[1] - cy, closest_pt[0] - cx)
            ellipse_tangent_angle = ellipse_angle_to_point + np.pi/2
            bezier_tangent_angle = np.arctan2(bezier_tangent[1], bezier_tangent[0])
            
            angle_diff = abs(ellipse_tangent_angle - bezier_tangent_angle)
            angle_diff = min(angle_diff, abs(angle_diff - np.pi))
            
            if abs(angle_diff) > 1e-10:
                # Derivatives with respect to ellipse parameters (numerical)
                for i in [self.ellipse.center.xi, self.ellipse.center.yi, 
                         self.ellipse.radius1_index, self.ellipse.radius2_index, self.ellipse.rotation_index]:
                    x_plus = x.copy()
                    x_plus[i] += eps
                    closest_pt_plus = self.ellipse.closest_point_on_perimeter(x_plus, bezier_point[0], bezier_point[1])
                    if closest_pt_plus is not None:
                        ellipse_angle_to_point_plus = np.arctan2(closest_pt_plus[1] - cy, closest_pt_plus[0] - cx)
                        ellipse_tangent_angle_plus = ellipse_angle_to_point_plus + np.pi/2
                        angle_diff_plus = abs(ellipse_tangent_angle_plus - bezier_tangent_angle)
                        angle_diff_plus = min(angle_diff_plus, abs(angle_diff_plus - np.pi))
                        J[1, i] = (angle_diff_plus - angle_diff) / eps
                    else:
                        J[1, i] = 0
                
                # Derivatives with respect to bezier control points (numerical)
                for i in range(len(self.bezier.points) * 2):
                    x_plus = x.copy()
                    x_plus[i] += eps
                    closest_t_plus = self.bezier.closest_path_part(x_plus, cx, cy)
                    bezier_point_plus = self.bezier.path_point(x_plus, closest_t_plus)
                    bezier_tangent_plus = self.bezier.path_tangent(x_plus, closest_t_plus)
                    bezier_point_plus = np.array(bezier_point_plus)
                    bezier_tangent_plus = np.array(bezier_tangent_plus)
                    
                    # Normalize tangent
                    tangent_norm_plus = np.linalg.norm(bezier_tangent_plus)
                    if tangent_norm_plus > 1e-10:
                        bezier_tangent_plus = bezier_tangent_plus / tangent_norm_plus
                        bezier_tangent_angle_plus = np.arctan2(bezier_tangent_plus[1], bezier_tangent_plus[0])
                        
                        closest_pt_plus = self.ellipse.closest_point_on_perimeter(x_plus, bezier_point_plus[0], bezier_point_plus[1])
                        if closest_pt_plus is not None:
                            ellipse_angle_to_point_plus = np.arctan2(closest_pt_plus[1] - cy, closest_pt_plus[0] - cx)
                            ellipse_tangent_angle_plus = ellipse_angle_to_point_plus + np.pi/2
                            angle_diff_plus = abs(ellipse_tangent_angle_plus - bezier_tangent_angle_plus)
                            angle_diff_plus = min(angle_diff_plus, abs(angle_diff_plus - np.pi))
                            J[1, i] = (angle_diff_plus - angle_diff) / eps
                        else:
                            J[1, i] = 0
                    else:
                        J[1, i] = 0
        
        return J



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
            "Is at": CoincidentConstraint,
            "Vertical to": VerticalConstraint,
            "Horizontal to": HorizontalConstraint,
        },
        "line": {
            "Is on": PointIsOnLineSegmentConstraint,
            "Starts at":
                lambda point, line:
                    CoincidentConstraint(line.p1, point),
            "Ends at":
                lambda point, line:
                    CoincidentConstraint(line.p2, point),
        },
        "arc": {
            "Is on": PointIsOnArcConstraint,
            "Starts at": PointCoincidentWithArcStartConstraint,
            "Ends at": PointCoincidentWithArcEndConstraint,
            "Concentric":
                lambda point, arc:
                    CoincidentConstraint(arc.center, point),
        },
        "circle": {
            "Is on": PointIsOnCircleConstraint,
            "Concentric":
                lambda point, circle:
                    CoincidentConstraint(circle.center, point),
        },
        "bezier": {
            "Is on": PointIsOnBezierPathConstraint,
            "Starts at":
                lambda point, bezier:
                    CoincidentConstraint(bezier.points[0], point),
            "Ends at":
                lambda point, bezier:
                    CoincidentConstraint(bezier.points[-1], point),
        },
        "ellipse": {
            "Is on": PointIsOnEllipseConstraint,
            "Concentric":
                lambda ellipse, point:
                    CoincidentConstraint(ellipse.center, point),
        }
    },
    "line": {
        "": {
            "Horizontal":
                lambda line:
                    HorizontalConstraint(line.p1, line.p2),
            "Vertical":
                lambda line:
                    VerticalConstraint(line.p1, line.p2),
        },
        "scalar": {
            "Angle is": LineAngleConstraint,
            "Length is": LineLengthConstraint,
        },
        "point": {
            "Is on":
                lambda line, point:
                    PointIsOnLineSegmentConstraint(point, line),
            "Starts at":
                lambda line, point:
                    CoincidentConstraint(point.p1, line),
            "Ends at":
                lambda line, point:
                    CoincidentConstraint(point.p2, line),
        },
        "line": {
            "Equal": LinesEqualLengthConstraint,
            "Perpendicular": LinesPerpendicularConstraint,
            "Parallel": LinesParallelConstraint,
        },
        "arc": {
            "Tangent":
                lambda line, arc:
                    LineTangentToArcConstraint(line, arc),
        },
        "circle": {
            "Tangent": LineTangentToCircleConstraint,
        },
        "bezier": {
            "Tangent": LineTangentToBezierConstraint,
        },
        "ellipse": {
            "Tangent": LineTangentToEllipseConstraint,
        }
    },
    "arc": {
        "": {
        },
        "scalar": {
            "Start angle is": ArcStartAngleConstraint,
            "End angle is": ArcEndAngleConstraint,
            "Span angle is": ArcSpanAngleConstraint,
            "Radius is": ArcRadiusConstraint,
        },
        "point": {
            "Is on":
                lambda arc, point:
                    PointIsOnArcConstraint(point, arc),
            "Concentric":
                lambda arc, point:
                    CoincidentConstraint(arc.center, point),
            "Starts at":
                lambda arc, point:
                    PointCoincidentWithArcStartConstraint(point, arc),
            "Ends at":
                lambda arc, point:
                    PointCoincidentWithArcEndConstraint(point, arc),
        },
        "line": {
            "Tangent": LineTangentToArcConstraint,
        },
        "arc": {
            "Tangent": ArcTangentToArcConstraint,
            "Concentric":
                lambda arc, circle:
                    CoincidentConstraint(arc.center, circle.center),
        },
        "circle": {
            "Tangent": ArcTangentToCircleConstraint,
            "Concentric":
                lambda arc, circle:
                    CoincidentConstraint(arc.center, circle.center),
        },
        "bezier": {
            "Tangent": ArcTangentToBezierConstraint,
        },
        "ellipse": {
            "Tangent":
                lambda arc, ellipse:
                    ArcTangentToEllipseConstraint(arc, ellipse),
        }
    },
    "circle": {
        "": {
        },
        "scalar": {
            "Radius is": CircleRadiusConstraint,
        },
        "point": {
            "Is on":
                lambda circle, point:
                    PointIsOnCircleConstraint(point, circle),
            "Concentric":
                lambda circle, point:
                    CoincidentConstraint(circle.center, point),
        },
        "line": {
            "Tangent":
                lambda circle, line:
                    LineTangentToCircleConstraint(line, circle),
        },
        "arc": {
            "Tangent":
                lambda circle, arc:
                    ArcTangentToCircleConstraint(arc, circle),
            "Concentric":
                lambda circle, arc:
                    CoincidentConstraint(circle.center, arc.center),
        },
        "circle": {
            "Tangent": CircleTangentToCircleConstraint,
            "Concentric":
                lambda circle1, circle2:
                    CoincidentConstraint(circle1.center,circle2.center),
        },
        "bezier": {
            "Tangent": CircleTangentToBezierConstraint,
        },
        "ellipse": {
            "Tangent": CircleTangentToEllipseConstraint,
        }
    },
    "ellipse": {
        "": {},
        "scalar": {
            "Major radius is": EllipseMajorRadiusConstraint,
            "Minor radius is": EllipseMinorRadiusConstraint,
            "Rotation is": EllipseRotationConstraint,
            "Eccentricity is": EllipseEccentricityConstraint,
        },
        "point": {
            "Is on": PointIsOnEllipseConstraint,
            "Concentric":
                lambda ellipse, point:
                    CoincidentConstraint(ellipse.center, point),
        },
        "line": {
            "Tangent": LineTangentToEllipseConstraint,
        },
        "arc": {
            "Tangent":
                lambda ellipse, arc:
                    ArcTangentToEllipseConstraint(arc, ellipse),
        },
        "circle": {
            "Tangent":
                lambda ellipse, circle:
                    CircleTangentToEllipseConstraint(circle, ellipse),
        },
        "ellipse": {
            "Concentric":
                lambda ellipse1, ellipse2:
                    CoincidentConstraint(ellipse1.center, ellipse2.center),
            "Tangent":
                lambda ellipse1, ellipse2:
                    EllipseTangentToEllipseConstraint(ellipse1, ellipse2),
        },
        "bezier": {
            "Tangent":
                lambda ellipse, bezier:
                    EllipseTangentToBezierConstraint(ellipse, bezier),
        }
    },
    "bezier": {
        "": {},
        "point": {
            "Is on":
                lambda bezier, point:
                    PointIsOnBezierPathConstraint(point, bezier),
            "Starts at":
                lambda bezier, point:
                    CoincidentConstraint(bezier.points[0], point),
            "Ends at":
                lambda bezier, point:
                    CoincidentConstraint(bezier.points[-1], point),
        },
        "line": {
            "Tangent":
                lambda bezier, line:
                    LineTangentToBezierConstraint(line, bezier),
        },
        "arc": {
            "Tangent":
                lambda bezier, arc:
                    ArcTangentToBezierConstraint(arc, bezier),
        },
        "circle": {
            "Tengent":
                lambda bezier, circle:
                    CircleTangentToBezierConstraint(circle, bezier),
        },
        "ellipse": {
            "Tangent":
                lambda bezier, ellipse:
                    EllipseTangentToBezierConstraint(ellipse, bezier),
        }
    },
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
    elif isinstance(obj, Ellipse):
        return "ellipse"
    elif isinstance(obj, BezierPath):
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

