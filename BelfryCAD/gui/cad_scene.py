from PySide6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent
from PySide6.QtCore import Qt, QPointF, QTimer
from PySide6.QtGui import QPen, QColor, QBrush, QPainterPath
from .cad_item import CadItem
from .control_points import ControlPoint, ControlDatum


class CadScene(QGraphicsScene):
    """Custom graphics scene for CAD operations with centralized event handling."""

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Dictionary to store tags for each item: {item: set_of_tags}
        self._item_tags = {}
        # Reverse lookup dictionary: {tag: set_of_items}
        self._tag_items = {}
        
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

    def add_tag_to_item(self, item, tag: str):
        """Add a tag to an item."""
        if item not in self._item_tags:
            self._item_tags[item] = set()
        self._item_tags[item].add(tag)

        # Update reverse lookup
        if tag not in self._tag_items:
            self._tag_items[tag] = set()
        self._tag_items[tag].add(item)

    def remove_tag_from_item(self, item, tag: str):
        """Remove a tag from an item."""
        if item in self._item_tags:
            self._item_tags[item].discard(tag)
            # Clean up empty tag sets
            if not self._item_tags[item]:
                del self._item_tags[item]

        # Update reverse lookup
        if tag in self._tag_items:
            self._tag_items[tag].discard(item)
            # Clean up empty item sets
            if not self._tag_items[tag]:
                del self._tag_items[tag]

    def set_item_tags(self, item, tags: list):
        """Set all tags for an item (replaces existing tags)."""
        # Remove item from all existing tags in reverse lookup
        if item in self._item_tags:
            for old_tag in self._item_tags[item]:
                if old_tag in self._tag_items:
                    self._tag_items[old_tag].discard(item)
                    if not self._tag_items[old_tag]:
                        del self._tag_items[old_tag]

        # Set new tags
        if tags:
            self._item_tags[item] = set(tags)
            # Update reverse lookup for new tags
            for tag in tags:
                if tag not in self._tag_items:
                    self._tag_items[tag] = set()
                self._tag_items[tag].add(item)
        elif item in self._item_tags:
            del self._item_tags[item]

    def get_item_tags(self, item) -> set:
        """Get all tags for an item."""
        return self._item_tags.get(item, set()).copy()

    def has_tag(self, item, tag: str) -> bool:
        """Check if an item has a specific tag."""
        return item in self._item_tags and tag in self._item_tags[item]

    def get_items_with_tag(self, tag: str) -> list:
        """Get all items that have a specific tag."""
        return list(self._tag_items.get(tag, set()))

    def get_items_with_all_tags(self, tags: list) -> list:
        """Get all items that have ALL of the specified tags."""
        if not tags:
            return []

        # Start with items that have the first tag, then intersect with others
        result_set = self._tag_items.get(tags[0], set()).copy()
        for tag in tags[1:]:
            if tag in self._tag_items:
                result_set.intersection_update(self._tag_items[tag])
            else:
                # If any tag doesn't exist, no items can have all tags
                return []

        return list(result_set)

    def get_items_with_any_tags(self, tags: list) -> list:
        """Get all items that have ANY of the specified tags."""
        if not tags:
            return []

        # Union all items that have any of the specified tags
        result_set = set()
        for tag in tags:
            if tag in self._tag_items:
                result_set.update(self._tag_items[tag])

        return list(result_set)

    def clear_item_tags(self, item):
        """Remove all tags from an item."""
        if item in self._item_tags:
            # Remove item from all tags in reverse lookup
            for tag in self._item_tags[item]:
                if tag in self._tag_items:
                    self._tag_items[tag].discard(item)
                    if not self._tag_items[tag]:
                        del self._tag_items[tag]
            del self._item_tags[item]

    def removeItem(self, item):
        """Override removeItem to clean up tags and control points when items are removed."""
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
        
        # Clean up tags
        self.clear_item_tags(item)
        
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
            if isinstance(item, ControlPoint) or isinstance(item, ControlDatum):
                if item.isVisible():
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
        if isinstance(control, ControlDatum):
            # Start editing the control datum
            control.start_editing()
        else:
            # Check for Command-click cycling on CubicBezierCadItem control points
            ctrl_pressed = event.modifiers() & Qt.KeyboardModifier.ControlModifier
            if ctrl_pressed and hasattr(control, 'cad_item'):
                cad_item = control.cad_item
                # Check if this is a CubicBezierCadItem
                if hasattr(cad_item, '_handle_control_point_click'):
                    # Find the control point index
                    if hasattr(cad_item, '_control_points') and control in cad_item._control_points:
                        point_index = cad_item._control_points.index(control)
                        # Call the control point click handler
                        if cad_item._handle_control_point_click(point_index, event.modifiers()):
                            event.accept()
                            return
            
            # Start dragging the control point
            self._dragging_control_point = control
            self._drag_start_pos = event.scenePos()
            control.setCursor(Qt.CursorShape.DragMoveCursor)
        
        event.accept()

    def _handle_cad_item_press(self, cad_item: CadItem, event: QGraphicsSceneMouseEvent):
        """Handle mouse press on a CAD item."""
        # Handle selection based on modifiers
        shift_pressed = event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ctrl_pressed = event.modifiers() & Qt.KeyboardModifier.ControlModifier
        
        if shift_pressed:
            # Add to selection
            self._add_to_selection(cad_item)
        elif ctrl_pressed:
            # Toggle selection
            self._toggle_selection(cad_item)
        else:
            # Single selection
            self._set_single_selection(cad_item)
        
        # Start dragging if the item is movable
        if cad_item.flags() & cad_item.GraphicsItemFlag.ItemIsMovable:
            self._dragging_item = cad_item
            self._drag_start_pos = event.scenePos()
        
        event.accept()

    def _handle_control_drag(self, scene_pos: QPointF, event: QGraphicsSceneMouseEvent):
        """Handle dragging of a control point."""
        if not self._dragging_control_point:
            return
        if not self._dragging_control_point.isVisible():
            return

        # Find the CAD item that owns this control point
        cp = self._dragging_control_point
        cad_item = cp.cad_item if hasattr(cp, 'cad_item') else None
        
        if cad_item:
            self._dragging_control_point.setPos(scene_pos)
            self._dragging_control_point.call_setter_with_updates(scene_pos)
        
        event.accept()

    def _handle_cad_item_drag(self, scene_pos: QPointF, event: QGraphicsSceneMouseEvent):
        """Handle dragging of a CAD item."""
        if not self._dragging_item:
            return
        
        # Calculate the movement delta
        delta = scene_pos - self._drag_start_pos
        
        # Move the CAD item
        current_pos = self._dragging_item.pos()
        new_pos = current_pos + delta
        self._dragging_item.setPos(new_pos)
        
        # Update control point positions
        self._update_control_points_for_item(self._dragging_item)
        
        # Update drag start position for next move
        self._drag_start_pos = scene_pos
        
        event.accept()

    def _handle_control_release(self, event: QGraphicsSceneMouseEvent):
        """Handle release of a control point."""
        if self._dragging_control_point:
            self._dragging_control_point.setCursor(Qt.CursorShape.ArrowCursor)
            self._dragging_control_point = None
        
        event.accept()

    def _handle_cad_item_release(self, event: QGraphicsSceneMouseEvent):
        """Handle release of a CAD item."""
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
        """Set a single CAD item as selected."""
        # Clear current selection
        self._clear_selection()
        
        # Add the new item
        self._selected_items.add(cad_item)
        cad_item.setSelected(True)
        self._update_control_points()

    def _clear_selection(self):
        """Clear all selections."""
        for item in self._selected_items:
            item.setSelected(False)
        self._selected_items.clear()
        self._hide_all_control_points()

    def _update_control_points(self):
        """Update control points based on current selection."""
        # Hide all control points first
        self._hide_all_control_points()
        
        # Show control points only for singly selected items
        if len(self._selected_items) == 1:
            cad_item = next(iter(self._selected_items))
            self._show_control_points_for_item(cad_item)

    def _show_control_points_for_item(self, cad_item: CadItem):
        """Show control points for a specific CAD item."""
        # Create control points if they don't exist
        if cad_item not in self._control_points:
            self._create_control_points_for_item(cad_item)
        
        # Show control points
        if cad_item in self._control_points:
            for cp in self._control_points[cad_item]:
                if cp:
                    cp.setVisible(True)
        
        # Show control datums
        if cad_item in self._control_datums:
            for cd in self._control_datums[cad_item]:
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
        if not hasattr(cad_item, 'createControls'):
            return
        
        try:
            # Get control points from the CAD item
            control_points = cad_item.createControls()
            if control_points:
                for cp in control_points:
                    if cp:
                        self.addItem(cp)
                
                self._control_points[cad_item] = control_points
                
                # Update control point positions after creation
                self._update_control_points_for_item(cad_item)
        except Exception as e:
            print(f"Error creating control points: {e}")

    def _update_control_points_for_item(self, cad_item: CadItem):
        """Update control point positions for a CAD item."""
        if cad_item not in self._control_points:
            return
        
        # Update control point positions based on CAD item's current geometry
        if hasattr(cad_item, 'updateControls'):
            cad_item.updateControls()
        
    def _update_selection_state(self):
        """Update selection state and control points."""
        # This method can be called periodically to ensure consistency
        pass
