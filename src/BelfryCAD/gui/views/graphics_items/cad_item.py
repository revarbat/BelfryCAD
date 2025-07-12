"""
Base CAD item class for graphics items with animated selection and control points.
"""

from typing import List, Optional
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import QPointF, QTimer, QEvent
from PySide6.QtGui import QPen, QColor, QBrush
from .control_points import ControlPoint
from .cad_decoration_items import (
    CenterlinesDecorationItem,
    DashedCircleDecorationItem,
    DashedLinesDecorationItem,
    RadiusLinesDecorationItem
)


class CadItem(QGraphicsItem):
    """Base class for all CAD graphics items."""

    def __init__(self):
        super().__init__()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setHandlesChildEvents(False)

        # Selection animation
        self._selection_animation_offset = 0.0
        self._selection_timer = QTimer()
        self._selection_timer.timeout.connect(self._update_selection_animation)

        # Decoration items (children)
        self._decoration_items = []
        self._decorations_created = False

        # Control point items (children)
        self._control_point_items = []
        
        # Track selection state for detecting changes
        self._was_singly_selected = False
        
        # Control points are now managed by the scene, not created automatically
        # QTimer.singleShot(0, self._create_control_points_impl)

    def __del__(self):
        """Destructor to ensure timer is stopped."""
        try:
            if hasattr(self, '_selection_timer'):
                self._selection_timer.stop()
        except:
            pass

    def itemChange(self, change, value):
        """Handle item state changes using Qt's built-in system."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            if value:  # Becoming selected
                self._start_selection_animation()
                if not self._decorations_created:
                    self._create_decorations()
                # Check selection state (control points managed by scene)
                self._check_selection_state()
            else:  # Becoming deselected
                self._stop_selection_animation()
                self._clear_decorations()
                self._was_singly_selected = False
        elif change == QGraphicsItem.GraphicsItemChange.ItemSceneChange:
            # Item is being removed from scene
            if value is None:  # Being removed from scene
                self._stop_selection_animation()
                self._clear_decorations()
                self._was_singly_selected = False
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Control points are managed by the scene, which will update them as needed
            pass
        return super().itemChange(change, value)

    def _is_singly_selected(self):
        """Check if this item is the only selected item in the scene."""
        if not self.scene():
            return False
        
        # Get all selected items in the scene
        selected_items = [item for item in self.scene().items() 
                         if hasattr(item, 'isSelected') and item.isSelected()]
        
        # Return True if this item is the only selected item
        return len(selected_items) == 1 and self in selected_items

    def _check_selection_state(self):
        """Check if control points should be shown or hidden based on selection state."""
        # Control points are now managed by the scene, not by individual CAD items
        # The scene will handle showing/hiding control points based on selection
        if self.isSelected() and self._is_singly_selected():
            # Single selection - control points will be shown by the scene
            self._was_singly_selected = True
        else:
            # Not selected or multiple selection - control points will be hidden by the scene
            self._was_singly_selected = False

    def _start_selection_animation(self):
        """Start the selection animation."""
        self._selection_animation_offset = 0.0
        self._selection_timer.start(50)  # Update every 50ms

    def _stop_selection_animation(self):
        """Stop the selection animation."""
        self._selection_timer.stop()
        self._selection_animation_offset = 0.0

    def _update_selection_animation(self):
        """Update the selection animation offset."""
        try:
            if not self.scene():
                self._stop_selection_animation()
                return

            self._selection_animation_offset += 0.1
            if self._selection_animation_offset >= 6.0:  # Complete rainbow cycle (6 color segments)
                self._selection_animation_offset = 0.0
            self.update()
        except RuntimeError:
            self._stop_selection_animation()
        except Exception:
            self._stop_selection_animation()

    def paint(self, painter, option, widget=None):
        """Main paint method that handles selection and calls paint_item."""
        # Draw the main item with selection animation if selected
        if self.isSelected():
            self.paint_item_with_selection(painter, option, widget)
        else:
            self.paint_item(painter, option, widget)

    def paint_item_with_selection(self, painter, option, widget=None):
        """Paint the item with selection animation. Override in subclasses for custom selection behavior."""
        # Default behavior: call paint_item with selection color
        self.paint_item_with_color(painter, option, widget, self._get_selection_color())

    def _get_selection_color(self):
        """Get the current selection color based on animation offset."""
        # Calculate color based on animation offset, avoiding very light colors
        # Animation goes from 0.0 to 6.0 for full cycle
        # Use a restricted color range that avoids green and cyan
        # Map 0.0-6.0 to colors: red -> magenta -> blue -> orange -> red
        
        offset = self._selection_animation_offset
        cycle = offset % 6.0  # Ensure we stay in 0-6 range
        
        if cycle < 1.5:
            # Red to magenta (0.0-1.5)
            hue = 0  # Red
            saturation = 255
            value = 255
        elif cycle < 3.0:
            # Magenta to blue (1.5-3.0)
            hue = int(((cycle - 1.5) / 1.5) * 60) + 300  # 300-360 (magenta to blue)
            saturation = 255
            value = 255
        elif cycle < 4.5:
            # Blue to orange (3.0-4.5)
            hue = int(((cycle - 3.0) / 1.5) * 60) + 240  # 240-300 (blue to magenta)
            saturation = 255
            value = 255
        else:
            # Orange to red (4.5-6.0)
            hue = int(((cycle - 4.5) / 1.5) * 30) + 0  # 0-30 (red to orange)
            saturation = 255
            value = 255
        
        # Create color from HSV (Hue, Saturation, Value)
        return QColor.fromHsv(hue, saturation, value)

    def paint_item_with_color(self, painter, option, widget=None, color=None):
        """Paint the item with a specific color. Override in subclasses."""
        # Default implementation: call paint_item
        self.paint_item(painter, option, widget)

    def _get_line_width(self):
        """Get the line width for this CAD item. Override in subclasses."""
        return 1.0  # Default line width

    def paint_item(self, painter, option, widget=None):
        """Override this method to paint the specific CAD item."""
        pass



    def _create_decorations(self):
        """Create decoration items."""
        self._create_decorations_impl()
        self._decorations_created = True

    def _create_decorations_impl(self):
        """Override to create specific decorations."""
        pass

    def _add_centerlines(self, center_point, radius=33.0):
        """Add centerlines decoration."""
        decoration = CenterlinesDecorationItem(center_point, radius, self)
        self._decoration_items.append(decoration)

    def _add_dashed_circle(self, center_point, radius, color=QColor(127, 127, 127), line_width=3.0):
        """Add dashed circle decoration."""
        decoration = DashedCircleDecorationItem(center_point, radius, color, line_width, self)
        self._decoration_items.append(decoration)

    def _add_dashed_lines(self, lines, color=QColor(127, 127, 127), line_width=3.0):
        """Add dashed lines decoration."""
        decoration = DashedLinesDecorationItem(lines, color, line_width, self)
        self._decoration_items.append(decoration)

    def _add_radius_lines(self, center_point, radius_points, color=QColor(127, 127, 127), line_width=3.0):
        """Add radius lines decoration."""
        decoration = RadiusLinesDecorationItem(center_point, radius_points, color, line_width, self)
        self._decoration_items.append(decoration)

    def createControlPoints(self):
        """Show control points for this CAD item. Called when item is singly selected."""
        # Control points are now managed by the scene, not by the CAD item
        # Clean up any old control points that might exist
        self.destroyControlPoints()
        pass

    def destroyControlPoints(self):
        """Destroy all control points for this CAD item."""
        if not hasattr(self, '_control_point_items'):
            return

        for item in self._control_point_items:
            try:
                if item:
                    item.getter = None
                    item.setter = None
                    item.setParentItem(None)
            except (RuntimeError, AttributeError, TypeError):
                pass

        self._control_point_items.clear()

    def updateControlPoints(self):
        """Update control point positions and values."""
        if not hasattr(self, '_control_point_items') or not self._control_point_items:
            return

        # Call the subclass implementation to update control points
        try:
            self.updateControls()
        except Exception as e:
            print(f"Error updating control points: {e}")

    def createControls(self):
        """Override to create and return a list of control points."""
        control_points = []
        # Call the subclass implementation
        try:
            control_points = self._create_controls_impl()
            if control_points:
                # Store the control points in the expected attribute
                self._control_point_items.extend(control_points)
                # Hide control points by default
                for cp in control_points:
                    if cp:
                        cp.setVisible(False)
        except (RuntimeError, AttributeError, TypeError):
            pass
        return control_points

    def _create_controls_impl(self):
        """Override to create and return a list of control points."""
        return []

    def _create_control_points_impl(self):
        """Create control points immediately after instantiation."""
        try:
            control_points = self.createControls()
            if control_points:
                self._control_point_items.extend(control_points)
                # Hide control points by default
                self.hideControls()
        except (RuntimeError, AttributeError, TypeError):
            pass

    def updateControls(self):
        """Override to update control point positions and values."""
        pass

    def getControlPoints(self, exclude_cps: Optional[List['ControlPoint']] = None) -> List[QPointF]:
        """
        Return a list of QPointF positions where control points should be positioned.
        This method should return the same positions that updateControls() sets
        for the control points, but without creating the actual control point objects.
        ControlDatums should not be included in this list.
        
        Args:
            exclude_cps: List of ControlPoint objects to exclude from the result.
                        Control points associated with these objects will be excluded.
        
        Returns:
            List of QPointF positions for control points (excluding ControlDatums and excluded points)
        """
        # Default implementation returns empty list
        # Subclasses should override this method
        return []
    
    def _should_exclude_control_point(self, cp_index: int, exclude_cps: Optional[List['ControlPoint']] = None) -> bool:
        """
        Helper method to determine if a control point at the given index should be excluded.
        
        Args:
            cp_index: Index of the control point to check
            exclude_cps: List of ControlPoint objects to exclude from the result.
        
        Returns:
            True if the control point should be excluded, False otherwise
        """
        if not exclude_cps:
            return False
        
        # Get the control point objects for this CAD item
        control_point_objects = self._get_control_point_objects()
        
        if cp_index < len(control_point_objects):
            cp_object = control_point_objects[cp_index]
            return cp_object in exclude_cps
        
        return False
    
    def _get_control_point_objects(self) -> List['ControlPoint']:
        """
        Get the list of ControlPoint objects for this CAD item.
        This method should be overridden by subclasses to provide the actual control point objects.
        
        Returns:
            List of ControlPoint objects for this CAD item
        """
        # Default implementation returns empty list
        # Subclasses should override this method
        return []

    def hideControls(self):
        """Hide all control points and control datums for this CAD item."""
        # Control points are now managed by the scene, not by the CAD item
        # Clean up any old control points that might exist
        self.destroyControlPoints()
        pass

    def showControls(self):
        """Show all control points and control datums for this CAD item."""
        # Control points are now managed by the scene, not by the CAD item
        # This method is kept for compatibility but does nothing
        pass

    def _clear_decorations(self):
        """Clear all decoration items."""
        if not hasattr(self, '_decoration_items'):
            return

        for decoration in self._decoration_items:
            try:
                if decoration:
                    decoration.setParentItem(None)
            except (RuntimeError, AttributeError, TypeError):
                pass

        self._decoration_items.clear()
        self._decorations_created = False

    def moveBy(self, dx, dy):
        """Move all underlying points by the specified offset. If the subclass has a 'points' property, move all points. Otherwise, must be overridden by subclass."""
        if hasattr(self, 'points') and hasattr(self, 'points'):
            pts = self.points
            # Support both list and tuple of points
            try:
                new_pts = [QPointF(pt.x() + dx, pt.y() + dy) for pt in pts]
                self.points = new_pts
                self.update()
            except Exception:
                raise NotImplementedError("Subclass must implement moveBy or provide a points property.")
        else:
            raise NotImplementedError("Subclass must implement moveBy or provide a points property.")

    def sceneEvent(self, event):
        """Handle scene events to detect selection changes."""
        if event.type() == QEvent.Type.GraphicsSceneMouseRelease:
            # Check selection state after mouse release (when selection might have changed)
            if self.isSelected():
                self._check_selection_state()
        return super().sceneEvent(event)