from PySide6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent
from PySide6.QtCore import Qt, QPointF, QTimer
from PySide6.QtGui import QPen, QColor, QBrush, QPainterPath
from ..graphics_items.cad_item import CadItem
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
        """Find a CAD item at the given scene position."""
        items = self.items(scene_pos)
        for item in items:
            if isinstance(item, CadItem):
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

    def set_snaps_system(self, snaps_system):
        """Set the snaps system reference for this scene."""
        self._snaps_system = snaps_system
    
    def get_precision(self):
        """Get the precision setting for this scene."""
        return self._precision
    
    def set_precision(self, precision):
        """Set the precision setting for this scene."""
        self._precision = precision

    def update_all_control_datums_precision(self, new_precision: int):
        """Update precision for all ControlDatums in all CAD items in the scene."""
        for item in self.items():
            if isinstance(item, CadItem):
                item.update_control_datums_precision(new_precision)

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
        """Handle dragging of a CAD item."""
        if self._dragging_item:
            delta = scene_pos - self._last_mouse_pos
            self._dragging_item.moveBy(delta.x(), delta.y())
            
            # Update control point positions after the CAD item moves
            self._update_control_points_for_cad_item(self._dragging_item)
            
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
        
        # Update control point positions to scene coordinates
        self._update_control_point_positions(cad_item)
        
        # Update ControlDatum precision to match current scene precision
        cad_item.update_control_datums_precision(self._precision)
        
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
        
        # Check if control points already exist
        if not hasattr(cad_item, '_control_point_items') or not cad_item._control_point_items:
            # Create control points by calling the CAD item's createControls method
            cad_item.createControls()
        
        # Use the control points created by the CAD item itself
        if hasattr(cad_item, '_control_point_items') and cad_item._control_point_items:
            for cp in cad_item._control_point_items:
                if cp:
                    # Add the control point to the scene if it's not already there
                    if cp.scene() != self:
                        self.addItem(cp)
                    cp.setVisible(False)
                    
                    # Categorize control points vs control datums
                    if hasattr(cp, 'prefix'):  # ControlDatum has prefix attribute
                        control_datums.append(cp)
                    else:
                        control_points.append(cp)
        
        self._control_points[cad_item] = control_points
        self._control_datums[cad_item] = control_datums

    def _move_control_point(self, cad_item: CadItem, cp_index: int, new_pos: QPointF):
        """Move a control point for a CAD item."""
        # Convert scene coordinates to item coordinates
        item_pos = cad_item.mapFromScene(new_pos)
        
        # Call the CAD item's control point movement method if available
        if hasattr(cad_item, '_set_point'):
            getattr(cad_item, '_set_point')(cp_index, item_pos)
        elif hasattr(cad_item, 'move_control_point'):
            getattr(cad_item, 'move_control_point')(cp_index, item_pos.x(), item_pos.y())

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

    def _update_control_point_positions(self, cad_item: CadItem):
        """Update control point positions to scene coordinates."""
        if cad_item in self._control_points:
            # Get the updated control point positions from the CAD item
            cp_data = cad_item.getControlPoints() if hasattr(cad_item, 'getControlPoints') else []
            
            # Update control point positions
            for i, cp in enumerate(self._control_points[cad_item]):
                if cp and i < len(cp_data):
                    # Use the positions directly (they are already in scene coordinates)
                    cp.setPos(cp_data[i])
        
        # Update control datum positions
        if cad_item in self._control_datums:
            for cd in self._control_datums[cad_item]:
                if cd and hasattr(cad_item, 'updateControls'):
                    # Call updateControls to update datum positions and values
                    cad_item.updateControls()

    def _update_control_points_for_cad_item(self, cad_item: CadItem):
        """Update control point positions for a CAD item after modification."""
        if cad_item in self._control_points:
            # Get the updated control point positions from the CAD item
            cp_data = cad_item.getControlPoints() if hasattr(cad_item, 'getControlPoints') else []
            
            # Update control point positions
            for i, cp in enumerate(self._control_points[cad_item]):
                if cp and i < len(cp_data):
                    # Use the positions directly (they are already in scene coordinates)
                    cp.setPos(cp_data[i])
        
        # Update control datum positions
        if cad_item in self._control_datums:
            for cd in self._control_datums[cad_item]:
                if cd and hasattr(cad_item, 'updateControls'):
                    # Call updateControls to update datum positions and values
                    cad_item.updateControls()

    def _update_selection_state(self):
        """Update the selection state (called by timer)."""
        # This method can be used for any periodic selection state updates
        pass
