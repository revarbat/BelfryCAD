"""Tests for GUI graphics items, widgets and scene — without a full running application."""

import math
import pytest

from PySide6.QtCore import QPointF, QRectF, QEvent, Qt
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene


# ---------------------------------------------------------------------------
# Ensure a QApplication exists for the whole session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


# ---------------------------------------------------------------------------
# CadPolygonGraphicsItem
# ---------------------------------------------------------------------------

class TestCadPolygonGraphicsItem:
    """Tests for CadPolygonGraphicsItem geometry and point management."""

    def _make_item(self, points=None):
        from BelfryCAD.gui.graphics_items.cad_polygon_graphics_item import CadPolygonGraphicsItem
        pts = points or [QPointF(0, 0), QPointF(10, 0), QPointF(10, 10), QPointF(0, 10)]
        return CadPolygonGraphicsItem(pts)

    def test_constructor_stores_points(self):
        from BelfryCAD.gui.graphics_items.cad_polygon_graphics_item import CadPolygonGraphicsItem
        pts = [QPointF(0, 0), QPointF(5, 0), QPointF(5, 5)]
        item = CadPolygonGraphicsItem(pts)
        assert item.getPointCount() == 3

    def test_constructor_empty_points(self):
        from BelfryCAD.gui.graphics_items.cad_polygon_graphics_item import CadPolygonGraphicsItem
        item = CadPolygonGraphicsItem([])
        assert item.getPointCount() == 0

    def test_constructor_none_points(self):
        from BelfryCAD.gui.graphics_items.cad_polygon_graphics_item import CadPolygonGraphicsItem
        item = CadPolygonGraphicsItem(None)
        assert item.getPointCount() == 0

    def test_points_property_returns_copy(self):
        item = self._make_item()
        pts = item.points
        pts.clear()
        assert item.getPointCount() == 4  # original unchanged

    def test_set_points(self):
        item = self._make_item()
        new_pts = [QPointF(1, 1), QPointF(2, 2), QPointF(3, 1)]
        item.setPoints(new_pts)
        assert item.getPointCount() == 3

    def test_set_points_none_clears(self):
        item = self._make_item()
        item.setPoints(None)
        assert item.getPointCount() == 0

    def test_add_point(self):
        item = self._make_item([QPointF(0, 0), QPointF(1, 0), QPointF(1, 1)])
        item.addPoint(QPointF(0, 1))
        assert item.getPointCount() == 4

    def test_insert_point(self):
        item = self._make_item([QPointF(0, 0), QPointF(2, 0), QPointF(2, 2)])
        item.insertPoint(1, QPointF(1, 0))
        assert item.getPointCount() == 4
        assert item.points[1] == QPointF(1, 0)

    def test_remove_point_valid(self):
        item = self._make_item([QPointF(0, 0), QPointF(1, 0), QPointF(1, 1), QPointF(0, 1)])
        item.removePoint(1)
        assert item.getPointCount() == 3

    def test_remove_point_out_of_range_noop(self):
        item = self._make_item()
        item.removePoint(99)
        assert item.getPointCount() == 4

    def test_move_point_valid(self):
        item = self._make_item([QPointF(0, 0), QPointF(1, 0), QPointF(1, 1)])
        item.movePoint(0, QPointF(5, 5))
        assert item.points[0] == QPointF(5, 5)

    def test_move_point_out_of_range_noop(self):
        item = self._make_item([QPointF(0, 0), QPointF(1, 0), QPointF(1, 1)])
        item.movePoint(99, QPointF(5, 5))
        assert item.getPointCount() == 3

    def test_is_closed_with_three_or_more(self):
        item = self._make_item([QPointF(0, 0), QPointF(1, 0), QPointF(1, 1)])
        assert item.isClosed() is True

    def test_is_closed_with_fewer_than_three(self):
        from BelfryCAD.gui.graphics_items.cad_polygon_graphics_item import CadPolygonGraphicsItem
        item = CadPolygonGraphicsItem([QPointF(0, 0), QPointF(1, 0)])
        assert item.isClosed() is False

    # --- getArea ---

    def test_get_area_square(self):
        # Unit square (0,0)–(1,0)–(1,1)–(0,1) → area = 1.0
        item = self._make_item([
            QPointF(0, 0), QPointF(1, 0), QPointF(1, 1), QPointF(0, 1)
        ])
        assert abs(item.getArea() - 1.0) < 1e-9

    def test_get_area_rectangle(self):
        item = self._make_item([
            QPointF(0, 0), QPointF(4, 0), QPointF(4, 3), QPointF(0, 3)
        ])
        assert abs(item.getArea() - 12.0) < 1e-9

    def test_get_area_triangle(self):
        # Right triangle with legs 3 and 4 → area = 6
        item = self._make_item([
            QPointF(0, 0), QPointF(3, 0), QPointF(0, 4)
        ])
        assert abs(item.getArea() - 6.0) < 1e-9

    def test_get_area_too_few_points(self):
        from BelfryCAD.gui.graphics_items.cad_polygon_graphics_item import CadPolygonGraphicsItem
        item = CadPolygonGraphicsItem([QPointF(0, 0), QPointF(1, 0)])
        assert item.getArea() == 0.0

    # --- getCentroid ---

    def test_get_centroid_square(self):
        item = self._make_item([
            QPointF(0, 0), QPointF(2, 0), QPointF(2, 2), QPointF(0, 2)
        ])
        c = item.getCentroid()
        assert abs(c.x() - 1.0) < 1e-9
        assert abs(c.y() - 1.0) < 1e-9

    def test_get_centroid_triangle(self):
        item = self._make_item([
            QPointF(0, 0), QPointF(6, 0), QPointF(3, 6)
        ])
        c = item.getCentroid()
        assert abs(c.x() - 3.0) < 1e-9
        assert abs(c.y() - 2.0) < 1e-9

    def test_get_centroid_single_point(self):
        from BelfryCAD.gui.graphics_items.cad_polygon_graphics_item import CadPolygonGraphicsItem
        item = CadPolygonGraphicsItem([QPointF(3, 7)])
        c = item.getCentroid()
        assert c == QPointF(3, 7)

    def test_get_centroid_empty(self):
        from BelfryCAD.gui.graphics_items.cad_polygon_graphics_item import CadPolygonGraphicsItem
        item = CadPolygonGraphicsItem([])
        c = item.getCentroid()
        assert c == QPointF()

    # --- boundingRect (not selected, no scene) ---

    def test_bounding_rect_basic(self):
        item = self._make_item([
            QPointF(1, 2), QPointF(5, 2), QPointF(5, 8), QPointF(1, 8)
        ])
        rect = item.boundingRect()
        # Should contain the polygon (may be expanded by pen/margin)
        assert rect.left() <= 1.0
        assert rect.top() <= 2.0
        assert rect.right() >= 5.0
        assert rect.bottom() >= 8.0

    def test_bounding_rect_fewer_than_three_points(self):
        from BelfryCAD.gui.graphics_items.cad_polygon_graphics_item import CadPolygonGraphicsItem
        item = CadPolygonGraphicsItem([QPointF(0, 0)])
        rect = item.boundingRect()
        assert rect == QRectF()

    # --- pen/brush ---

    def test_constructor_with_pen(self):
        from BelfryCAD.gui.graphics_items.cad_polygon_graphics_item import CadPolygonGraphicsItem
        pen = QPen(QColor("blue"), 2.0)
        item = CadPolygonGraphicsItem([QPointF(0, 0), QPointF(1, 0), QPointF(0, 1)], pen=pen)
        assert item.pen().color() == QColor("blue")
        assert item.pen().widthF() == 2.0

    def test_constructor_with_brush(self):
        from BelfryCAD.gui.graphics_items.cad_polygon_graphics_item import CadPolygonGraphicsItem
        brush = QBrush(QColor("red"))
        item = CadPolygonGraphicsItem(
            [QPointF(0, 0), QPointF(1, 0), QPointF(0, 1)], brush=brush
        )
        assert item.brush().color() == QColor("red")


# ---------------------------------------------------------------------------
# CadScene
# ---------------------------------------------------------------------------

class TestCadScene:
    """Tests for CadScene utility methods."""

    def _make_scene(self, precision=3):
        from BelfryCAD.gui.widgets.cad_scene import CadScene
        return CadScene(precision=precision)

    def test_default_precision(self):
        scene = self._make_scene(precision=4)
        assert scene.get_precision() == 4

    def test_set_precision(self):
        scene = self._make_scene()
        scene.set_precision(5)
        assert scene.get_precision() == 5

    def test_snaps_system_initially_none(self):
        scene = self._make_scene()
        assert scene.get_snaps_system() is None

    def test_add_remove_snaps_system(self):
        scene = self._make_scene()
        mock_snaps = object()
        scene.add_snaps_system(mock_snaps)
        assert scene.get_snaps_system() is mock_snaps
        scene.remove_snaps_system()
        assert scene.get_snaps_system() is None

    def test_control_point_dragging_flag(self):
        scene = self._make_scene()
        assert scene._control_point_dragging is False
        scene.set_control_point_dragging(True)
        assert scene._control_point_dragging is True
        scene.set_control_point_dragging(False)
        assert scene._control_point_dragging is False

    def test_updating_from_tree_flag(self):
        scene = self._make_scene()
        assert scene.is_updating_from_tree() is False
        scene.set_updating_from_tree(True)
        assert scene.is_updating_from_tree() is True
        scene.set_updating_from_tree(False)
        assert scene.is_updating_from_tree() is False

    def test_tool_manager_set(self):
        scene = self._make_scene()
        mock_tm = object()
        scene.set_tool_manager(mock_tm)
        assert scene._tool_manager is mock_tm

    def test_update_all_control_datums_precision(self):
        scene = self._make_scene(precision=3)
        scene.update_all_control_datums_precision(6)
        assert scene._precision == 6

    def test_add_arc(self):
        from BelfryCAD.gui.graphics_items.cad_arc_graphics_item import CadArcGraphicsItem
        scene = self._make_scene()
        arc = scene.addArc(QPointF(0, 0), 5.0, 0.0, 90.0)
        from BelfryCAD.gui.graphics_items.cad_arc_graphics_item import CadArcGraphicsItem
        assert isinstance(arc, CadArcGraphicsItem)
        assert arc in scene.items()

    def test_add_arc_with_pen(self):
        scene = self._make_scene()
        pen = QPen(QColor("red"), 2.0)
        arc = scene.addArc(QPointF(0, 0), 5.0, 0.0, 90.0, pen=pen)
        assert arc.pen().color() == QColor("red")

    def test_selection_changed_skipped_when_dragging(self):
        scene = self._make_scene()
        scene.set_control_point_dragging(True)
        received = []
        scene.scene_selection_changed.connect(received.append)
        scene._on_selection_changed()
        assert received == []

    def test_selection_changed_skipped_when_updating_from_tree(self):
        scene = self._make_scene()
        scene.set_updating_from_tree(True)
        received = []
        scene.scene_selection_changed.connect(received.append)
        scene._on_selection_changed()
        assert received == []

    def test_selection_changed_emits_empty_set_when_nothing_selected(self):
        scene = self._make_scene()
        received = []
        scene.scene_selection_changed.connect(received.append)
        scene._on_selection_changed()
        assert received == [set()]

    def test_refresh_gear_items_noop(self):
        scene = self._make_scene()
        scene.refresh_gear_items_for_unit_change()  # just checks it doesn't crash

    def test_remove_item(self):
        from BelfryCAD.gui.graphics_items.cad_polygon_graphics_item import CadPolygonGraphicsItem
        scene = self._make_scene()
        pts = [QPointF(0, 0), QPointF(1, 0), QPointF(1, 1)]
        item = CadPolygonGraphicsItem(pts)
        scene.addItem(item)
        scene.removeItem(item)
        assert item not in scene.items()


# ---------------------------------------------------------------------------
# ZoomEditWidget
# ---------------------------------------------------------------------------

class TestZoomEditWidget:
    """Tests for ZoomEditWidget display and value handling."""

    def _make_widget(self):
        from BelfryCAD.gui.widgets.zoom_edit_widget import ZoomEditWidget
        return ZoomEditWidget(view=None)  # view=None is fine for non-zoom-apply tests

    def test_initial_text(self):
        w = self._make_widget()
        assert w.scale_label.text() == "100"

    def test_set_zoom_value(self):
        w = self._make_widget()
        w.set_zoom_value(250)
        assert w.scale_label.text() == "250"

    def test_set_zoom_value_rounds(self):
        w = self._make_widget()
        w.set_zoom_value(150.7)
        assert w.scale_label.text() == "150"

    def test_get_zoom_value(self):
        w = self._make_widget()
        w.set_zoom_value(400)
        assert w.get_zoom_value() == 400

    def test_get_zoom_value_invalid_text_returns_100(self):
        w = self._make_widget()
        w.scale_label.setText("abc")
        assert w.get_zoom_value() == 100

    def test_set_editable_makes_editable(self):
        w = self._make_widget()
        w.set_editable(True)
        assert not w.scale_label.isReadOnly()

    def test_set_editable_false_makes_readonly(self):
        w = self._make_widget()
        w.set_editable(True)
        w.set_editable(False)
        assert w.scale_label.isReadOnly()

    def test_view_property(self):
        from BelfryCAD.gui.widgets.zoom_edit_widget import ZoomEditWidget
        mock_view = object()
        w = ZoomEditWidget(view=mock_view)
        assert w.view is mock_view

    def test_view_setter(self):
        w = self._make_widget()
        mock_view = object()
        w.view = mock_view
        assert w.view is mock_view


class TestDigitOnlyInputFilter:
    """Tests for DigitOnlyInputFilter event filter."""

    def _make_filter(self):
        from BelfryCAD.gui.widgets.zoom_edit_widget import DigitOnlyInputFilter
        return DigitOnlyInputFilter()

    class _MockKeyEvent:
        """Minimal mock for a key press event."""
        Type = QEvent.Type

        def __init__(self, key, event_type=QEvent.Type.KeyPress):
            self._key = key
            self._type = event_type

        def type(self):
            return self._type

        def key(self):
            return self._key

    def test_digit_key_allowed(self):
        f = self._make_filter()
        event = self._MockKeyEvent(Qt.Key.Key_5)
        assert f.eventFilter(None, event) is False  # False = allow

    def test_digit_zero_allowed(self):
        f = self._make_filter()
        event = self._MockKeyEvent(Qt.Key.Key_0)
        assert f.eventFilter(None, event) is False

    def test_digit_nine_allowed(self):
        f = self._make_filter()
        event = self._MockKeyEvent(Qt.Key.Key_9)
        assert f.eventFilter(None, event) is False

    def test_backspace_allowed(self):
        f = self._make_filter()
        event = self._MockKeyEvent(Qt.Key.Key_Backspace)
        assert f.eventFilter(None, event) is False

    def test_delete_allowed(self):
        f = self._make_filter()
        event = self._MockKeyEvent(Qt.Key.Key_Delete)
        assert f.eventFilter(None, event) is False

    def test_return_allowed(self):
        f = self._make_filter()
        event = self._MockKeyEvent(Qt.Key.Key_Return)
        assert f.eventFilter(None, event) is False

    def test_enter_allowed(self):
        f = self._make_filter()
        event = self._MockKeyEvent(Qt.Key.Key_Enter)
        assert f.eventFilter(None, event) is False

    def test_left_arrow_allowed(self):
        f = self._make_filter()
        event = self._MockKeyEvent(Qt.Key.Key_Left)
        assert f.eventFilter(None, event) is False

    def test_right_arrow_allowed(self):
        f = self._make_filter()
        event = self._MockKeyEvent(Qt.Key.Key_Right)
        assert f.eventFilter(None, event) is False

    def test_letter_blocked(self):
        f = self._make_filter()
        event = self._MockKeyEvent(Qt.Key.Key_A)
        assert f.eventFilter(None, event) is True  # True = block

    def test_period_blocked(self):
        f = self._make_filter()
        event = self._MockKeyEvent(Qt.Key.Key_Period)
        assert f.eventFilter(None, event) is True

    def test_non_keypress_allowed(self):
        f = self._make_filter()
        event = self._MockKeyEvent(Qt.Key.Key_A, QEvent.Type.KeyRelease)
        assert f.eventFilter(None, event) is False


# ---------------------------------------------------------------------------
# ControlPointShape
# ---------------------------------------------------------------------------

class TestControlPointShape:
    def test_enum_values(self):
        from BelfryCAD.gui.graphics_items.control_points import ControlPointShape
        assert ControlPointShape.ROUND.value == "round"
        assert ControlPointShape.SQUARE.value == "square"
        assert ControlPointShape.TRIANGLE.value == "triangle"
        assert ControlPointShape.DIAMOND.value == "diamond"
        assert ControlPointShape.PENTAGON.value == "pentagon"
        assert ControlPointShape.HEXAGON.value == "hexagon"

    def test_all_six_shapes_exist(self):
        from BelfryCAD.gui.graphics_items.control_points import ControlPointShape
        assert len(ControlPointShape) == 6


# ---------------------------------------------------------------------------
# ControlPoint (base class)
# ---------------------------------------------------------------------------

class TestControlPoint:
    """Tests for ControlPoint without a live scene."""

    def _make_cp(self, shape=None, big=False):
        from BelfryCAD.gui.graphics_items.control_points import ControlPoint, ControlPointShape
        cp_shape = shape or ControlPointShape.ROUND
        return ControlPoint(model_view=None, setter=None, cp_shape=cp_shape, big=big)

    def test_initial_z_value(self):
        cp = self._make_cp()
        assert cp.zValue() == 10001

    def test_initial_dragging_false(self):
        cp = self._make_cp()
        assert cp._is_dragging is False

    def test_set_dragging(self):
        cp = self._make_cp()
        cp.set_dragging(True)
        assert cp._is_dragging is True
        cp.set_dragging(False)
        assert cp._is_dragging is False

    def test_set_shape(self):
        from BelfryCAD.gui.graphics_items.control_points import ControlPointShape
        cp = self._make_cp()
        cp.setShape(ControlPointShape.SQUARE)
        assert cp.cp_shape == ControlPointShape.SQUARE

    def test_set_big(self):
        cp = self._make_cp()
        cp.setBig(True)
        assert cp.big is True
        cp.setBig(False)
        assert cp.big is False

    def test_set_setter(self):
        cp = self._make_cp()
        fn = lambda x: None
        cp.setSetter(fn)
        assert cp.setter is fn

    def test_call_setter_with_updates_calls_setter(self):
        from BelfryCAD.gui.graphics_items.control_points import ControlPoint, ControlPointShape

        called_with = []
        def my_setter(value):
            called_with.append(value)

        cp = ControlPoint(model_view=object(), setter=my_setter)
        cp.call_setter_with_updates(QPointF(3, 4))
        assert called_with == [QPointF(3, 4)]

    def test_call_setter_with_updates_no_setter(self):
        cp = self._make_cp()
        cp.setter = None
        cp.call_setter_with_updates(QPointF(1, 1))  # should not raise

    def test_bounding_rect_without_scene_fallback(self):
        """Without a scene, falls back to control_size=0.3."""
        cp = self._make_cp()
        rect = cp.boundingRect()
        # control_size=0.3, padding=0.15 → rect is (-0.15,-0.15,0.3,0.3)
        assert abs(rect.width() - 0.3) < 1e-9
        assert abs(rect.height() - 0.3) < 1e-9

    def test_bounding_rect_big_without_scene_fallback(self):
        """big=True also uses the fallback path when no scene."""
        cp = self._make_cp(big=True)
        rect = cp.boundingRect()
        assert abs(rect.width() - 0.3) < 1e-9

    def test_shape_round(self):
        from BelfryCAD.gui.graphics_items.control_points import ControlPointShape
        cp = self._make_cp(shape=ControlPointShape.ROUND)
        path = cp.shape()
        assert not path.isEmpty()

    def test_shape_square(self):
        from BelfryCAD.gui.graphics_items.control_points import ControlPointShape
        cp = self._make_cp(shape=ControlPointShape.SQUARE)
        path = cp.shape()
        assert not path.isEmpty()

    def test_shape_triangle(self):
        from BelfryCAD.gui.graphics_items.control_points import ControlPointShape
        cp = self._make_cp(shape=ControlPointShape.TRIANGLE)
        path = cp.shape()
        assert not path.isEmpty()

    def test_shape_diamond(self):
        from BelfryCAD.gui.graphics_items.control_points import ControlPointShape
        cp = self._make_cp(shape=ControlPointShape.DIAMOND)
        path = cp.shape()
        assert not path.isEmpty()

    def test_shape_pentagon(self):
        from BelfryCAD.gui.graphics_items.control_points import ControlPointShape
        cp = self._make_cp(shape=ControlPointShape.PENTAGON)
        path = cp.shape()
        assert not path.isEmpty()

    def test_shape_hexagon(self):
        from BelfryCAD.gui.graphics_items.control_points import ControlPointShape
        cp = self._make_cp(shape=ControlPointShape.HEXAGON)
        path = cp.shape()
        assert not path.isEmpty()

    def test_set_tooltip(self):
        cp = self._make_cp(shape=None)
        cp.setToolTip("test tip")
        assert cp.tool_tip == "test tip"

    def test_constructor_tooltip_set(self):
        from BelfryCAD.gui.graphics_items.control_points import ControlPoint
        cp = ControlPoint(model_view=None, setter=None, tool_tip="hello")
        assert cp.tool_tip == "hello"


# ---------------------------------------------------------------------------
# ControlDatum
# ---------------------------------------------------------------------------

class _MockCadScene:
    def get_precision(self):
        return 3


class _MockGridInfo:
    def format_label(self, value, no_subs=False):
        return f"{value:.3f}"


class _MockDocumentWindowDatum:
    cad_scene = _MockCadScene()
    grid_info = _MockGridInfo()


class _MockViewModelDatum:
    document_window = _MockDocumentWindowDatum()


def _make_datum(**kwargs):
    from BelfryCAD.gui.graphics_items.control_points import ControlDatum
    defaults = dict(
        model_view=_MockViewModelDatum(),
        setter=None,
        is_length=False,
        label="test",
        prefix="",
        suffix="",
    )
    defaults.update(kwargs)
    return ControlDatum(**defaults)


class TestControlDatum:

    def test_initial_value(self):
        d = _make_datum()
        assert d._current_value == 0.0

    def test_initial_precision(self):
        d = _make_datum()
        assert d._precision == 3

    # --- is_value_in_range ---

    def test_is_value_in_range_no_limits(self):
        d = _make_datum()
        d._current_value = 100.0
        assert d.is_value_in_range() is True

    def test_is_value_in_range_within_limits(self):
        d = _make_datum(min_value=0.0, max_value=10.0)
        assert d.is_value_in_range(5.0) is True

    def test_is_value_in_range_at_min(self):
        d = _make_datum(min_value=1.0)
        assert d.is_value_in_range(1.0) is True

    def test_is_value_in_range_below_min(self):
        d = _make_datum(min_value=1.0)
        assert d.is_value_in_range(0.5) is False

    def test_is_value_in_range_at_max(self):
        d = _make_datum(max_value=10.0)
        assert d.is_value_in_range(10.0) is True

    def test_is_value_in_range_above_max(self):
        d = _make_datum(max_value=10.0)
        assert d.is_value_in_range(10.1) is False

    def test_is_value_in_range_uses_current_value_when_none(self):
        d = _make_datum(min_value=0.0, max_value=5.0)
        d._current_value = 3.0
        assert d.is_value_in_range() is True
        d._current_value = -1.0
        assert d.is_value_in_range() is False

    # --- update_precision ---

    def test_update_precision_changes_precision(self):
        d = _make_datum()
        d.update_precision(5)
        assert d._precision == 5

    def test_update_precision_updates_format_string(self):
        d = _make_datum()
        d.update_precision(2)
        assert d._format_string == "{:.2f}"

    def test_update_precision_with_override_uses_override(self):
        d = _make_datum(precision_override=4)
        d.update_precision(2)  # should be ignored
        assert d._precision == 4

    # --- _format_text (is_length=False) ---

    def test_format_text_basic(self):
        d = _make_datum()
        d._format_string = "{:.2f}"
        text = d._format_text(3.14)
        assert "3.14" in text

    def test_format_text_strips_trailing_zeros(self):
        d = _make_datum()
        d._format_string = "{:.3f}"
        text = d._format_text(3.0)
        assert text == "3"

    def test_format_text_strips_trailing_zeros_partial(self):
        d = _make_datum()
        d._format_string = "{:.3f}"
        text = d._format_text(3.1)
        assert text == "3.1"

    def test_format_text_with_prefix(self):
        d = _make_datum(prefix="R=")
        d._format_string = "{:.1f}"
        text = d._format_text(5.0)
        assert text.startswith("R=")

    def test_format_text_with_suffix(self):
        d = _make_datum(suffix="mm")
        d._format_string = "{:.1f}"
        text = d._format_text(5.0)
        assert text.endswith("mm")

    def test_format_text_no_prefix_when_requested(self):
        d = _make_datum(prefix="X:")
        d._format_string = "{:.1f}"
        text = d._format_text(5.0, no_prefix=True)
        assert not text.startswith("X:")

    def test_format_text_no_suffix_when_requested(self):
        d = _make_datum(suffix="°")
        d._format_string = "{:.1f}"
        text = d._format_text(90.0, no_suffix=True)
        assert not text.endswith("°")

    # --- update_datum ---

    def test_update_datum_sets_value(self):
        d = _make_datum()
        d.update_datum(42.0, QPointF(1, 2))
        assert d._current_value == 42.0

    def test_update_datum_sets_position(self):
        d = _make_datum()
        d.update_datum(1.0, QPointF(5, 7))
        assert d._current_position == QPointF(5, 7)

    def test_update_datum_updates_cached_text(self):
        d = _make_datum()
        d._format_string = "{:.1f}"
        d.update_datum(99.0, QPointF(0, 0))
        assert "99" in d._cached_text

    # --- Properties ---

    def test_prefix_property(self):
        d = _make_datum(prefix="pfx")
        assert d.prefix == "pfx"
        d.prefix = "new"
        assert d.prefix == "new"

    def test_suffix_property(self):
        d = _make_datum(suffix="sfx")
        assert d.suffix == "sfx"
        d.suffix = "new"
        assert d.suffix == "new"

    def test_label_property(self):
        d = _make_datum(label="radius")
        assert d.label == "radius"
        d.label = "diameter"
        assert d.label == "diameter"

    def test_angle_property(self):
        d = _make_datum(angle=45.0)
        assert d.angle == 45.0
        d.angle = 90.0
        assert d.angle == 90.0

    def test_angle_default_none(self):
        d = _make_datum()
        assert d.angle is None

    def test_pixel_offset_property(self):
        d = _make_datum(pixel_offset=10)
        assert d.pixel_offset == 10
        d.pixel_offset = 20
        assert d.pixel_offset == 20

    def test_min_value_property(self):
        d = _make_datum(min_value=0.0)
        assert d.min_value == 0.0
        d.min_value = 1.0
        assert d.min_value == 1.0

    def test_max_value_property(self):
        d = _make_datum(max_value=100.0)
        assert d.max_value == 100.0
        d.max_value = 200.0
        assert d.max_value == 200.0

    def test_format_string_property(self):
        d = _make_datum()
        d.format_string = "{:.4f}"
        assert d.format_string == "{:.4f}"

    def test_precision_property_setter(self):
        d = _make_datum()
        d.precision = 6
        assert d.precision == 6

    def test_setter_property(self):
        d = _make_datum()
        fn = lambda x: None
        d.setter = fn
        assert d.setter is fn

    def test_z_value_above_control_point(self):
        d = _make_datum()
        assert d.zValue() == 10002

    def test_format_text_is_length_true(self):
        """is_length=True uses grid_info.format_label."""
        from BelfryCAD.gui.graphics_items.control_points import ControlDatum
        d = ControlDatum(
            model_view=_MockViewModelDatum(),
            setter=None,
            is_length=True,
            label="length",
        )
        text = d._format_text(5.0)
        # MockGridInfo formats as "5.000"
        assert "5" in text
