"""
ControlPoint - A class representing a control point for CAD items.
"""
import math
from PySide6.QtCore import (
    QPointF, QRectF, Qt, QRegularExpression
)
from PySide6.QtGui import (
    QPen, QBrush, QColor, QFont, QFontMetrics, QPainterPath,
    QRegularExpressionValidator, QTransform
)
from PySide6.QtWidgets import (
    QGraphicsItem, QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox
)


class ControlPoint(QGraphicsItem):
    """Base class for control point graphics items."""

    def __init__(
            self,
            cad_item=None,
            setter=None
    ):
        super().__init__()  # Use parent-child relationship
        self.setter = setter
        self.cad_item = cad_item
        self.control_size = 9
        
        # Use Qt's built-in flags (movable disabled since parent handles movement)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        
        # Set high Z value to appear above other items
        self.setZValue(10000)
        
        # Dragging state
        self._is_dragging = False

    def set_dragging(self, dragging: bool):
        """Set the dragging state of this control point."""
        self._is_dragging = dragging

    def call_setter_with_updates(self, value):
        """
        Call the setter with new scene coordinates and handle all necessary
        updates.
        """
        if self.setter and self.cad_item:
            try:
                # prepare CadItem for geometry change.
                self.cad_item.prepareGeometryChange()

                # Call the setter with the new position in scene coordinates
                self.setter(value)
                
                # Update control point positions if the CAD item has that method
                if hasattr(self.cad_item, 'updateControls'):
                    self.cad_item.updateControls()
                    
                self.cad_item.update()
                
            except (RuntimeError, AttributeError, TypeError) as e:
                print(f"Error in control point setter: {e}")

    def _get_control_size_in_scene_coords(self, painter):
        """Get control point size in scene coordinates based on current zoom level."""
        pixel_size = self.control_size
        scale = painter.transform().m11()
        return pixel_size / scale

    def boundingRect(self):
        """Return bounding rectangle for hit testing."""
        # Get the current scale from the scene to make bounding rect scale independent
        scene = self.scene()
        if scene and scene.views():
            # Get the first view's transform to determine current scale
            view = scene.views()[0]
            scale = view.transform().m11()
            # Convert pixel size to scene coordinates
            control_size = float(self.control_size) / scale
        else:
            # Fallback to a reasonable size if no scene/view available
            control_size = 0.3
        
        control_padding = control_size / 2
        return QRectF(-control_padding, -control_padding, control_size, control_size)

    def shape(self):
        """Return shape for hit testing."""
        path = QPainterPath()
        path.addEllipse(self.boundingRect())
        return path

    def paint(self, painter, option, widget=None):
        """Paint the control point."""
        painter.save()

        # Standardized control point styling
        control_pen = QPen(QColor(255, 0, 0), 2.0)
        control_pen.setCosmetic(True)
        control_brush = QBrush(QColor(255, 255, 255))
        painter.setPen(control_pen)
        painter.setBrush(control_brush)

        # Draw the control point ellipse
        control_rect = self.boundingRect()
        painter.drawEllipse(control_rect)

        painter.restore()

    def itemChange(self, change, value):
        """Handle item state changes using Qt's built-in system."""
        # Position changes are now handled by the parent CadItem's mouse event system
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        """Handle mouse press events for control point dragging."""
        # Accept the event so the scene can handle control point dragging
        event.accept()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events for control point dragging."""
        # Accept the event so the scene can handle control point dragging
        event.accept()
        super().mouseReleaseEvent(event)


class SquareControlPoint(ControlPoint):
    """Control point graphics item that draws as a square."""

    def paint(self, painter, option, widget=None):
        """Draw the control point as a square."""
        painter.save()

        # Standardized control point styling
        control_pen = QPen(QColor(255, 0, 0), 2.0)
        control_pen.setCosmetic(True)
        control_brush = QBrush(QColor(255, 255, 255))
        painter.setPen(control_pen)
        painter.setBrush(control_brush)

        # Draw the control point as a square
        control_rect = self.boundingRect()
        painter.drawRect(control_rect)

        painter.restore()

    def shape(self):
        """Return square shape for hit testing."""
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path


class DiamondControlPoint(ControlPoint):
    """Control point graphics item that draws as a diamond."""

    def paint(self, painter, option, widget=None):
        """Draw the control point as a diamond."""
        painter.save()

        # Standardized control point styling
        control_pen = QPen(QColor(255, 0, 0), 2.0)
        control_pen.setCosmetic(True)
        control_brush = QBrush(QColor(255, 255, 255))
        painter.setPen(control_pen)
        painter.setBrush(control_brush)

        # Get control point size in scene coordinates based on current zoom
        base_size = self._get_control_size_in_scene_coords(painter)
        control_size = base_size * 1.44  # 44% larger
        control_padding = control_size / 2

        # Create diamond shape using QPainterPath
        diamond_path = QPainterPath()
        diamond_path.moveTo(0, -control_padding)  # Top
        diamond_path.lineTo(control_padding, 0)  # Right
        diamond_path.lineTo(0, control_padding)  # Bottom
        diamond_path.lineTo(-control_padding, 0)  # Left
        diamond_path.closeSubpath()

        painter.drawPath(diamond_path)
        painter.restore()

    def shape(self):
        """Return diamond shape for hit testing."""
        path = QPainterPath()
        
        # Get the current scale from the scene to make shape scale independent
        scene = self.scene()
        if scene and scene.views():
            # Get the first view's transform to determine current scale
            view = scene.views()[0]
            scale = view.transform().m11()
            # Convert pixels to scene coordinates
            control_size = float(self.control_size) / scale
        else:
            # Fallback to a reasonable size if no scene/view available
            control_size = 0.3
        
        # Create diamond shape using the same logic as paint method
        base_size = control_size
        control_size = base_size * 1.44  # 44% larger (same as paint method)
        control_padding = control_size / 2
        
        # Create diamond shape using QPainterPath
        path.moveTo(0, -control_padding)  # Top
        path.lineTo(control_padding, 0)  # Right
        path.lineTo(0, control_padding)  # Bottom
        path.lineTo(-control_padding, 0)  # Left
        path.closeSubpath()
        
        return path


class ControlDatum(ControlPoint):
    """A control datum graphics item for displaying and editing data values."""

    def __init__(
        self,
        setter=None,
        format_string=None,
        prefix="",
        suffix="",
        cad_item=None,
        label = "value",
        angle = 45,
        pixel_offset = 10,
        precision=3
    ):
        super().__init__(
            cad_item=cad_item,
            setter=setter)
        self.setZValue(10002)
        # Store precision for dynamic updates
        self._precision = precision
        # Use provided format_string or create one from precision
        if format_string is None:
            self.format_string = f"{{:.{precision}f}}"
        else:
            self.format_string = format_string
        self.prefix = prefix
        self.suffix = suffix
        self.label = label
        self.angle = angle
        self.pixel_offset = pixel_offset
        self._is_editing = False
        self._current_value = 0.0
        self._current_position = QPointF(0, 0)
        self._bounding_rect = QRectF(0, 0, 0, 0)
        
        # Cache for performance optimization
        self._cached_text = self._format_text(self._current_value)
        self._cached_bounding_rect = QRectF(0, 0, 0, 0)
        self._cached_scale = 1.0
        self._needs_geometry_update = True

    def get_position(self):
        """Get the current position."""
        return self._current_position
    
    def update_precision(self, new_precision: int):
        """Update the precision and refresh the display."""
        self._precision = new_precision
        # Update format string if it was created from precision
        if self.format_string == f"{{:.{self._precision}f}}" or "{" in self.format_string:
            self.format_string = f"{{:.{new_precision}f}}"
        
        # Update cached text and trigger geometry update
        new_text = self._format_text(self._current_value)
        if new_text != self._cached_text:
            self._cached_text = new_text
            self._needs_geometry_update = True
            self.prepareGeometryChange()
        
        self.update()  # Trigger repaint

    def update_datum(self, value, position):
        """Update both the value and position of the datum."""
        # Check if we need to update geometry
        new_text = self._format_text(value)
        if new_text != self._cached_text:
            self._cached_text = new_text
            self._needs_geometry_update = True
            self.prepareGeometryChange()
        
        self._current_value = value
        self._current_position = position
        self.setPos(position)
        self.update()  # Trigger repaint

    def _format_text(self, value):
        """Format the text for display."""
        valstr = self.format_string.format(value)
        valstr = valstr.rstrip('0').rstrip('.')
        pfx = self.prefix if self.prefix else ""
        sfx = self.suffix if self.suffix else ""
        return f"{pfx}{valstr}{sfx}"

    def mousePressEvent(self, event):
        """Handle mouse press events for control datum editing."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Start editing the datum value
            self.start_editing()
            event.accept()
        else:
            event.ignore()

    def boundingRect(self):
        """Return the bounding rectangle of this datum label."""
        return self._bounding_rect

    def shape(self):
        """Return the shape for hit testing."""
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def paint(self, painter, option, widget=None):
        """Draw the datum label."""
        # Defensive check for attributes
        if not hasattr(self, '_is_editing') or not hasattr(self, 'prefix') or not hasattr(self, 'suffix') or not hasattr(self, 'format_string'):
            return
            
        if self._is_editing:
            return

        # Use cached text
        text = self._cached_text

        painter.save()

        # Set up font
        font = QFont("Arial", 14)
        painter.setFont(font)
        
        # Calculate text metrics
        font_metrics = QFontMetrics(font)
        text_rect = font_metrics.boundingRect(text)

        # Position label with fixed pixel offset
        padding = 4
        box_width = text_rect.width() + 4 * padding
        box_height = text_rect.height() + 2 * padding

        # Calculate label position relative to datum position
        ocos = math.cos(math.radians(self.angle))
        osin = math.sin(math.radians(self.angle))
        label_pos = QPointF(
            self.pixel_offset * ocos,
            -self.pixel_offset * osin
        )

        if ocos < 0:
            label_pos += QPointF(-box_width/2, 0)
        elif ocos > 0:
            label_pos += QPointF(box_width/2, 0)

        if osin > 0:
            label_pos += QPointF(0, -box_height/2)
        elif osin < 0:
            label_pos += QPointF(0, box_height/2)

        # Draw background rectangle
        background_rect = QRectF(
            -box_width/2,
            -box_height/2,
            box_width,
            box_height
        )

        # Only update geometry when needed
        scale = painter.transform().m11()
        if self._needs_geometry_update or abs(scale - self._cached_scale) > 0.01:
            t = QTransform()
            t.scale(1.0/scale, -1.0/scale)
            t.translate(label_pos.x(), label_pos.y())
            self._bounding_rect = t.mapRect(background_rect)
            self._cached_scale = scale
            self._needs_geometry_update = False

        # Draw background
        pen = QPen(QColor(0, 0, 0), 1.0)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 255)))
        painter.scale(1.0/scale, -1.0/scale)
        painter.translate(label_pos)
        painter.drawRect(background_rect)

        # Draw text
        painter.setPen(QPen(QColor(0, 0, 0), 1.0))
        painter.drawText(background_rect, Qt.AlignmentFlag.AlignCenter, text)

        painter.restore()

    def start_editing(self):
        """Start editing the datum value."""
        # Defensive check for attributes
        if not hasattr(self, '_is_editing'):
            return
            
        if self._is_editing:
            return

        self._is_editing = True
        self.update()

        # Use the current stored value
        current_value = self._current_value

        # Create editing dialog
        dialog = QDialog()
        dialog.setWindowTitle(f"Edit {self.label}")
        dialog.setModal(True)

        layout = QVBoxLayout()
        dialog.setLayout(layout)

        # Add label
        label = QLabel(f"Enter new {self.label}:")
        layout.addWidget(label)

        # Add line edit with validation
        line_edit = QLineEdit()
        line_edit.setText(f"{current_value:.5g}")
        line_edit.selectAll()
        
        # Create validator for digits, '-', and '.' only
        validator = QRegularExpressionValidator(QRegularExpression(r"^-?\d*\.?\d*$"))
        line_edit.setValidator(validator)
        
        layout.addWidget(line_edit)

        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        set_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        set_button.setText("Set")
        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setText("Cancel")
        
        # Initially disable Set button until valid input
        set_button.setEnabled(False)
        
        # Connect validation
        def validate_input():
            try:
                text = line_edit.text()
                if text and text != "-" and text != "." and text != "-.":
                    float(text)
                    set_button.setEnabled(True)
                else:
                    set_button.setEnabled(False)
            except ValueError:
                set_button.setEnabled(False)
        
        line_edit.textChanged.connect(validate_input)
        validate_input()  # Initial validation
        
        button_box.accepted.connect(lambda: self._finish_editing(dialog, line_edit))
        button_box.rejected.connect(lambda: self._cancel_editing(dialog))
        layout.addWidget(button_box)

        # Set focus to line edit
        line_edit.setFocus()

        # Show dialog
        dialog.exec()

    def _finish_editing(self, dialog, line_edit):
        """Finish editing and apply the new value."""
        try:
            new_value = float(line_edit.text())
            self.call_setter_with_updates(new_value)
        except ValueError:
            pass

        dialog.accept()
        if hasattr(self, '_is_editing'):
            self._is_editing = False
        self.update()

    def _cancel_editing(self, dialog):
        """Cancel editing."""
        dialog.reject()
        if hasattr(self, '_is_editing'):
            self._is_editing = False
        self.update()
