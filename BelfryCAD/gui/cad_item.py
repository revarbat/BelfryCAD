"""
Base CAD item class for graphics items with animated selection and control points.
"""

from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer
from PySide6.QtGui import QPen, QColor, QBrush, QPainterPath
from .control_points import ControlPoint


class CadItem(QGraphicsItem):
    """Base class for CAD items with animated selection outline."""
    
    def __init__(self):
        super().__init__()
        self._selection_animation_offset = 0.0
        self._selection_timer = None
        self._dragging_control_point = None
        self._drag_start_pos = QPointF()
        
        # Enable selection and movement
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
    
    def itemChange(self, change, value):
        """Handle item changes including selection state."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            if self.isSelected():
                self._start_selection_animation()
            else:
                self._stop_selection_animation()
        return super().itemChange(change, value)
    
    def _start_selection_animation(self):
        """Start the animated selection outline."""
        if not self._selection_timer:
            self._selection_timer = QTimer()
            self._selection_timer.timeout.connect(self._update_selection_animation)
            self._selection_timer.setInterval(100)  # 10 FPS
        self._selection_timer.start()
    
    def _stop_selection_animation(self):
        """Stop the animated selection outline."""
        if self._selection_timer:
            self._selection_timer.stop()
        self.update()  # Redraw to remove selection outline
    
    def _update_selection_animation(self):
        """Update the selection animation offset."""
        self._selection_animation_offset += 1.0
        if self._selection_animation_offset >= 4.0:
            self._selection_animation_offset = 0.0
        self.update()  # Trigger repaint
    
    def paint(self, painter, option, widget=None):
        """Base paint method - subclasses should call super().paint() after drawing their shape."""
        # Draw the item's content first (implemented by subclasses)
        self.paint_item(painter, option, widget)
        
        # Draw animated selection outline if selected
        if self.isSelected():
            self._draw_selection_outline(painter)
    
    def paint_item(self, painter, option, widget=None):
        """Override this method in subclasses to draw the item's content."""
        pass
    
    def _draw_selection_outline(self, painter):
        """Draw the animated dashed selection outline."""
        painter.save()
        
        # Create animated dashed pen
        pen = QPen(QColor(255, 0, 0), 5.0)
        pen.setCosmetic(True)
        pen.setDashPattern([2.0, 2.0])
        pen.setDashOffset(self._selection_animation_offset)
        
        painter.setPen(pen)
        painter.setBrush(QBrush())  # No fill
        
        # Call the subclass method to draw the selection outline
        self._draw_selection_shape(painter)
        
        painter.restore()
    
    def _draw_selection_shape(self, painter):
        """Override this method in subclasses to draw the selection outline."""
        # Default: draw the shape path
        shape_path = self._shape()
        painter.drawPath(shape_path)

        if self.isSelected():
            self._draw_decorations(painter)

            # Only draw control points if this is the only selected item
            if self._should_draw_control_points():
                control_points = self._get_control_points()
                for control_point in control_points:
                    control_point.draw(painter)
    
    def _should_draw_control_points(self):
        """Check if control points should be drawn (only when single item is selected)."""
        if not self.isSelected():
            return False
        
        # Get the scene and count selected items
        scene = self.scene()
        if scene is None:
            return True  # Default to showing control points if no scene
        
        selected_items = scene.selectedItems()
        # Only show control points if exactly one item is selected
        return len(selected_items) == 1

    def _draw_decorations(self, painter):
        """Override this method in subclasses to draw the decorations."""
        pass
    

    
    def draw_centerlines(self, painter, center_point, radius):
        """Draw crossed centerlines from center point to radius distance."""
        painter.save()
        
        # Standardized centerline styling
        dash_pattern = [10.0, 2.0, 2.0, 2.0]  # 10, 2, 2, 2 pattern
        pen = QPen(QColor(128, 128, 128), 0.02)  # Gray color
        pen.setCosmetic(True)
        pen.setDashPattern(dash_pattern)
        painter.setPen(pen)
        
        # Draw four centerlines from center to radius distance
        painter.drawLine(center_point, center_point + QPointF(radius, 0))    # Right
        painter.drawLine(center_point, center_point + QPointF(0, radius))    # Up
        painter.drawLine(center_point, center_point + QPointF(-radius, 0))   # Left
        painter.drawLine(center_point, center_point + QPointF(0, -radius))   # Down
        
        painter.restore()
    
    def _get_control_points(self):
        """Return a list of ControlPoint objects. Override in subclasses."""
        return []
    
    def boundingRect(self):
        """Return the bounding rectangle including control points when selected."""
        # Get the base bounding rect from subclass
        bounding_rect = self._boundingRect()
        
        # If selected and should show control points, expand to include control points
        if self._should_draw_control_points():
            control_points = self._get_control_points()
            
            for control_point in control_points:
                control_rect = control_point.bounding_rect()
                bounding_rect = bounding_rect.united(control_rect)
        
        return bounding_rect
    
    def shape(self):
        """Return the exact shape including control points when selected."""
        # Get the base shape from subclass
        base_path = self._shape()
        
        # If selected and should show control points, union control points with the base shape
        if self._should_draw_control_points():
            control_points = self._get_control_points()
            if control_points:  # Only if there are control points
                # Create a combined path by unioning base shape with control points
                combined_path = QPainterPath(base_path)
                
                for control_point in control_points:
                    control_path = QPainterPath()
                    control_rect = control_point.bounding_rect()
                    control_path.addEllipse(control_rect)
                    combined_path = combined_path.united(control_path)
                
                return combined_path
        
        return base_path
    
    def contains(self, point):
        """Check if a point is within the item or control points when selected."""
        # Check base shape first
        if self._contains(point):
            return True
        
        # If selected and should show control points, also check control points
        if self._should_draw_control_points():
            # Convert point to local coordinates if needed
            if hasattr(point, 'x') and hasattr(point, 'y'):
                local_point = point
            else:
                local_point = self.mapFromScene(point)
            
            control_points = self._get_control_points()
            
            for control_point in control_points:
                if control_point.contains(local_point):
                    return True
        
        return False
    
    def _boundingRect(self):
        """Override in subclasses to provide base bounding rectangle."""
        return QRectF()
    
    def _shape(self):
        """Override in subclasses to provide base shape."""
        return QPainterPath()
    
    def _contains(self, point) -> bool:
        """Override in subclasses to provide base contains logic."""
        return False
    
    def _control_point_changed(self, name: str, new_position: QPointF):
        """Override in subclasses to handle control point changes."""
        pass
    
    def mousePressEvent(self, event):
        """Handle mouse press for control point interaction."""
        if not self.isSelected() or event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        
        # Only handle control point interaction if control points should be drawn
        if self._should_draw_control_points():
            # Convert to local coordinates
            local_pos = event.pos()
            
            # Check control points from the list
            control_points = self._get_control_points()
            for control_point in control_points:
                if control_point.contains(local_pos):
                    self._dragging_control_point = control_point.name
                    self._drag_start_pos = local_pos
                    event.accept()
                    return
        
        # Let the base class handle normal dragging
        return super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for control point dragging."""
        if self._dragging_control_point:
            # Notify subclass of control point change
            self._control_point_changed(self._dragging_control_point, event.pos())
            event.accept()
            return
        
        # Let the base class handle normal dragging
        return super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release for control point interaction."""
        if self._dragging_control_point:
            self._dragging_control_point = None
            event.accept()
            return
        
        # Let the base class handle normal events
        return super().mouseReleaseEvent(event) 