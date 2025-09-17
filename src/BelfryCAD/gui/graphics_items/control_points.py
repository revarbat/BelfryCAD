"""
ControlPoint - A class representing a control point for CAD items.
"""
import math
from enum import Enum
from typing import Callable, TYPE_CHECKING, cast, Optional

from PySide6.QtCore import (
    Qt, QPointF, QRectF
)
from PySide6.QtGui import (
    QPen, QBrush, QColor, QFont, QFontMetrics, QPainterPath, QTransform
)
from PySide6.QtWidgets import (
    QGraphicsItem, QDialog, QVBoxLayout, QLabel, QDialogButtonBox
)

if TYPE_CHECKING:
    from BelfryCAD.gui.widgets.cad_expression_edit import CadExpressionEdit
    from BelfryCAD.gui.widgets.cad_scene import CadScene


class ControlPointShape(Enum):
    """Enum for control point types."""
    ROUND = "round"
    SQUARE = "square"
    TRIANGLE = "triangle"
    DIAMOND = "diamond"
    PENTAGON = "pentagon"
    HEXAGON = "hexagon"


class ControlPoint(QGraphicsItem):
    """Base class for control point graphics items."""

    def __init__(
            self,
            model_view,
            setter: Callable[[QPointF], None],
            cp_shape: ControlPointShape = ControlPointShape.ROUND,
            big: bool = False,
            tool_tip: Optional[str] = None
    ):
        super().__init__()  # Use parent-child relationship
        self.model_view = model_view
        self.setter = setter
        self.control_size = 9
        self.cp_shape = cp_shape
        self.tool_tip = tool_tip
        self.big = big
        
        # Use Qt's built-in flags - make selectable to be part of selection system
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

        if self.tool_tip:
            self.setToolTip(self.tool_tip)
        
        # Set high Z value to appear above other items
        self.setZValue(10001)
        
        # Dragging state
        self._is_dragging = False

    def scene(self) -> 'CadScene':
        """Get the scene."""
        return cast('CadScene', super().scene())

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
                
                # The viewmodel will emit control_points_updated signal
                # which is connected to update_controls in the document window
                # This ensures proper coordination of all updates
                
            except (RuntimeError, AttributeError, TypeError) as e:
                print(f"Error in control point setter: {e}")

    def boundingRect(self):
        """Return bounding rectangle for hit testing."""
        # Get the current scale from the scene to make bounding rect scale independent
        scene = self.scene()
        if scene and scene.views():
            # Get the first view's transform to determine current scale
            view = scene.views()[0]
            scale = view.transform().m11()
            if self.big:
                control_size = 12.0
            else:
                control_size = 9.0
            if self.cp_shape == ControlPointShape.TRIANGLE:
                control_size *= 1.5
            elif self.cp_shape == ControlPointShape.DIAMOND:
                control_size *= math.sqrt(2)
            elif self.cp_shape == ControlPointShape.PENTAGON:
                control_size *= 4/3
            elif self.cp_shape == ControlPointShape.HEXAGON:
                control_size *= 5/4
            # Convert pixel size to scene coordinates
            control_size = float(control_size) / scale
        else:
            # Fallback to a reasonable size if no scene/view available
            control_size = 0.3
        
        control_padding = control_size / 2
        return QRectF(-control_padding, -control_padding, control_size, control_size)

    def shape(self):
        """Return shape for hit testing."""
        path = QPainterPath()
        rect = self.boundingRect()
        control_padding = rect.width() / 2
        if self.cp_shape == ControlPointShape.ROUND:
            path.addEllipse(rect)
            return path
        elif self.cp_shape == ControlPointShape.SQUARE:
            path.addRect(rect)
            return path
        elif self.cp_shape == ControlPointShape.TRIANGLE:
            ngon = 3
        elif self.cp_shape == ControlPointShape.DIAMOND:
            ngon = 4
        elif self.cp_shape == ControlPointShape.PENTAGON:
            ngon = 5
        elif self.cp_shape == ControlPointShape.HEXAGON:
            ngon = 6
        else:
            ngon = 36

        for i in range(ngon):
            angle = math.radians(i * 360 / ngon + 90)
            x = control_padding * math.cos(angle)
            y = control_padding * math.sin(angle)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.closeSubpath()

        return path

    def paint(self, painter, option, widget=None):
        """Paint the control point."""
        painter.save()

        # Standardized control point styling
        control_pen = QPen(QColor(255, 0, 0), 2.0)
        control_pen.setCosmetic(True)
        painter.setPen(control_pen)

        if self.isSelected():
            control_brush = QBrush(QColor(255, 0, 0))
        else:
            control_brush = QBrush(QColor(255, 255, 255))
        painter.setBrush(control_brush)

        if self.cp_shape == ControlPointShape.ROUND:
            painter.drawEllipse(self.boundingRect())
        elif self.cp_shape == ControlPointShape.SQUARE:
            painter.drawRect(self.boundingRect())
        else:
            painter.drawPath(self.shape())

        painter.restore()

    def setShape(self, shape: ControlPointShape):
        """Set the shape of the control point."""
        self.cp_shape = shape
        self.update()

    def setBig(self, big: bool):
        """Set the size of the control point."""
        self.big = big
        self.update()

    def setToolTip(self, tool_tip: str):
        """Set the tooltip of the control point."""
        self.tool_tip = tool_tip
        super().setToolTip(tool_tip)

    def setSetter(self, setter: Callable[[QPointF], None]):
        """Set the setter of the control point."""
        self.setter = setter

    def itemChange(self, change, value):
        """Handle item state changes using Qt's built-in system."""
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        """Handle mouse press events for control point dragging."""
        # Set dragging state
        self._is_dragging = True
        
        # Notify scene that control point dragging has started
        scene = self.scene()
        if scene and hasattr(scene, 'set_control_point_dragging'):
            scene.set_control_point_dragging(True)
        
        # Accept the event to prevent it from propagating to the scene
        # This prevents deselection of the main CAD object
        event.accept()

    def mouseMoveEvent(self, event):
        """Handle mouse move events for control point dragging."""
        if event.buttons() & Qt.MouseButton.LeftButton and self._is_dragging:
            # Get the new position in scene coordinates
            raw_pos = event.scenePos()
            
            # Apply snapping if snaps system is available
            snapped_pos = raw_pos
            scene = self.scene()
            if scene:
                # Try to get snaps system from scene
                snaps_system = getattr(scene, '_snaps_system', None)
                if snaps_system and hasattr(snaps_system, 'get_snap_point'):
                    snapped_pos = snaps_system.get_snap_point(raw_pos)
                    if snapped_pos is None:
                        snapped_pos = raw_pos  # Fallback to original position if no snap
            
            # Call the setter to update the object property with snapped position
            if self.setter:
                self.call_setter_with_updates(snapped_pos)
            
            # Accept the event to prevent it from propagating to the scene
            event.accept()
        else:
            # If not dragging, let the event propagate normally
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events for control point dragging."""
        # Clear dragging state
        self._is_dragging = False
        
        # Notify scene that control point dragging has ended
        scene = self.scene()
        if scene and hasattr(scene, 'set_control_point_dragging'):
            scene.set_control_point_dragging(False)
        
        # Accept the event to prevent it from propagating to the scene
        # This prevents deselection of the main CAD object
        event.accept()


class ControlDatum(ControlPoint):
    """A control datum graphics item for displaying and editing data values."""

    def __init__(
        self,
        model_view,
        setter,
        format_string=None,
        prefix="",
        suffix="",
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
        document_window = self.model_view.document_window
        
        precision = document_window.cad_scene.get_precision()
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
        # Defensive check to ensure the datum is properly initialized
        if not hasattr(self, '_format_string') or not hasattr(self, '_cached_text'):
            return
            
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

    def _format_text(self, value, no_prefix=False, no_suffix=False):
        """Format the text for display."""
        # Defensive check to ensure the datum is properly initialized
        if not hasattr(self, '_format_string') or not hasattr(self, '_prefix') or not hasattr(self, '_suffix'):
            return str(value)
            
        if self._is_length:
            document_window = self.model_view.document_window
            grid_info = document_window.grid_info
            valstr = grid_info.format_label(value, no_subs=True).replace("\n", " ")
        else:
            valstr = self._format_string.format(value)
            if '.' in valstr:
                valstr = valstr.rstrip('0').rstrip('.')
        pfx = self._prefix if self._prefix and not no_prefix else ""
        sfx = self._suffix if self._suffix and not no_suffix else ""
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

        # Additional defensive check for cached text
        if not hasattr(self, '_cached_text') or self._cached_text is None:
            return

        # Use cached text
        text = self._cached_text

        painter.save()

        # Set up font
        font = QFont("Arial", 14)
        #font.setUnderline(True)
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
        current_value = self._format_text(self._current_value, no_prefix=True, no_suffix=True)
        
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
        
        document_window = self.scene().parent()
        expr_edit = CadExpressionEdit(document_window.cad_expression) # type: ignore
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
                    scale = self.model_view.document_window.grid_info.unit_scale
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
            scale = 1.0
            if self._is_length:
                scale = self.model_view.document_window.grid_info.unit_scale
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
