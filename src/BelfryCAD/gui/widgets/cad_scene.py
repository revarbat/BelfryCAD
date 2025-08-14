from PySide6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent
from PySide6.QtCore import Qt, QPointF, QTimer



from ..graphics_items.control_points import ControlPoint, ControlDatum


class CadScene(QGraphicsScene):
    """Custom graphics scene for CAD operations with centralized event handling."""

    def __init__(self, parent=None, precision=3):
        super().__init__(parent)
        
        # Store precision for CAD items to use
        self._precision = precision
        
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
        """Handle Qt's built-in selection changes."""
        selected_items = self.selectedItems()
        
        # Update control points for selected items
        self._hide_all_control_points()
        
        for view_item in selected_items:
            viewmodel = view_item.data(0)
            if viewmodel:
                # Update the viewmodel's selection state
                viewmodel.is_selected = True
                self._show_control_points_for_viewmodel(viewmodel)
        
        # Update non-selected viewmodels
        for item in self.items():
            if item not in selected_items:
                viewmodel = item.data(0)
                if viewmodel:
                    viewmodel.is_selected = False

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
