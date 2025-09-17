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
        
        # Snaps system reference (will be set by main window)
        self._snaps_system = None
        
        # CadTool manager reference (will be set by document window)
        self._tool_manager = None
        
        # Timer for animating selection outlines
        self._selection_animation_timer = QTimer()
        self._selection_animation_timer.timeout.connect(self._animate_selection_outlines)
        # Start with 50ms interval for smooth animation (20 FPS)
        self._selection_animation_timer.start(50)
        
        # Connect to Qt's built-in selection changed signal
        self.selectionChanged.connect(self._on_selection_changed)

    def removeItem(self, item):
        """Override removeItem to clean up when items are removed."""
        # Remove the item from the scene
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

    def get_precision(self):
        """Get the current precision setting."""
        return self._precision

    def set_precision(self, precision: int):
        """Set the precision setting."""
        self._precision = precision

    def add_snaps_system(self, snaps_system):
        """Add snaps system reference."""
        self._snaps_system = snaps_system

    def remove_snaps_system(self):
        """Remove snaps system reference."""
        self._snaps_system = None

    def get_snaps_system(self):
        """Get the snaps system reference."""
        return self._snaps_system

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

    def _animate_selection_outlines(self):
        """Update all selected items to animate their selection outlines."""
        # Get all selected items and trigger their update to animate the dashed outline
        selected_items = self.selectedItems()
        
        # If no items are selected, we can stop the timer to save resources
        if not selected_items:
            return
            
        for item in selected_items:
            # Only update items that have our custom selection animation
            if hasattr(item, 'update'):
                item.update()

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
        
        # If event was accepted by an item, don't process for tools
        if event.isAccepted():
            return
        
        # Delegate to active tool if available
        if self._tool_manager and self._tool_manager.get_active_tool():
            active_tool = self._tool_manager.get_active_tool()
            active_tool.handle_mouse_up(event)
            event.accept()

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events and delegate to active tool."""
        # First, let Qt handle the event normally
        super().keyPressEvent(event)
        
        # If event was accepted by an item, don't process for tools
        if event.isAccepted():
            return
        
        # Delegate to active tool if available
        if self._tool_manager and self._tool_manager.get_active_tool():
            active_tool = self._tool_manager.get_active_tool()
            active_tool.handle_key_press(event)
            event.accept()

    def keyReleaseEvent(self, event):
        """Handle key release events and delegate to active tool."""
        # First, let Qt handle the event normally
        super().keyReleaseEvent(event)
        
        # If event was accepted by an item, don't process for tools
        if event.isAccepted():
            return
        
        # Delegate to active tool if available
        if self._tool_manager and self._tool_manager.get_active_tool():
            active_tool = self._tool_manager.get_active_tool()
            active_tool.handle_key_release(event)
            event.accept()

        super().keyReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        """Handle mouse double-click events and delegate to active tool."""
        # First, let Qt handle the event normally
        super().mouseDoubleClickEvent(event)
        
        # If event was accepted by an item, don't process for tools
        if event.isAccepted():
            return
        
        # Delegate to active tool if available
        if self._tool_manager and self._tool_manager.get_active_tool():
            active_tool = self._tool_manager.get_active_tool()
            active_tool.handle_double_click(event)
            event.accept()

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
        
        # Update viewmodel selection state and collect object IDs
        for item in selected_items:
            # Get the viewmodel from the item data
            viewmodel = item.data(0)
            if viewmodel and hasattr(viewmodel, 'is_selected'):
                # Update the viewmodel's selection state
                viewmodel.is_selected = True
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
