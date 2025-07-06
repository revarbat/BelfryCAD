from PySide6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent
from PySide6.QtCore import Qt, QPointF, QTimer
from PySide6.QtGui import QPen, QColor, QBrush, QPainterPath
from ..graphics_items.cad_item import CadItem
from ..graphics_items.control_points import ControlPoint, ControlDatum


class CadScene(QGraphicsScene):
    """Custom graphics scene for CAD operations with centralized event handling."""

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Selection and interaction state
        self._selected_items = set()
        self._dragging_item = None
        self._dragging_control_point = None
        self._drag_start_pos = QPointF()
        self._last_mouse_pos = QPointF()
        
        # Control point management
        self._control_points = {}  # {cad_item: [control_points]}
        self._control_datums = {}  # {cad_item: [control_datums]}
        
        # Timer for selection state updates
        self._selection_timer = QTimer()
        self._selection_timer.timeout.connect(self._update_selection_state)
        self._selection_timer.setInterval(50)  # 50ms

    def removeItem(self, item):
        """Override removeItem to clean up control points when items are removed."""
        # Clean up control points
        if item in self._control_points:
            for cp in self._control_points[item]:
                if cp:
                    self.removeItem(cp)
            del self._control_points[item]
        
        if item in self._control_datums:
            for cd in self._control_datums[item]:
                if cd:
                    self.removeItem(cd)
            del self._control_datums[item]
        
        # Remove from selection
        self._selected_items.discard(item)
        
        super().removeItem(item)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """Handle all mouse press events."""
        scene_pos = event.scenePos()
        self._last_mouse_pos = scene_pos
        
        # Check if clicking on a control point or control datum
        clicked_control = self._find_control_at_position(scene_pos)
        if clicked_control:
            self._handle_control_press(clicked_control, event)
            return
        
        # Check if clicking on a CAD item
        clicked_item = self._find_cad_item_at_position(scene_pos)
        if clicked_item:
            self._handle_cad_item_press(clicked_item, event)
            return
        
        # Clicked on empty space - clear selection
        self._clear_selection()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        """Handle all mouse move events."""
        scene_pos = event.scenePos()
        
        if self._dragging_control_point:
            self._handle_control_drag(scene_pos, event)
        elif self._dragging_item:
            self._handle_cad_item_drag(scene_pos, event)
        
        self._last_mouse_pos = scene_pos
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """Handle all mouse release events."""
        if self._dragging_control_point:
            self._handle_control_release(event)
        elif self._dragging_item:
            self._handle_cad_item_release(event)
        
        super().mouseReleaseEvent(event)

    def _find_control_at_position(self, scene_pos: QPointF):
        """Find a control point or control datum at the given scene position."""
        items = self.items(scene_pos)
        for item in items:
            if isinstance(item, (ControlPoint, ControlDatum)):
                return item
        return None

    def _find_cad_item_at_position(self, scene_pos: QPointF):
        """Find a CAD item at the given scene position."""
        items = self.items(scene_pos)
        for item in items:
            if isinstance(item, CadItem):
                return item
        return None

    def _handle_control_press(self, control, event: QGraphicsSceneMouseEvent):
        """Handle mouse press on a control point or control datum."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging_control_point = control
            self._drag_start_pos = event.scenePos()
            control.set_dragging(True)
            event.accept()
        else:
            super().mousePressEvent(event)

    def _handle_cad_item_press(self, cad_item: CadItem, event: QGraphicsSceneMouseEvent):
        """Handle mouse press on a CAD item."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Handle selection
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self._toggle_selection(cad_item)
            elif event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                self._add_to_selection(cad_item)
            else:
                self._set_single_selection(cad_item)
            
            # Start dragging if not just selecting
            if not (event.modifiers() & (Qt.KeyboardModifier.ShiftModifier | Qt.KeyboardModifier.ControlModifier)):
                self._dragging_item = cad_item
                self._drag_start_pos = event.scenePos()
            
            event.accept()
        else:
            super().mousePressEvent(event)

    def _handle_control_drag(self, scene_pos: QPointF, event: QGraphicsSceneMouseEvent):
        """Handle dragging of a control point or control datum."""
        if self._dragging_control_point:
            delta = scene_pos - self._last_mouse_pos
            self._dragging_control_point.moveBy(delta.x(), delta.y())
            event.accept()

    def _handle_cad_item_drag(self, scene_pos: QPointF, event: QGraphicsSceneMouseEvent):
        """Handle dragging of a CAD item."""
        if self._dragging_item:
            delta = scene_pos - self._last_mouse_pos
            self._dragging_item.moveBy(delta.x(), delta.y())
            event.accept()

    def _handle_control_release(self, event: QGraphicsSceneMouseEvent):
        """Handle mouse release on a control point or control datum."""
        if self._dragging_control_point:
            self._dragging_control_point.set_dragging(False)
            self._dragging_control_point = None
            event.accept()

    def _handle_cad_item_release(self, event: QGraphicsSceneMouseEvent):
        """Handle mouse release on a CAD item."""
        if self._dragging_item:
            self._dragging_item = None
            event.accept()

    def _add_to_selection(self, cad_item: CadItem):
        """Add a CAD item to the current selection."""
        self._selected_items.add(cad_item)
        cad_item.setSelected(True)
        self._update_control_points()

    def _toggle_selection(self, cad_item: CadItem):
        """Toggle the selection state of a CAD item."""
        if cad_item in self._selected_items:
            self._selected_items.discard(cad_item)
            cad_item.setSelected(False)
        else:
            self._selected_items.add(cad_item)
            cad_item.setSelected(True)
        self._update_control_points()

    def _set_single_selection(self, cad_item: CadItem):
        """Set a single CAD item as the only selected item."""
        # Clear current selection
        for item in self._selected_items:
            item.setSelected(False)
        self._selected_items.clear()
        
        # Set new selection
        self._selected_items.add(cad_item)
        cad_item.setSelected(True)
        self._update_control_points()

    def _clear_selection(self):
        """Clear all selections."""
        for item in self._selected_items:
            item.setSelected(False)
        self._selected_items.clear()
        self._update_control_points()

    def _update_control_points(self):
        """Update control points for all selected items."""
        self._hide_all_control_points()
        
        for cad_item in self._selected_items:
            self._show_control_points_for_item(cad_item)

    def _show_control_points_for_item(self, cad_item: CadItem):
        """Show control points for a specific CAD item."""
        if cad_item not in self._control_points:
            self._create_control_points_for_item(cad_item)
        
        # Show control points
        for cp in self._control_points.get(cad_item, []):
            if cp:
                cp.setVisible(True)
        
        # Show control datums
        for cd in self._control_datums.get(cad_item, []):
            if cd:
                cd.setVisible(True)

    def _hide_all_control_points(self):
        """Hide all control points and control datums."""
        for control_points in self._control_points.values():
            for cp in control_points:
                if cp:
                    cp.setVisible(False)
        
        for control_datums in self._control_datums.values():
            for cd in control_datums:
                if cd:
                    cd.setVisible(False)

    def _create_control_points_for_item(self, cad_item: CadItem):
        """Create control points for a CAD item."""
        control_points = []
        control_datums = []
        
        # Get control point data from the CAD item
        cp_data = cad_item.get_control_points()
        if cp_data:
            for i, (x, y, cp_type) in enumerate(cp_data):
                cp = ControlPoint(x, y, cp_type, cad_item, i)
                self.addItem(cp)
                cp.setVisible(False)
                control_points.append(cp)
        
        # Get control datum data from the CAD item
        cd_data = cad_item.get_control_datums()
        if cd_data:
            for i, (x, y, datum_type) in enumerate(cd_data):
                cd = ControlDatum(x, y, datum_type, cad_item, i)
                self.addItem(cd)
                cd.setVisible(False)
                control_datums.append(cd)
        
        self._control_points[cad_item] = control_points
        self._control_datums[cad_item] = control_datums

    def _update_control_points_for_item(self, cad_item: CadItem):
        """Update control points for a CAD item (e.g., after item modification)."""
        # Remove old control points
        if cad_item in self._control_points:
            for cp in self._control_points[cad_item]:
                if cp:
                    self.removeItem(cp)
            del self._control_points[cad_item]
        
        if cad_item in self._control_datums:
            for cd in self._control_datums[cad_item]:
                if cd:
                    self.removeItem(cd)
            del self._control_datums[cad_item]
        
        # Create new control points if item is selected
        if cad_item in self._selected_items:
            self._create_control_points_for_item(cad_item)
            self._show_control_points_for_item(cad_item)

    def _update_selection_state(self):
        """Update the selection state (called by timer)."""
        # This method can be used for any periodic selection state updates
        pass
