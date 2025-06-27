"""
ControlPoint - A class representing a control point for CAD items.
"""

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QFontMetrics, QPainter, QPainterPath
from PySide6.QtWidgets import QGraphicsItem, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QDialogButtonBox


class ControlPoint(QGraphicsItem):
    """Base class for control point graphics items."""

    def __init__(
            self,
            parent=None,
            getter=None,
            setter=None
    ):
        super().__init__(parent)  # Use parent-child relationship
        self.getter = getter
        self.setter = setter
        
        # Use Qt's built-in flags
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        
        # Set high Z value to appear above other items
        self.setZValue(10000)
        
        # Set initial position from getter if available
        self.set_position_from_getter()

    def get_position(self):
        """Get the current position, using getter if available."""
        if self.getter:
            try:
                return self.getter()
            except (RuntimeError, AttributeError, TypeError):
                pass
        return QPointF(0, 0)  # Default fallback

    def set_position(self, new_position):
        """Set the position, using setter if available."""
        if self.setter:
            try:
                self.setter(new_position)
            except (RuntimeError, AttributeError, TypeError):
                pass
        self.setPos(new_position)

    def set_position_from_getter(self):
        """Set the position using the getter callback."""
        position = self.get_position()
        self.setPos(position)

    def _get_control_size_in_scene_coords(self, painter):
        """Get control point size in scene coordinates based on current zoom level."""
        pixel_size = 8
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
            # Convert 8 pixels to scene coordinates
            control_size = 8.0 / scale
        else:
            # Fallback to a reasonable size if no scene/view available
            control_size = 0.15
        
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

    def itemChange(self, change, value):
        """Handle item state changes using Qt's built-in system."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Position is changing - notify via setter
            if self.setter:
                try:
                    self.setter(value)
                except (RuntimeError, AttributeError, TypeError):
                    pass
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        """Handle mouse press using Qt's built-in system."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            event.ignore()

    def mouseReleaseEvent(self, event):
        """Handle mouse release using Qt's built-in system."""
        self.setCursor(Qt.CursorShape.ArrowCursor)
        event.accept()


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
        path.addRect(self.boundingRect())  # Use bounding rect for max hit area
        return path


class ControlDatum(ControlPoint):
    """A control datum graphics item for displaying and editing data values."""

    def __init__(self, getter, setter=None, pos_getter=None,
                 format_string="{:.3f}", prefix="", suffix="", parent=None):
        super().__init__(
            parent=parent,
            getter=getter, setter=setter)
        self.pos_getter = pos_getter
        self.format_string = format_string
        self.prefix = prefix
        self.suffix = suffix
        self._is_editing = False
        
        # Set initial position from pos_getter if available
        self.set_position_from_getter()

    def get_position(self):
        """Get the current position, using pos_getter if available."""
        if self.pos_getter:
            try:
                return self.pos_getter()
            except (RuntimeError, AttributeError, TypeError):
                pass
        return QPointF(0, 0)  # Default fallback

    def set_position_from_getter(self):
        """Set the position using the pos_getter callback."""
        position = self.get_position()
        self.setPos(position)

    def mousePressEvent(self, event):
        """Handle mouse press to start editing or allow dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.setter:
                self.start_editing()
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def boundingRect(self):
        """Return the bounding rectangle of this datum label."""
        # Defensive check for attributes
        if not hasattr(self, 'prefix') or not hasattr(self, 'suffix') or not hasattr(self, 'format_string'):
            return super().boundingRect()
            
        try:
            if self.getter:
                value = self.getter()
            else:
                return super().boundingRect()
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

        try:
            if self.getter:
                value = self.getter()
            else:
                return
        except:
            return

        # Set up font
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
        pixel_offset = 15
        scene_offset = pixel_offset / scale

        # Calculate label position relative to datum position
        datum_pos = self.get_position()
        label_pos = QPointF(
            datum_pos.x() + scene_offset,
            datum_pos.y() + scene_offset
        )

        # Draw background rectangle
        background_rect = QRectF(
            label_pos.x() - 2,
            label_pos.y() - text_rect.height() / 2 - 2,
            text_rect.width() + 4,
            text_rect.height() + 4
        )

        # Draw background
        painter.setPen(QPen(QColor(255, 255, 255), 1.0))
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        painter.drawRect(background_rect)

        # Draw text
        painter.setPen(QPen(QColor(0, 0, 0), 1.0))
        painter.drawText(label_pos, text)

    def start_editing(self):
        """Start editing the datum value."""
        # Defensive check for attributes
        if not hasattr(self, '_is_editing'):
            return
            
        if self._is_editing:
            return

        self._is_editing = True
        self.update()

        try:
            if self.getter:
                current_value = self.getter()
            else:
                current_value = 0.0
        except:
            current_value = 0.0

        # Create editing dialog
        dialog = QDialog()
        dialog.setWindowTitle("Edit Value")
        dialog.setModal(True)

        layout = QVBoxLayout()
        dialog.setLayout(layout)

        # Add label
        label = QLabel("Enter new value:")
        layout.addWidget(label)

        # Add line edit
        line_edit = QLineEdit()
        line_edit.setText(str(current_value))
        line_edit.selectAll()
        layout.addWidget(line_edit)

        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
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
            if self.setter:
                self.setter(new_value)
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
