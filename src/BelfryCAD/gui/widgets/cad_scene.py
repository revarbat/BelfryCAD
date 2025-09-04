import math
from typing import Optional

from PySide6.QtCore import Qt, QPointF, QTimer, Signal
from PySide6.QtGui import QKeyEvent, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene, QGraphicsSceneMouseEvent

from ..graphics_items.cad_arc_graphics_item import CadArcGraphicsItem


class CadScene(QGraphicsScene):
    """Custom graphics scene for CAD operations with centralized event handling."""

    # Signal to emit when selection changes with object IDs
    scene_selection_changed = Signal(set)  # set of selected object_ids

    def __init__(self, parent=None, precision=3):
        super().__init__(parent)
        
        # Store precision for CAD items to use
        self._precision = precision
        
        # Flag to prevent circular selection updates
        self._updating_selection_from_tree = False
        
        # Flag to prevent control point updates during dragging
        self._control_point_dragging = False
        
        # Control point management
        self._control_points = {}
        self._control_datums = {}
        
        # Snaps system reference (will be set by main window)
        self._snaps_system = None
        
        # CadTool manager reference (will be set by document window)
        self._tool_manager = None
        
        # Connect to Qt's built-in selection changed signal
        self.selectionChanged.connect(self._on_selection_changed)

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
        
        # This is now handled by Qt's built-in selection system
        
        super().removeItem(item)

    def addArc(
            self,
            center: QPointF,
            radius: float,
            start_degrees: float,
            end_degrees: float,
            pen: Optional[QPen] = None,
    ) -> CadArcGraphicsItem:
        """Add an arc to the scene."""
        arc_item = CadArcGraphicsItem(
            center, radius, start_degrees, end_degrees
        )
        if pen is not None:
            arc_item.setPen(pen)
        arc_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        arc_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        arc_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, False)
        self.addItem(arc_item)
        return arc_item

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

    def set_control_point_dragging(self, dragging: bool):
        """Set flag to indicate control point is being dragged."""
        self._control_point_dragging = dragging

    def set_tool_manager(self, tool_manager):
        """Set the tool manager reference."""
        self._tool_manager = tool_manager

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """Handle mouse press events and delegate to active tool."""
        # First, let Qt handle the event normally (for selection, etc.)
        super().mousePressEvent(event)
        
        # If event was accepted by an item, don't process for tools
        if event.isAccepted():
            return
        
        # Delegate to active tool if available
        if self._tool_manager and self._tool_manager.get_active_tool():
            active_tool = self._tool_manager.get_active_tool()
            active_tool.handle_mouse_down(event)
            event.accept()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        """Handle mouse move events and delegate to active tool."""
        # First, let Qt handle the event normally
        super().mouseMoveEvent(event)
        
        # Delegate to active tool if available
        if self._tool_manager and self._tool_manager.get_active_tool():
            active_tool = self._tool_manager.get_active_tool()
            active_tool.handle_mouse_move(event)
            event.accept()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """Handle mouse release events and delegate to active tool."""
        # First, let Qt handle the event normally
        super().mouseReleaseEvent(event)
        
        # Delegate to active tool if available
        if self._tool_manager and self._tool_manager.get_active_tool():
            active_tool = self._tool_manager.get_active_tool()
            active_tool.handle_mouse_up(event)
            event.accept()

    def keyPressEvent(self, event):
        """Handle key press events and delegate to active tool."""
        # Delegate to active tool if available
        if self._tool_manager and self._tool_manager.get_active_tool():
            active_tool = self._tool_manager.get_active_tool()
            active_tool.handle_key_press(event)
            if event.isAccepted():
                return
        
        # Let Qt handle the event normally
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """Handle key release events and delegate to active tool."""
        # Delegate to active tool if available
        if self._tool_manager and self._tool_manager.get_active_tool():
            active_tool = self._tool_manager.get_active_tool()
            active_tool.handle_key_release(event)
            if event.isAccepted():
                return
        
        # Let Qt handle the event normally
        super().keyReleaseEvent(event)

    def _on_selection_changed(self):
        """Handle selection changes and emit signals with object IDs."""
        # Don't emit signals if we're updating selection from tree to prevent circular updates
        if self._updating_selection_from_tree:
            return
        
        # Don't update control points if we're dragging one
        if self._control_point_dragging:
            return
            
        # Get all selected items
        selected_items = self.selectedItems()
        selected_object_ids = set()
        
        # Update control points for selected items
        self._hide_all_control_points()
        
        for item in selected_items:
            # Get the viewmodel from the item data
            viewmodel = item.data(0)
            if viewmodel and hasattr(viewmodel, 'is_selected'):
                # Update the viewmodel's selection state
                viewmodel.is_selected = True
                try:
                    self._show_control_points_for_viewmodel(viewmodel)
                except Exception as e:
                    # Log the error but don't crash
                    print(f"Error showing control points for viewmodel: {e}")
                # Collect object ID for the signal
                if hasattr(viewmodel, '_cad_object') and viewmodel._cad_object:
                    object_id = viewmodel._cad_object.object_id
                    selected_object_ids.add(object_id)
        
        # Update non-selected viewmodels
        for item in self.items():
            if item not in selected_items:
                viewmodel = item.data(0)
                if viewmodel and hasattr(viewmodel, 'is_selected'):
                    viewmodel.is_selected = False
        
        # Emit the signal with selected object IDs
        self.scene_selection_changed.emit(selected_object_ids)

    def set_updating_from_tree(self, updating: bool):
        """Set flag to indicate we're updating selection from tree (to prevent circular updates)."""
        self._updating_selection_from_tree = updating

    def is_updating_from_tree(self) -> bool:
        """Get flag indicating if we're updating selection from tree."""
        return getattr(self, '_updating_selection_from_tree', False)

    def _show_control_points_for_viewmodel(self, viewmodel):
        """Show control points for a specific viewmodel."""
        # Defensive check to ensure viewmodel has controls
        if not hasattr(viewmodel, 'controls'):
            return
            
        # Get control points and datums from viewmodel
        control_points = viewmodel.controls
        
        # Update control point positions to scene coordinates
        try:
            self._update_control_point_positions_for_viewmodel(viewmodel)
        except Exception as e:
            # Log the error but don't crash
            print(f"Error updating control point positions: {e}")
        
        # Show control points
        for cp in control_points:
            if cp and hasattr(cp, 'setVisible'):
                try:
                    cp.setVisible(True)
                except Exception as e:
                    # Log the error but don't crash
                    print(f"Error setting control point visibility: {e}")
        
        # Show control datums
        for cd in control_points:  # Control datums are also in controls list
            if hasattr(cd, 'setVisible') and cd:
                try:
                    cd.setVisible(True)
                except Exception as e:
                    # Log the error but don't crash
                    print(f"Error setting control datum visibility: {e}")

    def _hide_all_control_points(self):
        """Hide all control points and control datums."""
        for control_points in self._control_points.values():
            for cp in control_points:
                if cp and hasattr(cp, 'setVisible'):
                    try:
                        cp.setVisible(False)
                    except Exception as e:
                        # Log the error but don't crash
                        print(f"Error hiding control point: {e}")
        
        for control_datums in self._control_datums.values():
            for cd in control_datums:
                if cd and hasattr(cd, 'setVisible'):
                    try:
                        cd.setVisible(False)
                    except Exception as e:
                        # Log the error but don't crash
                        print(f"Error hiding control datum: {e}")

    def _update_control_point_positions_for_viewmodel(self, viewmodel):
        """Update control point positions for a viewmodel."""
        # This will be handled by the viewmodel's update_controls method
        # The viewmodel manages its own control point positions
        pass
