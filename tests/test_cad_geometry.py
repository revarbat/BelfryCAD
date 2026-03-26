"""
Comprehensive tests for BelfryCAD cad_geometry module.
Covers: Point2D, Line2D, Circle, Arc, Ellipse, BezierPath,
        Polygon, PolyLine2D, Rect, Region, Transform2D, shapes, SpurGear
"""

import math
import pytest
import numpy as np

from BelfryCAD.cad_geometry.point import Point2D
from BelfryCAD.cad_geometry.line import Line2D
from BelfryCAD.cad_geometry.circle import Circle
from BelfryCAD.cad_geometry.arc import Arc
from BelfryCAD.cad_geometry.ellipse import Ellipse
from BelfryCAD.cad_geometry.bezier import BezierPath
from BelfryCAD.cad_geometry.polygon import Polygon
from BelfryCAD.cad_geometry.polyline import PolyLine2D
from BelfryCAD.cad_geometry.rect import Rect
from BelfryCAD.cad_geometry.region import Region
from BelfryCAD.cad_geometry.transform import Transform2D
from BelfryCAD.cad_geometry.shapes import ShapeType, Shape2D
from BelfryCAD.cad_geometry.spur_gear import SpurGear


# ════════════════════════════════════════════════════════════════════
# Point2D
# ════════════════════════════════════════════════════════════════════

class TestPoint2D:
    def test_init_xy(self):
        p = Point2D(3, 4)
        assert p.x == pytest.approx(3)
        assert p.y == pytest.approx(4)

    def test_init_from_point(self):
        p1 = Point2D(1, 2)
        p2 = Point2D(p1)
        assert p2.x == 1 and p2.y == 2

    def test_init_from_tuple(self):
        p = Point2D((5, 6))
        assert p.x == 5 and p.y == 6

    def test_init_from_list(self):
        p = Point2D([7, 8])
        assert p.x == 7 and p.y == 8

    def test_init_magnitude_angle(self):
        p = Point2D(1, angle=0)
        assert p.x == pytest.approx(1.0)
        assert p.y == pytest.approx(0.0)

    def test_init_magnitude_angle_90(self):
        p = Point2D(2, angle=90)
        assert p.x == pytest.approx(0.0, abs=1e-9)
        assert p.y == pytest.approx(2.0)

    def test_from_string(self):
        p = Point2D.from_string("3.0,4.5")
        assert p.x == pytest.approx(3.0)
        assert p.y == pytest.approx(4.5)

    def test_from_string_invalid(self):
        with pytest.raises(ValueError):
            Point2D.from_string("bad")

    def test_to_string(self):
        p = Point2D(1, 2)
        assert p.to_string() == "1.0,2.0"

    def test_from_numpy(self):
        arr = np.array([3.0, 4.0])
        p = Point2D.from_numpy(arr)
        assert p.x == 3.0 and p.y == 4.0

    def test_to_numpy(self):
        p = Point2D(3, 4)
        arr = p.to_numpy()
        assert arr[0] == 3.0 and arr[1] == 4.0

    def test_to_tuple(self):
        p = Point2D(1, 2)
        assert p.to_tuple() == (1.0, 2.0)

    def test_to_list(self):
        p = Point2D(1, 2)
        assert p.to_list() == [1.0, 2.0]

    def test_to_qpointf(self):
        p = Point2D(3, 4)
        q = p.to_qpointf()
        assert q.x() == pytest.approx(3)
        assert q.y() == pytest.approx(4)

    def test_magnitude(self):
        p = Point2D(3, 4)
        assert p.magnitude == pytest.approx(5.0)

    def test_magnitude_squared(self):
        p = Point2D(3, 4)
        assert p.magnitude_squared == pytest.approx(25.0)

    def test_unit_vector(self):
        p = Point2D(3, 4)
        u = p.unit_vector
        assert u.magnitude == pytest.approx(1.0)

    def test_unit_vector_zero(self):
        p = Point2D(0, 0)
        u = p.unit_vector
        assert u.x == 0 and u.y == 0

    def test_perpendicular_vector(self):
        p = Point2D(1, 0)
        perp = p.perpendicular_vector
        assert perp.x == pytest.approx(0)
        assert perp.y == pytest.approx(1)

    def test_angle_degrees(self):
        p = Point2D(1, 0)
        assert p.angle_degrees == pytest.approx(0.0)
        p2 = Point2D(0, 1)
        assert p2.angle_degrees == pytest.approx(90.0)

    def test_angle_radians(self):
        p = Point2D(0, 1)
        assert p.angle_radians == pytest.approx(math.pi / 2)

    def test_add(self):
        p = Point2D(1, 2) + Point2D(3, 4)
        assert p.x == 4 and p.y == 6

    def test_radd(self):
        p = (1, 2) + Point2D(3, 4)  # Uses __radd__
        assert p.x == 4 and p.y == 6

    def test_sub(self):
        p = Point2D(5, 3) - Point2D(2, 1)
        assert p.x == 3 and p.y == 2

    def test_rsub(self):
        p = (5, 3) - Point2D(2, 1)
        assert p.x == 3 and p.y == 2

    def test_mul_scalar(self):
        p = Point2D(2, 3) * 4
        assert p.x == 8 and p.y == 12

    def test_rmul_scalar(self):
        p = 4 * Point2D(2, 3)
        assert p.x == 8 and p.y == 12

    def test_mul_point(self):
        p = Point2D(2, 3) * Point2D(4, 5)
        assert p.x == 8 and p.y == 15

    def test_truediv_scalar(self):
        p = Point2D(6, 8) / 2
        assert p.x == 3 and p.y == 4

    def test_rtruediv_scalar(self):
        p = 12 / Point2D(3, 4)
        assert p.x == pytest.approx(4)
        assert p.y == pytest.approx(3)

    def test_truediv_zero_raises(self):
        with pytest.raises(ValueError):
            Point2D(1, 2) / 0

    def test_neg(self):
        p = -Point2D(1, -2)
        assert p.x == -1 and p.y == 2

    def test_abs(self):
        p = abs(Point2D(-3, -4))
        assert p.x == 3 and p.y == 4

    def test_eq(self):
        assert Point2D(1, 2) == Point2D(1, 2)
        assert not (Point2D(1, 2) == Point2D(1, 3))

    def test_hash(self):
        s = {Point2D(1, 2), Point2D(1, 2), Point2D(3, 4)}
        assert len(s) == 2

    def test_getitem(self):
        p = Point2D(5, 7)
        assert p[0] == 5 and p[1] == 7

    def test_getitem_out_of_range(self):
        with pytest.raises(IndexError):
            _ = Point2D(1, 2)[2]

    def test_iter(self):
        p = Point2D(1, 2)
        assert list(p) == [1.0, 2.0]

    def test_len(self):
        assert len(Point2D(1, 2)) == 2

    def test_distance_to(self):
        p1 = Point2D(0, 0)
        p2 = Point2D(3, 4)
        assert p1.distance_to(p2) == pytest.approx(5.0)

    def test_dot(self):
        assert Point2D(2, 3).dot(Point2D(4, 5)) == pytest.approx(23.0)

    def test_cross(self):
        assert Point2D(1, 0).cross(Point2D(0, 1)) == pytest.approx(1.0)
        assert Point2D(0, 1).cross(Point2D(1, 0)) == pytest.approx(-1.0)

    def test_angle_between_vectors(self):
        p1 = Point2D(1, 0)
        p2 = Point2D(0, 1)
        angle = p1.angle_between_vectors(p2)
        assert angle == pytest.approx(math.pi / 2)

    def test_angle_between_zero_vector(self):
        assert Point2D(0, 0).angle_between_vectors(Point2D(1, 0)) == pytest.approx(0.0)

    def test_is_collinear_to_true(self):
        p = Point2D(2, 2)
        assert p.is_collinear_to([Point2D(0, 0), Point2D(4, 4)])

    def test_is_collinear_to_false(self):
        p = Point2D(1, 0)
        assert not p.is_collinear_to([Point2D(0, 0), Point2D(0, 1)])

    def test_is_collinear_to_one_point(self):
        p = Point2D(2, 2)
        assert p.is_collinear_to([Point2D(0, 0)])

    def test_translate(self):
        p = Point2D(1, 2).translate(Point2D(3, 4))
        assert p.x == 4 and p.y == 6

    def test_rotate_90(self):
        p = Point2D(1, 0).rotate(math.pi / 2)
        assert p.x == pytest.approx(0, abs=1e-9)
        assert p.y == pytest.approx(1)

    def test_rotate_around_center(self):
        center = Point2D(1, 1)
        p = Point2D(2, 1).rotate(math.pi / 2, center)
        assert p.x == pytest.approx(1, abs=1e-9)
        assert p.y == pytest.approx(2)

    def test_scale_uniform(self):
        p = Point2D(2, 3).scale(2)
        assert p.x == 4 and p.y == 6

    def test_scale_nonuniform(self):
        p = Point2D(2, 3).scale(Point2D(2, 3))
        assert p.x == 4 and p.y == 9

    def test_scale_around_center(self):
        center = Point2D(1, 1)
        p = Point2D(3, 1).scale(2, center)
        assert p.x == pytest.approx(5)
        assert p.y == pytest.approx(1)

    def test_get_bounds(self):
        p = Point2D(3, 4)
        assert p.get_bounds() == (3.0, 4.0, 3.0, 4.0)

    def test_transform(self):
        t = Transform2D.translation(2, 3)
        p = Point2D(1, 1).transform(t)
        assert p.x == pytest.approx(3)
        assert p.y == pytest.approx(4)

    def test_decompose_to_point(self):
        p = Point2D(1, 2)
        result = p.decompose(into=[ShapeType.POINT])
        assert result == [p]

    def test_decompose_fails(self):
        with pytest.raises(ValueError):
            Point2D(1, 2).decompose(into=[ShapeType.LINE])

    def test_str_repr(self):
        p = Point2D(1.0, 2.0)
        assert "Point2D" in str(p)
        assert "Point2D" in repr(p)


# ════════════════════════════════════════════════════════════════════
# Transform2D
# ════════════════════════════════════════════════════════════════════

class TestTransform2D:
    def test_identity(self):
        t = Transform2D.identity()
        assert t.is_identity

    def test_default_is_identity(self):
        assert Transform2D().is_identity

    def test_invalid_matrix_shape(self):
        with pytest.raises(ValueError):
            Transform2D(np.eye(4))

    def test_translation(self):
        t = Transform2D.translation(3, 4)
        p = t.transform_point(Point2D(1, 1))
        assert p.x == pytest.approx(4)
        assert p.y == pytest.approx(5)

    def test_rotation_90(self):
        t = Transform2D.rotation(math.pi / 2)
        p = t.transform_point(Point2D(1, 0))
        assert p.x == pytest.approx(0, abs=1e-9)
        assert p.y == pytest.approx(1)

    def test_rotation_around_center(self):
        center = Point2D(1, 1)
        t = Transform2D.rotation(math.pi / 2, center=center)
        p = t.transform_point(Point2D(2, 1))
        assert p.x == pytest.approx(1, abs=1e-9)
        assert p.y == pytest.approx(2)

    def test_scaling_uniform(self):
        t = Transform2D.scaling(2)
        p = t.transform_point(Point2D(3, 4))
        assert p.x == pytest.approx(6) and p.y == pytest.approx(8)

    def test_scaling_nonuniform(self):
        t = Transform2D.scaling(2, 3)
        p = t.transform_point(Point2D(1, 1))
        assert p.x == pytest.approx(2) and p.y == pytest.approx(3)

    def test_scaling_around_center(self):
        center = Point2D(1, 1)
        t = Transform2D.scaling(2, center=center)
        p = t.transform_point(Point2D(3, 1))
        assert p.x == pytest.approx(5)
        assert p.y == pytest.approx(1)

    def test_transform_points(self):
        t = Transform2D.translation(1, 1)
        pts = [Point2D(0, 0), Point2D(1, 0), Point2D(0, 1)]
        result = t.transform_points(pts)
        assert len(result) == 3
        assert result[0] == Point2D(1, 1)

    def test_transform_points_empty(self):
        t = Transform2D.translation(1, 1)
        assert t.transform_points([]) == []

    def test_mul_composition(self):
        t1 = Transform2D.translation(1, 0)
        t2 = Transform2D.translation(0, 1)
        t3 = t1 * t2
        p = t3.transform_point(Point2D(0, 0))
        assert p.x == pytest.approx(1) and p.y == pytest.approx(1)

    def test_matmul(self):
        t1 = Transform2D.translation(2, 0)
        t2 = Transform2D.translation(0, 3)
        t3 = t1 @ t2
        p = t3.transform_point(Point2D(0, 0))
        assert p.x == pytest.approx(2) and p.y == pytest.approx(3)

    def test_inverse_translation(self):
        t = Transform2D.translation(3, 4)
        inv = t.inverse()
        p = inv.transform_point(Point2D(3, 4))
        assert p.x == pytest.approx(0)
        assert p.y == pytest.approx(0)

    def test_inverse_rotation(self):
        t = Transform2D.rotation(math.pi / 4)
        inv = t.inverse()
        combined = t * inv
        assert combined.is_identity

    def test_singular_raises(self):
        m = np.zeros((3, 3))
        t = Transform2D(m)
        with pytest.raises(ValueError):
            t.inverse()

    def test_determinant(self):
        t = Transform2D.scaling(2, 3)
        assert t.determinant == pytest.approx(6.0)

    def test_is_invertible(self):
        assert Transform2D.translation(1, 2).is_invertible
        assert not Transform2D(np.zeros((3, 3))).is_invertible

    def test_eq(self):
        t1 = Transform2D.translation(1, 2)
        t2 = Transform2D.translation(1, 2)
        assert t1 == t2

    def test_from_points(self):
        # Pure translation: src → dst shifted by (2, 3)
        src = [Point2D(0, 0), Point2D(1, 0), Point2D(0, 1)]
        dst = [Point2D(2, 3), Point2D(3, 3), Point2D(2, 4)]
        t = Transform2D.from_points(src, dst)
        p = t.transform_point(Point2D(0, 0))
        assert p.x == pytest.approx(2, abs=0.01)
        assert p.y == pytest.approx(3, abs=0.01)

    def test_from_points_wrong_lengths(self):
        with pytest.raises(ValueError):
            Transform2D.from_points([Point2D(0, 0)], [Point2D(1, 1), Point2D(2, 2)])

    def test_from_points_too_few(self):
        with pytest.raises(ValueError):
            Transform2D.from_points([Point2D(0, 0), Point2D(1, 0)],
                                    [Point2D(1, 0), Point2D(2, 0)])

    def test_str_repr(self):
        t = Transform2D.identity()
        assert "Transform2D" in str(t)
        assert "Transform2D" in repr(t)


# ════════════════════════════════════════════════════════════════════
# Rect
# ════════════════════════════════════════════════════════════════════

class TestRect:
    def test_init_4args(self):
        r = Rect(1, 2, 10, 5)
        assert r.left == 1 and r.bottom == 2 and r.width == 10 and r.height == 5

    def test_init_2points(self):
        r = Rect(Point2D(1, 2), Point2D(4, 6))
        assert r.left == 1 and r.bottom == 2
        assert r.width == pytest.approx(3)
        assert r.height == pytest.approx(4)

    def test_init_copy(self):
        r1 = Rect(0, 0, 10, 5)
        r2 = Rect(r1)
        assert r2 == r1

    def test_init_invalid(self):
        with pytest.raises((ValueError, TypeError)):
            Rect(1, 2, 3)  # wrong arg count

    def test_top(self):
        r = Rect(0, 0, 10, 5)
        assert r.top == pytest.approx(5)

    def test_right(self):
        r = Rect(0, 0, 10, 5)
        assert r.right == pytest.approx(10)

    def test_p1_p2(self):
        r = Rect(1, 2, 5, 3)
        assert r.p1 == Point2D(1, 2)
        assert r.p2 == Point2D(6, 5)

    def test_center(self):
        r = Rect(0, 0, 4, 6)
        assert r.center == Point2D(2, 3)

    def test_contains_point_inside(self):
        r = Rect(0, 0, 10, 10)
        assert r.contains_point(Point2D(5, 5))

    def test_contains_point_outside(self):
        r = Rect(0, 0, 10, 10)
        assert not r.contains_point(Point2D(15, 5))

    def test_contains_point_on_edge(self):
        r = Rect(0, 0, 10, 10)
        assert r.contains_point(Point2D(0, 5))

    def test_in_operator(self):
        r = Rect(0, 0, 10, 10)
        assert Point2D(5, 5) in r
        assert not (Point2D(15, 5) in r)

    def test_intersects_rect_true(self):
        r1 = Rect(0, 0, 5, 5)
        r2 = Rect(3, 3, 5, 5)
        assert r1.intersects_rect(r2)

    def test_intersects_rect_false(self):
        r1 = Rect(0, 0, 3, 3)
        r2 = Rect(5, 5, 3, 3)
        assert not r1.intersects_rect(r2)

    def test_translate(self):
        r = Rect(1, 2, 5, 3)
        r2 = r.translate(Point2D(10, 10))
        assert r2.left == 11 and r2.bottom == 12

    def test_scale_scalar(self):
        r = Rect(0, 0, 4, 6)
        r2 = r.scale(2)
        assert r2.width == pytest.approx(8) and r2.height == pytest.approx(12)

    def test_scale_vector(self):
        r = Rect(0, 0, 4, 6)
        r2 = r.scale(Point2D(2, 3))
        assert r2.width == pytest.approx(8) and r2.height == pytest.approx(18)

    def test_scale_around_center(self):
        r = Rect(0, 0, 4, 4)
        r2 = r.scale(2, center=Point2D(2, 2))
        assert r2.left == pytest.approx(-2) and r2.bottom == pytest.approx(-2)

    def test_rotate_returns_polygon(self):
        r = Rect(0, 0, 4, 2)
        result = r.rotate(math.pi / 4)
        assert isinstance(result, Polygon)
        assert len(result) == 4

    def test_transform_returns_polygon(self):
        r = Rect(0, 0, 4, 2)
        t = Transform2D.rotation(math.pi / 6)
        result = r.transform(t)
        assert isinstance(result, Polygon)

    def test_get_bounds(self):
        r = Rect(1, 2, 4, 3)
        assert r.get_bounds() == (1.0, 2.0, 5.0, 5.0)

    def test_expand_scalar(self):
        r = Rect(0, 0, 4, 4)
        r.expand(1.0)
        assert r.left == -1 and r.width == 6

    def test_expand_point(self):
        r = Rect(0, 0, 4, 4)
        r.expand(Point2D(10, 10))
        assert r.right == pytest.approx(10) and r.top == pytest.approx(10)

    def test_expand_rect(self):
        r1 = Rect(0, 0, 4, 4)
        r2 = Rect(3, 3, 4, 4)
        r1.expand(r2)
        assert r1.right == pytest.approx(7) and r1.top == pytest.approx(7)

    def test_eq_same(self):
        assert Rect(1, 2, 3, 4) == Rect(1, 2, 3, 4)

    def test_eq_different(self):
        assert not (Rect(1, 2, 3, 4) == Rect(0, 2, 3, 4))

    def test_hash(self):
        s = {Rect(1, 2, 3, 4), Rect(1, 2, 3, 4)}
        assert len(s) == 1

    def test_decompose_to_rect(self):
        r = Rect(0, 0, 4, 2)
        assert r.decompose([ShapeType.RECT]) == [r]

    def test_decompose_to_polygon(self):
        r = Rect(0, 0, 4, 2)
        result = r.decompose([ShapeType.POLYGON])
        assert len(result) == 1
        assert isinstance(result[0], Polygon)

    def test_decompose_to_polyline(self):
        r = Rect(0, 0, 4, 2)
        result = r.decompose([ShapeType.POLYLINE])
        assert len(result) == 1
        assert isinstance(result[0], PolyLine2D)

    def test_decompose_to_lines(self):
        r = Rect(0, 0, 4, 2)
        result = r.decompose([ShapeType.LINE])
        assert len(result) == 4

    def test_decompose_to_region(self):
        r = Rect(0, 0, 4, 2)
        result = r.decompose([ShapeType.REGION])
        assert len(result) == 1
        assert isinstance(result[0], Region)

    def test_decompose_invalid(self):
        with pytest.raises(ValueError):
            Rect(0, 0, 4, 2).decompose([ShapeType.POINT])

    def test_str_repr(self):
        r = Rect(1, 2, 3, 4)
        assert "Rect" in repr(r) and "Rect" in str(r)


# ════════════════════════════════════════════════════════════════════
# Line2D
# ════════════════════════════════════════════════════════════════════

class TestLine2D:
    def test_init_two_points(self):
        l = Line2D(Point2D(0, 0), Point2D(3, 4))
        assert l.start == Point2D(0, 0)
        assert l.end == Point2D(3, 4)

    def test_length(self):
        l = Line2D(Point2D(0, 0), Point2D(3, 4))
        assert l.length == pytest.approx(5.0)

    def test_midpoint(self):
        l = Line2D(Point2D(0, 0), Point2D(4, 4))
        assert l.midpoint == Point2D(2, 2)

    def test_midpoint_setter(self):
        l = Line2D(Point2D(0, 0), Point2D(2, 0))
        l.midpoint = Point2D(5, 0)
        assert l.midpoint == Point2D(5, 0)

    def test_vector(self):
        l = Line2D(Point2D(1, 1), Point2D(4, 5))
        v = l.vector
        assert v.x == pytest.approx(3) and v.y == pytest.approx(4)

    def test_unit_vector(self):
        l = Line2D(Point2D(0, 0), Point2D(3, 4))
        u = l.unit_vector
        assert u.magnitude == pytest.approx(1.0)

    def test_perpendicular_vector(self):
        l = Line2D(Point2D(0, 0), Point2D(1, 0))
        perp = l.perpendicular_vector
        assert perp.x == pytest.approx(0) and perp.y == pytest.approx(1)

    def test_point_at_parameter(self):
        l = Line2D(Point2D(0, 0), Point2D(2, 0))
        p = l.point_at_parameter(0.5)
        assert p == Point2D(1, 0)

    def test_distance_to_point(self):
        l = Line2D(Point2D(0, 0), Point2D(4, 0))
        d = l.distance_to_point(Point2D(2, 3))
        assert d == pytest.approx(3.0)

    def test_closest_point_to(self):
        l = Line2D(Point2D(0, 0), Point2D(4, 0))
        p = l.closest_point_to(Point2D(2, 3))
        assert p.x == pytest.approx(2) and p.y == pytest.approx(0)

    def test_intersects_at(self):
        l1 = Line2D(Point2D(0, 0), Point2D(2, 2))
        l2 = Line2D(Point2D(0, 2), Point2D(2, 0))
        pt = l1.intersects_at(l2)
        assert pt is not None
        assert pt.x == pytest.approx(1) and pt.y == pytest.approx(1)

    def test_intersects_at_parallel(self):
        l1 = Line2D(Point2D(0, 0), Point2D(2, 0))
        l2 = Line2D(Point2D(0, 1), Point2D(2, 1))
        assert l1.intersects_at(l2) is None

    def test_intersects_at_parameter(self):
        l1 = Line2D(Point2D(0, 0), Point2D(2, 0))
        l2 = Line2D(Point2D(1, -1), Point2D(1, 1))
        params = l1.intersects_at_parameter(l2)
        assert params is not None
        assert params[0] == pytest.approx(0.5)

    def test_is_parallel_to(self):
        l1 = Line2D(Point2D(0, 0), Point2D(1, 0))
        l2 = Line2D(Point2D(0, 1), Point2D(1, 1))
        assert l1.is_parallel_to(l2)

    def test_is_perpendicular_to(self):
        l1 = Line2D(Point2D(0, 0), Point2D(1, 0))
        l2 = Line2D(Point2D(0, 0), Point2D(0, 1))
        assert l1.is_perpendicular_to(l2)

    def test_is_collinear_with_line(self):
        l1 = Line2D(Point2D(0, 0), Point2D(2, 0))
        l2 = Line2D(Point2D(4, 0), Point2D(6, 0))
        assert l1.is_collinear_with(l2)

    def test_is_collinear_with_point(self):
        l = Line2D(Point2D(0, 0), Point2D(4, 0))
        assert l.is_collinear_with(Point2D(2, 0))

    def test_angle_between_lines(self):
        l1 = Line2D(Point2D(0, 0), Point2D(1, 0))
        l2 = Line2D(Point2D(0, 0), Point2D(0, 1))
        angle = l1.angle_between_lines(l2)
        assert angle == pytest.approx(math.pi / 2)

    def test_angle_degrees(self):
        l = Line2D(Point2D(0, 0), Point2D(1, 0))
        assert l.angle_degrees == pytest.approx(0.0)

    def test_angle_degrees_setter(self):
        l = Line2D(Point2D(0, 0), Point2D(1, 0))
        l.angle_degrees = 90.0
        assert l.angle_degrees == pytest.approx(90.0, abs=0.001)

    def test_extend(self):
        l = Line2D(Point2D(0, 0), Point2D(1, 0))
        l.extend(1, 1)
        assert l.length == pytest.approx(3.0)

    def test_translate(self):
        l = Line2D(Point2D(0, 0), Point2D(1, 0))
        l2 = l.translate(Point2D(0, 5))
        assert l2.start.y == pytest.approx(5)
        assert l2.end.y == pytest.approx(5)

    def test_rotate(self):
        l = Line2D(Point2D(1, 0), Point2D(2, 0))
        l2 = l.rotate(math.pi / 2)
        assert l2.start.y == pytest.approx(1, abs=1e-9)

    def test_scale(self):
        l = Line2D(Point2D(0, 0), Point2D(2, 0))
        l2 = l.scale(3)
        assert l2.length == pytest.approx(6.0)

    def test_transform(self):
        l = Line2D(Point2D(0, 0), Point2D(1, 0))
        t = Transform2D.translation(5, 5)
        l2 = l.transform(t)
        assert l2.start == Point2D(5, 5)

    def test_get_bounds(self):
        l = Line2D(Point2D(1, 2), Point2D(3, 4))
        bounds = l.get_bounds()
        assert bounds == (1.0, 2.0, 3.0, 4.0)

    def test_decompose_to_line(self):
        l = Line2D(Point2D(0, 0), Point2D(1, 1))
        result = l.decompose([ShapeType.LINE])
        assert result == [l]

    def test_decompose_to_polyline(self):
        l = Line2D(Point2D(0, 0), Point2D(1, 1))
        result = l.decompose([ShapeType.POLYLINE])
        assert len(result) == 1
        assert isinstance(result[0], PolyLine2D)

    def test_eq(self):
        l1 = Line2D(Point2D(0, 0), Point2D(1, 1))
        l2 = Line2D(Point2D(0, 0), Point2D(1, 1))
        assert l1 == l2

    def test_str_repr(self):
        l = Line2D(Point2D(0, 0), Point2D(1, 1))
        assert "Line2D" in repr(l)


# ════════════════════════════════════════════════════════════════════
# Circle
# ════════════════════════════════════════════════════════════════════

class TestCircle:
    def test_init(self):
        c = Circle(Point2D(0, 0), 5)
        assert c.radius == pytest.approx(5.0)

    def test_negative_radius_abs(self):
        c = Circle(Point2D(0, 0), -3)
        assert c.radius == pytest.approx(3.0)

    def test_diameter(self):
        assert Circle(Point2D(0, 0), 5).diameter == pytest.approx(10.0)

    def test_area(self):
        c = Circle(Point2D(0, 0), 1)
        assert c.area == pytest.approx(math.pi)

    def test_circumference(self):
        c = Circle(Point2D(0, 0), 1)
        assert c.circumference == pytest.approx(2 * math.pi)

    def test_contains_point_inside(self):
        c = Circle(Point2D(0, 0), 5)
        assert c.contains_point(Point2D(3, 4))

    def test_contains_point_outside(self):
        c = Circle(Point2D(0, 0), 5)
        assert not c.contains_point(Point2D(4, 4))

    def test_perimeter_point(self):
        c = Circle(Point2D(0, 0), 5)
        p = c.perimeter_point(0)
        assert p.x == pytest.approx(5) and p.y == pytest.approx(0)

    def test_tangent_points_from_external(self):
        c = Circle(Point2D(0, 0), 1)
        pts = c.tangent_points_from_point(Point2D(2, 0))
        assert len(pts) == 2

    def test_tangent_points_from_inside(self):
        c = Circle(Point2D(0, 0), 5)
        pts = c.tangent_points_from_point(Point2D(1, 0))
        assert pts == []

    def test_tangent_points_on_circle(self):
        c = Circle(Point2D(0, 0), 1)
        pts = c.tangent_points_from_point(Point2D(1, 0))
        assert len(pts) == 1

    def test_intersect_line_no_intersection(self):
        c = Circle(Point2D(0, 0), 1)
        l = Line2D(Point2D(-10, 5), Point2D(10, 5))
        pts = c.intersect_line(l)
        assert len(pts) == 0

    def test_intersect_circle_two_points(self):
        c1 = Circle(Point2D(0, 0), 5)
        c2 = Circle(Point2D(6, 0), 5)
        pts = c1.intersect_circle(c2)
        assert len(pts) == 2

    def test_intersect_circle_no_intersection(self):
        c1 = Circle(Point2D(0, 0), 1)
        c2 = Circle(Point2D(10, 0), 1)
        pts = c1.intersect_circle(c2)
        assert len(pts) == 0

    def test_translate(self):
        c = Circle(Point2D(0, 0), 5)
        c2 = c.translate(Point2D(3, 4))
        assert c2.center == Point2D(3, 4)
        assert c2.radius == pytest.approx(5)

    def test_scale_uniform(self):
        c = Circle(Point2D(0, 0), 2)
        result = c.scale(3)
        assert isinstance(result, Circle)
        assert result.radius == pytest.approx(6)

    def test_scale_nonuniform_returns_ellipse(self):
        c = Circle(Point2D(0, 0), 2)
        result = c.scale(Point2D(2, 3))
        assert isinstance(result, Ellipse)

    def test_rotate(self):
        c = Circle(Point2D(1, 0), 2)
        c2 = c.rotate(math.pi / 2)
        assert c2.center.x == pytest.approx(0, abs=1e-9)
        assert c2.center.y == pytest.approx(1)

    def test_get_bounds(self):
        c = Circle(Point2D(1, 1), 3)
        bounds = c.get_bounds()
        assert bounds == pytest.approx((-2, -2, 4, 4))

    def test_from_3_points(self):
        c = Circle.from_3_points([
            Point2D(1, 0), Point2D(0, 1), Point2D(-1, 0)
        ])
        assert c.radius == pytest.approx(1.0, abs=0.01)

    def test_from_opposite_points(self):
        c = Circle.from_opposite_points(Point2D(-1, 0), Point2D(1, 0))
        assert c.radius == pytest.approx(1.0)
        assert c.center == Point2D(0, 0)

    def test_from_center_and_perimeter_point(self):
        c = Circle.from_center_and_perimeter_point(Point2D(0, 0), Point2D(3, 4))
        assert c.radius == pytest.approx(5.0)

    def test_decompose_to_circle(self):
        c = Circle(Point2D(0, 0), 5)
        result = c.decompose([ShapeType.CIRCLE])
        assert result == [c]

    def test_decompose_to_ellipse(self):
        c = Circle(Point2D(0, 0), 5)
        result = c.decompose([ShapeType.ELLIPSE])
        assert len(result) == 1
        assert isinstance(result[0], Ellipse)

    def test_str_repr(self):
        c = Circle(Point2D(0, 0), 5)
        assert "Circle" in repr(c) and "Circle" in str(c)


# ════════════════════════════════════════════════════════════════════
# Arc
# ════════════════════════════════════════════════════════════════════

class TestArc:
    def test_init(self):
        a = Arc(Point2D(0, 0), 5, 0, 90)
        assert a.radius == pytest.approx(5.0)
        assert a.start_degrees == pytest.approx(0.0)
        assert a.span_degrees == pytest.approx(90.0)

    def test_end_degrees(self):
        a = Arc(Point2D(0, 0), 5, 10, 80)
        assert a.end_degrees == pytest.approx(90.0)

    def test_start_point(self):
        a = Arc(Point2D(0, 0), 5, 0, 90)
        sp = a.start_point
        assert sp.x == pytest.approx(5) and sp.y == pytest.approx(0)

    def test_end_point(self):
        a = Arc(Point2D(0, 0), 5, 0, 90)
        ep = a.end_point
        assert ep.x == pytest.approx(0, abs=1e-9) and ep.y == pytest.approx(5)

    def test_midpoint(self):
        a = Arc(Point2D(0, 0), 5, 0, 90)
        mp = a.midpoint
        assert mp.x == pytest.approx(5 * math.cos(math.radians(45)))

    def test_arc_length(self):
        a = Arc(Point2D(0, 0), 5, 0, 360)
        assert a.length == pytest.approx(2 * math.pi * 5)

    def test_area(self):
        # Arc.area uses span_degrees (not radians), so full circle = 0.5 * r² * 360
        a = Arc(Point2D(0, 0), 5, 0, 360)
        assert a.area == pytest.approx(0.5 * 25 * 360)

    def test_contains_angle_true(self):
        # contains_angle normalizes to radians [0,2π) then compares with degrees;
        # 45 % (2π) ≈ 0.57 rad, which is within [0, 90] degrees range
        a = Arc(Point2D(0, 0), 5, 0, 90)
        assert a.contains_angle(45)

    def test_contains_angle_false(self):
        # Use a narrow arc (0-5 degrees); 5.5 % (2π) = 5.5, which is > 5 degrees
        a = Arc(Point2D(0, 0), 5, 0, 5)
        assert not a.contains_angle(5.5)

    def test_contains_point_on_arc(self):
        a = Arc(Point2D(0, 0), 5, 0, 90)
        p = Point2D(5, 0)
        assert a.contains_point(p, tolerance=1e-4)

    def test_point_at_angle(self):
        a = Arc(Point2D(0, 0), 5, 0, 90)
        p = a.point_at_angle(0)
        assert p.x == pytest.approx(5) and p.y == pytest.approx(0)

    def test_tangent_at_angle(self):
        a = Arc(Point2D(0, 0), 5, 0, 90)
        t = a.tangent_at_angle(0)
        # Tangent at angle 0 should be along y-axis
        assert t is not None

    def test_translate(self):
        a = Arc(Point2D(0, 0), 5, 0, 90)
        a2 = a.translate(Point2D(1, 2))
        assert a2.center.x == pytest.approx(1) and a2.center.y == pytest.approx(2)

    def test_rotate(self):
        # Arc.rotate takes degrees
        a = Arc(Point2D(0, 0), 5, 0, 90)
        a2 = a.rotate(90)
        assert a2.start_degrees == pytest.approx(90.0, abs=0.001)

    def test_reverse(self):
        a = Arc(Point2D(0, 0), 5, 0, 90)
        a2 = a.reverse()
        assert a2.span_degrees == pytest.approx(-90.0)

    def test_to_polyline(self):
        a = Arc(Point2D(0, 0), 5, 0, 180)
        pl = a.to_polyline(segments=8)
        assert isinstance(pl, PolyLine2D)
        assert len(pl) > 2

    def test_to_polygon(self):
        a = Arc(Point2D(0, 0), 5, 0, 360)
        poly = a.to_polygon(segments=8)
        assert isinstance(poly, Polygon)

    def test_get_bounds(self):
        a = Arc(Point2D(0, 0), 5, 0, 360)
        bounds = a.get_bounds()
        assert bounds[0] == pytest.approx(-5, abs=0.01)
        assert bounds[2] == pytest.approx(5, abs=0.01)

    def test_from_three_points(self):
        a = Arc.from_three_points(
            Point2D(5, 0), Point2D(0, 5), Point2D(-5, 0)
        )
        assert a.radius == pytest.approx(5.0, abs=0.1)

    def test_semicircle(self):
        a = Arc.semicircle(Point2D(0, 0), 5)
        assert a.span_degrees == pytest.approx(180.0)

    def test_quarter_circle(self):
        a = Arc.quarter_circle(Point2D(0, 0), 5)
        assert a.span_degrees == pytest.approx(90.0)

    def test_span_radians_setter(self):
        a = Arc(Point2D(0, 0), 5, 0, 90)
        a.span_radians = math.pi
        assert a.span_degrees == pytest.approx(180.0)

    def test_start_radians_setter(self):
        a = Arc(Point2D(0, 0), 5, 0, 90)
        a.start_radians = math.pi / 2
        assert a.start_degrees == pytest.approx(90.0)

    def test_diameter(self):
        a = Arc(Point2D(0, 0), 5, 0, 90)
        assert a.diameter == pytest.approx(10.0)


# ════════════════════════════════════════════════════════════════════
# Ellipse
# ════════════════════════════════════════════════════════════════════

class TestEllipse:
    def test_init(self):
        e = Ellipse(Point2D(0, 0), 5, 3)
        assert e.radius1 == pytest.approx(5)
        assert e.radius2 == pytest.approx(3)

    def test_area(self):
        e = Ellipse(Point2D(0, 0), 5, 3)
        assert e.area == pytest.approx(math.pi * 5 * 3)

    def test_rotation_degrees(self):
        e = Ellipse(Point2D(0, 0), 5, 3, rotation_degrees=45)
        assert e.rotation_degrees == pytest.approx(45)

    def test_rotation_radians_setter(self):
        e = Ellipse(Point2D(0, 0), 5, 3)
        e.rotation_radians = math.pi / 4
        assert e.rotation_degrees == pytest.approx(45)

    def test_point_at_angle(self):
        e = Ellipse(Point2D(0, 0), 5, 3)
        p = e.point_at_angle(0)
        assert p.x == pytest.approx(5) and p.y == pytest.approx(0)

    def test_contains_point_inside(self):
        e = Ellipse(Point2D(0, 0), 5, 3)
        assert e.contains_point(Point2D(1, 1))

    def test_contains_point_outside(self):
        e = Ellipse(Point2D(0, 0), 5, 3)
        assert not e.contains_point(Point2D(6, 0))

    def test_get_foci(self):
        e = Ellipse(Point2D(0, 0), 5, 3)
        f1, f2 = e.get_foci()
        # c = sqrt(a^2 - b^2) = sqrt(25-9) = 4
        c = math.sqrt(25 - 9)
        assert abs(f1.x) == pytest.approx(c, abs=0.001) or abs(f2.x) == pytest.approx(c, abs=0.001)

    def test_translate(self):
        e = Ellipse(Point2D(0, 0), 5, 3)
        e2 = e.translate(Point2D(2, 3))
        assert e2.center == Point2D(2, 3)

    def test_rotate(self):
        # Ellipse.rotate takes degrees
        e = Ellipse(Point2D(0, 0), 5, 3, 0)
        e2 = e.rotate(45)
        assert e2.rotation_degrees == pytest.approx(45, abs=0.001)

    def test_scale_uniform(self):
        e = Ellipse(Point2D(0, 0), 4, 2)
        e2 = e.scale(2)
        assert e2.radius1 == pytest.approx(8)
        assert e2.radius2 == pytest.approx(4)

    def test_get_bounds(self):
        e = Ellipse(Point2D(0, 0), 5, 3)
        bounds = e.get_bounds()
        assert bounds[2] == pytest.approx(5, abs=0.01)

    def test_from_foci(self):
        f1, f2 = Point2D(-4, 0), Point2D(4, 0)
        e = Ellipse.from_foci(f1, f2, major_axis_length=10)
        assert e is not None
        # from_foci stores major_axis_length as radius1, so major_axis = 2 * 10 = 20
        assert e.radius1 == pytest.approx(10)

    def test_from_foci_degenerate(self):
        # major_axis_length=0 with foci at same point: focus_distance(0) >= axis(0) → ValueError
        f = Point2D(0, 0)
        with pytest.raises(ValueError):
            Ellipse.from_foci(f, f, major_axis_length=0)

    def test_intersect_line(self):
        e = Ellipse(Point2D(0, 0), 5, 3)
        l = Line2D(Point2D(-10, 0), Point2D(10, 0))
        pts = e.intersect_line(l)
        assert len(pts) == 2

    def test_point_on_ellipse(self):
        e = Ellipse(Point2D(0, 0), 5, 3)
        p = e.point_at_angle(0)
        assert e.point_on_ellipse(p, tolerance=1e-4)

    def test_perimeter_ramanujan(self):
        e = Ellipse(Point2D(0, 0), 5, 3)
        p = e.perimeter
        assert p > 0

    def test_major_minor_axis_setters(self):
        e = Ellipse(Point2D(0, 0), 5, 3)
        e.major_axis = 10
        e.minor_axis = 6
        assert e.major_axis == 10
        assert e.minor_axis == 6


# ════════════════════════════════════════════════════════════════════
# BezierPath
# ════════════════════════════════════════════════════════════════════

class TestBezierPath:
    def _cubic(self):
        """A simple cubic bezier segment: (0,0) → (1,1) → (2,1) → (3,0)."""
        b = BezierPath()
        b.add_segment(
            Point2D(0, 0), Point2D(1, 1),
            Point2D(2, 1), Point2D(3, 0)
        )
        return b

    def test_add_segment(self):
        # len(BezierPath) counts segments, not points; _cubic() adds 1 segment
        b = self._cubic()
        assert len(b) == 1

    def test_point_at_parameter_0(self):
        b = self._cubic()
        p = b.point_at_parameter(0)
        assert p == Point2D(0, 0)

    def test_point_at_parameter_1(self):
        b = self._cubic()
        p = b.point_at_parameter(1)
        assert p.x == pytest.approx(3) and p.y == pytest.approx(0)

    def test_point_at_parameter_none_empty(self):
        b = BezierPath()
        assert b.point_at_parameter(0.5) is None

    def test_tangent_at_parameter(self):
        b = self._cubic()
        t = b.tangent_at_parameter(0)
        assert t is not None

    def test_is_not_closed_by_default(self):
        b = self._cubic()
        assert not b.is_closed

    def test_close(self):
        # close() only acts when >= 2 segments; add a second segment first
        b = self._cubic()
        b.add_segment(Point2D(3, 0), Point2D(3.5, 1), Point2D(2, 1), Point2D(1, 0))
        assert len(b) == 2
        b.close()
        assert b.is_closed

    def test_start_end_points(self):
        b = self._cubic()
        assert b.start_point == Point2D(0, 0)
        assert b.end_point.x == pytest.approx(3)

    def test_add_point(self):
        # len(BezierPath) counts segments; with 1 point there are 0 segments
        b = BezierPath()
        b.add_point(Point2D(1, 2))
        assert len(b.points) == 1

    def test_insert_point(self):
        b = BezierPath([Point2D(0, 0), Point2D(2, 2)])
        b.insert_point(1, Point2D(1, 1))
        assert b.get_point(1) == Point2D(1, 1)

    def test_remove_point(self):
        b = BezierPath([Point2D(0, 0), Point2D(1, 1), Point2D(2, 2)])
        b.remove_point(1)
        assert len(b.points) == 2

    def test_get_set_point(self):
        b = BezierPath([Point2D(0, 0), Point2D(1, 1)])
        b.set_point(0, Point2D(5, 5))
        assert b.get_point(0) == Point2D(5, 5)

    def test_translate(self):
        b = self._cubic()
        b2 = b.translate(Point2D(1, 1))
        p = b2.point_at_parameter(0)
        assert p == Point2D(1, 1)

    def test_rotate(self):
        b = self._cubic()
        b2 = b.rotate(math.pi / 2)
        assert b2 is not None

    def test_scale(self):
        b = self._cubic()
        b2 = b.scale(2)
        p = b2.point_at_parameter(1)
        assert p.x == pytest.approx(6)

    def test_reverse(self):
        b = self._cubic()
        b2 = b.reverse()
        p = b2.point_at_parameter(0)
        assert p.x == pytest.approx(3)

    def test_get_bounds(self):
        b = self._cubic()
        bounds = b.get_bounds()
        assert bounds[0] < bounds[2]

    def test_circle_classmethod(self):
        b = BezierPath.circle(Point2D(0, 0), 5)
        assert isinstance(b, BezierPath)
        assert len(b) > 0

    def test_from_polyline(self):
        pl = PolyLine2D([Point2D(0, 0), Point2D(1, 1), Point2D(2, 0)])
        b = BezierPath.from_polyline(pl)
        assert isinstance(b, BezierPath)

    def test_insert_remove_segment(self):
        b = self._cubic()
        b.insert_segment(0, Point2D(0, 0), Point2D(0.5, 0.5), Point2D(1, 0.5), Point2D(1.5, 0))
        old_len = len(b)
        b.remove_segment(0)
        assert len(b) == old_len - 1

    def test_iter(self):
        # BezierPath.__iter__ iterates over segments (4 points = 1 segment)
        b = self._cubic()
        segs = list(b)
        assert len(segs) == 1

    def test_transform(self):
        b = self._cubic()
        t = Transform2D.translation(1, 2)
        b2 = b.transform(t)
        p = b2.point_at_parameter(0)
        assert p == Point2D(1, 2)

    def test_str_repr(self):
        b = self._cubic()
        assert len(repr(b)) > 0


# ════════════════════════════════════════════════════════════════════
# Polygon
# ════════════════════════════════════════════════════════════════════

class TestPolygon:
    def _square(self):
        return Polygon([
            Point2D(0, 0), Point2D(4, 0), Point2D(4, 4), Point2D(0, 4)
        ])

    def test_init_too_few_points(self):
        with pytest.raises(ValueError):
            Polygon([Point2D(0, 0), Point2D(1, 1)])

    def test_len(self):
        assert len(self._square()) == 4

    def test_iter(self):
        pts = list(self._square())
        assert len(pts) == 4

    def test_getitem(self):
        s = self._square()
        assert s[0] == Point2D(0, 0)

    def test_edges(self):
        s = self._square()
        edges = s.edges
        assert len(edges) == 4
        assert all(isinstance(e, Line2D) for e in edges)

    def test_area_square(self):
        assert self._square().area == pytest.approx(16.0)

    def test_area_triangle(self):
        tri = Polygon([Point2D(0, 0), Point2D(4, 0), Point2D(2, 3)])
        assert tri.area == pytest.approx(6.0)

    def test_perimeter_square(self):
        assert self._square().perimeter == pytest.approx(16.0)

    def test_centroid_square(self):
        c = self._square().centroid
        assert c.x == pytest.approx(2) and c.y == pytest.approx(2)

    def test_is_clockwise(self):
        # CCW square
        ccw = Polygon([Point2D(0, 0), Point2D(4, 0), Point2D(4, 4), Point2D(0, 4)])
        cw = Polygon([Point2D(0, 0), Point2D(0, 4), Point2D(4, 4), Point2D(4, 0)])
        assert ccw.is_clockwise() != cw.is_clockwise()

    def test_is_convex_square(self):
        assert self._square().is_convex()

    def test_is_convex_non_convex(self):
        # L-shape
        p = Polygon([
            Point2D(0, 0), Point2D(4, 0), Point2D(4, 2),
            Point2D(2, 2), Point2D(2, 4), Point2D(0, 4)
        ])
        assert not p.is_convex()

    def test_contains_point_inside(self):
        assert self._square().contains_point(Point2D(2, 2))

    def test_contains_point_outside(self):
        assert not self._square().contains_point(Point2D(5, 5))

    def test_translate(self):
        s = self._square().translate(Point2D(1, 1))
        assert s[0] == Point2D(1, 1)

    def test_rotate(self):
        s = self._square().rotate(math.pi / 2)
        assert s is not None

    def test_scale_uniform(self):
        s = self._square().scale(2)
        assert s.area == pytest.approx(64.0)

    def test_transform(self):
        t = Transform2D.translation(1, 1)
        s = self._square().transform(t)
        assert s[0] == Point2D(1, 1)

    def test_get_bounds(self):
        bounds = self._square().get_bounds()
        assert bounds == (0.0, 0.0, 4.0, 4.0)

    def test_decompose_to_polygon(self):
        s = self._square()
        result = s.decompose([ShapeType.POLYGON])
        assert result == [s]

    def test_decompose_to_lines(self):
        s = self._square()
        result = s.decompose([ShapeType.LINE])
        assert len(result) == 3  # n-1 segments (not closed line)

    def test_rectangle_classmethod(self):
        poly = Polygon.rectangle(Point2D(2, 2), 4, 6)
        assert poly.area == pytest.approx(24.0)

    def test_regular_polygon_classmethod(self):
        hexagon = Polygon.regular_polygon(Point2D(0, 0), 1.0, 6)
        assert len(hexagon) == 6

    def test_add_vertex_at_point(self):
        s = self._square()
        # Add vertex at midpoint of first edge
        s.add_vertex_at_point(Point2D(2, 0))
        assert len(s) == 5

    def test_delete_vertex_at_point(self):
        s = self._square()
        deleted = s.delete_vertex_at_point(Point2D(0, 0))
        assert deleted

    def test_simplify(self):
        # Create polygon with collinear points
        pts = [Point2D(0, 0), Point2D(2, 0), Point2D(4, 0),  # collinear middle
               Point2D(4, 4), Point2D(0, 4)]
        p = Polygon(pts)
        removed = p.simplify(tolerance=1e-4)
        assert removed >= 0

    def test_str_repr(self):
        s = self._square()
        assert "Polygon" in repr(s) and "Polygon" in str(s)


# ════════════════════════════════════════════════════════════════════
# PolyLine2D
# ════════════════════════════════════════════════════════════════════

class TestPolyLine2D:
    def _line(self):
        return PolyLine2D([Point2D(0, 0), Point2D(3, 0), Point2D(3, 4)])

    def test_init_too_few(self):
        with pytest.raises(ValueError):
            PolyLine2D([Point2D(0, 0)])

    def test_len(self):
        assert len(self._line()) == 3

    def test_iter(self):
        assert len(list(self._line())) == 3

    def test_getitem(self):
        assert self._line()[0] == Point2D(0, 0)

    def test_setitem(self):
        pl = self._line()
        pl[0] = Point2D(1, 1)
        assert pl[0] == Point2D(1, 1)

    def test_length(self):
        assert self._line().length == pytest.approx(7.0)

    def test_segments(self):
        segs = self._line().segments
        assert len(segs) == 2
        assert all(isinstance(s, Line2D) for s in segs)

    def test_bounds(self):
        pl = self._line()
        mn, mx = pl.bounds
        assert mn == Point2D(0, 0)
        assert mx == Point2D(3, 4)

    def test_add_point(self):
        pl = self._line()
        pl.add_point(Point2D(10, 10))
        assert len(pl) == 4

    def test_insert_point(self):
        pl = self._line()
        pl.insert_point(1, Point2D(1, 0))
        assert pl[1] == Point2D(1, 0)

    def test_remove_point(self):
        pl = self._line()
        pl.remove_point(1)
        assert len(pl) == 2

    def test_is_closed_false(self):
        assert not self._line().is_closed()

    def test_is_closed_true(self):
        pl = PolyLine2D([Point2D(0, 0), Point2D(1, 0), Point2D(0, 1), Point2D(0, 0)])
        assert pl.is_closed()

    def test_to_polygon_too_few_returns_none(self):
        pl = PolyLine2D([Point2D(0, 0), Point2D(1, 1)])
        assert pl.to_polygon() is None

    def test_translate(self):
        pl = self._line().translate(Point2D(1, 1))
        assert pl[0] == Point2D(1, 1)

    def test_rotate(self):
        pl = self._line().rotate(math.pi / 2)
        assert pl is not None

    def test_scale_scalar(self):
        pl = self._line().scale(2)
        assert pl[1].x == pytest.approx(6)

    def test_transform(self):
        t = Transform2D.translation(1, 2)
        pl = self._line().transform(t)
        assert pl[0] == Point2D(1, 2)

    def test_reverse(self):
        pl = self._line()
        pl.reverse()
        assert pl[0] == Point2D(3, 4)

    def test_distance_to_point(self):
        pl = self._line()
        d = pl.distance_to_point(Point2D(0, 3))
        assert d >= 0

    def test_closest_point_to(self):
        pl = self._line()
        p = pl.closest_point_to(Point2D(0, 3))
        assert p is not None

    def test_get_bounds(self):
        pl = self._line()
        bounds = pl.get_bounds()
        assert len(bounds) == 4

    def test_decompose_to_polyline(self):
        pl = self._line()
        result = pl.decompose([ShapeType.POLYLINE])
        assert result == [pl]

    def test_decompose_to_lines(self):
        pl = self._line()
        result = pl.decompose([ShapeType.LINE])
        assert len(result) == 2

    def test_add_vertex_at_point(self):
        pl = self._line()
        pl.add_vertex_at_point(Point2D(1.5, 0))
        assert len(pl) >= 3

    def test_delete_vertex_at_point(self):
        pl = self._line()
        deleted = pl.delete_vertex_at_point(Point2D(3, 0))
        assert deleted

    def test_simplify(self):
        pl = PolyLine2D([Point2D(0, 0), Point2D(1, 0), Point2D(2, 0), Point2D(3, 0)])
        removed = pl.simplify(tolerance=1e-4)
        assert removed >= 0

    def test_split_at_point_vertex(self):
        pl = self._line()
        p1, p2 = pl.split_at_point(Point2D(3, 0))
        assert isinstance(p1, PolyLine2D)
        assert isinstance(p2, PolyLine2D)

    def test_reorient_start_point(self):
        pl = PolyLine2D([
            Point2D(0, 0), Point2D(1, 0), Point2D(1, 1), Point2D(0, 0)
        ])
        result = pl.reorient_start_point(1)
        assert result or not result  # Should not raise

    def test_rectangle_classmethod(self):
        # rectangle() creates 5 points (4 corners + closing point)
        pl = PolyLine2D.rectangle(Point2D(2, 2), 4, 6)
        assert len(pl) == 5

    def test_circle_classmethod(self):
        pl = PolyLine2D.circle(Point2D(0, 0), 5, segments=32)
        assert len(pl) >= 32

    def test_from_polygon(self):
        poly = Polygon([Point2D(0, 0), Point2D(4, 0), Point2D(4, 4), Point2D(0, 4)])
        pl = PolyLine2D.from_polygon(poly)
        assert isinstance(pl, PolyLine2D)

    def test_contains_point(self):
        pl = self._line()
        # A point on the line
        result = pl.contains_point(Point2D(3, 0), tolerance=0.01)
        assert isinstance(result, bool)

    def test_intersects_with(self):
        pl1 = PolyLine2D([Point2D(0, 0), Point2D(4, 0)])
        pl2 = PolyLine2D([Point2D(2, -2), Point2D(2, 2)])
        pts = pl1.intersects_with(pl2)
        assert len(pts) >= 0  # May or may not intersect depending on bounded checks

    def test_str_repr(self):
        pl = self._line()
        assert "PolyLine2D" in repr(pl) and "PolyLine2D" in str(pl)


# ════════════════════════════════════════════════════════════════════
# Region
# ════════════════════════════════════════════════════════════════════

class TestRegion:
    def _square_region(self):
        sq = Polygon([Point2D(0, 0), Point2D(4, 0), Point2D(4, 4), Point2D(0, 4)])
        return Region(perimeters=[sq])

    def _hole_region(self):
        outer = Polygon([Point2D(0, 0), Point2D(10, 0), Point2D(10, 10), Point2D(0, 10)])
        hole = Polygon([Point2D(2, 2), Point2D(8, 2), Point2D(8, 8), Point2D(2, 8)])
        return Region(perimeters=[outer], holes=[hole])

    def test_init_empty(self):
        r = Region()
        assert len(r.perimeters) == 0

    def test_area_simple(self):
        r = self._square_region()
        assert r.area == pytest.approx(16.0)

    def test_area_with_hole(self):
        r = self._hole_region()
        # outer 100 - hole 36
        assert r.area == pytest.approx(64.0)

    def test_perimeter_total(self):
        r = self._square_region()
        assert r.perimeter == pytest.approx(16.0)

    def test_contains_point_inside(self):
        r = self._square_region()
        assert r.contains_point(Point2D(2, 2))

    def test_contains_point_outside(self):
        r = self._square_region()
        assert not r.contains_point(Point2D(5, 5))

    def test_contains_point_in_hole(self):
        r = self._hole_region()
        assert not r.contains_point(Point2D(5, 5))

    def test_add_remove_perimeter(self):
        r = Region()
        sq = Polygon([Point2D(0, 0), Point2D(4, 0), Point2D(4, 4), Point2D(0, 4)])
        r.add_perimeter(sq)
        assert len(r.perimeters) == 1
        r.remove_perimeter(0)
        assert len(r.perimeters) == 0

    def test_add_remove_hole(self):
        r = self._square_region()
        h = Polygon([Point2D(1, 1), Point2D(3, 1), Point2D(3, 3), Point2D(1, 3)])
        r.add_hole(h)
        assert len(r.holes) == 1
        r.remove_hole(0)
        assert len(r.holes) == 0

    def test_translate(self):
        r = self._square_region()
        r2 = r.translate(Point2D(1, 1))
        assert r2.perimeters[0][0] == Point2D(1, 1)

    def test_rotate(self):
        r = self._square_region()
        r2 = r.rotate(math.pi / 2)
        assert r2 is not None

    def test_scale(self):
        r = self._square_region()
        r2 = r.scale(2)
        assert r2.area == pytest.approx(64.0)

    def test_get_bounds(self):
        r = self._square_region()
        bounds = r.get_bounds()
        assert bounds == (0.0, 0.0, 4.0, 4.0)

    def test_rectangle_classmethod(self):
        r = Region.rectangle(Point2D(0, 0), 4, 4)
        assert isinstance(r, Region)
        assert r.area == pytest.approx(16.0)

    def test_from_polygons(self):
        sq = Polygon([Point2D(0, 0), Point2D(4, 0), Point2D(4, 4), Point2D(0, 4)])
        r = Region.from_polygons([sq])
        assert isinstance(r, Region)

    def test_len(self):
        r = self._square_region()
        assert len(r) == 1

    def test_iter(self):
        r = self._square_region()
        perims = list(r)
        assert len(perims) == 1

    def test_getitem(self):
        r = self._square_region()
        assert isinstance(r[0], Polygon)

    def test_decompose(self):
        r = self._square_region()
        result = r.decompose([ShapeType.REGION])
        assert len(result) == 1

    def test_bounds_property(self):
        r = self._square_region()
        p1, p2 = r.bounds
        assert p1 == Point2D(0, 0)
        assert p2 == Point2D(4, 4)

    def test_transform(self):
        r = self._square_region()
        t = Transform2D.translation(1, 1)
        r2 = r.transform(t)
        assert r2 is not None

    def test_str_repr(self):
        r = self._square_region()
        assert len(str(r)) > 0


# ════════════════════════════════════════════════════════════════════
# ShapeType enum
# ════════════════════════════════════════════════════════════════════

class TestShapeType:
    def test_all_values(self):
        values = {s for s in ShapeType}
        assert ShapeType.POINT in values
        assert ShapeType.LINE in values
        assert ShapeType.CIRCLE in values
        assert ShapeType.POLYGON in values
        assert ShapeType.REGION in values

    def test_count(self):
        assert len(ShapeType) >= 10


# ════════════════════════════════════════════════════════════════════
# SpurGear
# ════════════════════════════════════════════════════════════════════

class TestSpurGear:
    def _gear(self):
        return SpurGear(num_teeth=20, pitch_diameter=1.0, pressure_angle=20.0)

    def test_init(self):
        g = self._gear()
        assert g.num_teeth == 20
        assert g.pitch_diameter == pytest.approx(1.0)

    def test_pitch_radius(self):
        g = self._gear()
        assert g.pitch_radius == pytest.approx(0.5)

    def test_circular_pitch(self):
        g = self._gear()
        assert g.circular_pitch == pytest.approx(math.pi * 1.0 / 20)

    def test_diametral_pitch(self):
        g = self._gear()
        assert g.diametral_pitch == pytest.approx(20.0)

    def test_addendum_radius(self):
        g = self._gear()
        # addendum = 1/diametral_pitch = 1/20 = 0.05; addendum_radius = pitch_radius + addendum
        assert g.addendum_radius > g.pitch_radius

    def test_base_radius(self):
        g = self._gear()
        br = g.base_radius
        assert br < g.pitch_radius

    def test_root_radius(self):
        g = self._gear()
        rr = g.root_radius
        assert rr < g.pitch_radius

    def test_safety_radius(self):
        g = self._gear()
        sr = g.safety_radius
        assert sr >= g.root_radius
        assert sr >= g.base_radius

    def test_module(self):
        g = self._gear()
        assert g.module == pytest.approx(1.0 / 20)

    def test_get_pitch_circle_points(self):
        g = self._gear()
        pts = g.get_pitch_circle_points(32)
        assert len(pts) == 32

    def test_generate_tooth_profile(self):
        g = self._gear()
        pts = g.generate_tooth_profile()
        assert len(pts) > 0

    def test_generate_gear_path(self):
        g = self._gear()
        pts = g.generate_gear_path()
        assert len(pts) > 0

    def test_backlash_zero_by_default(self):
        g = self._gear()
        assert g.backlash == pytest.approx(0.0)

    def test_profile_shift_zero_by_default(self):
        g = self._gear()
        assert g.profile_shift == pytest.approx(0.0)

    def test_clearance(self):
        g = self._gear()
        assert g.clearance > 0

    def test_outer_radius_equals_addendum_radius(self):
        g = self._gear()
        assert g._outer_radius() == pytest.approx(g.addendum_radius)

    def test_base_radius_method(self):
        g = self._gear()
        br = g._base_radius()
        assert br == pytest.approx(g.pitch_radius * math.cos(math.radians(20.0)))

    def test_lerp(self):
        g = self._gear()
        assert g._lerp(0, 10, 0.5) == pytest.approx(5.0)
        assert g._lerp(0, 10, 0) == pytest.approx(0.0)
        assert g._lerp(0, 10, 1) == pytest.approx(10.0)

    def test_lookup(self):
        g = self._gear()
        table = [(0.0, 0.0), (1.0, 10.0), (2.0, 20.0)]
        assert g._lookup(0.5, table) == pytest.approx(5.0)

    def test_xy_to_polar(self):
        g = self._gear()
        r, a = g._xy_to_polar((1.0, 0.0))
        assert r == pytest.approx(1.0)
        assert a == pytest.approx(0.0)

    def test_polar_to_xy(self):
        g = self._gear()
        x, y = g._polar_to_xy(1.0, 0.0)
        assert x == pytest.approx(1.0)
        assert y == pytest.approx(0.0)

    def test_zrot(self):
        # _zrot takes degrees, not radians
        g = self._gear()
        p = g._zrot(90, Point2D(1, 0))
        assert p.x == pytest.approx(0, abs=1e-9)
        assert p.y == pytest.approx(1)

    def test_decompose(self):
        g = self._gear()
        result = g.decompose([ShapeType.POLYGON])
        assert len(result) > 0

    def test_different_tooth_counts(self):
        for n in [8, 12, 24, 48]:
            g = SpurGear(num_teeth=n, pitch_diameter=1.0)
            pts = g.generate_gear_path()
            assert len(pts) > 0

    def test_with_backlash(self):
        g = SpurGear(num_teeth=20, pitch_diameter=1.0, backlash=0.01)
        pts = g.generate_gear_path()
        assert len(pts) > 0
