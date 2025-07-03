"""
ControlPoint - A class representing a control point for CAD items.
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QPen, QBrush, QColor, QFont, QFontMetrics, QPainterPath
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
        self.control_size = 7
        
        # Use Qt's built-in flags (movable disabled since parent handles movement)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)  # Parent handles movement
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        
        # Set high Z value to appear above other items
        self.setZValue(10000)

    def call_setter_with_updates(self, value):
        """Call the setter and handle all necessary updates."""
        if self.setter and self.cad_item:
            try:
                # prepare CadItem for geometry change.
                self.cad_item.prepareGeometryChange()

                # Call the setter with the new position
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
        """Mouse events are now handled by the parent CadItem."""
        # Let the parent CadItem handle all mouse events
        event.ignore()

    def mouseReleaseEvent(self, event):
        """Mouse events are now handled by the parent CadItem."""
        # Let the parent CadItem handle all mouse events
        event.ignore()


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

    def __init__(self, setter=None, format_string="{:.3f}", prefix="", suffix="", cad_item=None):
        super().__init__(
            cad_item=cad_item,
            setter=setter)
        self.format_string = format_string
        self.prefix = prefix
        self.suffix = suffix
        self._is_editing = False
        self._current_value = 0.0
        self._current_position = QPointF(0, 0)

    def get_position(self):
        """Get the current position."""
        return self._current_position

    def update_datum(self, value, position):
        """Update both the value and position of the datum."""
        self._current_value = value
        self._current_position = position
        self.setPos(position)
        self.update()  # Trigger repaint

    def mousePressEvent(self, event):
        """Mouse events are now handled by the parent CadItem."""
        # Let the parent CadItem handle all mouse events
        event.ignore()

    def boundingRect(self):
        """Return the bounding rectangle of this datum label."""
        # Defensive check for attributes
        if not hasattr(self, 'prefix') or not hasattr(self, 'suffix') or not hasattr(self, 'format_string'):
            return super().boundingRect()

        # Format text
        if self.prefix and self.suffix:
            text = f"{self.prefix}{self.format_string.format(self._current_value)}{self.suffix}"
        elif self.prefix:
            text = f"{self.prefix}{self.format_string.format(self._current_value)}"
        elif self.suffix:
            text = f"{self.format_string.format(self._current_value)}{self.suffix}"
        else:
            text = self.format_string.format(self._current_value)

        # Estimate text size
        text_width = len(text) * 8
        text_height = 16
        scene_width = text_width / 100
        scene_height = text_height / 100
        padding = 0.04

        # Calculate label position relative to datum position (which is at origin in local coords)
        pixel_offset = 15
        scene_offset = pixel_offset / 100  # Approximate scale factor

        return QRectF(
            scene_offset - padding,
            scene_offset - scene_height/2 - padding,
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
        # Defensive check for attributes
        if not hasattr(self, '_is_editing') or not hasattr(self, 'prefix') or not hasattr(self, 'suffix') or not hasattr(self, 'format_string'):
            return
            
        if self._is_editing:
            return

        # Set up font
        scale = painter.transform().m11()
        font = QFont("Arial", 12)
        font.setPointSizeF(12.0)
        painter.setFont(font)
        painter.scale(1.0/scale,-1.0/scale)

        # Format text
        if self.prefix and self.suffix:
            text = f"{self.prefix}{self.format_string.format(self._current_value)}{self.suffix}"
        elif self.prefix:
            text = f"{self.prefix}{self.format_string.format(self._current_value)}"
        elif self.suffix:
            text = f"{self.format_string.format(self._current_value)}{self.suffix}"
        else:
            text = self.format_string.format(self._current_value)

        # Calculate text metrics
        font_metrics = QFontMetrics(font)
        text_rect = font_metrics.boundingRect(text)

        # Position label with fixed pixel offset
        pixel_offset = 10
        scene_offset = pixel_offset

        # Calculate label position relative to datum position
        datum_pos = self.get_position()
        label_pos = QPointF(
            datum_pos.x() + scene_offset,
            datum_pos.y() - scene_offset
        )

        # Draw background rectangle
        background_rect = QRectF(
            label_pos.x() - 4,
            label_pos.y() - text_rect.height() / 2 - 2,
            text_rect.width() + 8,
            text_rect.height() + 4
        )

        # Draw background
        pen = QPen(QColor(0, 0, 0), 1.0)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 191)))
        painter.drawRect(background_rect)

        # Draw text
        painter.setPen(QPen(QColor(0, 0, 0), 1.0))
        painter.drawText(background_rect, Qt.AlignmentFlag.AlignCenter, text)

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
        dialog.setWindowTitle("Edit Value")
        dialog.setModal(True)

        layout = QVBoxLayout()
        dialog.setLayout(layout)

        # Add label
        label = QLabel("Enter new value:")
        layout.addWidget(label)

        # Add line edit with validation
        line_edit = QLineEdit()
        line_edit.setText(str(current_value))
        line_edit.selectAll()
        
        # Create validator for digits, '-', and '.' only
        from PySide6.QtGui import QRegularExpressionValidator
        from PySide6.QtCore import QRegularExpression
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
