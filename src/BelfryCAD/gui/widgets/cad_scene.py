from PySide6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent
from PySide6.QtCore import Qt, QPointF, QTimer, Signal



from ..graphics_items.control_points import ControlPoint, ControlDatum


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
        
        # Control point management
        self._control_points = {}  # {cad_item: [control_points]}
        self._control_datums = {}  # {cad_item: [control_datums]}
        
        # Snaps system reference (will be set by main window)
        self._snaps_system = None
        
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

    def _on_selection_changed(self):
        """Handle selection changes and emit signals with object IDs."""
        # Don't emit signals if we're updating selection from tree to prevent circular updates
        if self._updating_selection_from_tree:
            return
            
        # Get all selected items
        selected_items = self.selectedItems()
        selected_object_ids = set()
        
        # Update control points for selected items
        self._hide_all_control_points()
        
        for item in selected_items:
            # Get the viewmodel from the item data
            viewmodel = item.data(0)
            if viewmodel:
                # Update the viewmodel's selection state
                viewmodel.is_selected = True
                self._show_control_points_for_viewmodel(viewmodel)
                # Collect object ID for the signal
                if hasattr(viewmodel, '_cad_object') and viewmodel._cad_object:
                    object_id = viewmodel._cad_object.object_id
                    selected_object_ids.add(object_id)
        
        # Update non-selected viewmodels
        for item in self.items():
            if item not in selected_items:
                viewmodel = item.data(0)
                if viewmodel:
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
