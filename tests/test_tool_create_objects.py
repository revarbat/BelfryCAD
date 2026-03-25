"""Tests for tool create_object() methods, helper math, definitions, and state management."""

import math
import pytest

from BelfryCAD.models.document import Document
from BelfryCAD.cad_geometry import Point2D
from BelfryCAD.tools.base import CadTool, ToolState, ToolCategory, ToolDefinition, ToolManager
from BelfryCAD.tools.line import LineTool, LineMPTool
from BelfryCAD.tools.circle import CircleTool, Circle2PTTool, Circle3PTTool
from BelfryCAD.tools.arcs import ArcCenterTool, Arc3PointTool, ArcTangentTool
from BelfryCAD.tools.ellipse import EllipseCenterTool, EllipseDiagonalTool
from BelfryCAD.tools.bezier import BezierTool
from BelfryCAD.tools.polygon import RectangleTool
from BelfryCAD.models.cad_objects.line_cad_object import LineCadObject
from BelfryCAD.models.cad_objects.circle_cad_object import CircleCadObject
from BelfryCAD.models.cad_objects.arc_cad_object import ArcCadObject
from BelfryCAD.models.cad_objects.ellipse_cad_object import EllipseCadObject
from BelfryCAD.models.cad_objects.cubic_bezier_cad_object import CubicBezierCadObject
from BelfryCAD.models.cad_objects.rectangle_cad_object import RectangleCadObject


# ---------------------------------------------------------------------------
# Shared test infrastructure
# ---------------------------------------------------------------------------

class MockScene:
    """Minimal scene mock that avoids Qt scene method calls."""
    def views(self):
        return []


class MockDocumentWindow:
    def get_scene(self):
        return MockScene()

    def get_dpcm(self):
        return 96.0


class MockPreferences:
    def get(self, key, default=None):
        return default


@pytest.fixture
def doc():
    return Document()


@pytest.fixture
def window():
    return MockDocumentWindow()


@pytest.fixture
def prefs():
    return MockPreferences()


# ---------------------------------------------------------------------------
# LineTool
# ---------------------------------------------------------------------------

class TestLineTool:
    def test_definitions(self, window, doc, prefs):
        tool = LineTool(window, doc, prefs)
        assert len(tool.definitions) == 1
        defn = tool.definitions[0]
        assert defn.token == "LINE"
        assert defn.is_creator
        assert defn.secondary_key == "L"
        assert defn.category == ToolCategory.LINES

    def test_create_object(self, window, doc, prefs):
        tool = LineTool(window, doc, prefs)
        tool.points = [Point2D(0, 0), Point2D(10, 5)]
        obj = tool.create_object()
        assert isinstance(obj, LineCadObject)
        assert obj.start_point == Point2D(0, 0)
        assert obj.end_point == Point2D(10, 5)

    def test_create_object_uses_preferences(self, window, doc, prefs):
        class ColorPrefs:
            def get(self, key, default=None):
                return {"default_color": "red", "default_line_width": 2.0}.get(key, default)

        tool = LineTool(window, doc, ColorPrefs())
        tool.points = [Point2D(0, 0), Point2D(1, 1)]
        obj = tool.create_object()
        assert obj.color == "red"
        assert obj.line_width == 2.0

    def test_create_object_too_few_points(self, window, doc, prefs):
        tool = LineTool(window, doc, prefs)
        tool.points = [Point2D(0, 0)]
        assert tool.create_object() is None

    def test_create_object_no_points(self, window, doc, prefs):
        tool = LineTool(window, doc, prefs)
        assert tool.create_object() is None

    def test_cancel_resets_state(self, window, doc, prefs):
        tool = LineTool(window, doc, prefs)
        tool.state = ToolState.DRAWING
        tool.points = [Point2D(1, 2)]
        tool.cancel()
        assert tool.state == ToolState.ACTIVE
        assert tool.points == []

    def test_get_snap_point_no_snaps(self, window, doc, prefs):
        tool = LineTool(window, doc, prefs)
        pt = tool.get_snap_point(3.5, 7.2)
        assert pt == Point2D(3.5, 7.2)


# ---------------------------------------------------------------------------
# LineMPTool
# ---------------------------------------------------------------------------

class TestLineMPTool:
    def test_definitions(self, window, doc, prefs):
        tool = LineMPTool(window, doc, prefs)
        assert len(tool.definitions) == 2
        tokens = {d.token for d in tool.definitions}
        assert "LINEMP" in tokens
        assert "LINEMP21" in tokens

    def test_create_object_midpoint_variant(self, window, doc, prefs):
        """points[0]=midpoint, points[1]=endpoint → line extends symmetrically."""
        tool = LineMPTool(window, doc, prefs)
        # midpt=(5,0), endpoint=(10,0) → start=(10,0), end=(0,0)
        tool.points = [Point2D(5, 0), Point2D(10, 0)]
        obj = tool.create_object()
        assert isinstance(obj, LineCadObject)
        assert obj.start_point == Point2D(10, 0)
        assert obj.end_point == Point2D(0, 0)

    def test_create_object_midpoint_is_actual_midpoint(self, window, doc, prefs):
        tool = LineMPTool(window, doc, prefs)
        midpt = Point2D(5, 5)
        endpt = Point2D(8, 9)
        tool.points = [midpt, endpt]
        obj = tool.create_object()
        # endpt of created line = midpt + (midpt - endpt)
        expected_end = Point2D(2, 1)
        assert abs(obj.end_point.x - expected_end.x) < 1e-9
        assert abs(obj.end_point.y - expected_end.y) < 1e-9

    def test_create_object_too_few_points(self, window, doc, prefs):
        tool = LineMPTool(window, doc, prefs)
        tool.points = [Point2D(0, 0)]
        assert tool.create_object() is None


# ---------------------------------------------------------------------------
# CircleTool
# ---------------------------------------------------------------------------

class TestCircleTool:
    def test_definitions(self, window, doc, prefs):
        tool = CircleTool(window, doc, prefs)
        assert len(tool.definitions) == 1
        defn = tool.definitions[0]
        assert defn.token == "CIRCLE"
        assert defn.is_creator
        assert defn.secondary_key == "C"

    def test_create_object(self, window, doc, prefs):
        tool = CircleTool(window, doc, prefs)
        tool.points = [Point2D(0, 0), Point2D(5, 0)]
        obj = tool.create_object()
        assert isinstance(obj, CircleCadObject)
        assert obj.center_point == Point2D(0, 0)
        assert abs(obj.radius - 5.0) < 1e-9

    def test_create_object_diagonal_radius(self, window, doc, prefs):
        tool = CircleTool(window, doc, prefs)
        tool.points = [Point2D(0, 0), Point2D(3, 4)]
        obj = tool.create_object()
        assert abs(obj.radius - 5.0) < 1e-9

    def test_create_object_too_few_points(self, window, doc, prefs):
        tool = CircleTool(window, doc, prefs)
        tool.points = [Point2D(0, 0)]
        assert tool.create_object() is None

    def test_create_object_no_points(self, window, doc, prefs):
        tool = CircleTool(window, doc, prefs)
        assert tool.create_object() is None


# ---------------------------------------------------------------------------
# Circle2PTTool
# ---------------------------------------------------------------------------

class TestCircle2PTTool:
    def test_definitions(self, window, doc, prefs):
        tool = Circle2PTTool(window, doc, prefs)
        assert len(tool.definitions) == 1
        assert tool.definitions[0].token == "CIRCLE2PT"

    def test_create_object(self, window, doc, prefs):
        tool = Circle2PTTool(window, doc, prefs)
        tool.points = [Point2D(-5, 0), Point2D(5, 0)]
        obj = tool.create_object()
        assert isinstance(obj, CircleCadObject)
        assert abs(obj.center_point.x) < 1e-9
        assert abs(obj.center_point.y) < 1e-9
        assert abs(obj.radius - 5.0) < 1e-9

    def test_create_object_vertical_diameter(self, window, doc, prefs):
        tool = Circle2PTTool(window, doc, prefs)
        tool.points = [Point2D(0, -3), Point2D(0, 3)]
        obj = tool.create_object()
        assert abs(obj.center_point.x) < 1e-9
        assert abs(obj.center_point.y) < 1e-9
        assert abs(obj.radius - 3.0) < 1e-9

    def test_create_object_too_few_points(self, window, doc, prefs):
        tool = Circle2PTTool(window, doc, prefs)
        tool.points = [Point2D(0, 0)]
        assert tool.create_object() is None


# ---------------------------------------------------------------------------
# Circle3PTTool
# ---------------------------------------------------------------------------

class TestCircle3PTTool:
    def test_definitions(self, window, doc, prefs):
        tool = Circle3PTTool(window, doc, prefs)
        assert len(tool.definitions) == 1
        assert tool.definitions[0].token == "CIRCLE3PT"

    def test_create_object(self, window, doc, prefs):
        # Three points on circle centered at (0,0) radius 5
        tool = Circle3PTTool(window, doc, prefs)
        tool.points = [Point2D(5, 0), Point2D(0, 5), Point2D(-5, 0)]
        obj = tool.create_object()
        assert isinstance(obj, CircleCadObject)
        assert abs(obj.radius - 5.0) < 0.01

    def test_create_object_collinear_raises(self, window, doc, prefs):
        tool = Circle3PTTool(window, doc, prefs)
        tool.points = [Point2D(0, 0), Point2D(1, 0), Point2D(2, 0)]
        with pytest.raises(ValueError):
            tool.create_object()

    def test_create_object_too_few_points(self, window, doc, prefs):
        tool = Circle3PTTool(window, doc, prefs)
        tool.points = [Point2D(0, 0), Point2D(1, 1)]
        assert tool.create_object() is None

    def test_calculate_circle_horizontal_chord(self, window, doc, prefs):
        """_calculate_circle_from_3_points with horizontal p1-p3 chord."""
        tool = Circle3PTTool(window, doc, prefs)
        p1 = Point2D(5, 0)
        p2 = Point2D(0, 5)
        p3 = Point2D(-5, 0)
        result = tool._calculate_circle_from_3_points(p1, p2, p3)
        assert result is not None
        center, radius = result
        assert abs(radius - 5.0) < 0.01

    def test_calculate_circle_vertical_chord(self, window, doc, prefs):
        """_calculate_circle_from_3_points with vertical p2-p3 chord."""
        tool = Circle3PTTool(window, doc, prefs)
        p1 = Point2D(0, 5)
        p2 = Point2D(5, 0)
        p3 = Point2D(0, -5)
        result = tool._calculate_circle_from_3_points(p1, p2, p3)
        assert result is not None
        center, radius = result
        assert abs(radius - 5.0) < 0.01

    def test_calculate_circle_collinear_returns_none(self, window, doc, prefs):
        tool = Circle3PTTool(window, doc, prefs)
        result = tool._calculate_circle_from_3_points(
            Point2D(0, 0), Point2D(1, 0), Point2D(2, 0)
        )
        assert result is None


# ---------------------------------------------------------------------------
# ArcCenterTool
# ---------------------------------------------------------------------------

class TestArcCenterTool:
    def test_definitions(self, window, doc, prefs):
        tool = ArcCenterTool(window, doc, prefs)
        assert len(tool.definitions) == 1
        defn = tool.definitions[0]
        assert defn.token == "ARCCTR"
        assert defn.is_creator

    def test_create_object(self, window, doc, prefs):
        tool = ArcCenterTool(window, doc, prefs)
        # center=(0,0), start=(5,0)→0°, end=(0,5)→90°, span=90°
        tool.points = [Point2D(0, 0), Point2D(5, 0), Point2D(0, 5)]
        obj = tool.create_object()
        assert isinstance(obj, ArcCadObject)
        assert obj.center_point == Point2D(0, 0)
        assert abs(obj.radius - 5.0) < 1e-9
        assert abs(obj.start_degrees - 0.0) < 1e-6
        assert abs(obj.span_degrees - 90.0) < 1e-6

    def test_create_object_span_wraps_around(self, window, doc, prefs):
        """When end angle < start angle the span should be positive via +360."""
        tool = ArcCenterTool(window, doc, prefs)
        # start=(0,5)→90°, end=(5,0)→0° → raw span=-90 → normalised=270
        tool.points = [Point2D(0, 0), Point2D(0, 5), Point2D(5, 0)]
        obj = tool.create_object()
        assert isinstance(obj, ArcCadObject)
        assert obj.span_degrees > 0

    def test_create_object_identical_start_end_returns_none(self, window, doc, prefs):
        tool = ArcCenterTool(window, doc, prefs)
        tool.points = [Point2D(0, 0), Point2D(5, 0), Point2D(5, 0)]
        assert tool.create_object() is None

    def test_create_object_center_equals_start_returns_none(self, window, doc, prefs):
        tool = ArcCenterTool(window, doc, prefs)
        tool.points = [Point2D(0, 0), Point2D(0, 0), Point2D(5, 0)]
        assert tool.create_object() is None

    def test_create_object_too_few_points(self, window, doc, prefs):
        tool = ArcCenterTool(window, doc, prefs)
        tool.points = [Point2D(0, 0), Point2D(5, 0)]
        assert tool.create_object() is None


# ---------------------------------------------------------------------------
# Arc3PointTool
# ---------------------------------------------------------------------------

class TestArc3PointTool:
    def test_definitions(self, window, doc, prefs):
        tool = Arc3PointTool(window, doc, prefs)
        assert len(tool.definitions) == 2
        tokens = {d.token for d in tool.definitions}
        assert "ARC3PT" in tokens
        assert "ARC3PTLAST" in tokens

    def test_create_object(self, window, doc, prefs):
        tool = Arc3PointTool(window, doc, prefs)
        tool.points = [Point2D(5, 0), Point2D(0, 5), Point2D(-5, 0)]
        obj = tool.create_object()
        assert isinstance(obj, ArcCadObject)
        assert abs(obj.radius - 5.0) < 0.01

    def test_create_object_collinear_raises(self, window, doc, prefs):
        tool = Arc3PointTool(window, doc, prefs)
        tool.points = [Point2D(0, 0), Point2D(1, 0), Point2D(2, 0)]
        with pytest.raises(ValueError):
            tool.create_object()

    def test_create_object_too_few_points(self, window, doc, prefs):
        tool = Arc3PointTool(window, doc, prefs)
        tool.points = [Point2D(0, 0), Point2D(1, 1)]
        assert tool.create_object() is None


# ---------------------------------------------------------------------------
# ArcTangentTool
# ---------------------------------------------------------------------------

class TestArcTangentTool:
    def test_definitions(self, window, doc, prefs):
        tool = ArcTangentTool(window, doc, prefs)
        assert len(tool.definitions) == 1
        assert tool.definitions[0].token == "ARCTAN"

    def test_create_object(self, window, doc, prefs):
        tool = ArcTangentTool(window, doc, prefs)
        tool.points = [Point2D(0, 0), Point2D(5, 5), Point2D(10, 0)]
        obj = tool.create_object()
        assert isinstance(obj, ArcCadObject)
        assert obj.radius > 0

    def test_create_object_too_few_points(self, window, doc, prefs):
        tool = ArcTangentTool(window, doc, prefs)
        tool.points = [Point2D(0, 0), Point2D(5, 5)]
        assert tool.create_object() is None

    def test_calculate_tangent_arc_basic(self, window, doc, prefs):
        tool = ArcTangentTool(window, doc, prefs)
        result = tool._calculate_tangent_arc(
            Point2D(0, 0), Point2D(5, 5), Point2D(10, 0)
        )
        assert result is not None
        center, radius, start_deg, end_deg = result
        assert radius > 0

    def test_calculate_tangent_arc_zero_chord_returns_none(self, window, doc, prefs):
        tool = ArcTangentTool(window, doc, prefs)
        # start == end → zero chord length
        result = tool._calculate_tangent_arc(
            Point2D(5, 5), Point2D(0, 0), Point2D(5, 5)
        )
        assert result is None

    def test_calculate_tangent_arc_tangent_at_chord(self, window, doc, prefs):
        """Tangent point coincides with chord midpoint → uses default arc height."""
        tool = ArcTangentTool(window, doc, prefs)
        result = tool._calculate_tangent_arc(
            Point2D(0, 0), Point2D(5, 0), Point2D(10, 0)
        )
        assert result is not None
        _, radius, _, _ = result
        assert radius > 0

    def test_calculate_tangent_arc_tangent_below_chord(self, window, doc, prefs):
        """Tangent point on opposite side of chord → center on other side."""
        tool = ArcTangentTool(window, doc, prefs)
        result_above = tool._calculate_tangent_arc(
            Point2D(0, 0), Point2D(5, 3), Point2D(10, 0)
        )
        result_below = tool._calculate_tangent_arc(
            Point2D(0, 0), Point2D(5, -3), Point2D(10, 0)
        )
        assert result_above is not None
        assert result_below is not None
        center_above = result_above[0]
        center_below = result_below[0]
        # Centers should be on opposite sides of the chord (y axis)
        assert center_above.y * center_below.y < 0


# ---------------------------------------------------------------------------
# EllipseCenterTool
# ---------------------------------------------------------------------------

class TestEllipseCenterTool:
    def test_definitions(self, window, doc, prefs):
        tool = EllipseCenterTool(window, doc, prefs)
        assert len(tool.definitions) == 1
        defn = tool.definitions[0]
        assert defn.token == "ELLIPSECTR"
        assert defn.is_creator

    def test_create_object(self, window, doc, prefs):
        tool = EllipseCenterTool(window, doc, prefs)
        tool.points = [Point2D(0, 0), Point2D(10, 5)]
        obj = tool.create_object()
        assert isinstance(obj, EllipseCadObject)
        assert obj.center_point == Point2D(0, 0)
        assert obj.radius1 == 10.0
        assert obj.radius2 == 5.0

    def test_create_object_symmetric(self, window, doc, prefs):
        tool = EllipseCenterTool(window, doc, prefs)
        tool.points = [Point2D(3, 3), Point2D(8, 7)]
        obj = tool.create_object()
        assert abs(obj.radius1 - 5.0) < 1e-9
        assert abs(obj.radius2 - 4.0) < 1e-9

    def test_create_object_too_few_points(self, window, doc, prefs):
        tool = EllipseCenterTool(window, doc, prefs)
        tool.points = [Point2D(0, 0)]
        assert tool.create_object() is None


# ---------------------------------------------------------------------------
# EllipseDiagonalTool
# ---------------------------------------------------------------------------

class TestEllipseDiagonalTool:
    def test_definitions(self, window, doc, prefs):
        tool = EllipseDiagonalTool(window, doc, prefs)
        assert len(tool.definitions) == 1
        assert tool.definitions[0].token == "ELLIPSEDIAG"

    def test_create_object(self, window, doc, prefs):
        tool = EllipseDiagonalTool(window, doc, prefs)
        # bounding box (0,0)–(20,10) → center=(10,5), radii=10,5
        tool.points = [Point2D(0, 0), Point2D(20, 10)]
        obj = tool.create_object()
        assert isinstance(obj, EllipseCadObject)
        assert obj.center_point == Point2D(10, 5)
        assert abs(obj.radius1 - 10.0) < 1e-9
        assert abs(obj.radius2 - 5.0) < 1e-9

    def test_create_object_reversed_corners(self, window, doc, prefs):
        """Corners given in opposite order should produce same result."""
        tool = EllipseDiagonalTool(window, doc, prefs)
        tool.points = [Point2D(20, 10), Point2D(0, 0)]
        obj = tool.create_object()
        assert obj.center_point == Point2D(10, 5)
        assert abs(obj.radius1 - 10.0) < 1e-9
        assert abs(obj.radius2 - 5.0) < 1e-9

    def test_create_object_too_few_points(self, window, doc, prefs):
        tool = EllipseDiagonalTool(window, doc, prefs)
        tool.points = [Point2D(0, 0)]
        assert tool.create_object() is None


# ---------------------------------------------------------------------------
# BezierTool
# ---------------------------------------------------------------------------

class TestBezierTool:
    def test_definition(self, window, doc, prefs):
        tool = BezierTool(window, doc, prefs)
        assert len(tool.definitions) == 1
        assert tool.definitions[0].token == "BEZIER"
        assert tool.definitions[0].is_creator

    def test_create_object(self, window, doc, prefs):
        tool = BezierTool(window, doc, prefs)
        tool.points = [Point2D(0, 0), Point2D(1, 3), Point2D(3, 3), Point2D(4, 0)]
        obj = tool.create_object()
        assert isinstance(obj, CubicBezierCadObject)

    def test_create_object_too_few_points(self, window, doc, prefs):
        tool = BezierTool(window, doc, prefs)
        tool.points = [Point2D(0, 0), Point2D(1, 1), Point2D(2, 2)]
        assert tool.create_object() is None

    def test_calculate_control_points_two_points(self, window, doc, prefs):
        tool = BezierTool(window, doc, prefs)
        pts = [Point2D(0, 0), Point2D(4, 0)]
        cps = tool._calculate_control_points(pts)
        assert len(cps) == 4
        # Starts and ends at the original points
        assert cps[0] == Point2D(0, 0)
        assert cps[3] == Point2D(4, 0)

    def test_calculate_control_points_one_point(self, window, doc, prefs):
        tool = BezierTool(window, doc, prefs)
        assert tool._calculate_control_points([Point2D(0, 0)]) == []

    def test_calculate_control_points_empty(self, window, doc, prefs):
        tool = BezierTool(window, doc, prefs)
        assert tool._calculate_control_points([]) == []

    def test_calculate_control_points_deduplicates(self, window, doc, prefs):
        """Adjacent duplicate points should be removed."""
        tool = BezierTool(window, doc, prefs)
        pts = [Point2D(0, 0), Point2D(0, 0), Point2D(4, 0), Point2D(4, 0)]
        cps = tool._calculate_control_points(pts)
        # After dedup: 2 unique points → 4 control points
        assert len(cps) == 4

    def test_calculate_control_points_multi(self, window, doc, prefs):
        tool = BezierTool(window, doc, prefs)
        pts = [Point2D(0, 0), Point2D(2, 4), Point2D(4, 4), Point2D(6, 0)]
        cps = tool._calculate_control_points(pts)
        assert len(cps) > 4
        assert cps[0] == pts[0]
        assert cps[-1] == pts[-1]

    def test_get_tangent_points(self, window, doc, prefs):
        tool = BezierTool(window, doc, prefs)
        p1 = Point2D(0, 0)
        p2 = Point2D(4, 0)
        p3 = Point2D(8, 0)
        t1, t3 = tool._get_tangent_points(p1, p2, p3, 0.5)
        # For collinear points on x-axis, tangent points should also be on x-axis
        assert abs(t1.y) < 1e-9
        assert abs(t3.y) < 1e-9


# ---------------------------------------------------------------------------
# RectangleTool (supplemental coverage beyond test_rectangle_tool.py)
# ---------------------------------------------------------------------------

class TestRectangleTool:
    def test_definitions(self, window, doc, prefs):
        tool = RectangleTool(window, doc, prefs)
        assert len(tool.definitions) == 1
        defn = tool.definitions[0]
        assert defn.token == "RECTANGLE"
        assert defn.category == ToolCategory.POLYGONS

    def test_create_object_uses_preferences(self, window, doc, prefs):
        class ColorPrefs:
            def get(self, key, default=None):
                return {"default_color": "green", "default_line_width": 3.0}.get(key, default)

        tool = RectangleTool(window, doc, ColorPrefs())
        tool.points = [Point2D(0, 0), Point2D(10, 10)]
        obj = tool.create_object()
        assert obj.color == "green"
        assert obj.line_width == 3.0


# ---------------------------------------------------------------------------
# Base CadTool state management
# ---------------------------------------------------------------------------

class TestCadToolBase:
    def test_initial_state(self, window, doc, prefs):
        tool = LineTool(window, doc, prefs)
        assert tool.state == ToolState.INIT
        assert tool.points == []
        assert tool.temp_objects == []

    def test_cancel_from_drawing(self, window, doc, prefs):
        tool = LineTool(window, doc, prefs)
        tool.state = ToolState.DRAWING
        tool.points = [Point2D(1, 2), Point2D(3, 4)]
        tool.cancel()
        assert tool.state == ToolState.ACTIVE
        assert tool.points == []

    def test_get_snap_point_passthrough(self, window, doc, prefs):
        tool = CircleTool(window, doc, prefs)
        pt = tool.get_snap_point(12.3, 45.6)
        assert abs(pt.x - 12.3) < 1e-9
        assert abs(pt.y - 45.6) < 1e-9

    def test_get_snap_point_with_snaps_system(self, window, doc, prefs):
        """When document_window has snaps_system, use it."""
        from PySide6.QtCore import QPointF

        class MockSnapsSystem:
            def get_snap_point(self, mouse_pos, recent_points):
                return QPointF(99.0, 88.0)

        class WindowWithSnaps:
            snaps_system = MockSnapsSystem()
            def get_scene(self): return MockScene()
            def get_dpcm(self): return 96.0

        tool = LineTool(WindowWithSnaps(), doc, prefs)
        pt = tool.get_snap_point(1.0, 2.0)
        assert abs(pt.x - 99.0) < 1e-9
        assert abs(pt.y - 88.0) < 1e-9

    def test_definitions_populated(self, window, doc, prefs):
        for tool_class in [LineTool, CircleTool, ArcCenterTool,
                           EllipseCenterTool, RectangleTool]:
            tool = tool_class(window, doc, prefs)
            assert len(tool.definitions) >= 1
            assert tool.definition is not None


# ---------------------------------------------------------------------------
# ToolManager
# ---------------------------------------------------------------------------

class TestToolManager:
    def test_register_tool(self, window, doc, prefs):
        manager = ToolManager(window, doc, prefs)
        manager.register_tool(LineTool)
        assert "LINE" in manager.tools

    def test_register_multi_definition_tool(self, window, doc, prefs):
        manager = ToolManager(window, doc, prefs)
        manager.register_tool(LineMPTool)
        assert "LINEMP" in manager.tools
        assert "LINEMP21" in manager.tools

    def test_get_active_tool_initially_none(self, window, doc, prefs):
        manager = ToolManager(window, doc, prefs)
        assert manager.get_active_tool() is None

    def test_activate_tool(self, window, doc, prefs):
        manager = ToolManager(window, doc, prefs)
        manager.register_tool(LineTool)
        manager.activate_tool("LINE")
        active = manager.get_active_tool()
        assert isinstance(active, LineTool)
        assert active.state == ToolState.ACTIVE

    def test_activate_unknown_token(self, window, doc, prefs):
        manager = ToolManager(window, doc, prefs)
        manager.activate_tool("NOTEXIST")
        assert manager.get_active_tool() is None

    def test_tool_change_callback(self, window, doc, prefs):
        manager = ToolManager(window, doc, prefs)
        manager.register_tool(LineTool)
        received = []
        manager.add_tool_change_listener(received.append)
        manager.activate_tool("LINE")
        assert received == ["LINE"]

    def test_switch_tools(self, window, doc, prefs):
        manager = ToolManager(window, doc, prefs)
        manager.register_tool(LineTool)
        manager.register_tool(CircleTool)
        manager.activate_tool("LINE")
        manager.activate_tool("CIRCLE")
        assert isinstance(manager.get_active_tool(), CircleTool)
