from PySide6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent
from PySide6.QtCore import Qt, QPointF, QTimer



from ..graphics_items.control_points import ControlPoint, ControlDatum


class CadScene(QGraphicsScene):
    """Custom graphics scene for CAD operations with centralized event handling."""

    def __init__(self, parent=None, precision=3):
        super().__init__(parent)
        
        # Store precision for CAD items to use
        self._precision = precision
        
        # Selection and interaction state
        self._selected_items = set()
        self._dragging_item = None
        self._dragging_control_point = None
        self._drag_start_pos = QPointF()
        self._last_mouse_pos = QPointF()
        
        # Control point management
        self._control_points = {}  # {cad_item: [control_points]}
        self._control_datums = {}  # {cad_item: [control_datums]}
        
        # Snaps system reference (will be set by main window)
        self._snaps_system = None
        
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
        """Find a view item at the given scene position."""
        items = self.items(scene_pos)
        for item in items:
            # Check if this item has a viewmodel reference in data slot 0
            viewmodel = item.data(0)
            if viewmodel and hasattr(viewmodel, 'object_type'):
                return item
        return None

    def _handle_control_press(self, control, event: QGraphicsSceneMouseEvent):
        """Handle mouse press on a control point or control datum."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Handle ControlDatum differently - let it handle its own click event
            if isinstance(control, ControlDatum):
                # Let the ControlDatum handle its own mouse press event for editing
                control.mousePressEvent(event)
                return
            
            # For regular ControlPoints, start dragging
            self._dragging_control_point = control
            self._drag_start_pos = event.scenePos()
            control.set_dragging(True)
            event.accept()
        else:
            super().mousePressEvent(event)

    def _handle_cad_item_press(self, view_item, event: QGraphicsSceneMouseEvent):
        """Handle mouse press on a view item."""
        viewmodel = view_item.data(0)
        if not viewmodel:
            return
        
        # Handle selection based on modifier keys
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Ctrl+click: toggle selection
            self._toggle_selection(view_item)
        else:
            # Regular click: set single selection
            self._set_single_selection(view_item)
        
        # Start dragging if this is a left button press
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging_item = view_item
            self._drag_start_pos = event.scenePos()
        
        event.accept()

    def set_snaps_system(self, snaps_system):
        """Set the snaps system reference."""
        self._snaps_system = snaps_system

    def get_precision(self):
        """Get the current precision setting."""
        return self._precision

    def set_precision(self, precision):
        """Set the precision setting."""
        self._precision = precision

    def update_all_control_datums_precision(self, new_precision: int):
        """Update precision for all control datums."""
        self._precision = new_precision
        # This is now handled by viewmodels

    def refresh_gear_items_for_unit_change(self):
        """Refresh gear items when units change."""
        # This is now handled by viewmodels
        pass

    def _handle_control_drag(self, scene_pos: QPointF, event: QGraphicsSceneMouseEvent):
        """Handle dragging of a control point or control datum."""
        if self._dragging_control_point:
            # Don't drag ControlDatum items
            if isinstance(self._dragging_control_point, ControlDatum):
                return
            
            # Apply snapping if snaps system is available
            snapped_pos = scene_pos
            if self._snaps_system:
                # Exclude the current control point from snapping to avoid self-snapping
                exclude_cps = [self._dragging_control_point] if self._dragging_control_point else None
                # Exclude the CAD item that owns this control point from quadrant snapping
                exclude_cad_item = self._dragging_control_point.cad_item if self._dragging_control_point else None
                snapped_pos = self._snaps_system.get_snap_point(scene_pos, exclude_cps=exclude_cps, exclude_cad_item=exclude_cad_item)
            
            # Update the control point position
            self._dragging_control_point.setPos(snapped_pos)
            
            # Call the setter to update the CAD item
            if hasattr(self._dragging_control_point, 'setter') and self._dragging_control_point.setter:
                # Pass snapped coordinates to the setter
                cad_item = self._dragging_control_point.cad_item
                if cad_item:
                    self._dragging_control_point.call_setter_with_updates(snapped_pos)
                    
                    # Update control point positions after CAD item modification
                    self._update_control_points_for_cad_item(cad_item)
            
            event.accept()

    def _handle_cad_item_drag(self, scene_pos: QPointF, event: QGraphicsSceneMouseEvent):
        """Handle dragging of a view item."""
        if not self._dragging_item:
            return
        
        viewmodel = self._dragging_item.data(0)
        if not viewmodel:
            return
        
        # Calculate the translation
        delta = scene_pos - self._last_mouse_pos
        
        # Apply translation to the viewmodel
        viewmodel.translate(delta.x(), delta.y())
        
        # Update the view items
        viewmodel.update_view(self)
        
        event.accept()

    def _handle_control_release(self, event: QGraphicsSceneMouseEvent):
        """Handle mouse release on a control point or control datum."""
        if self._dragging_control_point:
            self._dragging_control_point.set_dragging(False)
            self._dragging_control_point = None
            event.accept()

    def _handle_cad_item_release(self, event: QGraphicsSceneMouseEvent):
        """Handle release of a view item drag."""
        if self._dragging_item:
            viewmodel = self._dragging_item.data(0)
            if viewmodel:
                # Emit the object_moved signal
                viewmodel.object_moved.emit(viewmodel.cad_object.center_point.to_qpointf())
            self._dragging_item = None

    def _add_to_selection(self, view_item):
        """Add a view item to the current selection using its viewmodel reference."""
        viewmodel = view_item.data(0)
        if viewmodel:
            self._selected_items.add(view_item)
            view_item.setSelected(True)
            # Update the viewmodel's selection state
            viewmodel.is_selected = True
            self._update_control_points()

    def _toggle_selection(self, view_item):
        """Toggle the selection state of a view item using its viewmodel reference."""
        viewmodel = view_item.data(0)
        if viewmodel:
            if view_item in self._selected_items:
                self._selected_items.discard(view_item)
                view_item.setSelected(False)
                viewmodel.is_selected = False
            else:
                self._selected_items.add(view_item)
                view_item.setSelected(True)
                viewmodel.is_selected = True
            self._update_control_points()

    def _set_single_selection(self, view_item):
        """Set a single view item as the only selected item using its viewmodel reference."""
        # Clear current selection
        for item in self._selected_items:
            item.setSelected(False)
            viewmodel = item.data(0)
            if viewmodel:
                viewmodel.is_selected = False
        self._selected_items.clear()
        
        # Set new selection
        viewmodel = view_item.data(0)
        if viewmodel:
            self._selected_items.add(view_item)
            view_item.setSelected(True)
            viewmodel.is_selected = True
            self._update_control_points()

    def _clear_selection(self):
        """Clear all selections."""
        for item in self._selected_items:
            item.setSelected(False)
            viewmodel = item.data(0)
            if viewmodel:
                viewmodel.is_selected = False
        self._selected_items.clear()
        self._update_control_points()

    def _update_control_points(self):
        """Update control points for all selected items."""
        self._hide_all_control_points()
        
        for view_item in self._selected_items:
            viewmodel = view_item.data(0)
            if viewmodel:
                self._show_control_points_for_viewmodel(viewmodel)

    def _show_control_points_for_viewmodel(self, viewmodel):
        """Show control points for a specific viewmodel."""
        # Get control points and datums from viewmodel
        control_points = viewmodel.controls
        
        # Update control point positions to scene coordinates
        self._update_control_point_positions_for_viewmodel(viewmodel)
        
        # Show control points
        for cp in control_points:
            if cp:
                cp.setVisible(True)
        
        # Show control datums
        for cd in control_points:  # Control datums are also in controls list
            if hasattr(cd, 'setVisible') and cd:
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

    def _update_control_point_positions_for_viewmodel(self, viewmodel):
        """Update control point positions for a viewmodel."""
        # This will be handled by the viewmodel's update_controls method
        # The viewmodel manages its own control point positions
        pass

    def _update_selection_state(self):
        """Update the selection state (called by timer)."""
        # This method can be used for any periodic selection state updates
        pass
