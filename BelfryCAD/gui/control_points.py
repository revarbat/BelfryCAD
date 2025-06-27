"""
ControlPoint - A class representing a control point for CAD items.
"""

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, QDateTime
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QFontMetrics, QPainter, QPainterPath
from PySide6.QtWidgets import QGraphicsItem, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QDialogButtonBox


class ControlPoint(QGraphicsItem):
    """Base class for control point graphics items."""

    def __init__(self, name: str, position: QPointF, parent=None, callback=None):
        super().__init__(None)  # Always top-level, not a child
        self.name = name
        self.position = position
        self.callback = callback  # Callback function to notify parent
        self.setZValue(10000)  # Very high Z level to appear above all other items
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)  # We handle movement manually
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        # Set a flag to indicate this is a control point
        self._is_control_point = True
        # Throttling for performance
        self._last_update_time = 0
        self._update_threshold = 8  # ~120 FPS for better responsiveness (1000ms / 120fps ≈ 8ms)
        # Update position when initialized
        self.setPos(position)

    def _get_control_size_in_scene_coords(self, painter):
        """Get control point size in scene coordinates based on current zoom level."""
        # Desired pixel size for control points
        pixel_size = 8  # 8 pixels diameter

        # Get the current scale factor from the painter's transform
        scale = painter.transform().m11()

        # Convert pixel size to scene coordinates
        scene_size = pixel_size / scale

        return scene_size

    def boundingRect(self):
        # Use a much larger fixed size for hit testing (0.5 scene units)
        control_size = 0.5
        control_padding = control_size / 2
        return QRectF(-control_padding, -control_padding, control_size, control_size)

    def shape(self):
        path = QPainterPath()
        path.addEllipse(self.boundingRect())
        return path

    def contains(self, point):
        result = self.shape().contains(point)
        return result

    def paint(self, painter, option, widget=None):
        """Paint the control point."""
        painter.save()

        # Standardized control point styling
        control_pen = QPen(QColor(255, 0, 0), 2.0)  # Red color
        control_pen.setCosmetic(True)
        control_brush = QBrush(QColor(255, 255, 255))  # White fill
        painter.setPen(control_pen)
        painter.setBrush(control_brush)

        # Get control point size in scene coordinates based on current zoom
        control_size = self._get_control_size_in_scene_coords(painter)
        control_padding = control_size / 2

        # Draw the control point ellipse
        control_rect = QRectF(
            -control_padding,
            -control_padding,
            control_size, control_size
        )
        painter.drawEllipse(control_rect)

        painter.restore()

    def update_position(self, new_position, skip_callback=False):
        """Update the control point position."""
        self.position = new_position
        self.setPos(new_position)
        self.update()
        # Call callback if provided and not skipping
        if self.callback and not skip_callback:
            self.callback(self.name, new_position)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Accept the event immediately to prevent propagation
            event.accept()

            # Set a flag to indicate we're handling this interaction
            self._interaction_started = True

            # Notify parent CAD item that interaction is starting
            if self.callback:
                try:
                    # Call a special method to notify about interaction start
                    if hasattr(self.callback, '__self__') and hasattr(self.callback.__self__, '_on_control_point_interaction_start'):
                        self.callback.__self__._on_control_point_interaction_start()
                except (RuntimeError, AttributeError, TypeError):
                    # Callback may be invalid, continue
                    pass

            # Grab focus to ensure we receive subsequent events
            self.setFocus()
            # Grab mouse to ensure we get all subsequent events
            self.grabMouse()
            self._drag_start_scene_pos = event.scenePos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

            # Prevent the scene from processing this event for selection
            try:
                if self.scene():
                    # Mark the scene to ignore this event for selection purposes
                    self.scene().setProperty("_control_point_interaction", True)
            except (RuntimeError, AttributeError, TypeError):
                # Scene may be invalid, continue
                pass
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        if hasattr(self, '_drag_start_scene_pos'):
            # Throttle updates for better performance
            current_time = QDateTime.currentMSecsSinceEpoch()
            if current_time - self._last_update_time < self._update_threshold:
                event.accept()
                return

            self._last_update_time = current_time

            new_scene_pos = event.scenePos()

            # Only update if position has changed significantly
            current_pos = self.pos()
            if (abs(new_scene_pos.x() - current_pos.x()) < 0.001 and
                abs(new_scene_pos.y() - current_pos.y()) < 0.001):
                event.accept()
                return

            self.setPos(new_scene_pos)
            self.position = new_scene_pos

            # Call callback with throttling protection
            if self.callback:
                try:
                    # Check if parent is already updating to prevent recursion
                    parent = self.callback.__self__ if hasattr(self.callback, '__self__') else None
                    if parent and not getattr(parent, '_updating_geometry', False):
                        self.callback(self.name, new_scene_pos)
                except (RuntimeError, AttributeError, TypeError):
                    # Callback may be invalid, continue
                    pass

            event.accept()
        else:
            event.ignore()

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        # Clear focus and release mouse grab
        self.clearFocus()
        self.ungrabMouse()
        # Accept the event to prevent deselection
        event.accept()

        # Clear the interaction flag
        if hasattr(self, '_interaction_started'):
            delattr(self, '_interaction_started')

        # Clear the scene property flag
        try:
            if self.scene():
                self.scene().setProperty("_control_point_interaction", False)
        except (RuntimeError, AttributeError, TypeError):
            # Scene may be invalid, continue
            pass

        # Don't immediately end the interaction - let it persist for a moment
        # to prevent immediate deselection. Use a timer to end it after a short delay.
        if self.callback and hasattr(self.callback, '__self__') and hasattr(self.callback.__self__, '_on_control_point_interaction_end'):
            try:
                from PySide6.QtCore import QTimer
                # Use method references instead of lambda to avoid circular references
                timer = QTimer()
                timer.singleShot(100, self._delayed_end_interaction)

                # Also set a backup timer to force clear flags after 1 second
                backup_timer = QTimer()
                backup_timer.singleShot(1000, self._force_clear_interaction)
            except (RuntimeError, AttributeError, TypeError):
                # Timer creation may fail, continue
                pass

    def _delayed_end_interaction(self):
        """End the interaction after a short delay to prevent immediate deselection."""
        if self.callback and hasattr(self.callback, '__self__') and hasattr(self.callback.__self__, '_on_control_point_interaction_end'):
            try:
                self.callback.__self__._on_control_point_interaction_end()
            except (RuntimeError, AttributeError, TypeError):
                # Callback may be invalid, continue
                pass

    def _force_clear_interaction(self):
        """Force clear interaction flags as a backup mechanism."""
        try:
            # Clear the interaction flag
            if hasattr(self, '_interaction_started'):
                delattr(self, '_interaction_started')

            # Clear the scene property flag
            if self.scene():
                self.scene().setProperty("_control_point_interaction", False)

            # Call the parent's force clear method if available
            if self.callback and hasattr(self.callback, '__self__') and hasattr(self.callback.__self__, '_force_clear_interaction_flags'):
                self.callback.__self__._force_clear_interaction_flags()
        except (RuntimeError, AttributeError, TypeError):
            # Ignore errors in backup cleanup
            pass

    def itemChange(self, change, value):
        """Handle item changes to ensure proper scene registration."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSceneChange:
            if value:  # Item is being added to a scene
                pass  # Removed debug print
            else:  # Item is being removed from a scene
                pass  # Removed debug print
        return super().itemChange(change, value)


class SquareControlPoint(ControlPoint):
    """Control point graphics item that draws as a square."""

    def paint(self, painter, option, widget=None):
        """Draw the control point as a square."""
        painter.save()

        # Standardized control point styling
        control_pen = QPen(QColor(255, 0, 0), 2.0)  # Red color
        control_pen.setCosmetic(True)
        control_brush = QBrush(QColor(255, 255, 255))  # White fill
        painter.setPen(control_pen)
        painter.setBrush(control_brush)

        # Get control point size in scene coordinates based on current zoom
        control_size = self._get_control_size_in_scene_coords(painter)
        control_padding = control_size / 2

        # Draw the control point as a square
        control_rect = QRectF(
            -control_padding,
            -control_padding,
            control_size, control_size
        )
        painter.drawRect(control_rect)

        painter.restore()

    def boundingRect(self):
        control_size = 0.5
        control_padding = control_size / 2
        return QRectF(-control_padding, -control_padding, control_size, control_size)

    def shape(self):
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path


class DiamondControlPoint(ControlPoint):
    """Control point graphics item that draws as a diamond."""

    def paint(self, painter, option, widget=None):
        """Draw the control point as a diamond."""
        painter.save()

        # Standardized control point styling
        control_pen = QPen(QColor(255, 0, 0), 2.0)  # Red color
        control_pen.setCosmetic(True)
        control_brush = QBrush(QColor(255, 255, 255))  # White fill
        painter.setPen(control_pen)
        painter.setBrush(control_brush)

        # Get control point size in scene coordinates based on current zoom
        # Diamond is 44% larger than standard
        base_size = self._get_control_size_in_scene_coords(painter)
        control_size = base_size * 1.44  # 44% larger
        control_padding = control_size / 2

        # Create diamond shape using QPainterPath
        diamond_path = QPainterPath()

        # Define diamond vertices (top, right, bottom, left)
        diamond_path.moveTo(0, -control_padding)  # Top
        diamond_path.lineTo(control_padding, 0)  # Right
        diamond_path.lineTo(0, control_padding)  # Bottom
        diamond_path.lineTo(-control_padding, 0)  # Left
        diamond_path.closeSubpath()

        painter.drawPath(diamond_path)

        painter.restore()

    def boundingRect(self):
        control_size = 0.5
        control_padding = control_size / 2
        return QRectF(-control_padding, -control_padding, control_size, control_size)

    def shape(self):
        path = QPainterPath()
        # Diamond shape, but use boundingRect for max hit area
        path.addRect(self.boundingRect())
        return path


class ControlDatum(ControlPoint):
    """A control datum graphics item for displaying and editing data values."""

    def __init__(self, name: str, position: QPointF, value_getter, value_setter=None,
                 format_string="{:.3f}", prefix="", suffix="", parent_item=None, parent=None):
        super().__init__(name, position, parent)
        self.value_getter = value_getter
        self.value_setter = value_setter
        self.format_string = format_string
        self.prefix = prefix
        self.suffix = suffix
        self.parent_item = parent_item

        # Editing state
        self._is_editing = False
        self._label_rect = QRectF()

        # Set up click handling
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

    def mousePressEvent(self, event):
        """Handle mouse press to start editing or dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.value_setter:
                # Start editing for datums with setters
                self.start_editing()
            else:
                # Allow dragging for datums without setters
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def boundingRect(self):
        """Return the bounding rectangle of this datum label."""
        # Get current value for text measurement
        try:
            value = self.value_getter()
        except:
            return super().boundingRect()

        # Format text
        if self.prefix and self.suffix:
            text = f"{self.prefix}{self.format_string.format(value)}{self.suffix}"
        elif self.prefix:
            text = f"{self.prefix}{self.format_string.format(value)}"
        elif self.suffix:
            text = f"{self.format_string.format(value)}{self.suffix}"
        else:
            text = self.format_string.format(value)

        # Estimate text size (we'll use a reasonable fixed size for bounding rect)
        # This is approximate since we don't have a painter context here
        text_width = len(text) * 8  # Rough estimate: 8 pixels per character
        text_height = 16  # Rough estimate: 16 pixels height

        # Convert to scene coordinates (approximate)
        scene_width = text_width / 100  # Rough conversion
        scene_height = text_height / 100  # Rough conversion

        # Add padding
        padding = 0.04  # 4 pixels at typical zoom

        return QRectF(
            -padding,
            -scene_height/2 - padding,
            scene_width + 2 * padding,
            scene_height + 2 * padding
        )

    def shape(self):
        """Return the shape for hit testing."""
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def paint(self, painter, option, widget=None):
        """Draw the datum label."""
        if self._is_editing:
            return

        # Get current value
        try:
            value = self.value_getter()
        except:
            return  # Can't display if value getter fails

        # Set up font and metrics
        scale = painter.transform().m11()
        font = QFont("Arial", 12)
        font.setPointSizeF(12.0)
        painter.setFont(font)

        # Format text
        if self.prefix and self.suffix:
            text = f"{self.prefix}{self.format_string.format(value)}{self.suffix}"
        elif self.prefix:
            text = f"{self.prefix}{self.format_string.format(value)}"
        elif self.suffix:
            text = f"{self.format_string.format(value)}{self.suffix}"
        else:
            text = self.format_string.format(value)

        # Calculate text metrics
        font_metrics = QFontMetrics(font)
        text_rect = font_metrics.boundingRect(text)

        # Position label with fixed pixel offset
        pixel_offset = 15  # Fixed 15 pixel offset
        scene_offset = pixel_offset / scale  # Convert pixels to scene units

        # Calculate label position relative to datum position
        label_pos = QPointF(
            self.position.x() + scene_offset,
            self.position.y() + scene_offset
        )

        # Transform to screen coordinates for consistent text size
        painter.save()
        painter.translate(label_pos)
        painter.scale(1.0 / scale, -1.0 / scale)

        # Calculate background rectangle
        padding = 4
        bg_rect = QRectF(
            0,
            -text_rect.height() / 2 - padding,
            text_rect.width() + 2 * padding,
            text_rect.height() + 2 * padding
        )

        # Store the label rect for click detection (in local coordinates)
        self._label_rect = bg_rect

        # Draw background
        painter.setBrush(QColor(255, 255, 255, 200))  # Semi-transparent white
        painter.setPen(QPen(QColor(128, 128, 128), 1.0))
        painter.drawRect(bg_rect)

        # Draw text
        painter.setPen(QPen(QColor(0, 0, 0), 1.0))
        painter.drawText(bg_rect, Qt.AlignmentFlag.AlignCenter, text)

        painter.restore()

    def start_editing(self):
        """Start editing the datum value."""
        if self._is_editing or not self.value_setter:
            return

        self._is_editing = True

        # Get current value for editing
        try:
            current_value = self.value_getter()
        except:
            current_value = 0.0

        # Create dialog for editing
        dialog = QDialog()
        dialog.setWindowTitle(f"Edit {self.name}")
        dialog.setModal(True)

        layout = QVBoxLayout()

        # Create label for displaying the current value
        label = QLabel(f"Current value: {self.prefix}{self.format_string.format(current_value)}{self.suffix}")
        layout.addWidget(label)

        # Create line edit for entering the new value
        line_edit = QLineEdit()
        line_edit.setText(f"{current_value:.3f}")
        line_edit.selectAll()
        layout.addWidget(line_edit)

        # Create button box for dialog buttons
        button_box = QDialogButtonBox()
        ok_button = button_box.addButton("OK", QDialogButtonBox.ButtonRole.AcceptRole)
        cancel_button = button_box.addButton("Cancel", QDialogButtonBox.ButtonRole.RejectRole)
        layout.addWidget(button_box)

        # Connect signals
        ok_button.clicked.connect(lambda: self._finish_editing(dialog, line_edit))
        cancel_button.clicked.connect(lambda: self._cancel_editing(dialog))

        dialog.setLayout(layout)

        # Show dialog
        result = dialog.exec()

    def _finish_editing(self, dialog, line_edit):
        """Finish editing and apply the new value."""
        try:
            new_value = float(line_edit.text())
            if self.value_setter:
                self.value_setter(new_value)
            dialog.accept()
        except ValueError:
            # Invalid input, don't close dialog
            pass
        finally:
            self._is_editing = False

    def _cancel_editing(self, dialog):
        """Cancel editing."""
        dialog.reject()
        self._is_editing = False
