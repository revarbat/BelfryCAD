"""
Base CAD item class for graphics items with animated selection and control points.
"""

from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer, QEvent
from PySide6.QtGui import QPen, QColor, QBrush, QPainterPath
from .control_points import (
    ControlPoint, SquareControlPoint,
    DiamondControlPoint, ControlDatum
)
from .cad_decoration_items import (
    CadDecorationItem,
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
                # Check if we should create control points
                self._check_selection_state()
            else:  # Becoming deselected
                self._stop_selection_animation()
                self._clear_decorations()
                self.destroyControlPoints()
                self._was_singly_selected = False
        elif change == QGraphicsItem.GraphicsItemChange.ItemSceneChange:
            # Item is being removed from scene
            if value is None:  # Being removed from scene
                self._stop_selection_animation()
                self._clear_decorations()
                self.destroyControlPoints()
                self._was_singly_selected = False
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update control point positions when the item moves
            self.updateControlPoints()
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
        """Check if control points should be created or destroyed based on selection state."""
        if self.isSelected():
            is_singly_selected = self._is_singly_selected()
            
            if is_singly_selected:
                # Single selection - create control points if not already created
                if not hasattr(self, '_control_point_items') or not self._control_point_items:
                    self.createControlPoints()
                self._was_singly_selected = True
            else:
                # Multiple selection - destroy control points
                self.destroyControlPoints()
                self._was_singly_selected = False
        else:
            # Not selected - destroy control points
            self.destroyControlPoints()
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
        # Draw the main item
        self.paint_item(painter, option, widget)

        # Draw selection shape if selected
        if self.isSelected():
            self._draw_selection(painter)

    def paint_item(self, painter, option, widget=None):
        """Override this method to paint the specific CAD item."""
        pass

    def _draw_selection(self, painter):
        """Draw rainbow cycling selection shape."""
        painter.save()

        # Calculate rainbow color based on animation offset
        # Animation goes from 0.0 to 6.0 for full rainbow cycle
        hue = (self._selection_animation_offset / 6.0) * 360.0  # Convert to 0-360 degrees
        
        # Create color from HSV (Hue, Saturation, Value)
        selection_color = QColor.fromHsv(int(hue), 255, 255)
        
        # Create pen with rainbow color and thickness
        pen = QPen(selection_color, 3.0)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(QBrush())  # No fill

        # Draw the selection outline using the item's shape
        shape = self.shape()
        if not shape.isEmpty():
            painter.drawPath(shape)

        painter.restore()

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
        """Create control points for this CAD item. Called when item is singly selected."""
        # Clear existing control points first
        self.destroyControlPoints()

        # Get control point definitions from subclass
        try:
            control_points = self._get_control_points()
        except (RuntimeError, AttributeError, TypeError):
            return

        # Create graphics items for each control point
        for cp in control_points:
            try:
                # Create control point as child of this item
                cp.setParentItem(self)
                
                # Set up getter and setter callbacks
                cp.getter = lambda name=cp.name: self._get_control_point_position(name)
                cp.setter = lambda pos, name=cp.name: self._control_point_changed(name, pos)
                
                self._control_point_items.append(cp)
            except (RuntimeError, AttributeError, TypeError) as e:
                print(f"Warning: Failed to create control point: {e}")
                continue

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
        """Update control point positions using their getter callbacks."""
        if not hasattr(self, '_control_point_items') or not self._control_point_items or not self.isSelected():
            return

        # Update positions of existing control points using their getters
        for item in self._control_point_items:
            try:
                if item.getter:
                    # Get current position from the getter callback
                    current_pos = item.getter()
                    # Update the control point's position
                    item.set_position(current_pos)
            except Exception as e:
                print(f"Error updating control point position: {e}")
                continue

    def _get_control_points(self):
        """Override to return list of control point definitions."""
        return []

    def _get_control_point_position(self, name: str) -> QPointF:
        """Get the current position of a control point. Override in subclasses."""
        # Default implementation - subclasses should override this
        return QPointF(0, 0)

    def _control_point_changed(self, name: str, new_position: QPointF):
        """Handle control point changes. Override in subclasses to update geometry."""
        # Convert from local to scene coordinates for geometry update
        scene_pos = self.mapToScene(new_position)
        self._update_geometry_from_control_point(name, scene_pos)
        # Update control point positions after geometry change
        self.updateControlPoints()

    def _update_geometry_from_control_point(self, name: str, new_position: QPointF):
        """Update the CAD item geometry based on control point changes. Override in subclasses."""
        pass

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        super().mouseReleaseEvent(event)

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

    def sceneEvent(self, event):
        """Handle scene events to detect selection changes."""
        if event.type() == QEvent.Type.GraphicsSceneMouseRelease:
            # Check selection state after mouse release (when selection might have changed)
            if self.isSelected():
                self._check_selection_state()
            else:
                self.destroyControlPoints()
                self._was_singly_selected = False
        return super().sceneEvent(event)

    def _on_selection_changed(self):
        """Called when the overall selection in the scene changes."""
        # This method can be called by the scene or view when selection changes
        if self.isSelected():
            self._check_selection_state()
        else:
            self.destroyControlPoints()
            self._was_singly_selected = False