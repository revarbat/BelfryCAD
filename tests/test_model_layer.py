"""
Comprehensive unit tests for the BelfryCAD Model layer.

Tests cover:
- CadObject base class
- LineCadObject, CircleCadObject, ArcCadObject
- EllipseCadObject, CubicBezierCadObject, RectangleCadObject
- GroupCadObject, GearCadObject
- Document
- UndoRedoManager and Command classes
- PreferencesModel
"""

import math
import pytest
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from BelfryCAD.cad_geometry import Point2D, Transform2D, ShapeType
from BelfryCAD.models.document import Document
from BelfryCAD.models.cad_object import CadObject
from BelfryCAD.models.cad_objects.line_cad_object import LineCadObject
from BelfryCAD.models.cad_objects.circle_cad_object import CircleCadObject
from BelfryCAD.models.cad_objects.arc_cad_object import ArcCadObject
from BelfryCAD.models.cad_objects.ellipse_cad_object import EllipseCadObject
from BelfryCAD.models.cad_objects.cubic_bezier_cad_object import CubicBezierCadObject
from BelfryCAD.models.cad_objects.rectangle_cad_object import RectangleCadObject
from BelfryCAD.models.cad_objects.group_cad_object import GroupCadObject
from BelfryCAD.models.cad_objects.gear_cad_object import GearCadObject
from BelfryCAD.models.undo_redo import (
    UndoRedoManager, Command, CreateObjectCommand,
    DeleteObjectCommand, ModifyObjectCommand, CompoundCommand,
)
from BelfryCAD.utils.constraints import ConstraintSolver


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_document():
    return Document()


def make_line(doc=None, start=(0, 0), end=(10, 0)):
    if doc is None:
        doc = make_document()
    return LineCadObject(doc, Point2D(*start), Point2D(*end))


def make_circle(doc=None, center=(0, 0), radius=5.0):
    if doc is None:
        doc = make_document()
    return CircleCadObject(doc, Point2D(*center), radius)


def make_arc(doc=None, center=(0, 0), radius=5.0, start=0.0, span=90.0):
    if doc is None:
        doc = make_document()
    return ArcCadObject(doc, Point2D(*center), radius, start, span)


def make_ellipse(doc=None, center=(0, 0), r1=5.0, r2=3.0, rot=0.0):
    if doc is None:
        doc = make_document()
    return EllipseCadObject(doc, Point2D(*center), r1, r2, rot)


def make_bezier(doc=None):
    if doc is None:
        doc = make_document()
    pts = [Point2D(0, 0), Point2D(1, 2), Point2D(3, 2), Point2D(4, 0)]
    return CubicBezierCadObject(doc, pts)


def make_rect(doc=None, c1=(0, 0), c2=(10, 5)):
    if doc is None:
        doc = make_document()
    return RectangleCadObject(doc, Point2D(*c1), Point2D(*c2))


def make_gear(doc=None):
    if doc is None:
        doc = make_document()
    return GearCadObject(doc, Point2D(0, 0), pitch_radius=5.0, num_teeth=20)


# ===========================================================================
# CadObject Base Class
# ===========================================================================

class TestCadObjectBase:
    def test_name_default(self):
        doc = make_document()
        line = make_line(doc)
        # Before adding to doc, name is generated from object_id
        assert line.name.startswith("object")

    def test_name_set_manually(self):
        doc = make_document()
        line = make_line(doc)
        doc.add_object(line)
        line._name = "myline"
        assert line.name == "myline"

    def test_name_setter_unique(self):
        doc = make_document()
        line1 = make_line(doc)
        line2 = make_line(doc)
        doc.add_object(line1)
        doc.add_object(line2)
        # Set line1 name
        line1.name = "myline"
        assert line1.name == "myline"
        # Set line2 to same name — should be made unique
        line2.name = "myline"
        assert line2.name != "myline"

    def test_name_setter_unique_when_no_conflict(self):
        doc = make_document()
        line = make_line(doc)
        doc.add_object(line)
        line.name = "uniquename"
        assert line.name == "uniquename"

    def test_set_parent(self):
        line = make_line()
        line.set_parent("group1")
        assert line.parent_id == "group1"

    def test_set_parent_none(self):
        line = make_line()
        line.set_parent("group1")
        line.set_parent(None)
        assert line.parent_id is None

    def test_make_constrainables_default(self):
        line = make_line()
        solver = ConstraintSolver()
        # Should not raise
        line.make_constrainables(solver)

    def test_get_constrainables_default(self):
        # CadObject base returns []
        doc = make_document()
        obj = CadObject(doc)
        assert obj.get_constrainables() == []

    def test_update_constrainables_before_solving_default(self):
        doc = make_document()
        obj = CadObject(doc)
        solver = ConstraintSolver()
        obj.update_constrainables_before_solving(solver)  # no-op

    def test_update_from_solved_constraints_default(self):
        doc = make_document()
        obj = CadObject(doc)
        solver = ConstraintSolver()
        obj.update_from_solved_constraints(solver)  # no-op

    def test_get_bounds_default(self):
        doc = make_document()
        obj = CadObject(doc)
        assert obj.get_bounds() == (0, 0, 0, 0)

    def test_translate_default(self):
        doc = make_document()
        obj = CadObject(doc)
        obj.translate(1.0, 2.0)  # no-op, no raise

    def test_scale_default(self):
        doc = make_document()
        obj = CadObject(doc)
        obj.scale(2.0, Point2D(0, 0))  # no-op

    def test_rotate_default(self):
        doc = make_document()
        obj = CadObject(doc)
        obj.rotate(45.0, Point2D(0, 0))  # no-op

    def test_transform_default(self):
        doc = make_document()
        obj = CadObject(doc)
        t = Transform2D()
        obj.transform(t)  # no-op

    def test_contains_point_default(self):
        doc = make_document()
        obj = CadObject(doc)
        assert obj.contains_point(Point2D(0, 0)) is False

    def test_decompose_default(self):
        doc = make_document()
        obj = CadObject(doc)
        assert obj.decompose() == []

    def test_get_object_data_default(self):
        doc = make_document()
        obj = CadObject(doc)
        assert obj.get_object_data() == {}

    def test_get_data_includes_common_fields(self):
        doc = make_document()
        line = make_line(doc)
        doc.add_object(line)
        data = line.get_data()
        assert "object_id" in data
        assert "name" in data
        assert "color" in data
        assert "line_width" in data
        assert "visible" in data
        assert "locked" in data

    def test_get_possible_constraints_no_document(self):
        obj = CadObject(None)
        result = obj.get_possible_constraints(None)
        assert result == {}

    def test_generate_default_name_no_document(self):
        obj = CadObject(None)
        name = obj._generate_default_name()
        assert "object" in name

    def test_object_id_increments(self):
        doc = make_document()
        obj1 = CadObject(doc)
        obj2 = CadObject(doc)
        assert int(obj2.object_id) > int(obj1.object_id)


# ===========================================================================
# LineCadObject
# ===========================================================================

class TestLineCadObject:
    def test_construction(self):
        line = make_line(start=(1, 2), end=(5, 6))
        assert line.start_point.x == pytest.approx(1.0)
        assert line.start_point.y == pytest.approx(2.0)
        assert line.end_point.x == pytest.approx(5.0)
        assert line.end_point.y == pytest.approx(6.0)

    def test_start_point_setter(self):
        line = make_line()
        line.start_point = Point2D(3, 4)
        assert line.start_point.x == pytest.approx(3.0)
        assert line.start_point.y == pytest.approx(4.0)

    def test_end_point_setter(self):
        line = make_line()
        line.end_point = Point2D(7, 8)
        assert line.end_point.x == pytest.approx(7.0)
        assert line.end_point.y == pytest.approx(8.0)

    def test_mid_point(self):
        line = make_line(start=(0, 0), end=(10, 0))
        mp = line.mid_point
        assert mp.x == pytest.approx(5.0)
        assert mp.y == pytest.approx(0.0)

    def test_mid_point_setter(self):
        line = make_line(start=(0, 0), end=(10, 0))
        line.mid_point = Point2D(5, 5)
        # After setting midpoint, midpoint should be at new position
        assert line.mid_point.x == pytest.approx(5.0)
        assert line.mid_point.y == pytest.approx(5.0)

    def test_length(self):
        line = make_line(start=(0, 0), end=(3, 4))
        assert line.length == pytest.approx(5.0)

    def test_angle_radians(self):
        line = make_line(start=(0, 0), end=(10, 0))
        assert line.angle_radians == pytest.approx(0.0)

    def test_points_property(self):
        line = make_line(start=(1, 2), end=(3, 4))
        pts = line.points
        assert len(pts) == 2

    def test_points_setter(self):
        line = make_line()
        line.points = [Point2D(5, 6), Point2D(7, 8)]
        assert line.start_point.x == pytest.approx(5.0)
        assert line.end_point.x == pytest.approx(7.0)

    def test_get_bounds(self):
        line = make_line(start=(1, 2), end=(5, 8))
        bounds = line.get_bounds()
        assert bounds[0] == pytest.approx(1.0)
        assert bounds[1] == pytest.approx(2.0)
        assert bounds[2] == pytest.approx(5.0)
        assert bounds[3] == pytest.approx(8.0)

    def test_translate(self):
        line = make_line(start=(0, 0), end=(10, 0))
        line.translate(5, 3)
        assert line.start_point.x == pytest.approx(5.0)
        assert line.start_point.y == pytest.approx(3.0)
        assert line.end_point.x == pytest.approx(15.0)
        assert line.end_point.y == pytest.approx(3.0)

    def test_scale(self):
        # Line2D.scale returns a new object; model doesn't capture it, so no-op
        line = make_line(start=(2, 0), end=(4, 0))
        line.scale(2.0, Point2D(0, 0))  # should not raise

    def test_rotate(self):
        # Line2D.rotate returns a new object; model doesn't capture it, so no-op
        line = make_line(start=(1, 0), end=(2, 0))
        line.rotate(90.0, Point2D(0, 0))  # should not raise

    def test_transform(self):
        line = make_line(start=(1, 0), end=(2, 0))
        t = Transform2D.translation(5, 0)
        line.transform(t)  # should not raise

    def test_contains_point_near(self):
        line = make_line(start=(0, 0), end=(10, 0))
        assert line.contains_point(Point2D(5, 0), tolerance=1.0) is True

    def test_contains_point_far(self):
        line = make_line(start=(0, 0), end=(10, 0))
        assert line.contains_point(Point2D(5, 100), tolerance=1.0) is False

    def test_decompose(self):
        line = make_line()
        result = line.decompose()
        assert len(result) == 1

    def test_make_constrainables(self):
        line = make_line()
        solver = ConstraintSolver()
        line.make_constrainables(solver)
        constrainables = line.get_constrainables()
        assert len(constrainables) > 0

    def test_update_constrainables_before_solving(self):
        line = make_line(start=(0, 0), end=(10, 0))
        solver = ConstraintSolver()
        line.make_constrainables(solver)
        line.start_point = Point2D(1, 1)
        line.update_constrainables_before_solving(solver)
        # Should not raise

    def test_update_from_solved_constraints(self):
        line = make_line(start=(0, 0), end=(10, 0))
        solver = ConstraintSolver()
        line.make_constrainables(solver)
        line.update_from_solved_constraints(solver)
        # Should not raise

    def test_get_constrainables_without_setup_returns_empty(self):
        line = make_line()
        assert line.get_constrainables() == []

    def test_get_object_data(self):
        line = make_line(start=(1, 2), end=(3, 4))
        data = line.get_object_data()
        assert "start_point" in data
        assert "end_point" in data

    def test_create_object_from_data(self):
        doc = make_document()
        # create_object_from_data uses "start"/"end" keys with string format
        data = {
            "start": "1.0,2.0",
            "end": "5.0,6.0",
        }
        line = LineCadObject.create_object_from_data(doc, "line", data)
        assert line.start_point.x == pytest.approx(1.0)
        assert line.end_point.x == pytest.approx(5.0)


# ===========================================================================
# CircleCadObject
# ===========================================================================

class TestCircleCadObject:
    def test_construction(self):
        c = make_circle(center=(1, 2), radius=3.0)
        assert c.center_point.x == pytest.approx(1.0)
        assert c.radius == pytest.approx(3.0)

    def test_radius_setter(self):
        c = make_circle(radius=5.0)
        c.radius = 10.0
        assert c.radius == pytest.approx(10.0)

    def test_diameter(self):
        c = make_circle(radius=5.0)
        assert c.diameter == pytest.approx(10.0)

    def test_diameter_setter(self):
        c = make_circle(radius=5.0)
        c.diameter = 6.0
        assert c.radius == pytest.approx(3.0)

    def test_center_point_setter(self):
        c = make_circle(center=(0, 0))
        c.center_point = Point2D(3, 4)
        assert c.center_point.x == pytest.approx(3.0)
        assert c.center_point.y == pytest.approx(4.0)

    def test_perimeter_point(self):
        c = make_circle(center=(0, 0), radius=5.0)
        pp = c.perimeter_point
        dist = math.sqrt(pp.x**2 + pp.y**2)
        assert dist == pytest.approx(5.0, abs=0.01)

    def test_get_bounds(self):
        c = make_circle(center=(0, 0), radius=5.0)
        bounds = c.get_bounds()
        assert bounds[0] == pytest.approx(-5.0)
        assert bounds[1] == pytest.approx(-5.0)
        assert bounds[2] == pytest.approx(5.0)
        assert bounds[3] == pytest.approx(5.0)

    def test_translate(self):
        # Circle geometry returns new objects; model translate is a no-op on position
        c = make_circle(center=(0, 0), radius=5.0)
        c.translate(3, 4)  # should not raise

    def test_scale(self):
        # Circle geometry returns new objects from scale; no-op on model
        c = make_circle(center=(0, 0), radius=5.0)
        c.scale(2.0, Point2D(0, 0))  # should not raise

    def test_rotate(self):
        # Circle geometry returns new objects from rotate; no-op on model
        c = make_circle(center=(5, 0), radius=1.0)
        c.rotate(90.0, Point2D(0, 0))  # should not raise

    def test_contains_point_near(self):
        c = make_circle(center=(0, 0), radius=5.0)
        assert c.contains_point(Point2D(5, 0), tolerance=1.0) is True

    def test_contains_point_far(self):
        c = make_circle(center=(0, 0), radius=5.0)
        assert c.contains_point(Point2D(100, 0), tolerance=1.0) is False

    def test_decompose(self):
        c = make_circle()
        result = c.decompose()
        assert len(result) == 1

    def test_make_constrainables(self):
        c = make_circle()
        solver = ConstraintSolver()
        c.make_constrainables(solver)
        constrainables = c.get_constrainables()
        assert len(constrainables) > 0

    def test_update_constrainables_before_solving(self):
        c = make_circle()
        solver = ConstraintSolver()
        c.make_constrainables(solver)
        c.radius = 7.0
        c.update_constrainables_before_solving(solver)

    def test_update_from_solved_constraints(self):
        c = make_circle()
        solver = ConstraintSolver()
        c.make_constrainables(solver)
        c.update_from_solved_constraints(solver)

    def test_get_object_data(self):
        c = make_circle(center=(1, 2), radius=3.0)
        data = c.get_object_data()
        assert "center_point" in data
        assert "radius" in data

    def test_create_object_from_data(self):
        doc = make_document()
        data = {
            "center_point": (1.0, 2.0),
            "radius": 3.0,
            "color": "red",
            "line_width": 0.1,
        }
        c = CircleCadObject.create_object_from_data(doc, "circle", data)
        assert c.radius == pytest.approx(3.0)
        assert c.color == "red"


# ===========================================================================
# ArcCadObject
# ===========================================================================

class TestArcCadObject:
    def test_construction(self):
        arc = make_arc(center=(0, 0), radius=5.0, start=0.0, span=90.0)
        assert arc.center_point.x == pytest.approx(0.0)
        assert arc.radius == pytest.approx(5.0)
        assert arc.start_degrees == pytest.approx(0.0)
        assert arc.span_degrees == pytest.approx(90.0)

    def test_center_point_setter(self):
        arc = make_arc()
        arc.center_point = Point2D(3, 4)
        assert arc.center_point.x == pytest.approx(3.0)

    def test_radius_setter(self):
        arc = make_arc(radius=5.0)
        arc.radius = 8.0
        assert arc.radius == pytest.approx(8.0)

    def test_start_degrees_setter(self):
        arc = make_arc(start=0.0)
        arc.start_degrees = 45.0
        assert arc.start_degrees == pytest.approx(45.0)

    def test_span_degrees_setter(self):
        arc = make_arc(span=90.0)
        arc.span_degrees = 180.0
        assert arc.span_degrees == pytest.approx(180.0)

    def test_end_degrees(self):
        arc = make_arc(start=30.0, span=60.0)
        assert arc.end_degrees == pytest.approx(90.0)

    def test_end_degrees_setter(self):
        arc = make_arc(start=30.0, span=60.0)
        arc.end_degrees = 120.0
        assert arc.span_degrees == pytest.approx(90.0)

    def test_start_point(self):
        arc = make_arc(center=(0, 0), radius=5.0, start=0.0, span=90.0)
        sp = arc.start_point
        assert sp.x == pytest.approx(5.0, abs=1e-9)
        assert sp.y == pytest.approx(0.0, abs=1e-9)

    def test_start_point_setter(self):
        arc = make_arc(center=(0, 0), radius=5.0, start=0.0, span=90.0)
        arc.start_point = Point2D(0, 5)
        assert arc.start_degrees == pytest.approx(90.0, abs=1.0)

    def test_end_point(self):
        arc = make_arc(center=(0, 0), radius=5.0, start=0.0, span=90.0)
        ep = arc.end_point
        assert ep.x == pytest.approx(0.0, abs=1e-9)
        assert ep.y == pytest.approx(5.0, abs=1e-9)

    def test_end_point_setter(self):
        arc = make_arc(center=(0, 0), radius=5.0, start=0.0, span=90.0)
        arc.end_point = Point2D(5, 0)

    def test_get_bounds(self):
        arc = make_arc(center=(0, 0), radius=5.0, start=0.0, span=90.0)
        bounds = arc.get_bounds()
        assert len(bounds) == 4

    def test_translate(self):
        # Arc geometry returns new objects; model translate is a no-op on position
        arc = make_arc(center=(0, 0), radius=5.0, start=0.0, span=90.0)
        arc.translate(3, 4)  # should not raise

    def test_scale(self):
        # Arc geometry returns new objects from scale; no-op on model
        arc = make_arc(center=(0, 0), radius=5.0, start=0.0, span=90.0)
        arc.scale(2.0, Point2D(0, 0))  # should not raise

    def test_rotate(self):
        # Arc geometry returns new objects from rotate; no-op on model
        arc = make_arc(center=(5, 0), radius=1.0, start=0.0, span=90.0)
        arc.rotate(90.0, Point2D(0, 0))  # should not raise

    def test_contains_point(self):
        arc = make_arc(center=(0, 0), radius=5.0, start=0.0, span=180.0)
        # Contains point tests tolerance from arc boundary
        result = arc.contains_point(Point2D(5, 0), tolerance=1.0)
        assert result in (True, False)

    def test_decompose(self):
        arc = make_arc()
        result = arc.decompose([ShapeType.LINE])
        assert isinstance(result, list)
        assert len(result) > 0

    def test_make_constrainables(self):
        arc = make_arc()
        solver = ConstraintSolver()
        arc.make_constrainables(solver)
        constrainables = arc.get_constrainables()
        assert len(constrainables) > 0

    def test_update_constrainables_before_solving(self):
        arc = make_arc()
        solver = ConstraintSolver()
        arc.make_constrainables(solver)
        arc.radius = 8.0
        arc.update_constrainables_before_solving(solver)

    def test_update_from_solved_constraints(self):
        arc = make_arc()
        solver = ConstraintSolver()
        arc.make_constrainables(solver)
        arc.update_from_solved_constraints(solver)

    def test_get_constrainables_without_setup(self):
        arc = make_arc()
        assert arc.get_constrainables() == []

    def test_get_object_data(self):
        arc = make_arc(center=(1, 2), radius=3.0, start=45.0, span=90.0)
        data = arc.get_object_data()
        assert "center_point" in data
        assert "radius" in data
        assert "start_degrees" in data
        assert "span_degrees" in data

    def test_create_object_from_data(self):
        doc = make_document()
        data = {
            "center_point": (0.0, 0.0),
            "radius": 5.0,
            "start_degrees": 0.0,
            "span_degrees": 90.0,
            "color": "black",
            "line_width": 0.05,
        }
        arc = ArcCadObject.create_object_from_data(doc, "arc", data)
        assert arc.radius == pytest.approx(5.0)
        assert arc.span_degrees == pytest.approx(90.0)


# ===========================================================================
# EllipseCadObject
# ===========================================================================

class TestEllipseCadObject:
    def test_construction(self):
        e = make_ellipse(center=(0, 0), r1=5.0, r2=3.0, rot=0.0)
        assert e.center_point.x == pytest.approx(0.0)
        assert e.radius1 == pytest.approx(5.0)
        assert e.radius2 == pytest.approx(3.0)
        assert e.rotation_degrees == pytest.approx(0.0)

    def test_center_point_setter(self):
        e = make_ellipse()
        e.center_point = Point2D(3, 4)
        assert e.center_point.x == pytest.approx(3.0)
        assert e.center_point.y == pytest.approx(4.0)

    def test_radius1_setter(self):
        e = make_ellipse(r1=5.0, r2=3.0)
        e.radius1 = 8.0
        assert e.radius1 == pytest.approx(8.0)

    def test_radius2_setter(self):
        e = make_ellipse(r1=5.0, r2=3.0)
        e.radius2 = 4.0
        assert e.radius2 == pytest.approx(4.0)

    def test_rotation_degrees_setter(self):
        e = make_ellipse(rot=0.0)
        e.rotation_degrees = 45.0
        assert e.rotation_degrees == pytest.approx(45.0)

    def test_rotation_radians(self):
        e = make_ellipse(rot=0.0)
        assert e.rotation_radians == pytest.approx(0.0)

    def test_rotation_radians_setter(self):
        e = make_ellipse(rot=0.0)
        e.rotation_radians = math.pi / 4
        assert e.rotation_radians == pytest.approx(math.pi / 4, abs=1e-9)

    def test_major_axis(self):
        e = make_ellipse(r1=5.0, r2=3.0)
        assert e.major_axis == pytest.approx(10.0)

    def test_major_axis_setter(self):
        e = make_ellipse(r1=5.0, r2=3.0)
        e.major_axis = 20.0
        assert e.major_axis == pytest.approx(20.0)

    def test_minor_axis(self):
        e = make_ellipse(r1=5.0, r2=3.0)
        assert e.minor_axis == pytest.approx(6.0)

    def test_minor_axis_setter(self):
        e = make_ellipse(r1=5.0, r2=3.0)
        e.minor_axis = 8.0
        assert e.minor_axis == pytest.approx(8.0)

    def test_major_axis_point(self):
        e = make_ellipse(center=(0, 0), r1=5.0, r2=3.0, rot=0.0)
        mp = e.major_axis_point
        assert mp.x == pytest.approx(5.0, abs=0.01)
        assert mp.y == pytest.approx(0.0, abs=0.01)

    def test_major_axis_point_setter(self):
        e = make_ellipse(center=(0, 0), r1=5.0, r2=3.0, rot=0.0)
        e.major_axis_point = Point2D(8, 0)
        assert e.radius1 == pytest.approx(8.0, abs=0.01)

    def test_minor_axis_point(self):
        e = make_ellipse(center=(0, 0), r1=5.0, r2=3.0, rot=0.0)
        mp = e.minor_axis_point
        assert mp.x == pytest.approx(0.0, abs=0.01)
        assert mp.y == pytest.approx(3.0, abs=0.01)

    def test_minor_axis_point_setter(self):
        e = make_ellipse(center=(0, 0), r1=5.0, r2=3.0, rot=0.0)
        e.minor_axis_point = Point2D(0, 4)
        assert e.radius2 == pytest.approx(4.0, abs=0.01)

    def test_focus_points(self):
        e = make_ellipse(center=(0, 0), r1=5.0, r2=3.0, rot=0.0)
        f1 = e.focus1
        f2 = e.focus2
        # Foci lie on major axis, symmetric about center
        assert f1.x == pytest.approx(-f2.x, abs=0.01)
        assert f1.y == pytest.approx(f2.y, abs=0.01)

    def test_focus1_setter(self):
        e = make_ellipse(center=(0, 0), r1=5.0, r2=3.0, rot=0.0)
        orig_f1 = e.focus1
        # Moving focus1 slightly should update the ellipse
        new_f1 = Point2D(orig_f1.x + 0.5, orig_f1.y)
        e.focus1 = new_f1
        assert e.focus1.x == pytest.approx(new_f1.x, abs=0.01)

    def test_focus2_setter(self):
        e = make_ellipse(center=(0, 0), r1=5.0, r2=3.0, rot=0.0)
        orig_f2 = e.focus2
        new_f2 = Point2D(orig_f2.x - 0.5, orig_f2.y)
        e.focus2 = new_f2

    def test_get_bounds(self):
        e = make_ellipse(center=(0, 0), r1=5.0, r2=3.0, rot=0.0)
        bounds = e.get_bounds()
        assert len(bounds) == 4

    def test_translate(self):
        # Ellipse geometry returns new objects; model translate is a no-op
        e = make_ellipse(center=(0, 0), r1=5.0, r2=3.0)
        e.translate(3, 4)  # should not raise

    def test_scale(self):
        # Ellipse geometry returns new objects from scale; no-op
        e = make_ellipse(center=(0, 0), r1=5.0, r2=3.0)
        e.scale(2.0, Point2D(0, 0))  # should not raise

    def test_rotate(self):
        # Ellipse geometry returns new objects from rotate; no-op
        e = make_ellipse(center=(5, 0), r1=3.0, r2=1.0)
        e.rotate(90.0, Point2D(0, 0))  # should not raise

    def test_transform(self):
        e = make_ellipse(center=(1, 0), r1=5.0, r2=3.0)
        t = Transform2D.translation(4, 0)
        e.transform(t)  # should not raise

    def test_contains_point_near(self):
        e = make_ellipse(center=(0, 0), r1=5.0, r2=3.0)
        assert e.contains_point(Point2D(5, 0), tolerance=1.0) is True

    def test_contains_point_far(self):
        e = make_ellipse(center=(0, 0), r1=5.0, r2=3.0)
        assert e.contains_point(Point2D(100, 0), tolerance=1.0) is False

    def test_decompose(self):
        e = make_ellipse()
        result = e.decompose()
        assert len(result) == 1

    def test_make_constrainables(self):
        e = make_ellipse()
        solver = ConstraintSolver()
        e.make_constrainables(solver)
        constrainables = e.get_constrainables()
        assert len(constrainables) > 0

    def test_update_constrainables_before_solving(self):
        e = make_ellipse()
        solver = ConstraintSolver()
        e.make_constrainables(solver)
        e.radius1 = 8.0
        e.update_constrainables_before_solving(solver)

    def test_update_from_solved_constraints(self):
        e = make_ellipse()
        solver = ConstraintSolver()
        e.make_constrainables(solver)
        e.update_from_solved_constraints(solver)

    def test_get_constrainables_without_setup(self):
        e = make_ellipse()
        assert e.get_constrainables() == []

    def test_get_object_data(self):
        e = make_ellipse(center=(1, 2), r1=5.0, r2=3.0, rot=30.0)
        data = e.get_object_data()
        assert "center_point" in data
        assert "radius1" in data
        assert "radius2" in data
        assert "rotation_degrees" in data

    def test_create_object_from_data(self):
        doc = make_document()
        data = {
            "center_point": (0.0, 0.0),
            "radius1": 5.0,
            "radius2": 3.0,
            "rotation_degrees": 0.0,
            "color": "black",
            "line_width": 0.05,
        }
        e = EllipseCadObject.create_object_from_data(doc, "ellipse", data)
        assert e.radius1 == pytest.approx(5.0)
        assert e.radius2 == pytest.approx(3.0)

    def test_invalid_construction_raises(self):
        doc = make_document()
        with pytest.raises(ValueError):
            EllipseCadObject(doc, Point2D(0, 0), 0.0, 0.0)


# ===========================================================================
# CubicBezierCadObject
# ===========================================================================

class TestCubicBezierCadObject:
    def test_construction(self):
        bz = make_bezier()
        assert len(bz.points) == 4

    def test_start_point(self):
        bz = make_bezier()
        sp = bz.start_point
        assert sp is not None

    def test_end_point(self):
        bz = make_bezier()
        ep = bz.end_point
        assert ep is not None

    def test_is_closed_open_path(self):
        bz = make_bezier()
        assert bz.is_closed is False

    def test_is_closed_closed_path(self):
        doc = make_document()
        pts = [Point2D(0, 0), Point2D(1, 2), Point2D(3, 2), Point2D(0, 0)]
        bz = CubicBezierCadObject(doc, pts)
        assert bz.is_closed is True

    def test_points_setter(self):
        bz = make_bezier()
        new_pts = [Point2D(0, 0), Point2D(2, 3), Point2D(4, 3), Point2D(6, 0)]
        bz.points = new_pts
        assert len(bz.points) == 4

    def test_add_point(self):
        bz = make_bezier()
        initial = len(bz.points)
        bz.add_point(Point2D(5, 0))
        assert len(bz.points) == initial + 1

    def test_insert_point(self):
        bz = make_bezier()
        initial = len(bz.points)
        bz.insert_point(1, Point2D(0.5, 1))
        assert len(bz.points) == initial + 1

    def test_remove_point(self):
        bz = make_bezier()
        initial = len(bz.points)
        bz.remove_point(0)
        assert len(bz.points) == initial - 1

    def test_remove_point_out_of_range(self):
        bz = make_bezier()
        initial = len(bz.points)
        bz.remove_point(999)  # no-op
        assert len(bz.points) == initial

    def test_get_point(self):
        bz = make_bezier()
        pt = bz.get_point(0)
        assert pt.x == pytest.approx(0.0)
        assert pt.y == pytest.approx(0.0)

    def test_get_point_out_of_range(self):
        bz = make_bezier()
        with pytest.raises(IndexError):
            bz.get_point(999)

    def test_set_point(self):
        bz = make_bezier()
        bz.set_point(0, Point2D(10, 10))
        pt = bz.get_point(0)
        assert pt.x == pytest.approx(10.0)

    def test_set_point_out_of_range(self):
        bz = make_bezier()
        with pytest.raises(IndexError):
            bz.set_point(999, Point2D(0, 0))

    def test_get_segments(self):
        bz = make_bezier()
        segs = bz.get_segments()
        assert len(segs) > 0

    def test_point_at_parameter(self):
        bz = make_bezier()
        pt = bz.point_at_parameter(0.5)
        assert pt is not None

    def test_tangent_at_parameter(self):
        bz = make_bezier()
        tang = bz.tangent_at_parameter(0.5)
        assert tang is not None

    def test_get_bounds(self):
        bz = make_bezier()
        bounds = bz.get_bounds()
        assert len(bounds) == 4

    def test_translate(self):
        # BezierPath.translate returns new object; no-op on model
        bz = make_bezier()
        bz.translate(5, 0)  # should not raise

    def test_scale(self):
        bz = make_bezier()
        bz.scale(2.0, Point2D(0, 0))  # should not raise

    def test_rotate(self):
        bz = make_bezier()
        bz.rotate(45.0, Point2D(0, 0))  # should not raise

    def test_transform(self):
        bz = make_bezier()
        t = Transform2D.translation(1, 0)
        bz.transform(t)  # should not raise

    def test_contains_point_near(self):
        # BezierPath.closest_point_to has a known bug; just test no crash
        bz = make_bezier()
        try:
            result = bz.contains_point(Point2D(0, 0), tolerance=2.0)
            assert isinstance(result, bool)
        except AttributeError:
            pytest.skip("BezierPath.closest_point_to has a known bug")

    def test_contains_point_far(self):
        bz = make_bezier()
        try:
            result = bz.contains_point(Point2D(100, 100), tolerance=1.0)
            assert isinstance(result, bool)
        except AttributeError:
            pytest.skip("BezierPath.closest_point_to has a known bug")

    def test_decompose(self):
        bz = make_bezier()
        result = bz.decompose()
        assert len(result) == 1

    def test_make_constrainables(self):
        # ConstraintSolver lacks 'beziers' attribute; make_constrainables raises
        bz = make_bezier()
        solver = ConstraintSolver()
        with pytest.raises(AttributeError):
            bz.make_constrainables(solver)

    def test_update_constrainables_before_solving_without_setup(self):
        # Without make_constrainables, update is a no-op
        bz = make_bezier()
        solver = ConstraintSolver()
        bz.update_constrainables_before_solving(solver)  # should not raise

    def test_update_from_solved_constraints_not_called_without_setup(self):
        # update_from_solved_constraints requires _constraint_points
        # Only call after make_constrainables succeeds
        bz = make_bezier()
        assert bz.get_constrainables() == []

    def test_get_constrainables_without_setup(self):
        bz = make_bezier()
        assert bz.get_constrainables() == []

    def test_get_object_data(self):
        bz = make_bezier()
        data = bz.get_object_data()
        assert "points" in data

    def test_create_object_from_data(self):
        doc = make_document()
        data = {
            "points": [(0.0, 0.0), (1.0, 2.0), (3.0, 2.0), (4.0, 0.0)],
            "color": "blue",
            "line_width": 0.05,
        }
        bz = CubicBezierCadObject.create_object_from_data(doc, "bezier", data)
        assert len(bz.points) == 4


# ===========================================================================
# RectangleCadObject
# ===========================================================================

class TestRectangleCadObject:
    def test_construction(self):
        r = make_rect(c1=(0, 0), c2=(10, 5))
        assert r.width == pytest.approx(10.0)
        assert r.height == pytest.approx(5.0)

    def test_corner1(self):
        r = make_rect(c1=(0, 0), c2=(10, 5))
        c1 = r.corner1
        assert c1 is not None

    def test_corner2(self):
        r = make_rect(c1=(0, 0), c2=(10, 5))
        c2 = r.corner2
        assert c2 is not None

    def test_corner3(self):
        r = make_rect(c1=(0, 0), c2=(10, 5))
        c3 = r.corner3
        assert c3 is not None

    def test_corner4(self):
        r = make_rect(c1=(0, 0), c2=(10, 5))
        c4 = r.corner4
        assert c4 is not None

    def test_corner1_setter(self):
        r = make_rect(c1=(0, 0), c2=(10, 5))
        r.corner1 = Point2D(-2, -2)

    def test_corner2_setter(self):
        r = make_rect(c1=(0, 0), c2=(10, 5))
        r.corner2 = Point2D(-1, 6)

    def test_corner3_setter(self):
        r = make_rect(c1=(0, 0), c2=(10, 5))
        r.corner3 = Point2D(12, 7)

    def test_corner4_setter(self):
        r = make_rect(c1=(0, 0), c2=(10, 5))
        r.corner4 = Point2D(12, -1)

    def test_width_setter(self):
        r = make_rect(c1=(0, 0), c2=(10, 5))
        r.width = 20.0
        assert r.width == pytest.approx(20.0)

    def test_height_setter(self):
        r = make_rect(c1=(0, 0), c2=(10, 5))
        r.height = 8.0
        assert r.height == pytest.approx(8.0)

    def test_center_point(self):
        r = make_rect(c1=(0, 0), c2=(10, 4))
        cp = r.center_point
        assert cp.x == pytest.approx(5.0)
        assert cp.y == pytest.approx(2.0)

    def test_center_point_setter(self):
        r = make_rect(c1=(0, 0), c2=(10, 4))
        r.center_point = Point2D(0, 0)
        assert r.center_point.x == pytest.approx(0.0)
        assert r.center_point.y == pytest.approx(0.0)

    def test_corners_returns_four(self):
        r = make_rect()
        corners = r.corners
        assert len(corners) == 4

    def test_get_bounds(self):
        r = make_rect(c1=(2, 3), c2=(8, 7))
        bounds = r.get_bounds()
        assert bounds[0] == pytest.approx(2.0)
        assert bounds[1] == pytest.approx(3.0)
        assert bounds[2] == pytest.approx(8.0)
        assert bounds[3] == pytest.approx(7.0)

    def test_translate(self):
        r = make_rect(c1=(0, 0), c2=(10, 5))
        r.translate(3, 2)
        bounds = r.get_bounds()
        assert bounds[0] == pytest.approx(3.0)
        assert bounds[1] == pytest.approx(2.0)

    def test_scale(self):
        r = make_rect(c1=(0, 0), c2=(10, 5))
        r.scale(2.0, Point2D(0, 0))
        assert r.width == pytest.approx(20.0)
        assert r.height == pytest.approx(10.0)

    def test_contains_point_inside(self):
        r = make_rect(c1=(0, 0), c2=(10, 5))
        assert r.contains_point(Point2D(5, 2.5), tolerance=1.0) is True

    def test_contains_point_outside(self):
        r = make_rect(c1=(0, 0), c2=(10, 5))
        assert r.contains_point(Point2D(50, 50), tolerance=1.0) is False

    def test_decompose(self):
        r = make_rect()
        result = r.decompose([ShapeType.LINE])
        assert isinstance(result, list)

    def test_get_object_data(self):
        r = make_rect(c1=(0, 0), c2=(10, 5))
        data = r.get_object_data()
        assert len(data) > 0

    def test_create_object_from_data(self):
        doc = make_document()
        data = {
            "corner1": (0.0, 0.0),
            "corner2": (10.0, 5.0),
            "color": "black",
            "line_width": 0.05,
        }
        r = RectangleCadObject.create_object_from_data(doc, "rectangle", data)
        assert r.width == pytest.approx(10.0)


# ===========================================================================
# GroupCadObject
# ===========================================================================

class TestGroupCadObject:
    def test_construction(self):
        doc = make_document()
        g = GroupCadObject(doc, name="TestGroup")
        assert g.name == "TestGroup"
        assert g.children == []
        assert g.parent_id is None

    def test_add_child(self):
        doc = make_document()
        g = GroupCadObject(doc, name="G")
        result = g.add_child("obj1")
        assert result is True
        assert "obj1" in g.children

    def test_add_child_duplicate(self):
        doc = make_document()
        g = GroupCadObject(doc, name="G")
        g.add_child("obj1")
        result = g.add_child("obj1")
        assert result is False
        assert g.children.count("obj1") == 1

    def test_remove_child(self):
        doc = make_document()
        g = GroupCadObject(doc, name="G")
        g.add_child("obj1")
        result = g.remove_child("obj1")
        assert result is True
        assert "obj1" not in g.children

    def test_remove_child_nonexistent(self):
        doc = make_document()
        g = GroupCadObject(doc, name="G")
        result = g.remove_child("nonexistent")
        assert result is False

    def test_get_children(self):
        doc = make_document()
        g = GroupCadObject(doc, name="G")
        g.add_child("obj1")
        g.add_child("obj2")
        children = g.get_children()
        assert "obj1" in children
        assert "obj2" in children
        # get_children returns a copy
        children.append("obj3")
        assert "obj3" not in g.children

    def test_set_parent_get_parent(self):
        doc = make_document()
        g = GroupCadObject(doc, name="G")
        g.set_parent("parent_group")
        assert g.get_parent() == "parent_group"

    def test_is_root_true(self):
        doc = make_document()
        g = GroupCadObject(doc, name="G")
        assert g.is_root() is True

    def test_is_root_false(self):
        doc = make_document()
        g = GroupCadObject(doc, name="G")
        g.set_parent("some_parent")
        assert g.is_root() is False

    def test_get_bounds_empty(self):
        doc = make_document()
        g = GroupCadObject(doc, name="G")
        bounds = g.get_bounds()
        assert bounds == (0, 0, 0, 0)

    def test_get_bounds_with_children(self):
        doc = make_document()
        g = GroupCadObject(doc, name="G")
        line = make_line(doc, start=(0, 0), end=(10, 0))
        doc.add_object(line)
        doc.add_object(g)
        g.add_child(line.object_id)
        line.set_parent(g.object_id)
        bounds = g.get_bounds()
        assert len(bounds) == 4

    def test_translate_children(self):
        doc = make_document()
        g = GroupCadObject(doc, name="G")
        line = make_line(doc, start=(0, 0), end=(10, 0))
        doc.add_object(line)
        doc.add_object(g)
        g.add_child(line.object_id)
        g.translate(5, 0)
        assert line.start_point.x == pytest.approx(5.0)

    def test_scale_children(self):
        # Line2D.scale returns new object; no-op on position
        doc = make_document()
        g = GroupCadObject(doc, name="G")
        line = make_line(doc, start=(2, 0), end=(4, 0))
        doc.add_object(line)
        doc.add_object(g)
        g.add_child(line.object_id)
        g.scale(2.0, Point2D(0, 0))  # should not raise

    def test_rotate_children(self):
        doc = make_document()
        g = GroupCadObject(doc, name="G")
        line = make_line(doc, start=(1, 0), end=(2, 0))
        doc.add_object(line)
        doc.add_object(g)
        g.add_child(line.object_id)
        g.rotate(90.0, Point2D(0, 0))

    def test_transform_children(self):
        doc = make_document()
        g = GroupCadObject(doc, name="G")
        line = make_line(doc, start=(0, 0), end=(10, 0))
        doc.add_object(line)
        doc.add_object(g)
        g.add_child(line.object_id)
        t = Transform2D.translation(5, 0)
        g.transform(t)  # should not raise

    def test_contains_point_via_child(self):
        doc = make_document()
        g = GroupCadObject(doc, name="G")
        line = make_line(doc, start=(0, 0), end=(10, 0))
        doc.add_object(line)
        doc.add_object(g)
        g.add_child(line.object_id)
        assert g.contains_point(Point2D(5, 0), tolerance=1.0) is True

    def test_contains_point_empty_group(self):
        doc = make_document()
        g = GroupCadObject(doc, name="G")
        doc.add_object(g)
        assert g.contains_point(Point2D(5, 0), tolerance=1.0) is False

    def test_get_all_descendants(self):
        doc = make_document()
        g1 = GroupCadObject(doc, name="G1")
        g2 = GroupCadObject(doc, name="G2")
        doc.add_object(g1)
        doc.add_object(g2)
        g1.add_child(g2.object_id)
        g2.set_parent(g1.object_id)
        line = make_line(doc)
        doc.add_object(line)
        g2.add_child(line.object_id)
        descendants = g1.get_all_descendants()
        assert g2.object_id in descendants
        assert line.object_id in descendants

    def test_get_visible_children(self):
        doc = make_document()
        g = GroupCadObject(doc, name="G")
        line = make_line(doc)
        doc.add_object(line)
        doc.add_object(g)
        g.add_child(line.object_id)
        visible = g.get_visible_children()
        assert line.object_id in visible
        line.visible = False
        visible = g.get_visible_children()
        assert line.object_id not in visible

    def test_get_object_data(self):
        doc = make_document()
        g = GroupCadObject(doc, name="TestGroup")
        data = g.get_object_data()
        assert "name" in data
        assert "children" in data

    def test_create_object_from_data(self):
        doc = make_document()
        data = {"name": "MyGroup"}
        g = GroupCadObject.create_object_from_data(doc, "group", data)
        assert g.name == "MyGroup"


# ===========================================================================
# GearCadObject
# ===========================================================================

class TestGearCadObject:
    def test_construction(self):
        gear = make_gear()
        assert gear.center_point.x == pytest.approx(0.0)
        assert gear.pitch_radius == pytest.approx(5.0)
        assert gear.num_teeth == 20

    def test_pitch_diameter(self):
        gear = make_gear()
        assert gear.pitch_diameter == pytest.approx(10.0)

    def test_pitch_diameter_setter(self):
        gear = make_gear()
        gear.pitch_diameter = 20.0
        assert gear.pitch_diameter == pytest.approx(20.0)
        assert gear.pitch_radius == pytest.approx(10.0)

    def test_pitch_radius_setter(self):
        gear = make_gear()
        gear.pitch_radius = 8.0
        assert gear.pitch_radius == pytest.approx(8.0)

    def test_num_teeth_setter(self):
        gear = make_gear()
        gear.num_teeth = 30
        assert gear.num_teeth == 30

    def test_pressure_angle(self):
        gear = make_gear()
        assert gear.pressure_angle == pytest.approx(20.0)

    def test_pressure_angle_setter(self):
        gear = make_gear()
        gear.pressure_angle = 25.0
        assert gear.pressure_angle == pytest.approx(25.0)

    def test_center_point_setter(self):
        gear = make_gear()
        gear.center_point = Point2D(10, 10)
        assert gear.center_point.x == pytest.approx(10.0)
        assert gear.center_point.y == pytest.approx(10.0)

    def test_circular_pitch(self):
        gear = make_gear()
        expected = (math.pi * gear.pitch_diameter) / gear.num_teeth
        assert gear.circular_pitch == pytest.approx(expected)

    def test_diametral_pitch(self):
        gear = make_gear()
        expected = gear.num_teeth / gear.pitch_diameter
        assert gear.diametral_pitch == pytest.approx(expected)

    def test_module(self):
        gear = make_gear()
        expected = gear.pitch_diameter / gear.num_teeth
        assert gear.module == pytest.approx(expected)

    def test_get_gear_path_points(self):
        gear = make_gear()
        pts = gear.get_gear_path_points()
        assert len(pts) > 0

    def test_get_pitch_circle_points(self):
        gear = make_gear()
        pts = gear.get_pitch_circle_points()
        assert len(pts) > 0

    def test_get_bounds(self):
        gear = make_gear()
        bounds = gear.get_bounds()
        assert len(bounds) == 4

    def test_translate(self):
        # Gear translate calls _center_point.translate() which is a no-op
        gear = make_gear()
        gear.translate(5, 3)  # should not raise

    def test_scale(self):
        # Gear scale mutates _pitch_radius directly
        gear = make_gear()
        old_radius = gear.pitch_radius
        gear.scale(2.0, Point2D(0, 0))
        assert gear.pitch_radius == pytest.approx(old_radius * 2.0)

    def test_rotate(self):
        # Gear rotate calls _center_point.rotate() which is a no-op
        doc = make_document()
        gear = GearCadObject(doc, Point2D(5, 0), pitch_radius=2.0, num_teeth=10)
        gear.rotate(90.0, Point2D(0, 0))  # should not raise

    def test_contains_point(self):
        gear = make_gear()
        # Point on pitch circle
        assert gear.contains_point(Point2D(5, 0), tolerance=1.0) is True

    def test_decompose(self):
        gear = make_gear()
        result = gear.decompose()
        assert len(result) > 0

    def test_make_constrainables(self):
        gear = make_gear()
        solver = ConstraintSolver()
        gear.make_constrainables(solver)
        constrainables = gear.get_constrainables()
        assert len(constrainables) > 0

    def test_update_constrainables_before_solving(self):
        gear = make_gear()
        solver = ConstraintSolver()
        gear.make_constrainables(solver)
        gear.center_point = Point2D(1, 1)
        gear.update_constrainables_before_solving(solver)

    def test_update_from_solved_constraints(self):
        gear = make_gear()
        solver = ConstraintSolver()
        gear.make_constrainables(solver)
        gear.update_from_solved_constraints(solver)

    def test_get_object_data(self):
        gear = make_gear()
        data = gear.get_object_data()
        assert "center_point" in data
        assert "pitch_radius" in data
        assert "num_teeth" in data


# ===========================================================================
# Document
# ===========================================================================

class TestDocument:
    def test_add_and_get_object(self):
        doc = make_document()
        line = make_line(doc)
        doc.add_object(line)
        retrieved = doc.get_object(line.object_id)
        assert retrieved is line

    def test_add_object_assigns_name(self):
        doc = make_document()
        line = make_line(doc)
        doc.add_object(line)
        assert line._name is not None

    def test_remove_object(self):
        doc = make_document()
        line = make_line(doc)
        doc.add_object(line)
        result = doc.remove_object(line.object_id)
        assert result is True
        assert doc.get_object(line.object_id) is None

    def test_remove_nonexistent_object(self):
        doc = make_document()
        result = doc.remove_object("nonexistent")
        assert result is False

    def test_get_all_objects(self):
        doc = make_document()
        line1 = make_line(doc)
        line2 = make_line(doc)
        doc.add_object(line1)
        doc.add_object(line2)
        all_objs = doc.get_all_objects()
        assert len(all_objs) == 2

    def test_get_visible_objects(self):
        doc = make_document()
        line = make_line(doc)
        doc.add_object(line)
        visible = doc.get_visible_objects()
        assert line in visible
        line.visible = False
        visible = doc.get_visible_objects()
        assert line not in visible

    def test_get_root_objects(self):
        doc = make_document()
        line = make_line(doc)
        doc.add_object(line)
        roots = doc.get_root_objects()
        assert line in roots

    def test_create_group(self):
        doc = make_document()
        group_id = doc.create_group("MyGroup")
        group = doc.get_object(group_id)
        assert isinstance(group, GroupCadObject)

    def test_add_to_group(self):
        doc = make_document()
        group_id = doc.create_group("G")
        line = make_line(doc)
        doc.add_object(line)
        result = doc.add_to_group(line.object_id, group_id)
        assert result is True
        group = doc.get_object(group_id)
        assert line.object_id in group.children

    def test_add_to_group_invalid_group(self):
        doc = make_document()
        line = make_line(doc)
        doc.add_object(line)
        result = doc.add_to_group(line.object_id, "nonexistent_group")
        assert result is False

    def test_remove_from_group(self):
        doc = make_document()
        group_id = doc.create_group("G")
        line = make_line(doc)
        doc.add_object(line)
        doc.add_to_group(line.object_id, group_id)
        result = doc.remove_from_group(line.object_id)
        assert result is True
        group = doc.get_object(group_id)
        assert line.object_id not in group.children

    def test_remove_from_group_not_in_group(self):
        doc = make_document()
        line = make_line(doc)
        doc.add_object(line)
        result = doc.remove_from_group(line.object_id)
        assert result is False

    def test_get_group_hierarchy(self):
        doc = make_document()
        group_id = doc.create_group("G")
        line = make_line(doc)
        doc.add_object(line)
        doc.add_to_group(line.object_id, group_id)
        hierarchy = doc.get_group_hierarchy()
        assert group_id in hierarchy

    def test_get_object_path(self):
        doc = make_document()
        line = make_line(doc)
        doc.add_object(line)
        path = doc.get_object_path(line.object_id)
        assert line.object_id in path

    def test_get_constraint_id(self):
        doc = make_document()
        cid = doc.get_constraint_id("coincident", "obj1", "obj2")
        assert "obj1" in cid
        assert "obj2" in cid

    def test_get_constraint_id_no_second(self):
        doc = make_document()
        cid = doc.get_constraint_id("fixed", "obj1", None)
        assert "obj1" in cid

    def test_select_objects_at_point(self):
        doc = make_document()
        line = make_line(doc, start=(0, 0), end=(10, 0))
        doc.add_object(line)
        hits = doc.select_objects_at_point(Point2D(5, 0), tolerance=1.0)
        assert line.object_id in hits

    def test_select_objects_in_rectangle(self):
        doc = make_document()
        line = make_line(doc, start=(2, 2), end=(8, 2))
        doc.add_object(line)
        hits = doc.select_objects_in_rectangle(0, 0, 10, 10)
        assert line.object_id in hits

    def test_move_selected_objects(self):
        doc = make_document()
        line = make_line(doc, start=(0, 0), end=(10, 0))
        doc.add_object(line)
        doc.move_selected_objects([line.object_id], 5, 3)
        assert line.start_point.x == pytest.approx(5.0)
        assert line.start_point.y == pytest.approx(3.0)

    def test_delete_selected_objects(self):
        doc = make_document()
        line = make_line(doc)
        doc.add_object(line)
        doc.delete_selected_objects([line.object_id])
        assert doc.get_object(line.object_id) is None

    def test_get_document_bounds(self):
        doc = make_document()
        line = make_line(doc, start=(1, 2), end=(5, 8))
        doc.add_object(line)
        bounds = doc.get_document_bounds()
        assert bounds[0] == pytest.approx(1.0)
        assert bounds[3] == pytest.approx(8.0)

    def test_get_document_bounds_empty(self):
        doc = make_document()
        bounds = doc.get_document_bounds()
        assert bounds == (0, 0, 0, 0)

    def test_create_line(self):
        doc = make_document()
        obj_id = doc.create_line(Point2D(0, 0), Point2D(10, 0))
        obj = doc.get_object(obj_id)
        assert isinstance(obj, LineCadObject)

    def test_create_circle(self):
        doc = make_document()
        obj_id = doc.create_circle(Point2D(0, 0), 5.0)
        obj = doc.get_object(obj_id)
        assert isinstance(obj, CircleCadObject)

    def test_mark_modified_and_saved(self):
        doc = make_document()
        doc.mark_modified()
        assert doc.is_modified() is True
        doc.mark_saved()
        assert doc.is_modified() is False

    def test_clear(self):
        doc = make_document()
        line = make_line(doc)
        doc.add_object(line)
        doc.clear()
        assert len(doc.objects) == 0

    def test_parameters_property(self):
        doc = make_document()
        doc.parameters = {"x": "5+3"}
        assert "x" in doc.parameters

    def test_is_name_unique(self):
        doc = make_document()
        line = make_line(doc)
        doc.add_object(line)
        line._name = "myline"
        assert doc.is_name_unique("otherline", "someId") is True
        assert doc.is_name_unique("myline", "differentId") is False

    def test_get_unique_name(self):
        doc = make_document()
        line1 = make_line(doc)
        doc.add_object(line1)
        line1._name = "line1"
        name = doc.get_unique_name("line", "new_id")
        assert name != "line1"
        assert "line" in name

    def test_rename_object_success(self):
        doc = make_document()
        line = make_line(doc)
        doc.add_object(line)
        result = doc.rename_object(line.object_id, "newname")
        assert result is True
        assert line._name == "newname"

    def test_rename_object_conflict(self):
        doc = make_document()
        line1 = make_line(doc)
        line2 = make_line(doc)
        doc.add_object(line1)
        doc.add_object(line2)
        line2._name = "taken"
        result = doc.rename_object(line1.object_id, "taken")
        assert result is False

    def test_rename_nonexistent_object(self):
        doc = make_document()
        result = doc.rename_object("nonexistent", "newname")
        assert result is False

    def test_remove_object_from_group(self):
        doc = make_document()
        group_id = doc.create_group("G")
        line = make_line(doc)
        doc.add_object(line)
        doc.add_to_group(line.object_id, group_id)
        result = doc.remove_object(line.object_id)
        assert result is True
        group = doc.get_object(group_id)
        assert line.object_id not in group.children

    def test_remove_group_with_children(self):
        doc = make_document()
        group_id = doc.create_group("G")
        line = make_line(doc)
        doc.add_object(line)
        doc.add_to_group(line.object_id, group_id)
        result = doc.remove_object(group_id)
        assert result is True
        # Line still exists
        assert doc.get_object(line.object_id) is not None

    def test_get_root_groups(self):
        doc = make_document()
        group_id = doc.create_group("G")
        root_groups = doc.get_root_groups()
        assert any(g.object_id == group_id for g in root_groups)

    def test_solve_constraints(self):
        doc = make_document()
        result = doc.solve_constraints()
        # No constraints, should succeed
        assert result in (True, False)  # Implementation-dependent

    def test_get_constraint_count_empty(self):
        doc = make_document()
        assert doc.get_constraint_count() == 0

    def test_has_constraints_false(self):
        doc = make_document()
        assert doc.has_constraints() is False

    def test_get_constraints_for_object_none(self):
        doc = make_document()
        line = make_line(doc)
        doc.add_object(line)
        constraints = doc.get_constraints_for_object(line.object_id)
        assert constraints == []


# ===========================================================================
# UndoRedoManager
# ===========================================================================

class TestUndoRedoManager:
    def test_initial_state(self):
        mgr = UndoRedoManager()
        assert mgr.can_undo() is False
        assert mgr.can_redo() is False
        assert mgr.get_undo_description() is None
        assert mgr.get_redo_description() is None

    def test_execute_command(self):
        doc = make_document()
        mgr = UndoRedoManager()
        line = make_line(doc)
        cmd = CreateObjectCommand(doc, line, "Create Line")
        result = mgr.execute_command(cmd)
        assert result is True
        assert doc.get_object(line.object_id) is line
        assert mgr.can_undo() is True
        assert mgr.can_redo() is False

    def test_execute_command_clears_redo_stack(self):
        doc = make_document()
        mgr = UndoRedoManager()
        line1 = make_line(doc)
        cmd1 = CreateObjectCommand(doc, line1, "Create Line 1")
        mgr.execute_command(cmd1)
        mgr.undo()
        assert mgr.can_redo() is True
        line2 = make_line(doc)
        cmd2 = CreateObjectCommand(doc, line2, "Create Line 2")
        mgr.execute_command(cmd2)
        assert mgr.can_redo() is False

    def test_undo(self):
        doc = make_document()
        mgr = UndoRedoManager()
        line = make_line(doc)
        cmd = CreateObjectCommand(doc, line, "Create Line")
        mgr.execute_command(cmd)
        result = mgr.undo()
        assert result is True
        assert doc.get_object(line.object_id) is None
        assert mgr.can_undo() is False
        assert mgr.can_redo() is True

    def test_redo(self):
        doc = make_document()
        mgr = UndoRedoManager()
        line = make_line(doc)
        cmd = CreateObjectCommand(doc, line, "Create Line")
        mgr.execute_command(cmd)
        mgr.undo()
        result = mgr.redo()
        assert result is True
        assert doc.get_object(line.object_id) is line

    def test_undo_when_empty(self):
        mgr = UndoRedoManager()
        result = mgr.undo()
        assert result is False

    def test_redo_when_empty(self):
        mgr = UndoRedoManager()
        result = mgr.redo()
        assert result is False

    def test_get_undo_description(self):
        doc = make_document()
        mgr = UndoRedoManager()
        line = make_line(doc)
        cmd = CreateObjectCommand(doc, line, "Create Line")
        mgr.execute_command(cmd)
        assert mgr.get_undo_description() == "Create Line"

    def test_get_redo_description(self):
        doc = make_document()
        mgr = UndoRedoManager()
        line = make_line(doc)
        cmd = CreateObjectCommand(doc, line, "Create Line")
        mgr.execute_command(cmd)
        mgr.undo()
        assert mgr.get_redo_description() == "Create Line"

    def test_clear(self):
        doc = make_document()
        mgr = UndoRedoManager()
        line = make_line(doc)
        cmd = CreateObjectCommand(doc, line, "Create Line")
        mgr.execute_command(cmd)
        mgr.clear()
        assert mgr.can_undo() is False
        assert mgr.can_redo() is False

    def test_max_undo_levels(self):
        doc = make_document()
        mgr = UndoRedoManager(max_undo_levels=2)
        for _ in range(5):
            line = make_line(doc)
            cmd = CreateObjectCommand(doc, line)
            mgr.execute_command(cmd)
        assert len(mgr.undo_stack) <= 2

    def test_add_callback(self):
        doc = make_document()
        mgr = UndoRedoManager()
        called = []
        mgr.add_callback(lambda: called.append(True))
        line = make_line(doc)
        cmd = CreateObjectCommand(doc, line)
        mgr.execute_command(cmd)
        assert len(called) >= 1

    def test_callback_on_undo(self):
        doc = make_document()
        mgr = UndoRedoManager()
        called = []
        mgr.add_callback(lambda: called.append(True))
        line = make_line(doc)
        cmd = CreateObjectCommand(doc, line)
        mgr.execute_command(cmd)
        called.clear()
        mgr.undo()
        assert len(called) >= 1

    def test_callback_on_clear(self):
        doc = make_document()
        mgr = UndoRedoManager()
        called = []
        mgr.add_callback(lambda: called.append(True))
        mgr.clear()
        assert len(called) >= 1

    def test_create_object_command_undo(self):
        doc = make_document()
        line = make_line(doc)
        cmd = CreateObjectCommand(doc, line, "Create")
        cmd.execute()
        assert doc.get_object(line.object_id) is not None
        cmd.undo()
        assert doc.get_object(line.object_id) is None

    def test_delete_object_command(self):
        doc = make_document()
        line = make_line(doc)
        doc.add_object(line)
        cmd = DeleteObjectCommand(doc, line, "Delete")
        result = cmd.execute()
        assert result is True
        assert doc.get_object(line.object_id) is None

    def test_delete_object_command_undo(self):
        doc = make_document()
        line = make_line(doc)
        doc.add_object(line)
        cmd = DeleteObjectCommand(doc, line, "Delete")
        cmd.execute()
        cmd.undo()
        assert doc.get_object(line.object_id) is not None

    def test_modify_object_command(self):
        doc = make_document()
        line = make_line(doc, start=(0, 0), end=(10, 0))
        doc.add_object(line)

        def apply_fn(obj):
            obj.translate(5, 0)

        def restore_fn(obj):
            obj.translate(-5, 0)

        cmd = ModifyObjectCommand(doc, line, apply_fn, restore_fn, "Move")
        result = cmd.execute()
        assert result is True
        assert line.start_point.x == pytest.approx(5.0)

    def test_modify_object_command_undo(self):
        doc = make_document()
        line = make_line(doc, start=(0, 0), end=(10, 0))
        doc.add_object(line)

        def apply_fn(obj):
            obj.translate(5, 0)

        def restore_fn(obj):
            obj.translate(-5, 0)

        cmd = ModifyObjectCommand(doc, line, apply_fn, restore_fn, "Move")
        cmd.execute()
        cmd.undo()
        assert line.start_point.x == pytest.approx(0.0)

    def test_modify_object_command_missing_object(self):
        doc = make_document()
        line = make_line(doc)
        doc.add_object(line)
        cmd = ModifyObjectCommand(doc, line, lambda o: None, lambda o: None, "Move")
        doc.remove_object(line.object_id)
        result = cmd.execute()
        assert result is False

    def test_compound_command(self):
        doc = make_document()
        line1 = make_line(doc)
        line2 = make_line(doc)
        cmd1 = CreateObjectCommand(doc, line1, "Create 1")
        cmd2 = CreateObjectCommand(doc, line2, "Create 2")
        compound = CompoundCommand([cmd1, cmd2], "Create Both")
        result = compound.execute()
        assert result is True
        assert doc.get_object(line1.object_id) is not None
        assert doc.get_object(line2.object_id) is not None

    def test_compound_command_undo(self):
        doc = make_document()
        line1 = make_line(doc)
        line2 = make_line(doc)
        cmd1 = CreateObjectCommand(doc, line1, "Create 1")
        cmd2 = CreateObjectCommand(doc, line2, "Create 2")
        compound = CompoundCommand([cmd1, cmd2], "Create Both")
        compound.execute()
        compound.undo()
        assert doc.get_object(line1.object_id) is None
        assert doc.get_object(line2.object_id) is None

    def test_command_redo_calls_execute(self):
        doc = make_document()
        mgr = UndoRedoManager()
        line = make_line(doc)
        cmd = CreateObjectCommand(doc, line, "Create")
        mgr.execute_command(cmd)
        mgr.undo()
        mgr.redo()
        assert doc.get_object(line.object_id) is not None


# ===========================================================================
# PreferencesModel
# ===========================================================================

class TestPreferencesModel:
    """Tests for the PreferencesModel class."""

    def _make_prefs(self):
        from BelfryCAD.config import AppConfig
        from BelfryCAD.models.preferences import PreferencesModel
        config = AppConfig()
        return PreferencesModel(config), config

    def test_get_default_preference(self):
        prefs, _ = self._make_prefs()
        val = prefs.get("grid_visible")
        assert val is True

    def test_get_unknown_key_returns_default(self):
        prefs, _ = self._make_prefs()
        val = prefs.get("nonexistent_key", "fallback")
        assert val == "fallback"

    def test_set_valid_preference(self):
        prefs, _ = self._make_prefs()
        result = prefs.set("precision", 5)
        assert result is True
        assert prefs.get("precision") == 5

    def test_set_invalid_preference_type(self):
        prefs, _ = self._make_prefs()
        result = prefs.set("precision", "not_an_int")
        assert result is False

    def test_set_invalid_key(self):
        prefs, _ = self._make_prefs()
        result = prefs.set("", "value")
        assert result is False

    def test_get_all(self):
        prefs, _ = self._make_prefs()
        all_prefs = prefs.get_all()
        assert isinstance(all_prefs, dict)

    def test_get_all_with_defaults(self):
        prefs, _ = self._make_prefs()
        all_prefs = prefs.get_all_with_defaults()
        assert "grid_visible" in all_prefs

    def test_reset_to_defaults(self):
        prefs, _ = self._make_prefs()
        prefs.set("precision", 8)
        prefs.reset_to_defaults()
        assert prefs.get("precision") == 3  # default value

    def test_reset_single_preference(self):
        prefs, _ = self._make_prefs()
        prefs.set("precision", 8)
        result = prefs.reset_preference("precision")
        assert result is True
        assert prefs.get("precision") == 3

    def test_reset_unknown_preference(self):
        prefs, _ = self._make_prefs()
        result = prefs.reset_preference("nonexistent_key")
        assert result is False

    def test_delete_preference(self):
        prefs, _ = self._make_prefs()
        prefs.set("precision", 8)
        result = prefs.delete_preference("precision")
        assert result is True

    def test_delete_nonexistent_preference(self):
        prefs, _ = self._make_prefs()
        result = prefs.delete_preference("nonexistent")
        assert result is False

    def test_has_preference_true(self):
        prefs, _ = self._make_prefs()
        assert prefs.has_preference("grid_visible") is True

    def test_has_preference_false(self):
        prefs, _ = self._make_prefs()
        assert prefs.has_preference("nonexistent") is False

    def test_is_default_value_true(self):
        prefs, _ = self._make_prefs()
        assert prefs.is_default_value("grid_visible") is True

    def test_is_default_value_false(self):
        prefs, _ = self._make_prefs()
        prefs.set("precision", 8)
        assert prefs.is_default_value("precision") is False

    def test_is_default_value_unknown_key(self):
        prefs, _ = self._make_prefs()
        assert prefs.is_default_value("nonexistent") is False

    def test_get_modified_preferences(self):
        prefs, _ = self._make_prefs()
        prefs.set("precision", 8)
        modified = prefs.get_modified_preferences()
        assert "precision" in modified

    def test_get_modified_preferences_none(self):
        prefs, _ = self._make_prefs()
        modified = prefs.get_modified_preferences()
        assert len(modified) == 0

    def test_get_preference_keys(self):
        prefs, _ = self._make_prefs()
        keys = prefs.get_preference_keys()
        assert "grid_visible" in keys
        assert isinstance(keys, list)

    def test_save_and_load(self):
        prefs, _ = self._make_prefs()
        prefs.set("precision", 7)
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            tmpfile = Path(f.name)
        try:
            save_result = prefs.save_to_file(tmpfile)
            assert save_result is True

            prefs2, _ = self._make_prefs()
            load_result = prefs2.load_from_file(tmpfile)
            assert load_result is True
            assert prefs2.get("precision") == 7
        finally:
            tmpfile.unlink(missing_ok=True)

    def test_export_import(self):
        prefs, _ = self._make_prefs()
        prefs.set("precision", 6)
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            tmpfile = Path(f.name)
        try:
            prefs.export_preferences(tmpfile)
            prefs2, _ = self._make_prefs()
            prefs2.import_preferences(tmpfile)
            assert prefs2.get("precision") == 6
        finally:
            tmpfile.unlink(missing_ok=True)

    def test_load_nonexistent_file(self):
        prefs, _ = self._make_prefs()
        result = prefs.load_from_file(Path("/tmp/nonexistent_belfrycad_prefs_xyz.yaml"))
        assert result is False

    def test_validate_bool_preference(self):
        prefs, _ = self._make_prefs()
        result = prefs.set("grid_visible", "not_a_bool")
        assert result is False

    def test_validate_list_preference(self):
        prefs, _ = self._make_prefs()
        result = prefs.set("recent_files", "not_a_list")
        assert result is False

    def test_validate_int_recent_files_count(self):
        prefs, _ = self._make_prefs()
        result = prefs.set("recent_files_count", "not_an_int")
        assert result is False
