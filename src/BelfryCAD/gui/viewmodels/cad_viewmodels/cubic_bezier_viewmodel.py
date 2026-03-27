"""
CubicBezier ViewModel for BelfryCAD.

This ViewModel handles presentation logic for cubic Bezier CAD objects and emits signals
for UI updates when Bezier properties change.
"""

import math
from typing import List, Tuple, Optional, TYPE_CHECKING, Any

from PySide6.QtCore import Qt, QPointF, QLineF, Signal
from PySide6.QtGui import QColor, QPen, QPainterPath
from PySide6.QtWidgets import QGraphicsScene

from .cad_viewmodel import CadViewModel
from ...graphics_items.control_points import (
    ControlPoint,
    ControlPointShape
)
from ...graphics_items.cad_bezier_graphics_item import CadBezierGraphicsItem
from ...graphics_items.construction_line_item import ConstructionLineItem, DashPattern
from ....models.cad_objects.cubic_bezier_cad_object import CubicBezierCadObject, TangentPointMode
from ....cad_geometry import Point2D

if TYPE_CHECKING:
    from ....gui.document_window import DocumentWindow


class CubicBezierViewModel(CadViewModel):
    """Presentation logic for cubic Bezier CAD objects with signals"""
    
    # Bezier-specific signals
    points_changed = Signal(list)  # new points list
    start_point_changed = Signal(QPointF)  # new start point
    end_point_changed = Signal(QPointF)  # new end point
    is_closed_changed = Signal(bool)  # new closed state
    
    def __init__(self, document_window: 'DocumentWindow', bezier_object: CubicBezierCadObject):
        super().__init__(document_window, bezier_object)
        self._bezier_object = bezier_object  # Keep reference for type-specific access
        
    def update_view(self, scene: QGraphicsScene):
        """
        Creates and/or updates the view items for this Bezier curve.
        This is called when the Bezier curve is added to the scene, and when the Bezier curve is modified.
        """
        self._clear_view_items(scene)

        color = QColor(self._bezier_object.color)
        line_width = self._bezier_object.line_width or 0.05
        points = self.points
        
        if len(points) >= 4:  # Need at least 4 points for a cubic Bezier
            # Create Bezier curve path
            path = QPainterPath()
            
            # Start at the first point
            path.moveTo(points[0])
            
            # Create cubic Bezier segments.
            # For a closed bezier the last point is an explicit duplicate of the
            # first point, so the loop already draws the closing segment — no
            # extra cubicTo needed.
            for i in range(0, len(points) - 3, 3):
                if i + 3 < len(points):
                    path.cubicTo(
                        points[i + 1],  # Control point 1
                        points[i + 2],  # Control point 2
                        points[i + 3]   # End point
                    )
            
            pen = QPen(color, line_width)
            view_item = CadBezierGraphicsItem(path, pen=pen)
            self._view_items.append(view_item)

        self._add_view_items_to_scene(scene)
        self.update_decorations(scene)
        self.update_controls(scene)
    
    def show_decorations(self, scene: QGraphicsScene):
        """
        Show the decorations.
        This is called when this object is selected.
        """
        self._clear_decorations(scene)

        # Only show construction lines when exactly one CAD object is selected
        if len(self._document_window._current_selection) != 1:
            return

        points = self.points
        for i in range(0, len(points), 3):
            # Line from anchor's predecessor to the anchor (e.g. p2→p3, p5→p6)
            if i > 0 and points[i - 1] != points[i]:
                self._decorations.append(ConstructionLineItem(
                    line=QLineF(points[i - 1], points[i]),
                    dash_pattern=DashPattern.SHORT_DASHED,
                ))
            # Line from the anchor to its successor (e.g. p0→p1, p3→p4, p6→p7)
            if i < len(points) - 1 and points[i] != points[i + 1]:
                self._decorations.append(ConstructionLineItem(
                    line=QLineF(points[i], points[i + 1]),
                    dash_pattern=DashPattern.SHORT_DASHED,
                ))
        self._add_decorations_to_scene(scene)
    
    def hide_decorations(self, scene: QGraphicsScene):
        """
        Hide the decorations.
        This is called when this object is deselected.
        """
        self._clear_decorations(scene)
    
    def update_decorations(self, scene: QGraphicsScene):
        """
        Update the decorations.
        This is called when this object is modified.
        """
        if self._decorations:
            self.hide_decorations(scene)
            self.show_decorations(scene)
    
    def show_controls(self, scene: QGraphicsScene):
        """
        Show the controls.
        This is called when this object becomes the only object selected.
        """
        self._clear_controls(scene)

        points = self.points
        n = len(points)
        closed = self.is_closed
        for i, point in enumerate(points):
            # For a closed bezier p_last is an explicit duplicate of p0.
            # Omit its control point so the seam appears as a single tangent point.
            if closed and i == n - 1:
                continue
            if i % 3 == 0:
                tangent_idx = i // 3
                mode = self._bezier_object.get_tangent_mode(tangent_idx)
                if mode == TangentPointMode.DISJOINT:
                    shape = ControlPointShape.DIAMOND
                elif mode == TangentPointMode.TANGENT:
                    shape = ControlPointShape.SQUARE
                else:  # EQUAL
                    shape = ControlPointShape.ROUND
                big = True
                dbl_click = lambda idx=tangent_idx: self._cycle_tangent_mode(idx)
            else:
                shape = ControlPointShape.ROUND
                big = False
                dbl_click = None
            cp = ControlPoint(
                model_view=self,
                setter=lambda new_pos, idx=i: self._set_point(idx, new_pos),
                tool_tip=f"Bezier Control Point {i}",
                cp_shape=shape,
                big=big,
                double_click_handler=dbl_click,
            )
            self._controls.append(cp)

        self._add_controls_to_scene(scene)

    def hide_controls(self, scene: QGraphicsScene):
        """
        Hide the controls.
        This is called when this object is deselected, or when an additional object becomes selected.
        """
        self._clear_controls(scene)

    def _update_view_geometry_in_place(self):
        """Update the bezier graphics item in-place after a translation."""
        if not self._view_items:
            return
        points = self.points
        if len(points) < 4:
            return
        path = QPainterPath()
        path.moveTo(points[0])
        for i in range(0, len(points) - 3, 3):
            if i + 3 < len(points):
                path.cubicTo(points[i + 1], points[i + 2], points[i + 3])
        self._view_items[0].setBezierPath(path)

    def update_controls(self, scene: QGraphicsScene):
        """
        Update the controls.
        This is called when this object is modified.
        """
        if not self._controls:
            return

        points = self.points

        # Update control points
        for cp, point in zip(self._controls, points):
            cp.setPos(point)

        self.control_points_updated.emit()

    def get_properties(self) -> List[str]:
        """Get properties of the cubic bezier"""
        return [ ]
    
    def get_property_value(self, name: str) -> Any:
        """Get a cubic bezier property"""
        raise ValueError(f"Invalid property name: {name}")

    def set_property_value(self, name: str, value: Any):
        """Set a cubic bezier property"""
        raise ValueError(f"Invalid property name: {name}")
    
    @property
    def object_type(self) -> str:
        """Get object type"""
        return "cubic_bezier"
    
    @property
    def line_width(self) -> Optional[float]:
        """Get line width from model"""
        return self._bezier_object.line_width
    
    @line_width.setter
    def line_width(self, value: Optional[float]):
        """Set line width in model"""
        if self._bezier_object.line_width != value:
            self._bezier_object.line_width = value
            self.object_modified.emit()
    
    @property
    def points(self) -> List[QPointF]:
        """Get all control points as QPointF list"""
        points = self._bezier_object.points
        return [QPointF(p.x, p.y) for p in points]
    
    @points.setter
    def points(self, value: List[QPointF]):
        """Set all control points and emit signal"""
        if self.points != value:
            point_list = [Point2D(p.x(), p.y()) for p in value]
            self._bezier_object.points = point_list
            self.points_changed.emit(value)
            self.object_modified.emit()
    
    @property
    def start_point(self) -> Optional[QPointF]:
        """Get start point as QPointF"""
        start = self._bezier_object.start_point
        if start:
            return QPointF(start.x, start.y)
        return None
    
    @property
    def end_point(self) -> Optional[QPointF]:
        """Get end point as QPointF"""
        end = self._bezier_object.end_point
        if end:
            return QPointF(end.x, end.y)
        return None
    
    @property
    def is_closed(self) -> bool:
        """Get closed state"""
        return self._bezier_object.is_closed
    
    def add_point(self, point: QPointF):
        """Add a new control point"""
        self._bezier_object.add_point(Point2D(point.x(), point.y()))
        self.object_modified.emit()
    
    def insert_point(self, index: int, point: QPointF):
        """Insert a control point at index"""
        self._bezier_object.insert_point(index, Point2D(point.x(), point.y()))
        self.object_modified.emit()
    
    def remove_point(self, index: int):
        """Remove a control point at index"""
        self._bezier_object.remove_point(index)
        self.object_modified.emit()
    
    def get_point(self, index: int) -> Optional[QPointF]:
        """Get control point at index"""
        point = self._bezier_object.get_point(index)
        if point:
            return QPointF(point.x, point.y)
        return None
    
    def set_point(self, index: int, point: QPointF):
        """Set control point at index"""
        self._bezier_object.set_point(index, Point2D(point.x(), point.y()))
        self.object_modified.emit()

    def scale(self, scale_factor: float, center: QPointF):
        """Scale the Bezier curve around the given center"""
        center_point = Point2D(center.x(), center.y())
        self._bezier_object.scale(scale_factor, center_point)
        
    def rotate(self, angle: float, center: QPointF):
        """Rotate the Bezier curve around the given center"""
        center_point = Point2D(center.x(), center.y())
        self._bezier_object.rotate(angle, center_point)
        self.object_moved.emit(QPointF(0, 0))
        
    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get bounding box of the Bezier curve"""
        return self._bezier_object.get_bounds()
    
    def contains_point(self, point: QPointF, tolerance: float = 5.0) -> bool:
        """Check if point is near the Bezier curve"""
        return self._bezier_object.contains_point(Point2D(point), tolerance)
    
    def _enforce_tangent_mode_constraints(self, tangent_idx: int):
        """
        Adjust the handles around a tangent point so their positions are valid for
        the tangent point's current mode.

        Transitions that require work:
          * → TANGENT : make the after-handle direction opposite the before-handle,
                        preserving the after-handle's current length.
          * → EQUAL   : same as TANGENT, but also equalise the lengths (use the
                        before-handle length for both).
          * → DISJOINT: nothing to do – any handle position is acceptable.
        """
        mode = self._bezier_object.get_tangent_mode(tangent_idx)
        if mode == TangentPointMode.DISJOINT:
            return

        n = len(self.points)
        anchor_idx = 3 * tangent_idx
        if anchor_idx >= n:
            return

        closed = self.is_closed

        # Index of the handle just before the anchor (index % 3 == 2)
        if anchor_idx > 0:
            before_idx = anchor_idx - 1
        elif closed:
            before_idx = n - 2
        else:
            before_idx = None

        # Index of the handle just after the anchor (index % 3 == 1)
        if anchor_idx < n - 1:
            after_idx = anchor_idx + 1
        elif closed:
            after_idx = 1
        else:
            after_idx = None

        # Need both handles to enforce a constraint
        if before_idx is None or after_idx is None:
            return

        anchor = self.get_point(anchor_idx)
        before_handle = self.get_point(before_idx)
        after_handle = self.get_point(after_idx)
        if not anchor or not before_handle or not after_handle:
            return

        before_delta = before_handle - anchor
        before_len = math.hypot(before_delta.x(), before_delta.y())
        before_angle = math.atan2(before_delta.y(), before_delta.x())

        after_delta = after_handle - anchor
        after_len = math.hypot(after_delta.x(), after_delta.y())

        if before_len < 1e-10:
            return  # degenerate; nothing useful to mirror

        if mode == TangentPointMode.TANGENT:
            # Opposite direction, keep after-handle's existing length
            new_len = after_len
        else:  # EQUAL
            # Opposite direction, match before-handle's length
            new_len = before_len

        new_after = anchor + QPointF(
            new_len * math.cos(before_angle + math.pi),
            new_len * math.sin(before_angle + math.pi),
        )
        self.set_point(after_idx, new_after)

    def _cycle_tangent_mode(self, tangent_idx: int):
        """Cycle the tangent point mode: DISJOINT → TANGENT → EQUAL → DISJOINT."""
        modes = [TangentPointMode.DISJOINT, TangentPointMode.TANGENT, TangentPointMode.EQUAL]
        current = self._bezier_object.get_tangent_mode(tangent_idx)
        next_mode = modes[(modes.index(current) + 1) % len(modes)]
        self._bezier_object.set_tangent_mode(tangent_idx, next_mode)
        # For closed curves the first and last tangent points are the same physical point
        if self.is_closed:
            n = len(self.points)
            last_tangent_idx = (n - 1) // 3
            if tangent_idx == 0:
                self._bezier_object.set_tangent_mode(last_tangent_idx, next_mode)
            elif tangent_idx == last_tangent_idx:
                self._bezier_object.set_tangent_mode(0, next_mode)
        # Adjust handles to satisfy the new mode's constraints
        self._enforce_tangent_mode_constraints(tangent_idx)
        # Rebuild view and controls (shape may have changed)
        scene = self._document_window.cad_scene
        if scene:
            self.update_view(scene)
            self.show_controls(scene)
            self.update_controls(scene)

    def _set_point(self, index: int, new_position: QPointF):
        """Set a control point from control point movement"""
        n = len(self.points)
        if index < 0 or index >= n:
            return

        closed = self.is_closed

        if index % 3 == 2:
            # Handle before the anchor at index+1
            tangent_idx = (index + 1) // 3
            mode = self._bezier_object.get_tangent_mode(tangent_idx)
            self.set_point(index, new_position)
            if mode != TangentPointMode.DISJOINT:
                if index < n - 2:
                    mid_point = self.get_point(index + 1)
                    next_point = self.get_point(index + 2)
                    if mid_point and next_point:
                        prev_delta = new_position - mid_point
                        next_delta = next_point - mid_point
                        prev_angle = math.atan2(prev_delta.y(), prev_delta.x())
                        next_angle = math.atan2(next_delta.y(), next_delta.x())
                        if mode == TangentPointMode.EQUAL:
                            old_rad = math.hypot(prev_delta.x(), prev_delta.y())
                        else:  # TANGENT
                            old_rad = math.hypot(next_delta.x(), next_delta.y())
                        new_point = mid_point + QPointF(
                            old_rad * math.cos(prev_angle + math.pi),
                            old_rad * math.sin(prev_angle + math.pi)
                        )
                        self.set_point(index + 2, new_point)
                elif closed and index == n - 2:
                    # Closed: anchor is p_last (== p0); opposite handle wraps to p1
                    mid_point = self.get_point(n - 1)
                    next_point = self.get_point(1)
                    if mid_point and next_point:
                        prev_delta = new_position - mid_point
                        next_delta = next_point - mid_point
                        prev_angle = math.atan2(prev_delta.y(), prev_delta.x())
                        next_angle = math.atan2(next_delta.y(), next_delta.x())
                        if mode == TangentPointMode.EQUAL:
                            old_rad = math.hypot(prev_delta.x(), prev_delta.y())
                        else:  # TANGENT
                            old_rad = math.hypot(next_delta.x(), next_delta.y())
                        new_point = mid_point + QPointF(
                            old_rad * math.cos(prev_angle + math.pi),
                            old_rad * math.sin(prev_angle + math.pi)
                        )
                        self.set_point(1, new_point)

        if index % 3 == 0:
            old_point = self.get_point(index)
            if old_point:
                delta = new_position - old_point
                self.set_point(index, new_position)
                if index > 0:
                    prev_point = self.get_point(index - 1)
                    if prev_point:
                        self.set_point(index - 1, prev_point + delta)
                if index < n - 1:
                    next_point = self.get_point(index + 1)
                    if next_point:
                        self.set_point(index + 1, next_point + delta)
                # Closed curve: moving the seam anchor also moves the opposite end and its handle
                if closed and index == 0:
                    last_point = self.get_point(n - 1)
                    if last_point:
                        self.set_point(n - 1, last_point + delta)
                    second_last = self.get_point(n - 2)
                    if second_last:
                        self.set_point(n - 2, second_last + delta)
                elif closed and index == n - 1:
                    first_point = self.get_point(0)
                    if first_point:
                        self.set_point(0, first_point + delta)
                    second_point = self.get_point(1)
                    if second_point:
                        self.set_point(1, second_point + delta)

        if index % 3 == 1:
            # Handle after the anchor at index-1
            tangent_idx = (index - 1) // 3
            mode = self._bezier_object.get_tangent_mode(tangent_idx)
            self.set_point(index, new_position)
            if mode != TangentPointMode.DISJOINT:
                if index > 1:
                    prev_point = self.get_point(index - 2)
                    mid_point = self.get_point(index - 1)
                    if mid_point and prev_point:
                        prev_delta = prev_point - mid_point
                        next_delta = new_position - mid_point
                        prev_angle = math.atan2(prev_delta.y(), prev_delta.x())
                        next_angle = math.atan2(next_delta.y(), next_delta.x())
                        if mode == TangentPointMode.EQUAL:
                            old_rad = math.hypot(next_delta.x(), next_delta.y())
                        else:  # TANGENT
                            old_rad = math.hypot(prev_delta.x(), prev_delta.y())
                        new_point = mid_point + QPointF(
                            old_rad * math.cos(next_angle + math.pi),
                            old_rad * math.sin(next_angle + math.pi)
                        )
                        self.set_point(index - 2, new_point)
                elif closed and index == 1:
                    # Closed: anchor is p0 (== p_last); opposite handle wraps to p_last-1
                    mid_point = self.get_point(0)
                    prev_point = self.get_point(n - 2)
                    if mid_point and prev_point:
                        prev_delta = prev_point - mid_point
                        next_delta = new_position - mid_point
                        prev_angle = math.atan2(prev_delta.y(), prev_delta.x())
                        next_angle = math.atan2(next_delta.y(), next_delta.x())
                        if mode == TangentPointMode.EQUAL:
                            old_rad = math.hypot(next_delta.x(), next_delta.y())
                        else:  # TANGENT
                            old_rad = math.hypot(prev_delta.x(), prev_delta.y())
                        new_point = mid_point + QPointF(
                            old_rad * math.cos(next_angle + math.pi),
                            old_rad * math.sin(next_angle + math.pi)
                        )
                        self.set_point(n - 2, new_point)

        self.update_all()
