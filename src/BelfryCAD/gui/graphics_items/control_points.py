"""
ControlPoint - A class representing a control point for CAD items.
"""
import math
from typing import Callable, TYPE_CHECKING
from PySide6.QtCore import (
    Qt, QPointF, QRectF, QTimer, QPropertyAnimation, QEasingCurve
)
from PySide6.QtGui import (
    QPen, QBrush, QColor, QFont, QFontMetrics, QPainterPath, QTransform
)
from PySide6.QtWidgets import (
    QGraphicsItem, QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox
)

if TYPE_CHECKING:
    from BelfryCAD.gui.widgets.cad_expression_edit import CadExpressionEdit


class ControlPoint(QGraphicsItem):
    """Base class for control point graphics items."""

    def __init__(
            self,
            model_view=None,
            setter=None,
            tool_tip=None
    ):
        super().__init__()  # Use parent-child relationship
        self.model_view = model_view
        self.setter = setter
        self.control_size = 9
        self.tool_tip = tool_tip
        
        # Use Qt's built-in flags (movable disabled since parent handles movement)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

        if self.tool_tip:
            self.setToolTip(self.tool_tip)
        
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
        if self.setter and self.model_view:
            try:
                # Call the setter with the new position in scene coordinates
                self.setter(value)
                self.model_view.update_view()
                
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
        model_view=None,
        setter=None,
        format_string=None,
        prefix="",
        suffix="",
        cad_item=None,
        label="value",
        angle=None,
        pixel_offset=0,
        precision_override=None,
        is_length=True,
        min_value=None,
        max_value=None
    ):
        super().__init__(
            model_view=model_view,
            setter=setter)
        self.setZValue(10002)
        # Store precision for dynamic updates
        main_window = self.cad_item.main_window # type: ignore
        if precision_override is None:
            precision = main_window.cad_scene.get_precision()
        else:
            precision = precision_override
        self._precision = precision
        self._precision_override = precision_override
        # Use provided format_string or create one from precision
        if format_string is None:
            self._format_string = f"{{:.{precision}f}}"
        else:
            self._format_string = format_string
        self._prefix = prefix
        self._suffix = suffix
        self._label = label
        self._angle = angle
        self._pixel_offset = pixel_offset
        self._is_length = is_length
        self._min_value = min_value
        self._max_value = max_value
        self._is_editing = False
        self._current_value = 0.0
        self._current_position = QPointF(0, 0)
        self._bounding_rect = QRectF(0, 0, 0, 0)
        
        # Cache for performance optimization
        self._cached_text = self._format_text(self._current_value)
        self._cached_bounding_rect = QRectF(0, 0, 0, 0)
        self._cached_scale = 1.0
        self._needs_geometry_update = True
        
        # Set tooltip to label if it's not "value"
        if self._label != "value":
            self.setToolTip(self._label)
        else:
            self.setToolTip("")

    def get_position(self):
        """Get the current position."""
        return self._current_position
    
    def is_value_in_range(self, value=None):
        """Check if the given value (or current value if None) is within the min/max range."""
        if value is None:
            value = self._current_value
        
        if self._min_value is not None and value < self._min_value:
            return False
        if self._max_value is not None and value > self._max_value:
            return False
        return True
    
    def update_precision(self, new_precision: int):
        """Update the precision and refresh the display."""
        if self._precision_override is None:
            self._precision = new_precision
        else:
            self._precision = self._precision_override
        # Update format string if it was created from precision
        self._format_string = f"{{:.{self._precision}f}}"
        
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
        if self._is_length:
            main_window = self.cad_item.main_window # type: ignore
            grid_info = main_window.grid_info
            valstr = grid_info.format_label(value, no_subs=True).replace("\n", " ")
        else:
            valstr = self._format_string.format(value)
            if '.' in valstr:
                valstr = valstr.rstrip('0').rstrip('.')
        pfx = self._prefix if self._prefix else ""
        sfx = self._suffix if self._suffix else ""
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
        if self._angle is not None:
            ocos = math.cos(math.radians(self._angle))
            osin = math.sin(math.radians(self._angle))
        else:
            ocos = 0
            osin = 0
        label_pos = QPointF(
            self._pixel_offset * ocos,
            -self._pixel_offset * osin
        )

        epsilon = 1e-6
        if ocos < -epsilon:
            label_pos += QPointF(-box_width/2, 0)
        elif ocos > epsilon:
            label_pos += QPointF(box_width/2, 0)

        if osin > epsilon:
            label_pos += QPointF(0, -box_height/2)
        elif osin < -epsilon:
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
        """Start editing the control datum value."""
        if hasattr(self, '_is_editing') and self._is_editing:
            return
        
        self._is_editing = True
        
        # Get current value
        current_value = self._format_text(self._current_value)
        
        # Create dialog
        dialog = QDialog()
        dialog.setWindowTitle(f"Edit {self._label}")
        dialog.setModal(True)

        layout = QVBoxLayout()
        dialog.setLayout(layout)

        # Add label
        label = QLabel(f"Enter new {self._label}:")
        layout.addWidget(label)

        # Add CadExpressionEdit for expression editing
        # Import at runtime to avoid circular imports
        from BelfryCAD.gui.widgets.cad_expression_edit import CadExpressionEdit
        
        main_window = self.scene().parent()
        expr_edit = CadExpressionEdit(main_window.cad_expression) # type: ignore
        expr_edit.setMinimumWidth(200)
        expr_edit.setText(current_value)
        expr_edit.selectAll()
        layout.addWidget(expr_edit)

        # Add "Out of Range" indicator label
        out_of_range_label = QLabel("Out of Range")
        out_of_range_label.setStyleSheet("color: red; font-weight: bold;")
        out_of_range_label.setVisible(False)  # Initially hidden
        layout.addWidget(out_of_range_label)

        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        set_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        set_button.setText("Set")
        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setText("Cancel")
        set_button.setEnabled(False)

        # Connect validation
        def validate_input():
            text = expr_edit.text()
            if expr_edit.get_error() is None and text.strip():
                try:
                    # Evaluate the expression to check if it's within range
                    new_value = float(expr_edit._expression.evaluate(text))
                    scale = self.cad_item.main_window.grid_info.unit_scale # type: ignore
                    scaled_value = new_value * scale
                    
                    # Check if the value is within range
                    if self.is_value_in_range(scaled_value):
                        set_button.setEnabled(True)
                        out_of_range_label.setVisible(False)
                    else:
                        set_button.setEnabled(False)
                        out_of_range_label.setVisible(True)
                except Exception:
                    set_button.setEnabled(False)
                    out_of_range_label.setVisible(False)  # Hide for invalid expressions
            else:
                set_button.setEnabled(False)
                out_of_range_label.setVisible(False)  # Hide for empty/invalid input
        expr_edit.textChanged.connect(validate_input)
        validate_input()

        button_box.accepted.connect(lambda: self._finish_editing(dialog, expr_edit))
        button_box.rejected.connect(lambda: self._cancel_editing(dialog))
        # Also connect dialog's rejected signal to handle Escape key
        dialog.rejected.connect(lambda: self._cancel_editing(dialog))
        layout.addWidget(button_box)

        # Set focus to expression edit
        expr_edit.setFocus()

        # Show dialog
        dialog.exec()

    def _finish_editing(self, dialog, expr_edit):
        """Finish editing and apply the new value."""
        try:
            # Evaluate the expression to a float
            new_value = float(expr_edit._expression.evaluate(expr_edit.text()))
            scale = self.cad_item.main_window.grid_info.unit_scale # type: ignore
            self.call_setter_with_updates(new_value * scale)
        except Exception:
            pass

        dialog.accept()
        if hasattr(self, '_is_editing'):
            self._is_editing = False
        self.update()
        # Force a complete redraw to ensure the control datum is visible
        self.prepareGeometryChange()
        if self.scene():
            self.scene().update()

    def _cancel_editing(self, dialog):
        """Cancel editing."""
        dialog.reject()
        if hasattr(self, '_is_editing'):
            self._is_editing = False
        self.update()
        # Force a complete redraw to ensure the control datum is visible
        self.prepareGeometryChange()
        if self.scene():
            self.scene().update()

    @property
    def precision(self):
        """Get the precision."""
        return self._precision

    @precision.setter
    def precision(self, value: int):
        """Set the precision."""
        self.update_precision(value)

    @property
    def format_string(self):
        """Get the format string."""
        return self._format_string

    @format_string.setter
    def format_string(self, value: str):
        """Set the format string."""
        self._format_string = value

    @property
    def prefix(self):
        """Get the prefix."""
        return self._prefix

    @prefix.setter
    def prefix(self, value: str):
        """Set the prefix."""
        self._prefix = value

    @property
    def suffix(self):
        """Get the suffix."""
        return self._suffix

    @suffix.setter
    def suffix(self, value: str):
        """Set the suffix."""
        self._suffix = value

    @property
    def label(self):
        """Get the label."""
        return self._label

    @label.setter
    def label(self, value: str):
        """Set the label."""
        self._label = value

    @property
    def angle(self):
        """Get the angle."""
        return self._angle

    @angle.setter
    def angle(self, value: float):
        """Set the angle."""
        self._angle = value

    @property
    def pixel_offset(self):
        """Get the pixel offset."""
        return self._pixel_offset

    @pixel_offset.setter
    def pixel_offset(self, value: float):
        """Set the pixel offset."""
        self._pixel_offset = value

    @property
    def min_value(self):
        """Get the minimum value."""
        return self._min_value

    @min_value.setter
    def min_value(self, value):
        """Set the minimum value."""
        self._min_value = value

    @property
    def max_value(self):
        """Get the maximum value."""
        return self._max_value

    @max_value.setter
    def max_value(self, value):
        """Set the maximum value."""
        self._max_value = value

    @property
    def setter(self) -> Callable:
        """Get the setter."""
        return self._setter

    @setter.setter
    def setter(self, value: Callable):
        """Set the setter."""
        self._setter = value
