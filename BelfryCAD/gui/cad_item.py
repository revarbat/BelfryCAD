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
        
        # Control point dragging (no longer used)
        self._dragging_control_point = None
        self._drag_start_pos = None
        
        # Decoration items
        self._decoration_items = []
        self._decorations_created = False
        
        # Graphics control point items
        self._control_point_items = []
        self._control_point_interaction_active = False  # Track if control points are being interacted with
        
        # Recursion protection
        self._updating_control_points = False
        self._updating_geometry = False
        
        # Control point update throttling
        self._control_point_update_timer = QTimer()
        self._control_point_update_timer.setSingleShot(True)
        self._control_point_update_timer.timeout.connect(self._delayed_control_point_update)
        self._pending_control_point_update = False
        
        # Timeout protection for control point updates
        self._control_point_update_count = 0
        self._max_control_point_updates = 100  # Prevent infinite loops
    
    def __del__(self):
        """Destructor to ensure timer is stopped."""
        try:
            if hasattr(self, '_selection_timer'):
                self._selection_timer.stop()
        except:
            pass
        try:
            if hasattr(self, '_control_point_update_timer'):
                self._control_point_update_timer.stop()
        except:
            pass
        try:
            # Clear control points and decorations to prevent dangling references
            if hasattr(self, '_control_point_items'):
                for cp in self._control_point_items:
                    try:
                        if hasattr(cp, 'callback'):
                            cp.callback = None
                    except:
                        pass
                self._control_point_items.clear()
        except:
            pass
        try:
            if hasattr(self, '_decoration_items'):
                self._decoration_items.clear()
        except:
            pass
    
    def itemChange(self, change, value):
        """Handle item state changes."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            if value:  # Becoming selected
                self._start_selection_animation()
                if not self._decorations_created:
                    self._create_decorations()
                self._create_graphics_control_points()
            else:
                # Check if any control point is currently being interacted with
                control_point_interacting = False
                if hasattr(self, '_control_point_items') and self._control_point_items:
                    for cp in self._control_point_items:
                        try:
                            if hasattr(cp, '_interaction_started') and cp._interaction_started:
                                control_point_interacting = True
                                break
                        except (RuntimeError, AttributeError, TypeError):
                            # Control point may be invalid, continue checking others
                            continue
                
                # Check if the scene has a control point interaction flag
                scene_control_point_interaction = False
                try:
                    if self.scene():
                        scene_control_point_interaction = self.scene().property("_control_point_interaction")
                except (RuntimeError, AttributeError, TypeError):
                    # Scene may be invalid
                    pass
                
                # Prevent deselection if we have control points and the mouse is over a control point
                if (hasattr(self, '_control_point_items') and self._control_point_items and 
                    (self._control_point_interaction_active or control_point_interacting or scene_control_point_interaction)):
                    return True  # Prevent deselection
                
                self._stop_selection_animation()
                # Clear decorations when deselected
                self._clear_decorations()
                self._clear_graphics_control_points()
        elif change == QGraphicsItem.GraphicsItemChange.ItemSceneChange:
            # Item is being removed from scene
            if value is None:  # Being removed from scene
                self._stop_selection_animation()
                self._clear_decorations()
                self._clear_graphics_control_points()
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update control point positions when the item moves
            if hasattr(self, '_control_point_items'):
                for cp in self._control_point_items:
                    try:
                        # cp.position is in item local coordinates; map to scene
                        scene_pos = self.mapToScene(cp.position)
                        cp.setPos(scene_pos)
                    except (RuntimeError, AttributeError, TypeError):
                        # Control point may be invalid, continue with others
                        continue
        return super().itemChange(change, value)
    
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
            # Check if the item still exists and is valid
            if not self.scene():
                self._stop_selection_animation()
                return
                
            self._selection_animation_offset += 0.1
            if self._selection_animation_offset >= 4.0:
                self._selection_animation_offset = 0.0
            self.update()
        except RuntimeError:
            # Item has been deleted, stop the animation
            self._stop_selection_animation()
        except Exception:
            # Any other error, stop the animation
            self._stop_selection_animation()
    
    def paint(self, painter, option, widget=None):
        """Main paint method that handles selection and calls paint_item."""
        # Draw selection outline if selected
        # Draw the main item
        self.paint_item(painter, option, widget)
        
        # Draw selection shape if selected
        if self.isSelected():
            self._draw_selection(painter)
    
    def paint_item(self, painter, option, widget=None):
        """Override this method to paint the specific CAD item."""
        pass
    
    def _draw_selection(self, painter):
        """Draw animated selection shape."""
        painter.save()
        
        # Create animated dashed outline
        pen = QPen(QColor(0, 255, 0), 3.0)  # Bright green, thicker for visibility
        pen.setCosmetic(True)
        pen.setStyle(Qt.PenStyle.DashLine)
        
        # Animate dash pattern
        dash_offset = self._selection_animation_offset
        pen.setDashPattern([6.0, 4.0])
        pen.setDashOffset(dash_offset)
        painter.setPen(pen)
        painter.setBrush(QBrush())  # No fill
        
        # Draw outline around the item's shape
        shape = self.shape()
        if not shape.isEmpty():
            painter.drawPath(shape)
        
        painter.restore()
    
    def _create_decorations(self):
        """Override to create decoration items for this CAD item."""
        pass
    
    def _add_centerlines(self, center_point, radius=33.0):
        """Add centerlines decoration."""
        decoration_item = CenterlinesDecorationItem(center_point, radius, self)
        self._decoration_items.append(decoration_item)
        if self.scene() and decoration_item not in self.scene().items():
            self.scene().addItem(decoration_item)
    
    def _add_dashed_circle(self, center_point, radius, color=QColor(127, 127, 127), line_width=3.0):
        """Add dashed circle decoration."""
        decoration_item = DashedCircleDecorationItem(center_point, radius, color, line_width, self)
        self._decoration_items.append(decoration_item)
        if self.scene() and decoration_item not in self.scene().items():
            self.scene().addItem(decoration_item)
    
    def _add_dashed_lines(self, lines, color=QColor(127, 127, 127), line_width=3.0):
        """Add dashed lines decoration."""
        decoration_item = DashedLinesDecorationItem(lines, color, line_width, self)
        self._decoration_items.append(decoration_item)
        if self.scene() and decoration_item not in self.scene().items():
            self.scene().addItem(decoration_item)
    
    def _add_radius_lines(self, center_point, radius_points, color=QColor(127, 127, 127), line_width=3.0):
        """Add radius lines decoration."""
        decoration_item = RadiusLinesDecorationItem(center_point, radius_points, color, line_width, self)
        self._decoration_items.append(decoration_item)
        if self.scene() and decoration_item not in self.scene().items():
            self.scene().addItem(decoration_item)
    
    def _create_graphics_control_points(self):
        """Create graphics control point items."""
        # Clear existing graphics control points
        self._clear_graphics_control_points()
        
        # Get control point definitions
        try:
            control_points = self._get_control_points()
        except (RuntimeError, AttributeError, TypeError):
            # Failed to get control points, return early
            return
        
        # Create graphics items for each control point
        for cp in control_points:
            try:
                # The control point's position is in local coordinates
                # Convert to scene coordinates for positioning
                scene_pos = self.mapToScene(cp.position)
                
                # Create the control point with scene coordinates
                cp.position = scene_pos  # Store scene position
                cp.setPos(scene_pos)
                
                # Add directly to scene (not as child of CAD item)
                self._control_point_items.append(cp)
                if self.scene() and cp not in self.scene().items():
                    # Try adding with explicit flags
                    cp.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                    cp.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
                    cp.setAcceptHoverEvents(True)
                    cp.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
                    self.scene().addItem(cp)
                
                # Set callback to notify this CAD item when control point changes
                cp.callback = self._control_point_changed
                # Install this CadItem as a scene event filter on the control point
                cp.installSceneEventFilter(self)
            except (RuntimeError, AttributeError, TypeError) as e:
                # Failed to create control point, continue with others
                print(f"Warning: Failed to create control point: {e}")
                continue
    
    def _clear_graphics_control_points(self):
        """Clear all graphics control point items."""
        if not hasattr(self, '_control_point_items'):
            return
            
        # Create a copy of the list to avoid modification during iteration
        control_points_to_remove = list(self._control_point_items)
        
        for item in control_points_to_remove:
            try:
                # Check if item is still valid and in a scene
                if item and hasattr(item, 'scene') and item.scene():
                    # Remove from scene first
                    item.scene().removeItem(item)
                # Clear the item's callback to prevent callbacks after removal
                if hasattr(item, 'callback'):
                    item.callback = None
            except (RuntimeError, AttributeError, TypeError):
                # Item may have been deleted or is invalid, just continue
                pass
        
        # Clear the list
        self._control_point_items.clear()
    
    def _update_graphics_control_points(self):
        """Update positions of graphics control points."""
        control_points = self._get_control_points()
        for i, cp in enumerate(control_points):
            if i < len(self._control_point_items):
                graphics_item = self._control_point_items[i]
                graphics_item.update_position(cp.position)
    
    def _get_control_points(self):
        """Override to return list of control point graphics items."""
        return []
    
    def boundingRect(self):
        """Return bounding rectangle including decorations."""
        base_rect = self._boundingRect()
        # Include decoration items
        for decoration_item in self._decoration_items:
            if hasattr(decoration_item, 'boundingRect'):
                dec_rect = decoration_item.boundingRect()
                dec_rect.translate(decoration_item.pos())
                base_rect = base_rect.united(dec_rect)
        return base_rect
    
    def shape(self):
        """Return the shape for hit testing."""
        return self._shape()
    
    def contains(self, point):
        """Check if point is within the item, excluding control point areas."""
        # First check if the point is within any control point
        for control_point in self._control_point_items:
            # Convert point to control point's local coordinates
            control_local_point = control_point.mapFromScene(point)
            if control_point.contains(control_local_point):
                # Point is within a control point, so don't claim it
                return False
        
        # Point is not within any control point, check if it's within this item
        result = self._contains(point)
        return result
    
    def _boundingRect(self):
        return QRectF()
    
    def _shape(self):
        return QPainterPath()
    
    def _contains(self, point) -> bool:
        return False
    
    def _control_point_changed(self, name: str, new_position: QPointF):
        """Handle control point changes. Override in subclasses to update geometry."""
        # Prevent recursion with timeout protection
        if self._updating_geometry:
            return
            
        # Mark that control point interaction is active
        self._control_point_interaction_active = True
        
        # Update the CAD item geometry based on the control point change
        self._updating_geometry = True
        try:
            self._update_geometry_from_control_point(name, new_position)
        except Exception as e:
            print(f"Error updating geometry from control point: {e}")
        finally:
            self._updating_geometry = False
        
        # Schedule a throttled control point position update
        self._schedule_control_point_update()
    
    def _update_geometry_from_control_point(self, name: str, new_position: QPointF):
        """Update the CAD item geometry based on control point changes. Override in subclasses."""
        # Default implementation - subclasses should override this
        pass
    
    def _update_control_point_positions_if_needed(self):
        """Update control point positions without recreating them."""
        # Prevent recursion with timeout protection
        if self._updating_control_points:
            return
            
        self._updating_control_points = True
        try:
            # Get the current control point definitions
            try:
                control_points = self._get_control_points()
            except Exception as e:
                print(f"Error getting control points: {e}")
                return
            
            # Update positions of existing control points
            for i, cp_def in enumerate(control_points):
                if i < len(self._control_point_items):
                    graphics_item = self._control_point_items[i]
                    try:
                        # Convert local position to scene coordinates
                        scene_pos = self.mapToScene(cp_def.position)
                        
                        # Only update if position has changed significantly (avoid micro-updates)
                        current_pos = graphics_item.pos()
                        if (abs(scene_pos.x() - current_pos.x()) > 0.001 or 
                            abs(scene_pos.y() - current_pos.y()) > 0.001):
                            # Skip callback to prevent recursion
                            graphics_item.update_position(scene_pos, skip_callback=True)
                    except Exception as e:
                        print(f"Error updating control point position: {e}")
                        continue
        except Exception as e:
            print(f"Error in control point position update: {e}")
        finally:
            self._updating_control_points = False
    
    def _refresh_control_points_after_geometry_change(self):
        """Refresh all control points after geometry has been updated."""
        # Prevent recursion with timeout protection
        if self._updating_control_points or self._updating_geometry:
            return
            
        # Only refresh if we have control points and are selected
        if hasattr(self, '_control_point_items') and self._control_point_items and self.isSelected():
            # Use the more efficient position update instead of full recreation
            self._update_control_point_positions_if_needed()
    
    def _delayed_control_point_update(self):
        """Perform delayed control point update to prevent excessive updates."""
        try:
            if self._pending_control_point_update:
                self._pending_control_point_update = False
                
                # Check for infinite loop protection
                self._control_point_update_count += 1
                if self._control_point_update_count > self._max_control_point_updates:
                    print("Warning: Control point update limit reached, stopping updates")
                    self._control_point_update_count = 0
                    return
                
                self._update_control_point_positions_if_needed()
        except Exception as e:
            print(f"Error in delayed control point update: {e}")
            # Reset the flag to prevent infinite loops
            self._pending_control_point_update = False
            self._control_point_update_count = 0
    
    def _schedule_control_point_update(self):
        """Schedule a control point update with throttling."""
        try:
            if not self._pending_control_point_update:
                self._pending_control_point_update = True
                self._control_point_update_timer.start(16)  # ~60 FPS
        except Exception as e:
            print(f"Error scheduling control point update: {e}")
            # Reset the flag to prevent infinite loops
            self._pending_control_point_update = False
            self._control_point_update_count = 0
    
    def _on_control_point_interaction_start(self):
        """Called when control point interaction begins."""
        self._control_point_interaction_active = True
    
    def _on_control_point_interaction_end(self):
        """Called when control point interaction ends."""
        self._control_point_interaction_active = False
        # Reset the update counter when interaction ends
        self._control_point_update_count = 0
    
    def _force_clear_interaction_flags(self):
        """Force clear all interaction flags to prevent hanging."""
        try:
            self._control_point_interaction_active = False
            self._updating_control_points = False
            self._updating_geometry = False
            self._pending_control_point_update = False
            
            # Stop any running timers
            if hasattr(self, '_control_point_update_timer'):
                self._control_point_update_timer.stop()
            
            # Clear control point interaction flags
            if hasattr(self, '_control_point_items'):
                for cp in self._control_point_items:
                    try:
                        if hasattr(cp, '_interaction_started'):
                            delattr(cp, '_interaction_started')
                    except:
                        pass
            
            # Clear scene property
            try:
                if self.scene():
                    self.scene().setProperty("_control_point_interaction", False)
            except:
                pass
        except Exception as e:
            print(f"Error clearing interaction flags: {e}")
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for control point dragging (legacy system)."""
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events (legacy system)."""
        super().mouseReleaseEvent(event)
    
    def _draw_control_points(self, painter):
        """Draw all control points (legacy system)."""
        pass
    
    def _clear_decorations(self):
        """Clear all decoration items."""
        if not hasattr(self, '_decoration_items'):
            return
            
        # Create a copy of the list to avoid modification during iteration
        decorations_to_remove = list(self._decoration_items)
        
        for decoration_item in decorations_to_remove:
            try:
                # Check if item is still valid and in a scene
                if decoration_item and hasattr(decoration_item, 'scene') and decoration_item.scene():
                    decoration_item.scene().removeItem(decoration_item)
            except (RuntimeError, AttributeError, TypeError):
                # Item may have been deleted or is invalid, just continue
                pass
        
        # Clear the list
        self._decoration_items.clear()
        self._decorations_created = False
    
    def sceneEventFilter(self, watched, event):
        """Intercept mouse press events on control points to prevent deselection."""
        from PySide6.QtCore import QEvent
        # Only intercept events from our control points
        try:
            if watched in getattr(self, '_control_point_items', []):
                if event.type() == 160:  # QEvent.GraphicsSceneMousePress
                    cp_name = getattr(watched, 'name', None)
                    event.accept()
                    self._on_control_point_interaction_start()
                    return True
                elif event.type() == 161:  # QEvent.GraphicsSceneMouseRelease
                    # Always allow mouse release events to pass through
                    return False
                else:
                    cp_name = getattr(watched, 'name', None)
        except (RuntimeError, AttributeError, TypeError):
            # Event filtering may fail, continue with default behavior
            pass
        # Default: do not filter (allow events to pass through)
        return False 