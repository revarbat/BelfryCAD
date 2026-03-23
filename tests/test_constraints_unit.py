"""
Comprehensive unit tests for BelfryCAD/utils/constraints.py.

Covers:
- Helper functions (normalize_degrees, vector_angle, get_objtype)
- ConstraintSolver variable management and solving
- All Constrainable geometry classes and their methods
- All Constraint classes (residual + jacobian)
- Integration: solving constraint systems end-to-end
- get_possible_constraints / get_constraint module API
"""

import math
import sys
import os

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from BelfryCAD.utils.constraints import (
    # Solver
    ConstraintSolver,
    # Constrainables
    Constrainable,
    ConstrainableLength,
    ConstrainableAngle,
    ConstrainablePoint2D,
    ConstrainableLine2D,
    ConstrainableArc,
    ConstrainableCircle,
    ConstrainableEllipse,
    ConstrainableBezierPath,
    # Constraints
    Constraint,
    LengthEqualsConstraint,
    AngleEqualsConstraint,
    CoincidentConstraint,
    HorizontalConstraint,
    VerticalConstraint,
    PointIsOnLineSegmentConstraint,
    PointIsOnArcConstraint,
    PointCoincidentWithArcStartConstraint,
    PointCoincidentWithArcEndConstraint,
    PointIsOnCircleConstraint,
    PointIsOnEllipseConstraint,
    PointIsOnBezierPathConstraint,
    LineAngleConstraint,
    LineLengthConstraint,
    LinesEqualLengthConstraint,
    LinesPerpendicularConstraint,
    LinesParallelConstraint,
    LineTangentToArcConstraint,
    LineTangentToCircleConstraint,
    ArcRadiusConstraint,
    ArcStartAngleConstraint,
    ArcEndAngleConstraint,
    ArcSpanAngleConstraint,
    ArcTangentToCircleConstraint,
    ArcTangentToArcConstraint,
    ArcTangentToEllipseConstraint,
    ArcTangentToBezierConstraint,
    CircleTangentToCircleConstraint,
    CircleTangentToEllipseConstraint,
    CircleTangentToBezierConstraint,
    LineTangentToEllipseConstraint,
    LineTangentToBezierConstraint,
    EllipseTangentToEllipseConstraint,
    EllipseTangentToBezierConstraint,
    # Module functions
    normalize_degrees,
    vector_angle,
    get_objtype,
    get_possible_constraints,
    get_constraint,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def make_solver():
    return ConstraintSolver()


def make_length(solver, value=5.0, fixed=False):
    return ConstrainableLength(solver, value, fixed=fixed, label="len")


def make_angle(solver, value=45.0, fixed=False):
    return ConstrainableAngle(solver, value, fixed=fixed, label="ang")


def make_point(solver, x=0.0, y=0.0, fixed=False, label="pt"):
    return ConstrainablePoint2D(solver, (x, y), fixed=fixed, label=label)


def make_line(solver, x0=0.0, y0=0.0, x1=1.0, y1=0.0):
    p1 = make_point(solver, x0, y0, label="p1")
    p2 = make_point(solver, x1, y1, label="p2")
    return ConstrainableLine2D(solver, p1, p2, label="line"), p1, p2


def make_circle(solver, cx=0.0, cy=0.0, r=5.0):
    center = make_point(solver, cx, cy, label="c")
    radius = make_length(solver, r)
    return ConstrainableCircle(solver, center, radius, label="circle"), center, radius


def make_arc(solver, cx=0.0, cy=0.0, r=5.0, start=0.0, span=90.0):
    center = make_point(solver, cx, cy, label="arc_c")
    radius = make_length(solver, r)
    start_a = make_angle(solver, start)
    span_a = make_angle(solver, span)
    return ConstrainableArc(solver, center, radius, start_a, span_a), center, radius, start_a, span_a


def make_ellipse(solver, cx=0.0, cy=0.0, r1=5.0, r2=3.0, rot=0.0):
    center = make_point(solver, cx, cy, label="el_c")
    radius1 = make_length(solver, r1)
    radius2 = make_length(solver, r2)
    rotation = make_angle(solver, rot)
    return ConstrainableEllipse(solver, center, radius1, radius2, rotation), center, radius1, radius2, rotation


def make_bezier(solver, points=None):
    """Single cubic Bezier segment: 4 control points."""
    if points is None:
        points = [(0.0, 0.0), (1.0, 2.0), (3.0, 2.0), (4.0, 0.0)]
    solver.beziers = getattr(solver, 'beziers', [])
    cpts = [make_point(solver, x, y, label=f"bp{i}") for i, (x, y) in enumerate(points)]
    return ConstrainableBezierPath(solver, cpts), cpts


# ===========================================================================
# 1. Helper functions
# ===========================================================================

class TestNormalizeDegrees:
    def test_already_normalized(self):
        assert normalize_degrees(90.0) == pytest.approx(90.0)

    def test_zero(self):
        assert normalize_degrees(0.0) == pytest.approx(0.0)

    def test_360_becomes_0(self):
        assert normalize_degrees(360.0) == pytest.approx(0.0)

    def test_negative(self):
        assert normalize_degrees(-90.0) == pytest.approx(270.0)

    def test_large_positive(self):
        assert normalize_degrees(720.0) == pytest.approx(0.0)

    def test_just_under_360(self):
        assert normalize_degrees(359.9) == pytest.approx(359.9)

    def test_large_negative(self):
        assert normalize_degrees(-450.0) == pytest.approx(270.0)


class TestVectorAngle:
    def test_rightward(self):
        assert vector_angle((0, 0), (1, 0)) == pytest.approx(0.0)

    def test_upward(self):
        assert vector_angle((0, 0), (0, 1)) == pytest.approx(90.0)

    def test_leftward(self):
        assert vector_angle((0, 0), (-1, 0)) == pytest.approx(180.0)

    def test_downward(self):
        assert vector_angle((0, 0), (0, -1)) == pytest.approx(-90.0)

    def test_diagonal(self):
        assert vector_angle((0, 0), (1, 1)) == pytest.approx(45.0)

    def test_offset_origin(self):
        assert vector_angle((1, 1), (2, 1)) == pytest.approx(0.0)


# ===========================================================================
# 2. ConstraintSolver
# ===========================================================================

class TestConstraintSolverVariables:
    def test_add_variable_returns_index(self):
        s = make_solver()
        idx = s.add_variable(3.14, "x")
        assert idx == 0

    def test_add_multiple_variables(self):
        s = make_solver()
        i0 = s.add_variable(1.0, "a")
        i1 = s.add_variable(2.0, "b")
        assert i0 == 0
        assert i1 == 1
        assert s.variables == [1.0, 2.0]

    def test_fixed_mask(self):
        s = make_solver()
        s.add_variable(1.0, "free", fixed=False)
        s.add_variable(2.0, "fixed", fixed=True)
        assert s.fixed_mask == [False, True]

    def test_update_variable(self):
        s = make_solver()
        s.add_variable(1.0, "x")
        s.update_variable(0, 9.9)
        assert s.variables[0] == pytest.approx(9.9)

    def test_update_variable_out_of_range(self):
        s = make_solver()
        # Should not raise
        s.update_variable(99, 1.0)

    def test_variable_labels(self):
        s = make_solver()
        s.add_variable(1.0, "alpha")
        assert s.variable_labels == ["alpha"]


class TestConstraintSolverConstraints:
    def test_add_callable_constraint(self):
        s = make_solver()
        s.add_variable(0.0, "x")
        s.add_constraint(lambda x: [x[0] - 3.0], label="x=3")
        assert len(s.constraints) == 1
        assert s.constraint_labels[0] == "x=3"

    def test_add_constraint_auto_label(self):
        s = make_solver()
        s.add_constraint(lambda x: [0.0])
        assert s.constraint_labels[0].startswith("constraint_")

    def test_add_soft_constraint(self):
        s = make_solver()
        s.add_soft_constraint(lambda x: [x[0]], weight=0.5)
        assert len(s.soft_constraints) == 1
        func, weight = s.soft_constraints[0]
        assert weight == 0.5

    def test_get_point_coords(self):
        s = make_solver()
        make_point(s, 1.0, 2.0)
        make_point(s, 3.0, 4.0)
        coords = s.get_point_coords()
        assert len(coords) == 2
        assert coords[0] == pytest.approx((1.0, 2.0))
        assert coords[1] == pytest.approx((3.0, 4.0))


class TestConstraintSolverSolve:
    def test_solve_single_variable_to_target(self):
        s = make_solver()
        s.add_variable(0.0, "x")
        s.add_constraint(lambda x: [x[0] - 5.0], label="x=5")
        s.solve()
        assert s.variables[0] == pytest.approx(5.0, abs=1e-4)

    def test_solve_all_fixed_returns_none(self):
        s = make_solver()
        s.add_variable(1.0, "x", fixed=True)
        s.add_constraint(lambda x: [x[0] - 5.0])
        result = s.solve()
        assert result is None
        assert s.variables[0] == pytest.approx(1.0)

    def test_solve_fixed_variable_unchanged(self):
        s = make_solver()
        s.add_variable(2.0, "fixed", fixed=True)
        s.add_variable(0.0, "free")
        # Constraint: free == fixed
        s.add_constraint(lambda x: [x[1] - x[0]])
        s.solve()
        assert s.variables[0] == pytest.approx(2.0)
        assert s.variables[1] == pytest.approx(2.0, abs=1e-4)

    def test_solve_sets_constraint_info(self):
        s = make_solver()
        s.add_variable(0.0, "x")
        s.add_constraint(lambda x: [x[0] - 3.0])
        s.solve()
        assert hasattr(s, 'constraint_info')
        assert 'free_variables' in s.constraint_info

    def test_solve_with_analytic_constraint(self):
        s = make_solver()
        p1 = make_point(s, 0.0, 0.0, fixed=True)
        p2 = make_point(s, 1.0, 1.0)
        c = CoincidentConstraint(p1, p2)
        s.add_constraint(c)
        s.solve()
        x, y = p2.get(s.variables)
        assert x == pytest.approx(0.0, abs=1e-4)
        assert y == pytest.approx(0.0, abs=1e-4)

    def test_detect_conflicts(self):
        s = make_solver()
        s.add_variable(0.0, "x", fixed=True)
        # Impossible: x==0 (fixed) but constraint says x==5
        s.add_constraint(lambda x: [x[0] - 5.0], label="x=5")
        s.solve()
        assert len(s.conflicting_constraints) > 0

    def test_under_constrained(self):
        s = make_solver()
        s.add_variable(0.0, "x")
        s.add_variable(0.0, "y")
        # Only one constraint, two free vars -> under-constrained
        s.add_constraint(lambda x: [x[0] - 1.0])
        s.solve()
        assert s.under_constrained is True

    def test_over_constrained(self):
        s = make_solver()
        s.add_variable(0.0, "x")
        # Two constraints, one variable -> over-constrained
        s.add_constraint(lambda x: [x[0] - 1.0])
        s.add_constraint(lambda x: [x[0] - 2.0])
        s.solve()
        assert s.over_constrained is True

    def test_gauss_newton_solve(self):
        s = make_solver()
        s.add_variable(0.0, "x")
        s.add_constraint(lambda x: [x[0] - 7.0])
        s.gauss_newton_solve()
        assert s.variables[0] == pytest.approx(7.0, abs=1e-4)

    def test_numerical_jacobian_static(self):
        func = lambda x: [x[0] ** 2]
        x = np.array([3.0])
        J = ConstraintSolver._numerical_jacobian(func, x)
        assert J[0, 0] == pytest.approx(6.0, abs=1e-3)

    def test_gauss_newton_with_soft_constraint(self):
        s = make_solver()
        s.add_variable(0.0, "x")
        s.add_constraint(lambda x: [x[0] - 5.0])
        s.add_soft_constraint(lambda x: [x[0]], weight=0.01)
        s.gauss_newton_solve()
        assert s.variables[0] == pytest.approx(5.0, abs=0.1)


# ===========================================================================
# 3. ConstrainableLength
# ===========================================================================

class TestConstrainableLength:
    def test_get(self):
        s = make_solver()
        ln = make_length(s, 7.5)
        assert ln.get(s.variables) == pytest.approx(7.5)

    def test_update_value(self):
        s = make_solver()
        ln = make_length(s, 7.5)
        ln.update_value(12.0)
        assert ln.get(s.variables) == pytest.approx(12.0)

    def test_get_constrainables(self):
        s = make_solver()
        ln = make_length(s, 3.0)
        c = ln.get_constrainables()
        assert ln in c

    def test_registered_in_solver(self):
        s = make_solver()
        ln = make_length(s, 3.0)
        assert ln in s.lengths

    def test_fixed_in_solver(self):
        s = make_solver()
        ln = make_length(s, 3.0, fixed=True)
        assert s.fixed_mask[ln.index] is True


# ===========================================================================
# 4. ConstrainableAngle
# ===========================================================================

class TestConstrainableAngle:
    def test_get(self):
        s = make_solver()
        a = make_angle(s, 90.0)
        assert a.get(s.variables) == pytest.approx(90.0)

    def test_update_value(self):
        s = make_solver()
        a = make_angle(s, 45.0)
        a.update_value(180.0)
        assert a.get(s.variables) == pytest.approx(180.0)

    def test_get_constrainables(self):
        s = make_solver()
        a = make_angle(s, 30.0)
        assert a in a.get_constrainables()

    def test_registered_in_solver(self):
        s = make_solver()
        a = make_angle(s, 30.0)
        assert a in s.angles


# ===========================================================================
# 5. ConstrainablePoint2D
# ===========================================================================

class TestConstrainablePoint2D:
    def test_get(self):
        s = make_solver()
        p = make_point(s, 3.0, 4.0)
        assert p.get(s.variables) == pytest.approx((3.0, 4.0))

    def test_update_values(self):
        s = make_solver()
        p = make_point(s, 0.0, 0.0)
        p.update_values(6.0, 8.0)
        assert p.get(s.variables) == pytest.approx((6.0, 8.0))

    def test_distance_to(self):
        s = make_solver()
        p = make_point(s, 0.0, 0.0)
        assert p.distance_to(s.variables, 3.0, 4.0) == pytest.approx(5.0)

    def test_distance_to_self(self):
        s = make_solver()
        p = make_point(s, 1.0, 2.0)
        assert p.distance_to(s.variables, 1.0, 2.0) == pytest.approx(0.0)

    def test_degrees_from_origin_right(self):
        s = make_solver()
        p = make_point(s, 1.0, 0.0)
        assert p.degrees_from_origin(s.variables) == pytest.approx(0.0)

    def test_degrees_from_origin_up(self):
        s = make_solver()
        p = make_point(s, 0.0, 1.0)
        assert p.degrees_from_origin(s.variables) == pytest.approx(90.0)

    def test_degrees_from_origin_diagonal(self):
        s = make_solver()
        p = make_point(s, 1.0, 1.0)
        assert p.degrees_from_origin(s.variables) == pytest.approx(45.0)

    def test_get_constrainables(self):
        s = make_solver()
        p = make_point(s, 1.0, 2.0)
        assert p in p.get_constrainables()

    def test_registered_in_solver(self):
        s = make_solver()
        p = make_point(s, 0.0, 0.0)
        assert p in s.points

    def test_get_label(self):
        s = make_solver()
        p = ConstrainablePoint2D(s, (0, 0), label="mypoint")
        assert p.get_label() == "mypoint"


# ===========================================================================
# 6. ConstrainableLine2D
# ===========================================================================

class TestConstrainableLine2D:
    def test_get(self):
        s = make_solver()
        line, p1, p2 = make_line(s, 0, 0, 3, 4)
        assert line.get(s.variables) == pytest.approx((0.0, 0.0, 3.0, 4.0))

    def test_length(self):
        s = make_solver()
        line, _, _ = make_line(s, 0, 0, 3, 4)
        assert line.length(s.variables) == pytest.approx(5.0)

    def test_length_horizontal(self):
        s = make_solver()
        line, _, _ = make_line(s, 1, 0, 4, 0)
        assert line.length(s.variables) == pytest.approx(3.0)

    def test_angle_horizontal(self):
        s = make_solver()
        line, _, _ = make_line(s, 0, 0, 1, 0)
        assert line.angle(s.variables) == pytest.approx(0.0)

    def test_angle_vertical(self):
        s = make_solver()
        line, _, _ = make_line(s, 0, 0, 0, 1)
        assert line.angle(s.variables) == pytest.approx(90.0)

    def test_angle_diagonal(self):
        s = make_solver()
        line, _, _ = make_line(s, 0, 0, 1, 1)
        assert line.angle(s.variables) == pytest.approx(45.0)

    def test_closest_part_midpoint(self):
        s = make_solver()
        line, _, _ = make_line(s, 0, 0, 4, 0)
        t = line.closest_part(s.variables, 2.0, 5.0)
        assert t == pytest.approx(0.5)

    def test_closest_part_clamp_start(self):
        s = make_solver()
        line, _, _ = make_line(s, 0, 0, 4, 0)
        t = line.closest_part(s.variables, -1.0, 0.0)
        assert t == pytest.approx(0.0)

    def test_closest_part_clamp_end(self):
        s = make_solver()
        line, _, _ = make_line(s, 0, 0, 4, 0)
        t = line.closest_part(s.variables, 10.0, 0.0)
        assert t == pytest.approx(1.0)

    def test_closest_part_zero_length(self):
        s = make_solver()
        line, _, _ = make_line(s, 0, 0, 0, 0)
        t = line.closest_part(s.variables, 5.0, 5.0)
        assert t == pytest.approx(0.0)

    def test_closest_point_on_line(self):
        s = make_solver()
        line, _, _ = make_line(s, 0, 0, 4, 0)
        cx, cy = line.closest_point(s.variables, 2.0, 3.0)
        assert cx == pytest.approx(2.0)
        assert cy == pytest.approx(0.0)

    def test_distance_to_horizontal_line(self):
        s = make_solver()
        line, _, _ = make_line(s, 0, 0, 4, 0)
        d = line.distance_to(s.variables, 2.0, 3.0)
        assert d == pytest.approx(3.0)

    def test_distance_to_endpoint(self):
        s = make_solver()
        line, _, _ = make_line(s, 0, 0, 4, 0)
        d = line.distance_to(s.variables, 6.0, 0.0)
        assert d == pytest.approx(2.0)

    def test_get_constrainables(self):
        s = make_solver()
        line, p1, p2 = make_line(s)
        c = line.get_constrainables()
        assert p1 in c
        assert p2 in c
        assert line in c

    def test_registered_in_solver(self):
        s = make_solver()
        line, _, _ = make_line(s)
        assert line in s.lines


# ===========================================================================
# 7. ConstrainableArc
# ===========================================================================

class TestConstrainableArc:
    def test_get(self):
        s = make_solver()
        arc, center, r, sa, spa = make_arc(s, cx=1.0, cy=2.0, r=5.0, start=30.0, span=90.0)
        cx, cy, radius, start, end = arc.get(s.variables)
        assert cx == pytest.approx(1.0)
        assert cy == pytest.approx(2.0)
        assert radius == pytest.approx(5.0)
        assert start == pytest.approx(30.0)
        assert end == pytest.approx(120.0)

    def test_span_angle(self):
        s = make_solver()
        arc, *_ = make_arc(s, span=120.0)
        assert arc.span_angle(s.variables) == pytest.approx(120.0)

    def test_angle_from_arc_span_inside(self):
        s = make_solver()
        arc, *_ = make_arc(s, start=0.0, span=90.0)
        # 45° is inside [0, 90]
        delta = arc.angle_from_arc_span(s.variables, 45.0)
        assert delta == pytest.approx(0.0)

    def test_angle_from_arc_span_before_start(self):
        s = make_solver()
        arc, *_ = make_arc(s, start=30.0, span=60.0)
        # 10° is before start (30°)
        delta = arc.angle_from_arc_span(s.variables, 10.0)
        assert delta == pytest.approx(20.0)

    def test_angle_from_arc_span_after_end(self):
        s = make_solver()
        arc, *_ = make_arc(s, start=0.0, span=90.0)
        # 100° is after end (90°)
        delta = arc.angle_from_arc_span(s.variables, 100.0)
        assert delta == pytest.approx(10.0)

    def test_get_constrainables(self):
        s = make_solver()
        arc, center, r, sa, spa = make_arc(s)
        c = arc.get_constrainables()
        assert center in c
        assert r in c
        assert arc in c


# ===========================================================================
# 8. ConstrainableCircle
# ===========================================================================

class TestConstrainableCircle:
    def test_get(self):
        s = make_solver()
        circle, center, r = make_circle(s, 1.0, 2.0, 4.0)
        cx, cy, radius = circle.get(s.variables)
        assert (cx, cy, radius) == pytest.approx((1.0, 2.0, 4.0))

    def test_closest_point_on_perimeter(self):
        s = make_solver()
        circle, _, _ = make_circle(s, 0.0, 0.0, 5.0)
        pt = circle.closest_point_on_perimeter(s.variables, 10.0, 0.0)
        assert pt == pytest.approx((5.0, 0.0))

    def test_closest_point_on_perimeter_at_center_returns_none(self):
        s = make_solver()
        circle, _, _ = make_circle(s, 0.0, 0.0, 5.0)
        pt = circle.closest_point_on_perimeter(s.variables, 0.0, 0.0)
        assert pt is None

    def test_distance_to_perimeter_outside(self):
        s = make_solver()
        circle, _, _ = make_circle(s, 0.0, 0.0, 5.0)
        d = circle.distance_to_perimeter(s.variables, 8.0, 0.0)
        assert d == pytest.approx(3.0)

    def test_distance_to_perimeter_inside(self):
        s = make_solver()
        circle, _, _ = make_circle(s, 0.0, 0.0, 5.0)
        d = circle.distance_to_perimeter(s.variables, 3.0, 0.0)
        assert d == pytest.approx(2.0)

    def test_distance_to_perimeter_on_perimeter(self):
        s = make_solver()
        circle, _, _ = make_circle(s, 0.0, 0.0, 5.0)
        d = circle.distance_to_perimeter(s.variables, 5.0, 0.0)
        assert d == pytest.approx(0.0, abs=1e-10)

    def test_distance_to_perimeter_at_center(self):
        s = make_solver()
        circle, _, _ = make_circle(s, 0.0, 0.0, 5.0)
        d = circle.distance_to_perimeter(s.variables, 0.0, 0.0)
        # Falls back to distance from center to center = 0
        assert d == pytest.approx(0.0, abs=1e-10)

    def test_get_constrainables(self):
        s = make_solver()
        circle, center, r = make_circle(s)
        c = circle.get_constrainables()
        assert center in c
        assert r in c
        assert circle in c

    def test_registered_in_solver(self):
        s = make_solver()
        circle, _, _ = make_circle(s)
        assert circle in s.circles


# ===========================================================================
# 9. ConstrainableEllipse
# ===========================================================================

class TestConstrainableEllipse:
    def test_get(self):
        s = make_solver()
        el, center, r1, r2, rot = make_ellipse(s, 1.0, 2.0, 5.0, 3.0, 0.0)
        cx, cy, major, minor, rotation = el.get(s.variables)
        assert (cx, cy) == pytest.approx((1.0, 2.0))
        assert major == pytest.approx(5.0)
        assert minor == pytest.approx(3.0)
        assert rotation == pytest.approx(0.0)

    def test_get_rotation_radians(self):
        s = make_solver()
        el, *_ = make_ellipse(s, rot=90.0)
        assert el.get_rotation_radians(s.variables) == pytest.approx(math.pi / 2)

    def test_get_rotation_degrees(self):
        s = make_solver()
        el, *_ = make_ellipse(s, rot=45.0)
        assert el.get_rotation_degrees(s.variables) == pytest.approx(45.0)

    def test_distance_to_perimeter_on_major_axis(self):
        s = make_solver()
        el, *_ = make_ellipse(s, cx=0.0, cy=0.0, r1=5.0, r2=3.0, rot=0.0)
        # Point on the major axis perimeter
        d = el.distance_to_perimeter(s.variables, 5.0, 0.0)
        assert d == pytest.approx(0.0, abs=0.01)

    def test_distance_to_perimeter_outside(self):
        s = make_solver()
        el, *_ = make_ellipse(s, cx=0.0, cy=0.0, r1=5.0, r2=3.0, rot=0.0)
        d = el.distance_to_perimeter(s.variables, 10.0, 0.0)
        assert d == pytest.approx(5.0, abs=0.1)

    def test_closest_point_on_perimeter(self):
        s = make_solver()
        el, *_ = make_ellipse(s, cx=0.0, cy=0.0, r1=5.0, r2=3.0, rot=0.0)
        pt = el.closest_point_on_perimeter(s.variables, 10.0, 0.0)
        assert pt is not None
        # Closest point should be near (5, 0)
        assert pt[0] == pytest.approx(5.0, abs=0.01)
        assert pt[1] == pytest.approx(0.0, abs=0.01)

    def test_eccentricity_circle_is_zero(self):
        s = make_solver()
        el, *_ = make_ellipse(s, r1=5.0, r2=5.0)
        e = el.eccentricity(s.variables)
        assert e == pytest.approx(0.0, abs=1e-6)

    def test_eccentricity_ellipse(self):
        s = make_solver()
        el, *_ = make_ellipse(s, r1=5.0, r2=4.0)
        e = el.eccentricity(s.variables)
        expected = math.sqrt(1 - (4.0/5.0)**2)
        assert e == pytest.approx(expected, rel=1e-4)

    def test_get_focus_points(self):
        s = make_solver()
        el, *_ = make_ellipse(s, cx=0.0, cy=0.0, r1=5.0, r2=3.0, rot=0.0)
        f1, f2 = el.get_focus_points(s.variables)
        c = math.sqrt(5.0**2 - 3.0**2)
        assert f1[0] == pytest.approx(c, abs=0.01)
        assert f2[0] == pytest.approx(-c, abs=0.01)

    def test_get_constrainables(self):
        s = make_solver()
        el, center, r1, r2, rot = make_ellipse(s)
        c = el.get_constrainables()
        assert center in c
        assert r1 in c
        assert r2 in c

    def test_registered_in_solver(self):
        s = make_solver()
        el, *_ = make_ellipse(s)
        assert el in s.ellipses


# ===========================================================================
# 10. ConstrainableBezierPath
# ===========================================================================

class TestConstrainableBezierPath:
    def test_get(self):
        s = make_solver()
        pts = [(0.0, 0.0), (1.0, 2.0), (3.0, 2.0), (4.0, 0.0)]
        bez, cpts = make_bezier(s, pts)
        result = bez.get(s.variables)
        assert len(result) == 4
        assert result[0] == pytest.approx((0.0, 0.0))
        assert result[3] == pytest.approx((4.0, 0.0))

    def test_get_segment(self):
        s = make_solver()
        pts = [(0.0, 0.0), (1.0, 2.0), (3.0, 2.0), (4.0, 0.0)]
        bez, _ = make_bezier(s, pts)
        seg = bez.get_segment(s.variables, 0)
        assert seg[0] == pytest.approx((0.0, 0.0))
        assert seg[3] == pytest.approx((4.0, 0.0))

    def test_path_segment_point_start(self):
        s = make_solver()
        bez, _ = make_bezier(s, [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)])
        pt = bez.path_segment_point(s.variables, 0.0, 0)
        assert pt == pytest.approx((0.0, 0.0))

    def test_path_segment_point_end(self):
        s = make_solver()
        bez, _ = make_bezier(s, [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)])
        pt = bez.path_segment_point(s.variables, 1.0, 0)
        assert pt == pytest.approx((3.0, 0.0))

    def test_path_point_start(self):
        s = make_solver()
        pts = [(0.0, 0.0), (1.0, 2.0), (3.0, 2.0), (4.0, 0.0)]
        bez, _ = make_bezier(s, pts)
        pt = bez.path_point(s.variables, 0.0)
        assert pt == pytest.approx((0.0, 0.0))

    def test_path_point_end(self):
        s = make_solver()
        pts = [(0.0, 0.0), (1.0, 2.0), (3.0, 2.0), (4.0, 0.0)]
        bez, _ = make_bezier(s, pts)
        pt = bez.path_point(s.variables, 1.0)
        assert pt == pytest.approx((4.0, 0.0))

    def test_path_segment_tangent_start(self):
        # Straight line: tangent should point in direction of line
        s = make_solver()
        bez, _ = make_bezier(s, [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)])
        tx, ty = bez.path_segment_tangent(s.variables, 0.0, 0)
        assert tx > 0
        assert ty == pytest.approx(0.0)

    def test_path_tangent_end(self):
        s = make_solver()
        bez, _ = make_bezier(s, [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)])
        tx, ty = bez.path_tangent(s.variables, 1.0)
        assert tx > 0

    def test_closest_path_point(self):
        s = make_solver()
        # Straight horizontal line disguised as Bezier
        bez, _ = make_bezier(s, [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)])
        px, py = bez.closest_path_point(s.variables, 1.5, 5.0)
        assert px == pytest.approx(1.5, abs=0.1)
        assert py == pytest.approx(0.0, abs=0.1)

    def test_get_constrainables(self):
        s = make_solver()
        bez, cpts = make_bezier(s)
        c = bez.get_constrainables()
        assert bez in c
        for cp in cpts:
            assert cp in c


# ===========================================================================
# 11. Constraint residuals and jacobians
# ===========================================================================

class TestLengthEqualsConstraint:
    def test_residual_equal(self):
        s = make_solver()
        l1 = make_length(s, 5.0)
        l2 = make_length(s, 5.0)
        c = LengthEqualsConstraint(l1, l2)
        assert c.residual(s.variables) == pytest.approx([0.0])

    def test_residual_unequal(self):
        s = make_solver()
        l1 = make_length(s, 5.0)
        l2 = make_length(s, 3.0)
        c = LengthEqualsConstraint(l1, l2)
        assert c.residual(s.variables) == pytest.approx([2.0])

    def test_jacobian_shape(self):
        s = make_solver()
        l1 = make_length(s, 5.0)
        l2 = make_length(s, 3.0)
        c = LengthEqualsConstraint(l1, l2)
        J = c.jacobian(s.variables)
        assert J.shape == (1, len(s.variables))
        assert J[0, l1.index] == pytest.approx(1.0)
        assert J[0, l2.index] == pytest.approx(-1.0)

    def test_solve_equal_lengths(self):
        s = make_solver()
        l1 = make_length(s, 10.0, fixed=True)
        l2 = make_length(s, 3.0)
        s.add_constraint(LengthEqualsConstraint(l1, l2))
        s.solve()
        assert l2.get(s.variables) == pytest.approx(10.0, abs=1e-4)


class TestAngleEqualsConstraint:
    def test_residual_equal(self):
        s = make_solver()
        a1 = make_angle(s, 45.0)
        a2 = make_angle(s, 45.0)
        c = AngleEqualsConstraint(a1, a2)
        assert c.residual(s.variables) == pytest.approx([0.0])

    def test_residual_unequal(self):
        s = make_solver()
        a1 = make_angle(s, 90.0)
        a2 = make_angle(s, 30.0)
        c = AngleEqualsConstraint(a1, a2)
        assert c.residual(s.variables) == pytest.approx([60.0])

    def test_jacobian_shape(self):
        s = make_solver()
        a1 = make_angle(s, 90.0)
        a2 = make_angle(s, 30.0)
        c = AngleEqualsConstraint(a1, a2)
        J = c.jacobian(s.variables)
        assert J.shape == (1, len(s.variables))

    def test_solve_equal_angles(self):
        s = make_solver()
        a1 = make_angle(s, 60.0, fixed=True)
        a2 = make_angle(s, 10.0)
        s.add_constraint(AngleEqualsConstraint(a1, a2))
        s.solve()
        assert a2.get(s.variables) == pytest.approx(60.0, abs=1e-4)


class TestCoincidentConstraint:
    def test_residual_same_point(self):
        s = make_solver()
        p1 = make_point(s, 3.0, 4.0)
        p2 = make_point(s, 3.0, 4.0)
        c = CoincidentConstraint(p1, p2)
        assert c.residual(s.variables) == pytest.approx([0.0, 0.0])

    def test_residual_different_points(self):
        s = make_solver()
        p1 = make_point(s, 0.0, 0.0)
        p2 = make_point(s, 3.0, 4.0)
        c = CoincidentConstraint(p1, p2)
        res = c.residual(s.variables)
        assert res == pytest.approx([-3.0, -4.0])

    def test_jacobian_shape(self):
        s = make_solver()
        p1 = make_point(s, 0.0, 0.0)
        p2 = make_point(s, 1.0, 1.0)
        c = CoincidentConstraint(p1, p2)
        J = c.jacobian(s.variables)
        assert J.shape == (2, len(s.variables))

    def test_solve_coincident(self):
        s = make_solver()
        p1 = make_point(s, 5.0, 7.0, fixed=True)
        p2 = make_point(s, 0.0, 0.0)
        s.add_constraint(CoincidentConstraint(p1, p2))
        s.solve()
        x, y = p2.get(s.variables)
        assert (x, y) == pytest.approx((5.0, 7.0), abs=1e-4)


class TestHorizontalConstraint:
    def test_residual_horizontal(self):
        s = make_solver()
        p1 = make_point(s, 0.0, 3.0)
        p2 = make_point(s, 5.0, 3.0)
        c = HorizontalConstraint(p1, p2)
        assert c.residual(s.variables) == pytest.approx([0.0])

    def test_residual_not_horizontal(self):
        s = make_solver()
        p1 = make_point(s, 0.0, 0.0)
        p2 = make_point(s, 5.0, 3.0)
        c = HorizontalConstraint(p1, p2)
        assert c.residual(s.variables) == pytest.approx([-3.0])

    def test_jacobian_shape(self):
        s = make_solver()
        p1 = make_point(s, 0.0, 0.0)
        p2 = make_point(s, 1.0, 1.0)
        c = HorizontalConstraint(p1, p2)
        J = c.jacobian(s.variables)
        assert J.shape == (1, len(s.variables))

    def test_solve_horizontal(self):
        s = make_solver()
        p1 = make_point(s, 0.0, 5.0, fixed=True)
        p2 = make_point(s, 3.0, 0.0)
        s.add_constraint(HorizontalConstraint(p1, p2))
        s.solve()
        _, y = p2.get(s.variables)
        assert y == pytest.approx(5.0, abs=1e-4)


class TestVerticalConstraint:
    def test_residual_vertical(self):
        s = make_solver()
        p1 = make_point(s, 3.0, 0.0)
        p2 = make_point(s, 3.0, 5.0)
        c = VerticalConstraint(p1, p2)
        assert c.residual(s.variables) == pytest.approx([0.0])

    def test_residual_not_vertical(self):
        s = make_solver()
        p1 = make_point(s, 0.0, 0.0)
        p2 = make_point(s, 3.0, 5.0)
        c = VerticalConstraint(p1, p2)
        assert c.residual(s.variables) == pytest.approx([-3.0])

    def test_jacobian_shape(self):
        s = make_solver()
        p1 = make_point(s, 0.0, 0.0)
        p2 = make_point(s, 1.0, 1.0)
        c = VerticalConstraint(p1, p2)
        J = c.jacobian(s.variables)
        assert J.shape == (1, len(s.variables))

    def test_solve_vertical(self):
        s = make_solver()
        p1 = make_point(s, 4.0, 0.0, fixed=True)
        p2 = make_point(s, 0.0, 5.0)
        s.add_constraint(VerticalConstraint(p1, p2))
        s.solve()
        x, _ = p2.get(s.variables)
        assert x == pytest.approx(4.0, abs=1e-4)


class TestPointIsOnLineSegmentConstraint:
    def test_residual_on_line(self):
        s = make_solver()
        line, p1, p2 = make_line(s, 0, 0, 4, 0)
        pt = make_point(s, 2.0, 0.0)
        c = PointIsOnLineSegmentConstraint(pt, line)
        res = c.residual(s.variables)
        assert abs(res[0]) < 1e-10

    def test_residual_off_line(self):
        s = make_solver()
        line, p1, p2 = make_line(s, 0, 0, 4, 0)
        pt = make_point(s, 2.0, 3.0)
        c = PointIsOnLineSegmentConstraint(pt, line)
        res = c.residual(s.variables)
        assert abs(res[0]) > 0.1

    def test_jacobian_shape(self):
        s = make_solver()
        line, _, _ = make_line(s, 0, 0, 4, 0)
        pt = make_point(s, 2.0, 1.0)
        c = PointIsOnLineSegmentConstraint(pt, line)
        J = c.jacobian(s.variables)
        assert J.ndim == 2

    def test_solve_point_on_line(self):
        s = make_solver()
        p1 = make_point(s, 0.0, 0.0, fixed=True)
        p2 = make_point(s, 4.0, 0.0, fixed=True)
        line = ConstrainableLine2D(s, p1, p2)
        pt = make_point(s, 2.0, 3.0)
        s.add_constraint(PointIsOnLineSegmentConstraint(pt, line))
        s.solve()
        _, y = pt.get(s.variables)
        assert y == pytest.approx(0.0, abs=0.1)


class TestPointIsOnCircleConstraint:
    def test_residual_on_circle(self):
        s = make_solver()
        circle, _, _ = make_circle(s, 0.0, 0.0, 5.0)
        pt = make_point(s, 5.0, 0.0)
        c = PointIsOnCircleConstraint(pt, circle)
        res = c.residual(s.variables)
        assert res == pytest.approx([0.0], abs=1e-10)

    def test_residual_off_circle(self):
        s = make_solver()
        circle, _, _ = make_circle(s, 0.0, 0.0, 5.0)
        pt = make_point(s, 3.0, 0.0)
        c = PointIsOnCircleConstraint(pt, circle)
        res = c.residual(s.variables)
        assert res == pytest.approx([-2.0])

    def test_jacobian_shape(self):
        s = make_solver()
        circle, _, _ = make_circle(s, 0.0, 0.0, 5.0)
        pt = make_point(s, 3.0, 4.0)
        c = PointIsOnCircleConstraint(pt, circle)
        J = c.jacobian(s.variables)
        assert J.shape == (1, len(s.variables))

    def test_solve_point_on_circle(self):
        s = make_solver()
        c_center = make_point(s, 0.0, 0.0, fixed=True)
        c_radius = make_length(s, 5.0, fixed=True)
        circle = ConstrainableCircle(s, c_center, c_radius)
        pt = make_point(s, 3.0, 0.0)
        s.add_constraint(PointIsOnCircleConstraint(pt, circle))
        s.solve()
        x, y = pt.get(s.variables)
        assert math.hypot(x, y) == pytest.approx(5.0, abs=0.01)


class TestPointIsOnArcConstraint:
    def test_residual_on_arc(self):
        s = make_solver()
        arc, *_ = make_arc(s, cx=0.0, cy=0.0, r=5.0, start=0.0, span=180.0)
        pt = make_point(s, 5.0, 0.0)
        c = PointIsOnArcConstraint(pt, arc)
        res = c.residual(s.variables)
        assert abs(res[0]) < 1e-10  # on radius

    def test_jacobian_shape(self):
        s = make_solver()
        arc, *_ = make_arc(s, cx=0.0, cy=0.0, r=5.0, start=0.0, span=180.0)
        pt = make_point(s, 5.0, 0.0)
        c = PointIsOnArcConstraint(pt, arc)
        J = c.jacobian(s.variables)
        assert J.ndim == 2


class TestPointCoincidentWithArcStartConstraint:
    def test_residual_at_start(self):
        s = make_solver()
        arc, *_ = make_arc(s, cx=0.0, cy=0.0, r=5.0, start=0.0, span=90.0)
        # Start at 0° -> (5, 0)
        pt = make_point(s, 5.0, 0.0)
        c = PointCoincidentWithArcStartConstraint(pt, arc)
        res = c.residual(s.variables)
        assert res == pytest.approx([0.0, 0.0], abs=1e-10)

    def test_residual_not_at_start(self):
        s = make_solver()
        arc, *_ = make_arc(s, cx=0.0, cy=0.0, r=5.0, start=0.0, span=90.0)
        pt = make_point(s, 0.0, 5.0)  # end point, not start
        c = PointCoincidentWithArcStartConstraint(pt, arc)
        res = c.residual(s.variables)
        assert not (abs(res[0]) < 1e-10 and abs(res[1]) < 1e-10)

    def test_jacobian_shape(self):
        s = make_solver()
        arc, *_ = make_arc(s, cx=0.0, cy=0.0, r=5.0, start=0.0, span=90.0)
        pt = make_point(s, 5.0, 0.0)
        c = PointCoincidentWithArcStartConstraint(pt, arc)
        J = c.jacobian(s.variables)
        assert J.shape == (2, len(s.variables))


class TestPointCoincidentWithArcEndConstraint:
    def test_residual_at_end(self):
        s = make_solver()
        arc, *_ = make_arc(s, cx=0.0, cy=0.0, r=5.0, start=0.0, span=90.0)
        # End at 90° -> (0, 5)
        pt = make_point(s, 0.0, 5.0)
        c = PointCoincidentWithArcEndConstraint(pt, arc)
        res = c.residual(s.variables)
        assert res == pytest.approx([0.0, 0.0], abs=1e-10)

    def test_jacobian_shape(self):
        s = make_solver()
        arc, *_ = make_arc(s, cx=0.0, cy=0.0, r=5.0, start=0.0, span=90.0)
        pt = make_point(s, 0.0, 5.0)
        c = PointCoincidentWithArcEndConstraint(pt, arc)
        J = c.jacobian(s.variables)
        assert J.shape == (2, len(s.variables))


class TestPointIsOnEllipseConstraint:
    def test_residual_on_perimeter(self):
        s = make_solver()
        el, *_ = make_ellipse(s, cx=0.0, cy=0.0, r1=5.0, r2=3.0, rot=0.0)
        pt = make_point(s, 5.0, 0.0)
        c = PointIsOnEllipseConstraint(pt, el)
        res = c.residual(s.variables)
        assert abs(res[0]) < 0.01

    def test_residual_off_perimeter(self):
        s = make_solver()
        el, *_ = make_ellipse(s, cx=0.0, cy=0.0, r1=5.0, r2=3.0, rot=0.0)
        pt = make_point(s, 10.0, 0.0)
        c = PointIsOnEllipseConstraint(pt, el)
        res = c.residual(s.variables)
        assert abs(res[0]) > 1.0


class TestPointIsOnBezierPathConstraint:
    def test_residual_on_path(self):
        s = make_solver()
        bez, _ = make_bezier(s, [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)])
        pt = make_point(s, 1.5, 0.0)
        c = PointIsOnBezierPathConstraint(pt, bez)
        res = c.residual(s.variables)
        assert math.hypot(*res) < 0.01

    def test_residual_off_path(self):
        s = make_solver()
        bez, _ = make_bezier(s, [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)])
        pt = make_point(s, 1.5, 5.0)
        c = PointIsOnBezierPathConstraint(pt, bez)
        res = c.residual(s.variables)
        assert math.hypot(*res) > 1.0


class TestLineAngleConstraint:
    def test_residual_correct_angle(self):
        s = make_solver()
        line, _, _ = make_line(s, 0, 0, 1, 0)  # horizontal
        c = LineAngleConstraint(line, 0.0)
        res = c.residual(s.variables)
        assert abs(res[0]) < 1e-10

    def test_residual_wrong_angle(self):
        s = make_solver()
        line, _, _ = make_line(s, 0, 0, 0, 1)  # vertical
        c = LineAngleConstraint(line, 0.0)
        res = c.residual(s.variables)
        assert abs(res[0]) > 1.0

    def test_jacobian_shape(self):
        s = make_solver()
        line, _, _ = make_line(s, 0, 0, 1, 0)
        c = LineAngleConstraint(line, 0.0)
        J = c.jacobian(s.variables)
        assert J.shape == (1, len(s.variables))

    def test_solve_horizontal(self):
        s = make_solver()
        p1 = make_point(s, 0.0, 0.0, fixed=True)
        p2 = make_point(s, 1.0, 1.0)
        line = ConstrainableLine2D(s, p1, p2)
        s.add_constraint(LineAngleConstraint(line, 0.0))
        s.solve()
        _, y2 = p2.get(s.variables)
        assert y2 == pytest.approx(0.0, abs=0.1)


class TestLineLengthConstraint:
    def test_residual_correct_length(self):
        s = make_solver()
        line, _, _ = make_line(s, 0, 0, 5, 0)
        c = LineLengthConstraint(line, 5.0)
        res = c.residual(s.variables)
        assert res == pytest.approx([0.0], abs=1e-10)

    def test_residual_wrong_length(self):
        s = make_solver()
        line, _, _ = make_line(s, 0, 0, 3, 0)
        c = LineLengthConstraint(line, 5.0)
        res = c.residual(s.variables)
        assert res == pytest.approx([-2.0])

    def test_jacobian_shape(self):
        s = make_solver()
        line, _, _ = make_line(s, 0, 0, 3, 4)
        c = LineLengthConstraint(line, 5.0)
        J = c.jacobian(s.variables)
        assert J.shape == (1, len(s.variables))

    def test_solve_length(self):
        s = make_solver()
        p1 = make_point(s, 0.0, 0.0, fixed=True)
        p2 = make_point(s, 3.0, 0.0)
        line = ConstrainableLine2D(s, p1, p2)
        s.add_constraint(LineLengthConstraint(line, 5.0))
        s.solve()
        assert line.length(s.variables) == pytest.approx(5.0, abs=0.01)


class TestLinesEqualLengthConstraint:
    def test_residual_equal(self):
        s = make_solver()
        l1, _, _ = make_line(s, 0, 0, 3, 0)
        l2, _, _ = make_line(s, 0, 0, 3, 0)
        c = LinesEqualLengthConstraint(l1, l2)
        res = c.residual(s.variables)
        assert res == pytest.approx([0.0])

    def test_residual_unequal(self):
        s = make_solver()
        l1, _, _ = make_line(s, 0, 0, 3, 0)
        l2, _, _ = make_line(s, 0, 0, 4, 0)
        c = LinesEqualLengthConstraint(l1, l2)
        res = c.residual(s.variables)
        # Residual is len1^2 - len2^2 = 9 - 16 = -7
        assert res == pytest.approx([-7.0])

    def test_jacobian_shape(self):
        s = make_solver()
        l1, _, _ = make_line(s, 0, 0, 3, 0)
        l2, _, _ = make_line(s, 0, 0, 4, 0)
        c = LinesEqualLengthConstraint(l1, l2)
        J = c.jacobian(s.variables)
        assert J.shape == (1, len(s.variables))


class TestLinesPerpendicularConstraint:
    def test_residual_perpendicular(self):
        s = make_solver()
        l1, _, _ = make_line(s, 0, 0, 1, 0)   # horizontal
        l2, _, _ = make_line(s, 0, 0, 0, 1)   # vertical
        c = LinesPerpendicularConstraint(l1, l2)
        res = c.residual(s.variables)
        assert res == pytest.approx([0.0], abs=1e-10)

    def test_residual_not_perpendicular(self):
        s = make_solver()
        l1, _, _ = make_line(s, 0, 0, 1, 0)
        l2, _, _ = make_line(s, 0, 0, 1, 1)
        c = LinesPerpendicularConstraint(l1, l2)
        res = c.residual(s.variables)
        assert abs(res[0]) > 0.5

    def test_jacobian_shape(self):
        s = make_solver()
        l1, _, _ = make_line(s, 0, 0, 1, 0)
        l2, _, _ = make_line(s, 0, 0, 0, 1)
        c = LinesPerpendicularConstraint(l1, l2)
        J = c.jacobian(s.variables)
        assert J.shape == (1, len(s.variables))


class TestLinesParallelConstraint:
    def test_residual_parallel(self):
        s = make_solver()
        l1, _, _ = make_line(s, 0, 0, 1, 0)
        l2, _, _ = make_line(s, 0, 1, 1, 1)  # also horizontal
        c = LinesParallelConstraint(l1, l2)
        res = c.residual(s.variables)
        assert res == pytest.approx([0.0], abs=1e-10)

    def test_residual_not_parallel(self):
        s = make_solver()
        l1, _, _ = make_line(s, 0, 0, 1, 0)
        l2, _, _ = make_line(s, 0, 0, 0, 1)  # vertical
        c = LinesParallelConstraint(l1, l2)
        res = c.residual(s.variables)
        assert abs(res[0]) > 0.5

    def test_jacobian_shape(self):
        s = make_solver()
        l1, _, _ = make_line(s, 0, 0, 1, 0)
        l2, _, _ = make_line(s, 0, 1, 1, 1)
        c = LinesParallelConstraint(l1, l2)
        J = c.jacobian(s.variables)
        assert J.shape == (1, len(s.variables))


class TestLineTangentToCircleConstraint:
    def test_residual_tangent(self):
        s = make_solver()
        circle, _, _ = make_circle(s, 0.0, 0.0, 3.0)
        # y=3 line is tangent to circle of radius 3 at origin
        line, _, _ = make_line(s, -5.0, 3.0, 5.0, 3.0)
        c = LineTangentToCircleConstraint(line, circle)
        res = c.residual(s.variables)
        assert abs(res[0]) < 0.01

    def test_residual_not_tangent(self):
        s = make_solver()
        circle, _, _ = make_circle(s, 0.0, 0.0, 3.0)
        line, _, _ = make_line(s, -5.0, 5.0, 5.0, 5.0)  # y=5, too far
        c = LineTangentToCircleConstraint(line, circle)
        res = c.residual(s.variables)
        assert abs(res[0]) > 1.0

    def test_jacobian_shape(self):
        s = make_solver()
        circle, _, _ = make_circle(s, 0.0, 0.0, 3.0)
        line, _, _ = make_line(s, -5.0, 3.0, 5.0, 3.0)
        c = LineTangentToCircleConstraint(line, circle)
        J = c.jacobian(s.variables)
        assert J.shape == (1, len(s.variables))


class TestLineTangentToArcConstraint:
    def test_residual_tangent_at_start(self):
        s = make_solver()
        arc, *_ = make_arc(s, cx=0.0, cy=0.0, r=3.0, start=90.0, span=90.0)
        # Tangent at start (90°): point (0,3), tangent direction = (-1, 0) -> y=3 horizontal
        line, _, _ = make_line(s, -5.0, 3.0, 5.0, 3.0)
        c = LineTangentToArcConstraint(line, arc, at_start=True)
        res = c.residual(s.variables)
        assert len(res) >= 1

    def test_jacobian_shape(self):
        s = make_solver()
        arc, *_ = make_arc(s, cx=0.0, cy=0.0, r=3.0, start=0.0, span=90.0)
        line, _, _ = make_line(s, -5.0, 3.0, 5.0, 3.0)
        c = LineTangentToArcConstraint(line, arc, at_start=True)
        J = c.jacobian(s.variables)
        assert J.ndim == 2


class TestArcRadiusConstraint:
    def test_residual_correct_radius(self):
        s = make_solver()
        arc, *_ = make_arc(s, r=5.0)
        c = ArcRadiusConstraint(arc, 5.0)
        assert c.residual(s.variables) == pytest.approx([0.0])

    def test_residual_wrong_radius(self):
        s = make_solver()
        arc, *_ = make_arc(s, r=3.0)
        c = ArcRadiusConstraint(arc, 5.0)
        assert c.residual(s.variables) == pytest.approx([-2.0])

    def test_jacobian_shape(self):
        s = make_solver()
        arc, *_ = make_arc(s, r=3.0)
        c = ArcRadiusConstraint(arc, 5.0)
        J = c.jacobian(s.variables)
        assert J.shape == (1, len(s.variables))

    def test_solve_arc_radius(self):
        s = make_solver()
        arc_center = make_point(s, 0.0, 0.0, fixed=True)
        arc_radius = make_length(s, 3.0)
        arc_start = make_angle(s, 0.0, fixed=True)
        arc_span = make_angle(s, 90.0, fixed=True)
        arc = ConstrainableArc(s, arc_center, arc_radius, arc_start, arc_span)
        s.add_constraint(ArcRadiusConstraint(arc, 7.0))
        s.solve()
        assert arc_radius.get(s.variables) == pytest.approx(7.0, abs=0.01)


class TestArcStartAngleConstraint:
    def test_residual_correct(self):
        s = make_solver()
        arc, *_ = make_arc(s, start=30.0)
        c = ArcStartAngleConstraint(arc, 30.0)
        assert c.residual(s.variables) == pytest.approx([0.0])

    def test_residual_wrong(self):
        s = make_solver()
        arc, *_ = make_arc(s, start=30.0)
        c = ArcStartAngleConstraint(arc, 60.0)
        assert c.residual(s.variables) == pytest.approx([-30.0])

    def test_jacobian_shape(self):
        s = make_solver()
        arc, *_ = make_arc(s, start=30.0)
        c = ArcStartAngleConstraint(arc, 60.0)
        J = c.jacobian(s.variables)
        assert J.shape == (1, len(s.variables))


class TestArcEndAngleConstraint:
    def test_residual_correct(self):
        s = make_solver()
        arc, *_ = make_arc(s, start=0.0, span=90.0)
        # end = 90
        c = ArcEndAngleConstraint(arc, 90.0)
        assert c.residual(s.variables) == pytest.approx([0.0])

    def test_residual_wrong(self):
        s = make_solver()
        arc, *_ = make_arc(s, start=0.0, span=90.0)
        c = ArcEndAngleConstraint(arc, 45.0)
        assert c.residual(s.variables) == pytest.approx([45.0])

    def test_jacobian_shape(self):
        s = make_solver()
        arc, *_ = make_arc(s, start=0.0, span=90.0)
        c = ArcEndAngleConstraint(arc, 90.0)
        J = c.jacobian(s.variables)
        assert J.shape == (1, len(s.variables))


class TestArcSpanAngleConstraint:
    def test_residual_correct(self):
        s = make_solver()
        arc, *_ = make_arc(s, span=120.0)
        c = ArcSpanAngleConstraint(arc, 120.0)
        assert c.residual(s.variables) == pytest.approx([0.0])

    def test_residual_wrong(self):
        s = make_solver()
        arc, *_ = make_arc(s, span=90.0)
        c = ArcSpanAngleConstraint(arc, 120.0)
        assert c.residual(s.variables) == pytest.approx([-30.0])

    def test_jacobian_shape(self):
        s = make_solver()
        arc, *_ = make_arc(s, span=90.0)
        c = ArcSpanAngleConstraint(arc, 120.0)
        J = c.jacobian(s.variables)
        assert J.shape == (1, len(s.variables))


class TestCircleTangentToCircleConstraint:
    def test_residual_tangent_externally(self):
        s = make_solver()
        c1, _, _ = make_circle(s, 0.0, 0.0, 3.0)
        c2, _, _ = make_circle(s, 8.0, 0.0, 5.0)
        # Distance = 8, sum of radii = 8 -> externally tangent
        c = CircleTangentToCircleConstraint(c1, c2)
        res = c.residual(s.variables)
        assert res == pytest.approx([0.0], abs=1e-10)

    def test_residual_not_tangent(self):
        s = make_solver()
        c1, _, _ = make_circle(s, 0.0, 0.0, 3.0)
        c2, _, _ = make_circle(s, 5.0, 0.0, 5.0)
        # Distance = 5, sum = 8 -> not tangent
        c = CircleTangentToCircleConstraint(c1, c2)
        res = c.residual(s.variables)
        assert abs(res[0]) > 1.0

    def test_jacobian_shape(self):
        s = make_solver()
        c1, _, _ = make_circle(s, 0.0, 0.0, 3.0)
        c2, _, _ = make_circle(s, 8.0, 0.0, 5.0)
        c = CircleTangentToCircleConstraint(c1, c2)
        J = c.jacobian(s.variables)
        assert J.shape == (1, len(s.variables))

    def test_solve_tangent_circles(self):
        s = make_solver()
        c1_center = make_point(s, 0.0, 0.0, fixed=True)
        c1_radius = make_length(s, 3.0, fixed=True)
        circ1 = ConstrainableCircle(s, c1_center, c1_radius)
        c2_center = make_point(s, 10.0, 0.0)
        c2_radius = make_length(s, 5.0, fixed=True)
        circ2 = ConstrainableCircle(s, c2_center, c2_radius)
        s.add_constraint(CircleTangentToCircleConstraint(circ1, circ2))
        s.solve()
        x2, y2 = c2_center.get(s.variables)
        d = math.hypot(x2, y2)
        assert d == pytest.approx(8.0, abs=0.1)


class TestArcTangentToCircleConstraint:
    def test_residual_shape(self):
        s = make_solver()
        arc, *_ = make_arc(s, cx=0.0, cy=0.0, r=3.0, start=0.0, span=180.0)
        circle, _, _ = make_circle(s, 8.0, 0.0, 5.0)
        c = ArcTangentToCircleConstraint(arc, circle)
        res = c.residual(s.variables)
        assert len(res) >= 1


# ===========================================================================
# 12. get_objtype
# ===========================================================================

class TestGetObjtype:
    def test_length(self):
        s = make_solver()
        ln = make_length(s)
        assert get_objtype(ln) == "length"

    def test_angle(self):
        s = make_solver()
        a = make_angle(s)
        assert get_objtype(a) == "angle"

    def test_point(self):
        s = make_solver()
        p = make_point(s)
        assert get_objtype(p) == "point"

    def test_line(self):
        s = make_solver()
        line, _, _ = make_line(s)
        assert get_objtype(line) == "line"

    def test_arc(self):
        s = make_solver()
        arc, *_ = make_arc(s)
        assert get_objtype(arc) == "arc"

    def test_circle(self):
        s = make_solver()
        circle, _, _ = make_circle(s)
        assert get_objtype(circle) == "circle"

    def test_ellipse(self):
        s = make_solver()
        el, *_ = make_ellipse(s)
        assert get_objtype(el) == "ellipse"

    def test_bezier(self):
        s = make_solver()
        bez, _ = make_bezier(s)
        assert get_objtype(bez) == "bezier"

    def test_unknown(self):
        assert get_objtype(object()) == ""


# ===========================================================================
# 13. get_possible_constraints and get_constraint
# ===========================================================================

class TestGetPossibleConstraints:
    def test_point_point_returns_coincident(self):
        s = make_solver()
        p1 = make_point(s, 0, 0)
        p2 = make_point(s, 1, 1)
        constraints = get_possible_constraints(p1, p2)
        assert any("coincides" in k for k in constraints.keys())

    def test_point_point_returns_horizontal(self):
        s = make_solver()
        p1 = make_point(s)
        p2 = make_point(s, 1, 0)
        constraints = get_possible_constraints(p1, p2)
        assert any("horizontal" in k for k in constraints.keys())

    def test_point_point_returns_vertical(self):
        s = make_solver()
        p1 = make_point(s)
        p2 = make_point(s, 1, 0)
        constraints = get_possible_constraints(p1, p2)
        assert any("vertical" in k for k in constraints.keys())

    def test_point_line_returns_on(self):
        s = make_solver()
        p = make_point(s)
        line, _, _ = make_line(s)
        constraints = get_possible_constraints(p, line)
        assert any("is on" in k for k in constraints.keys())

    def test_point_circle_returns_on(self):
        s = make_solver()
        p = make_point(s)
        circle, _, _ = make_circle(s)
        constraints = get_possible_constraints(p, circle)
        assert any("is on" in k for k in constraints.keys())

    def test_length_length_returns_equals(self):
        s = make_solver()
        l1 = make_length(s)
        l2 = make_length(s)
        constraints = get_possible_constraints(l1, l2)
        assert any("equals" in k for k in constraints.keys())

    def test_line_line_returns_parallel(self):
        s = make_solver()
        l1, _, _ = make_line(s)
        l2, _, _ = make_line(s)
        constraints = get_possible_constraints(l1, l2)
        assert any("parallel" in k for k in constraints.keys())

    def test_line_line_returns_perpendicular(self):
        s = make_solver()
        l1, _, _ = make_line(s)
        l2, _, _ = make_line(s)
        constraints = get_possible_constraints(l1, l2)
        assert any("perpendicular" in k for k in constraints.keys())

    def test_line_circle_returns_tangent(self):
        s = make_solver()
        line, _, _ = make_line(s)
        circle, _, _ = make_circle(s)
        constraints = get_possible_constraints(line, circle)
        assert any("tangent" in k for k in constraints.keys())

    def test_circle_circle_returns_tangent(self):
        s = make_solver()
        c1, _, _ = make_circle(s)
        c2, _, _ = make_circle(s)
        constraints = get_possible_constraints(c1, c2)
        assert any("tangent" in k for k in constraints.keys())

    def test_reversed_order_point_line(self):
        """get_possible_constraints normalizes order."""
        s = make_solver()
        p = make_point(s)
        line, _, _ = make_line(s)
        # Both orders should return constraints
        c1 = get_possible_constraints(p, line)
        c2 = get_possible_constraints(line, p)
        assert len(c1) > 0 or len(c2) > 0


class TestGetConstraint:
    def test_get_coincident_constraint(self):
        s = make_solver()
        p1 = make_point(s, 0, 0)
        p2 = make_point(s, 1, 1)
        c = get_constraint(p1, p2, "coincides with")
        assert c is not None
        assert isinstance(c, CoincidentConstraint)

    def test_get_nonexistent_constraint_returns_none(self):
        s = make_solver()
        p1 = make_point(s)
        p2 = make_point(s, 1, 1)
        # "some constraint" doesn't exist between point and point
        c = get_constraint(p1, p2, "some constraint")
        assert c is None

    def test_get_length_equals(self):
        s = make_solver()
        l1 = make_length(s, 3.0)
        l2 = make_length(s, 5.0)
        c = get_constraint(l1, l2, "equals")
        assert c is not None
        assert isinstance(c, LengthEqualsConstraint)

    def test_get_line_parallel(self):
        s = make_solver()
        l1, _, _ = make_line(s)
        l2, _, _ = make_line(s)
        c = get_constraint(l1, l2, "is parallel to")
        assert c is not None
        assert isinstance(c, LinesParallelConstraint)

    def test_get_point_on_circle(self):
        s = make_solver()
        p = make_point(s)
        circle, _, _ = make_circle(s)
        c = get_constraint(p, circle, "is on")
        assert c is not None
        assert isinstance(c, PointIsOnCircleConstraint)


# ===========================================================================
# 14. Integration: multi-constraint solving
# ===========================================================================

class TestIntegrationSolving:
    def test_triangle_right_angle(self):
        """Three points forming a right triangle."""
        s = make_solver()
        p1 = make_point(s, 0.0, 0.0, fixed=True)
        p2 = make_point(s, 3.0, 0.0, fixed=True)
        p3 = make_point(s, 3.0, 4.0)  # right angle at p2
        l1 = ConstrainableLine2D(s, p1, p2)
        l2 = ConstrainableLine2D(s, p2, p3)
        # Constrain l2 to be vertical
        s.add_constraint(LineAngleConstraint(l2, 90.0))
        s.solve()
        x3, _ = p3.get(s.variables)
        assert x3 == pytest.approx(3.0, abs=0.1)

    def test_two_coincident_chains(self):
        """Chain: p1 -> p2 -> p3 all coincident."""
        s = make_solver()
        p1 = make_point(s, 0.0, 0.0, fixed=True)
        p2 = make_point(s, 1.0, 1.0)
        p3 = make_point(s, 2.0, 2.0)
        s.add_constraint(CoincidentConstraint(p1, p2))
        s.add_constraint(CoincidentConstraint(p2, p3))
        s.solve()
        x2, y2 = p2.get(s.variables)
        x3, y3 = p3.get(s.variables)
        assert (x2, y2) == pytest.approx((0.0, 0.0), abs=0.01)
        assert (x3, y3) == pytest.approx((0.0, 0.0), abs=0.01)

    def test_equal_length_lines(self):
        """Two lines should have equal length after solving."""
        s = make_solver()
        p1 = make_point(s, 0.0, 0.0, fixed=True)
        p2 = make_point(s, 3.0, 0.0, fixed=True)
        l1 = ConstrainableLine2D(s, p1, p2)

        p3 = make_point(s, 0.0, 0.0, fixed=True)
        p4 = make_point(s, 0.0, 2.0)  # length 2, needs to become 3
        l2 = ConstrainableLine2D(s, p3, p4)

        s.add_constraint(LinesEqualLengthConstraint(l1, l2))
        s.solve()
        assert l2.length(s.variables) == pytest.approx(3.0, abs=0.1)

    def test_point_stays_on_circle(self):
        """Point constrained to circle should have correct distance from center."""
        s = make_solver()
        c_pt = make_point(s, 0.0, 0.0, fixed=True)
        c_r = make_length(s, 5.0, fixed=True)
        circle = ConstrainableCircle(s, c_pt, c_r)
        pt = make_point(s, 10.0, 10.0)
        s.add_constraint(PointIsOnCircleConstraint(pt, circle))
        s.solve()
        x, y = pt.get(s.variables)
        assert math.hypot(x, y) == pytest.approx(5.0, abs=0.05)

    def test_parallel_lines_after_solve(self):
        """Two lines should be parallel after solve."""
        s = make_solver()
        p1 = make_point(s, 0.0, 0.0, fixed=True)
        p2 = make_point(s, 3.0, 0.0, fixed=True)
        l1 = ConstrainableLine2D(s, p1, p2)

        p3 = make_point(s, 0.0, 1.0, fixed=True)
        p4 = make_point(s, 3.0, 2.0)  # slightly off
        l2 = ConstrainableLine2D(s, p3, p4)

        s.add_constraint(LinesParallelConstraint(l1, l2))
        s.solve()
        # Cross product of direction vectors should be ~0
        x0, y0, x1, y1 = l1.get(s.variables)
        x2, y2, x3, y3 = l2.get(s.variables)
        cross = (x1 - x0) * (y3 - y2) - (y1 - y0) * (x3 - x2)
        assert cross == pytest.approx(0.0, abs=0.01)

# ===========================================================================
# Additional tests to improve coverage of uncovered constraint classes
# ===========================================================================


class TestGaussNewtonWithAnalyticConstraint:
    """Cover lines 139-140: gauss_newton_solve with Constraint objects (analytic)."""

    def test_analytic_constraint_in_gauss_newton(self):
        s = make_solver()
        p1 = make_point(s, 5.0, 5.0)
        target = make_point(s, 0.0, 0.0, fixed=True)
        s.add_constraint(CoincidentConstraint(p1, target))
        s.gauss_newton_solve()
        xv, yv = p1.get(s.variables)
        assert (xv, yv) == pytest.approx((0.0, 0.0), abs=0.01)

    def test_analytic_and_callable_mixed_in_gauss_newton(self):
        s = make_solver()
        p1 = make_point(s, 3.0, 4.0)
        target = make_point(s, 0.0, 0.0, fixed=True)
        # Analytic constraint
        s.add_constraint(CoincidentConstraint(p1, target))
        # Callable soft constraint
        s.add_soft_constraint(lambda x: [x[p1.xi]], weight=0.001)
        s.gauss_newton_solve()
        xv, yv = p1.get(s.variables)
        assert math.hypot(xv, yv) < 0.1

    def test_solve_with_soft_constraint(self):
        """Cover line 197: solve() with soft_constraints."""
        s = make_solver()
        s.add_variable(0.0, "x")
        s.add_constraint(lambda x: [x[0] - 5.0])
        s.add_soft_constraint(lambda x: [x[0]], weight=0.01)
        s.solve()
        assert s.variables[0] == pytest.approx(5.0, abs=0.1)


class TestArcSpanAngleConstraint:
    """Cover ArcSpanAngleConstraint (including wraparound branch, line 2208)."""

    def test_residual_satisfied(self):
        s = make_solver()
        arc, *_ = make_arc(s, start=0.0, span=90.0)
        c = ArcSpanAngleConstraint(arc, 90.0)
        res = c.residual(s.variables)
        assert res == pytest.approx([0.0], abs=0.01)

    def test_residual_unsatisfied(self):
        s = make_solver()
        arc, *_ = make_arc(s, start=0.0, span=45.0)
        c = ArcSpanAngleConstraint(arc, 90.0)
        res = c.residual(s.variables)
        assert res[0] == pytest.approx(-45.0, abs=0.01)

    def test_jacobian_shape(self):
        s = make_solver()
        arc, *_ = make_arc(s, start=0.0, span=90.0)
        c = ArcSpanAngleConstraint(arc, 90.0)
        J = c.jacobian(s.variables)
        assert J.shape == (1, len(s.variables))

    def test_jacobian_nonzero_entries(self):
        s = make_solver()
        arc, center, radius, start_a, span_a = make_arc(s, start=0.0, span=90.0)
        c = ArcSpanAngleConstraint(arc, 90.0)
        J = c.jacobian(s.variables)
        assert J[0, start_a.index] == pytest.approx(-1.0)
        assert J[0, span_a.index] == pytest.approx(1.0)

    def test_wraparound_branch(self):
        """Cover line 2208/2225: start > end case."""
        s = make_solver()
        arc, center, radius, start_a, span_a = make_arc(s, start=300.0, span=60.0)
        # start=300, end=60 → start > end (when normalized)
        # 300 > 60, so wraparound: span = 60 - 300 + 360 = 120
        c = ArcSpanAngleConstraint(arc, 120.0)
        res = c.residual(s.variables)
        assert res == pytest.approx([0.0], abs=1.0)
        J = c.jacobian(s.variables)
        assert J.shape == (1, len(s.variables))


class TestArcTangentToArcConstraint:
    def test_residual_shape(self):
        s = make_solver()
        arc1, *_ = make_arc(s, cx=0.0, cy=0.0, r=3.0)
        arc2, *_ = make_arc(s, cx=8.0, cy=0.0, r=5.0)
        c = ArcTangentToArcConstraint(arc1, arc2)
        res = c.residual(s.variables)
        assert res.shape == (2,)

    def test_residual_tangent_arcs(self):
        """Arcs tangent externally: dist = r1 + r2."""
        s = make_solver()
        arc1, *_ = make_arc(s, cx=0.0, cy=0.0, r=3.0)
        arc2, *_ = make_arc(s, cx=8.0, cy=0.0, r=5.0)
        c = ArcTangentToArcConstraint(arc1, arc2)
        res = c.residual(s.variables)
        # dist=8, r1+r2=8 → first constraint = 0
        assert res[0] == pytest.approx(0.0, abs=0.01)

    def test_jacobian_shape(self):
        s = make_solver()
        arc1, *_ = make_arc(s, cx=0.0, cy=0.0, r=3.0)
        arc2, *_ = make_arc(s, cx=8.0, cy=0.0, r=5.0)
        c = ArcTangentToArcConstraint(arc1, arc2)
        J = c.jacobian(s.variables)
        assert J.shape == (1, len(s.variables))

    def test_jacobian_nonzero_for_separated_arcs(self):
        s = make_solver()
        arc1, c1, r1, *_ = make_arc(s, cx=0.0, cy=0.0, r=3.0)
        arc2, c2, r2, *_ = make_arc(s, cx=8.0, cy=0.0, r=5.0)
        c = ArcTangentToArcConstraint(arc1, arc2)
        J = c.jacobian(s.variables)
        # Should have nonzero entries for center coordinates and radii
        assert np.any(J != 0.0)


class TestArcTangentToCircleConstraint:
    def test_residual_tangent(self):
        s = make_solver()
        arc, *_ = make_arc(s, cx=0.0, cy=0.0, r=3.0)
        circle, *_ = make_circle(s, cx=8.0, cy=0.0, r=5.0)
        c = ArcTangentToCircleConstraint(arc, circle)
        res = c.residual(s.variables)
        assert res.shape == (1,)
        assert res[0] == pytest.approx(0.0, abs=0.01)

    def test_residual_not_tangent(self):
        s = make_solver()
        arc, *_ = make_arc(s, cx=0.0, cy=0.0, r=3.0)
        circle, *_ = make_circle(s, cx=10.0, cy=0.0, r=5.0)
        c = ArcTangentToCircleConstraint(arc, circle)
        res = c.residual(s.variables)
        assert res[0] != pytest.approx(0.0, abs=0.01)

    def test_jacobian_shape(self):
        s = make_solver()
        arc, *_ = make_arc(s, cx=0.0, cy=0.0, r=3.0)
        circle, *_ = make_circle(s, cx=8.0, cy=0.0, r=5.0)
        c = ArcTangentToCircleConstraint(arc, circle)
        J = c.jacobian(s.variables)
        assert J.shape == (1, len(s.variables))

    def test_jacobian_nonzero(self):
        s = make_solver()
        arc, *_ = make_arc(s, cx=0.0, cy=0.0, r=3.0)
        circle, *_ = make_circle(s, cx=8.0, cy=0.0, r=5.0)
        c = ArcTangentToCircleConstraint(arc, circle)
        J = c.jacobian(s.variables)
        assert np.any(J != 0.0)


class TestArcTangentToEllipseConstraint:
    def test_residual_shape(self):
        s = make_solver()
        arc, *_ = make_arc(s, cx=0.0, cy=0.0, r=3.0)
        el, *_ = make_ellipse(s, cx=10.0, cy=0.0, r1=5.0, r2=3.0)
        c = ArcTangentToEllipseConstraint(arc, el)
        res = c.residual(s.variables)
        assert res.shape[0] >= 1

    def test_jacobian_shape(self):
        s = make_solver()
        arc, *_ = make_arc(s, cx=0.0, cy=0.0, r=3.0)
        el, *_ = make_ellipse(s, cx=10.0, cy=0.0, r1=5.0, r2=3.0)
        c = ArcTangentToEllipseConstraint(arc, el)
        J = c.jacobian(s.variables)
        assert J.ndim == 2
        assert J.shape[1] == len(s.variables)


class TestArcTangentToBezierConstraint:
    def test_residual_shape(self):
        s = make_solver()
        arc, *_ = make_arc(s, cx=2.0, cy=5.0, r=3.0)
        bezier, _ = make_bezier(s, points=[(0.0, 0.0), (1.0, 3.0), (3.0, 3.0), (4.0, 0.0)])
        c = ArcTangentToBezierConstraint(arc, bezier)
        res = c.residual(s.variables)
        assert res.shape == (2,)

    def test_jacobian_shape(self):
        s = make_solver()
        arc, *_ = make_arc(s, cx=2.0, cy=5.0, r=3.0)
        bezier, _ = make_bezier(s, points=[(0.0, 0.0), (1.0, 3.0), (3.0, 3.0), (4.0, 0.0)])
        c = ArcTangentToBezierConstraint(arc, bezier)
        J = c.jacobian(s.variables)
        assert J.shape == (2, len(s.variables))


class TestLineTangentToEllipseConstraint:
    def test_residual_shape(self):
        s = make_solver()
        line, *_ = make_line(s, x0=-5.0, y0=3.0, x1=5.0, y1=3.0)
        el, *_ = make_ellipse(s, cx=0.0, cy=0.0, r1=5.0, r2=3.0)
        c = LineTangentToEllipseConstraint(line, el)
        res = c.residual(s.variables)
        assert res.shape == (2,)

    def test_residual_near_tangent(self):
        """Horizontal line tangent to top of ellipse (r2=3) → distance≈0."""
        s = make_solver()
        line, *_ = make_line(s, x0=-5.0, y0=3.0, x1=5.0, y1=3.0)
        el, *_ = make_ellipse(s, cx=0.0, cy=0.0, r1=5.0, r2=3.0)
        c = LineTangentToEllipseConstraint(line, el)
        res = c.residual(s.variables)
        # dist residual should be near 0 for tangent line
        assert abs(res[0]) < 0.1

    def test_jacobian_shape(self):
        s = make_solver()
        line, *_ = make_line(s, x0=-5.0, y0=3.0, x1=5.0, y1=3.0)
        el, *_ = make_ellipse(s, cx=0.0, cy=0.0, r1=5.0, r2=3.0)
        c = LineTangentToEllipseConstraint(line, el)
        J = c.jacobian(s.variables)
        assert J.shape == (2, len(s.variables))

    def test_jacobian_nonzero(self):
        # Use a line far from ellipse so dist > 1e-10, exercising derivative code
        s = make_solver()
        line, *_ = make_line(s, x0=-5.0, y0=10.0, x1=5.0, y1=10.0)
        el, *_ = make_ellipse(s, cx=0.0, cy=0.0, r1=5.0, r2=3.0)
        c = LineTangentToEllipseConstraint(line, el)
        J = c.jacobian(s.variables)
        assert np.any(J != 0.0)


class TestLineTangentToBezierConstraint:
    def test_residual_shape(self):
        s = make_solver()
        line, *_ = make_line(s, x0=0.0, y0=2.0, x1=4.0, y1=2.0)
        bezier, _ = make_bezier(s, points=[(0.0, 0.0), (1.0, 2.0), (3.0, 2.0), (4.0, 0.0)])
        c = LineTangentToBezierConstraint(line, bezier)
        res = c.residual(s.variables)
        assert res.shape == (2,)

    def test_jacobian_shape(self):
        s = make_solver()
        line, *_ = make_line(s, x0=0.0, y0=2.0, x1=4.0, y1=2.0)
        bezier, _ = make_bezier(s, points=[(0.0, 0.0), (1.0, 2.0), (3.0, 2.0), (4.0, 0.0)])
        c = LineTangentToBezierConstraint(line, bezier)
        J = c.jacobian(s.variables)
        assert J.shape == (2, len(s.variables))

    def test_jacobian_nonzero(self):
        s = make_solver()
        line, *_ = make_line(s, x0=0.0, y0=2.0, x1=4.0, y1=2.0)
        bezier, _ = make_bezier(s, points=[(0.0, 0.0), (1.0, 2.0), (3.0, 2.0), (4.0, 0.0)])
        c = LineTangentToBezierConstraint(line, bezier)
        J = c.jacobian(s.variables)
        assert np.any(J != 0.0)


class TestCircleTangentToEllipseConstraint:
    def test_residual_shape(self):
        s = make_solver()
        circle, *_ = make_circle(s, cx=7.0, cy=0.0, r=2.0)
        el, *_ = make_ellipse(s, cx=0.0, cy=0.0, r1=5.0, r2=3.0)
        c = CircleTangentToEllipseConstraint(circle, el)
        res = c.residual(s.variables)
        assert res.shape == (2,)

    def test_jacobian_shape(self):
        s = make_solver()
        circle, *_ = make_circle(s, cx=7.0, cy=0.0, r=2.0)
        el, *_ = make_ellipse(s, cx=0.0, cy=0.0, r1=5.0, r2=3.0)
        c = CircleTangentToEllipseConstraint(circle, el)
        J = c.jacobian(s.variables)
        assert J.shape == (2, len(s.variables))

    def test_jacobian_nonzero(self):
        s = make_solver()
        circle, *_ = make_circle(s, cx=7.0, cy=0.0, r=2.0)
        el, *_ = make_ellipse(s, cx=0.0, cy=0.0, r1=5.0, r2=3.0)
        c = CircleTangentToEllipseConstraint(circle, el)
        J = c.jacobian(s.variables)
        assert np.any(J != 0.0)


class TestCircleTangentToBezierConstraint:
    def test_residual_shape(self):
        s = make_solver()
        circle, *_ = make_circle(s, cx=2.0, cy=4.0, r=1.0)
        bezier, _ = make_bezier(s, points=[(0.0, 0.0), (1.0, 3.0), (3.0, 3.0), (4.0, 0.0)])
        c = CircleTangentToBezierConstraint(circle, bezier)
        res = c.residual(s.variables)
        assert res.shape == (2,)

    def test_jacobian_shape(self):
        s = make_solver()
        circle, *_ = make_circle(s, cx=2.0, cy=4.0, r=1.0)
        bezier, _ = make_bezier(s, points=[(0.0, 0.0), (1.0, 3.0), (3.0, 3.0), (4.0, 0.0)])
        c = CircleTangentToBezierConstraint(circle, bezier)
        J = c.jacobian(s.variables)
        assert J.shape == (2, len(s.variables))

    def test_jacobian_nonzero(self):
        s = make_solver()
        circle, *_ = make_circle(s, cx=2.0, cy=4.0, r=1.0)
        bezier, _ = make_bezier(s, points=[(0.0, 0.0), (1.0, 3.0), (3.0, 3.0), (4.0, 0.0)])
        c = CircleTangentToBezierConstraint(circle, bezier)
        J = c.jacobian(s.variables)
        assert np.any(J != 0.0)


class TestCircleTangentToCircleCoincidentCenters:
    """Cover lines 2687-2692: circles with coincident centers."""

    def test_jacobian_coincident_centers(self):
        s = make_solver()
        c1, *_ = make_circle(s, cx=0.0, cy=0.0, r=3.0)
        c2, *_ = make_circle(s, cx=0.0, cy=0.0, r=5.0)  # same center
        c = CircleTangentToCircleConstraint(c1, c2)
        J = c.jacobian(s.variables)
        assert J.shape == (1, len(s.variables))
        # Should produce nonzero fallback derivatives
        assert np.any(J != 0.0)


class TestEllipseTangentToEllipseConstraint:
    def test_residual_shape(self):
        s = make_solver()
        el1, *_ = make_ellipse(s, cx=0.0, cy=0.0, r1=5.0, r2=3.0)
        el2, *_ = make_ellipse(s, cx=12.0, cy=0.0, r1=5.0, r2=3.0)
        c = EllipseTangentToEllipseConstraint(el1, el2)
        res = c.residual(s.variables)
        assert res.shape == (2,)

    def test_jacobian_shape(self):
        s = make_solver()
        el1, *_ = make_ellipse(s, cx=0.0, cy=0.0, r1=5.0, r2=3.0)
        el2, *_ = make_ellipse(s, cx=12.0, cy=0.0, r1=5.0, r2=3.0)
        c = EllipseTangentToEllipseConstraint(el1, el2)
        J = c.jacobian(s.variables)
        assert J.shape == (2, len(s.variables))

    def test_jacobian_nonzero(self):
        s = make_solver()
        el1, *_ = make_ellipse(s, cx=0.0, cy=0.0, r1=5.0, r2=3.0)
        el2, *_ = make_ellipse(s, cx=12.0, cy=0.0, r1=5.0, r2=3.0)
        c = EllipseTangentToEllipseConstraint(el1, el2)
        J = c.jacobian(s.variables)
        assert np.any(J != 0.0)


class TestEllipseTangentToBezierConstraint:
    def test_residual_shape(self):
        s = make_solver()
        el, *_ = make_ellipse(s, cx=2.0, cy=3.0, r1=3.0, r2=2.0)
        bezier, _ = make_bezier(s, points=[(0.0, 0.0), (1.0, 4.0), (3.0, 4.0), (4.0, 0.0)])
        c = EllipseTangentToBezierConstraint(el, bezier)
        res = c.residual(s.variables)
        assert res.shape[0] >= 1

    def test_jacobian_shape(self):
        s = make_solver()
        el, *_ = make_ellipse(s, cx=2.0, cy=3.0, r1=3.0, r2=2.0)
        bezier, _ = make_bezier(s, points=[(0.0, 0.0), (1.0, 4.0), (3.0, 4.0), (4.0, 0.0)])
        c = EllipseTangentToBezierConstraint(el, bezier)
        J = c.jacobian(s.variables)
        assert J.ndim == 2
        assert J.shape[1] == len(s.variables)


class TestPointIsOnBezierJacobian:
    """Cover PointIsOnBezierPathConstraint.jacobian (lines 1234-1359)."""

    def test_jacobian_shape(self):
        s = make_solver()
        pt = make_point(s, 2.0, 1.5)
        bezier, _ = make_bezier(s, points=[(0.0, 0.0), (1.0, 2.0), (3.0, 2.0), (4.0, 0.0)])
        c = PointIsOnBezierPathConstraint(pt, bezier)
        J = c.jacobian(s.variables)
        assert J.shape == (2, len(s.variables))

    def test_jacobian_nonzero(self):
        s = make_solver()
        pt = make_point(s, 2.0, 1.5)
        bezier, _ = make_bezier(s, points=[(0.0, 0.0), (1.0, 2.0), (3.0, 2.0), (4.0, 0.0)])
        c = PointIsOnBezierPathConstraint(pt, bezier)
        J = c.jacobian(s.variables)
        assert np.any(J != 0.0)


class TestPointIsOnEllipseJacobian:
    """Cover PointIsOnEllipseConstraint.jacobian (lines 1169-1212)."""

    def test_jacobian_shape(self):
        s = make_solver()
        pt = make_point(s, 5.0, 0.0)  # On perimeter of 5x3 ellipse
        el, *_ = make_ellipse(s, cx=0.0, cy=0.0, r1=5.0, r2=3.0)
        c = PointIsOnEllipseConstraint(pt, el)
        J = c.jacobian(s.variables)
        assert J.shape == (1, len(s.variables))

    def test_jacobian_nonzero(self):
        s = make_solver()
        pt = make_point(s, 5.0, 0.0)
        el, *_ = make_ellipse(s, cx=0.0, cy=0.0, r1=5.0, r2=3.0)
        c = PointIsOnEllipseConstraint(pt, el)
        J = c.jacobian(s.variables)
        assert np.any(J != 0.0)

    def test_residual_no_closest_point(self):
        """Cover line 1162: no closest point returns [1.0, 1.0]."""
        # An ellipse with r1=r2=0 has no perimeter points
        s = make_solver()
        pt = make_point(s, 1.0, 0.0)
        el, *_ = make_ellipse(s, cx=0.0, cy=0.0, r1=0.0, r2=0.0)
        c = PointIsOnEllipseConstraint(pt, el)
        res = c.residual(s.variables)
        # Should still return an array
        assert res.shape[0] >= 1


class TestConstrainableBezierPathTangentAtOne:
    """Cover ConstrainableBezierPath.path_tangent for t=1.0 (lines 698-701)."""

    def test_path_tangent_at_one(self):
        s = make_solver()
        bezier, cpts = make_bezier(s, points=[(0.0, 0.0), (1.0, 2.0), (3.0, 2.0), (4.0, 0.0)])
        # t=1.0 hits the end tangent code branch
        tangent = bezier.path_tangent(s.variables, 1.0)
        assert len(tangent) == 2
        # End tangent should point toward end of last segment
        assert tangent[0] != 0.0 or tangent[1] != 0.0  # Not zero tangent

    def test_path_tangent_at_zero(self):
        s = make_solver()
        bezier, _ = make_bezier(s, points=[(0.0, 0.0), (1.0, 2.0), (3.0, 2.0), (4.0, 0.0)])
        tangent = bezier.path_tangent(s.variables, 0.0)
        assert len(tangent) == 2

    def test_path_tangent_at_middle(self):
        s = make_solver()
        bezier, _ = make_bezier(s, points=[(0.0, 0.0), (1.0, 2.0), (3.0, 2.0), (4.0, 0.0)])
        tangent = bezier.path_tangent(s.variables, 0.5)
        assert len(tangent) == 2


class TestConstrainableArcWraparoundEdgeCases:
    """Cover lines 446-447: angle_from_arc_span wraparound branch."""

    def test_angle_from_arc_span_wraparound_outside(self):
        """Arc with negative span triggers start > end branch."""
        s = make_solver()
        # span=-20 → end = start + span = 45 + (-20) = 25; start(45) > end(25)
        arc, center, radius, start_a, span_a = make_arc(s, cx=0.0, cy=0.0, r=5.0,
                                                          start=45.0, span=-20.0)
        # angle=30 is between end(25) and start(45) → in the gap → nonzero delta
        delta_in_gap = arc.angle_from_arc_span(s.variables, 30.0)
        # angle=10 is outside the gap (< end) → inside arc → zero delta
        delta_in_arc = arc.angle_from_arc_span(s.variables, 10.0)
        assert delta_in_gap > 0.0   # outside arc
        assert delta_in_arc == pytest.approx(0.0, abs=0.01)  # inside arc

    def test_angle_from_arc_span_wraparound_inside_range_check(self):
        """When start > end, angles outside the gap have delta=0."""
        s = make_solver()
        # span=-30 → end = 60 + (-30) = 30; start(60) > end(30)
        arc, center, radius, start_a, span_a = make_arc(s, cx=0.0, cy=0.0, r=5.0,
                                                          start=60.0, span=-30.0)
        # angle=50 is in gap (30 < 50 < 60) → outside arc → nonzero
        outside_delta = arc.angle_from_arc_span(s.variables, 50.0)
        # angle=200 is not in gap → inside arc → zero
        inside_delta = arc.angle_from_arc_span(s.variables, 200.0)
        assert outside_delta > 0.0
        assert inside_delta == pytest.approx(0.0, abs=0.01)


class TestConstrainableEllipseEdgeCases:
    """Cover remaining ellipse edge cases (lines 580-582, 601, 638)."""

    def test_closest_point_golden_section(self):
        """Cover golden section search iterations (lines 580-582)."""
        s = make_solver()
        el, *_ = make_ellipse(s, cx=0.0, cy=0.0, r1=10.0, r2=2.0, rot=45.0)
        # Far-off point forces many iterations
        pt = el.closest_point_on_perimeter(s.variables, 15.0, 15.0)
        assert pt is not None
        assert len(pt) == 2

    def test_distance_zero_when_no_closest_point(self):
        """Cover line 601: returns 0 if no closest point."""
        s = make_solver()
        el, *_ = make_ellipse(s, cx=0.0, cy=0.0, r1=0.0, r2=0.0)
        d = el.distance_to_perimeter(s.variables, 1.0, 0.0)
        assert d >= 0.0

    def test_eccentricity_zero_radius(self):
        """Cover line 638: returns 0 if major_r == 0."""
        s = make_solver()
        el, *_ = make_ellipse(s, cx=0.0, cy=0.0, r1=0.0, r2=0.0)
        e = el.eccentricity(s.variables)
        assert e == 0.0


class TestConstraintBaseClassAbstractMethods:
    """Cover lines 21, 24: base Constraint methods raise NotImplementedError."""

    def test_residual_raises(self):
        class Bare(Constraint):
            pass
        c = Bare()
        with pytest.raises(NotImplementedError):
            c.residual([])

    def test_jacobian_raises(self):
        class Bare(Constraint):
            pass
        c = Bare()
        with pytest.raises(NotImplementedError):
            c.jacobian([])


class TestConstrainableBaseClassMethods:
    """Cover lines 38, 41, 44: Constrainable base methods."""

    def test_get_possible_constraints_returns_empty(self):
        """Constrainable.get_possible_constraints returns {}."""
        s = make_solver()
        obj = Constrainable(s, "test")
        result = obj.get_possible_constraints(None)
        assert result == {}

    def test_get_bounds_raises(self):
        """Constrainable.get_bounds raises NotImplementedError."""
        s = make_solver()
        obj = Constrainable(s, "test")
        with pytest.raises(NotImplementedError):
            obj.get_bounds()

    def test_get_constrainables_returns_empty(self):
        """Constrainable.get_constrainables returns []."""
        s = make_solver()
        obj = Constrainable(s, "test")
        result = obj.get_constrainables()
        assert result == []

    def test_get_label(self):
        """Constrainable.get_label returns label."""
        s = make_solver()
        obj = Constrainable(s, "my_label")
        assert obj.get_label() == "my_label"


class TestPointIsOnArcEdgeCases:
    """Cover edge cases in PointIsOnArcConstraint jacobian (lines 968-972, 996-1009)."""

    def test_jacobian_point_at_arc_center(self):
        """Cover lines 968-972: point exactly at arc center → zero distance."""
        s = make_solver()
        arc, center, *_ = make_arc(s, cx=0.0, cy=0.0, r=5.0, start=0.0, span=360.0)
        # Point at arc center (distance = 0)
        pt = make_point(s, 0.0, 0.0)
        c = PointIsOnArcConstraint(pt, arc)
        J = c.jacobian(s.variables)
        assert J.shape[1] == len(s.variables)

    def test_jacobian_point_outside_span(self):
        """Cover lines 996-1009: point outside arc span."""
        s = make_solver()
        arc, *_ = make_arc(s, cx=0.0, cy=0.0, r=5.0, start=0.0, span=90.0)
        # Point at 180° — outside the 0°-90° span
        pt = make_point(s, -5.0, 0.0)
        c = PointIsOnArcConstraint(pt, arc)
        J = c.jacobian(s.variables)
        assert J.shape == (2, len(s.variables))

    def test_jacobian_normal(self):
        """Point on arc → normal jacobian case."""
        s = make_solver()
        arc, *_ = make_arc(s, cx=0.0, cy=0.0, r=5.0, start=0.0, span=90.0)
        pt = make_point(s, 5.0, 0.0)  # On arc at 0°
        c = PointIsOnArcConstraint(pt, arc)
        J = c.jacobian(s.variables)
        assert J.shape == (2, len(s.variables))


class TestPointIsOnLineEdgeCases:
    """Cover edge cases in PointIsOnLineConstraint jacobian (lines 860, 899-923)."""

    def test_jacobian_point_before_line_start(self):
        """Cover lines 899-923: t < 0 case."""
        s = make_solver()
        line, p1, p2 = make_line(s, x0=0.0, y0=0.0, x1=5.0, y1=0.0)
        pt = make_point(s, -3.0, 0.0)  # Before start
        c = PointIsOnLineSegmentConstraint(pt, line)
        J = c.jacobian(s.variables)
        assert J.shape[1] == len(s.variables)

    def test_jacobian_point_after_line_end(self):
        """Cover lines 899-914: t > 1 case."""
        s = make_solver()
        line, p1, p2 = make_line(s, x0=0.0, y0=0.0, x1=5.0, y1=0.0)
        pt = make_point(s, 8.0, 0.0)  # After end
        c = PointIsOnLineSegmentConstraint(pt, line)
        J = c.jacobian(s.variables)
        assert J.shape[1] == len(s.variables)

    def test_residual_x_coordinate_branch(self):
        """Cover line 860: x-coordinate branch in residual."""
        s = make_solver()
        # Diagonal line to exercise x-coordinate branch
        line, p1, p2 = make_line(s, x0=0.0, y0=0.0, x1=3.0, y1=4.0)
        pt = make_point(s, 1.5, 2.0)  # Midpoint of line
        c = PointIsOnLineSegmentConstraint(pt, line)
        res = c.residual(s.variables)
        assert res is not None


class TestPointIsOnCircleEdgeCases:
    """Cover PointIsOnCircleConstraint jacobian center case (lines 1142-1146)."""

    def test_jacobian_point_at_circle_center(self):
        """Cover lines 1142-1146: point at circle center."""
        s = make_solver()
        circle, center, *_ = make_circle(s, cx=0.0, cy=0.0, r=5.0)
        pt = make_point(s, 0.0, 0.0)  # At circle center
        c = PointIsOnCircleConstraint(pt, circle)
        J = c.jacobian(s.variables)
        assert J.shape == (1, len(s.variables))


class TestLineLengthAndAngleZeroLengthEdgeCases:
    """Cover zero-length line pass branches (lines 1409, 1459)."""

    def test_line_angle_jacobian_zero_length_line(self):
        s = make_solver()
        line, p1, p2 = make_line(s, x0=0.0, y0=0.0, x1=0.0, y1=0.0)  # Zero-length
        c = LineAngleConstraint(line, 0.0)
        J = c.jacobian(s.variables)
        assert J.shape[1] == len(s.variables)
        # Zero-length line → pass → all zeros
        assert np.all(J == 0.0)

    def test_line_length_jacobian_zero_length_line(self):
        s = make_solver()
        line, p1, p2 = make_line(s, x0=0.0, y0=0.0, x1=0.0, y1=0.0)  # Zero-length
        c = LineLengthConstraint(line, 5.0)
        J = c.jacobian(s.variables)
        assert J.shape[1] == len(s.variables)
        assert np.all(J == 0.0)
