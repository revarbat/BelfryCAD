from PySide6.QtCore import QObject, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QGraphicsView, QWidget

from ...grid_info import GridInfo


class DigitOnlyInputFilter(QObject):
    """Input filter that only allows digits."""

    def __init__(self, parent=None):
        super().__init__(parent)

    def eventFilter(self, obj, event):
        if event.type() == event.Type.KeyPress:
            key = event.key()
            # Allow digits 0-9, backspace, delete, home, end, left, right, enter
            if (key >= Qt.Key.Key_0 and key <= Qt.Key.Key_9) or \
               key in [Qt.Key.Key_Backspace, Qt.Key.Key_Delete,
                      Qt.Key.Key_Home, Qt.Key.Key_End,
                      Qt.Key.Key_Left, Qt.Key.Key_Right,
                      Qt.Key.Key_Return, Qt.Key.Key_Enter]:
                return False  # Allow the event
            else:
                return True   # Block the event
        return False


class ZoomEditWidget(QWidget):
    """A widget for editing and displaying zoom level, with label and percent sign."""
    def __init__(self, view: QGraphicsView, parent=None):
        super().__init__(parent)
        self._view = view

        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for compact appearance

        self.zoom_label = QLabel("Zoom:")
        self.zoom_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.scale_label = QLineEdit("100")
        self.scale_label.setFixedWidth(50)
        self.scale_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.scale_label.setToolTip("Double-click to edit zoom level (1-10000)")
        self.scale_label.setReadOnly(True)

        self.percent_label = QLabel("%")
        self.percent_label.setFixedWidth(20)
        self.percent_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Digit filter
        self.digit_filter = DigitOnlyInputFilter()
        self.scale_label.installEventFilter(self.digit_filter)

        layout.addWidget(self.zoom_label)
        layout.addWidget(self.scale_label)
        layout.addWidget(self.percent_label)

        self.scale_label.mouseDoubleClickEvent = self._scale_label_double_click
        self.scale_label.returnPressed.connect(self._apply_zoom_from_label)
        self.scale_label.editingFinished.connect(self._apply_zoom_from_label)

    @property
    def view(self):
        return self._view

    @view.setter
    def view(self, view: QGraphicsView):
        self._view = view

    def set_zoom_value(self, value):
        self.scale_label.setText(str(int(value)))

    def get_zoom_value(self):
        try:
            return int(self.scale_label.text())
        except ValueError:
            return 100

    def set_editable(self, editable: bool):
        self.scale_label.setReadOnly(not editable)
        if editable:
            self.scale_label.selectAll()
            self.scale_label.setFocus()

    def _scale_label_double_click(self, event):
        """Handle double-click event on the scale label."""
        current_zoom = self.get_zoom_value()
        self.set_zoom_value(current_zoom)
        self.set_editable(True)
        # Call the original mouse double-click event
        QLineEdit.mouseDoubleClickEvent(self.scale_label, event)

    def _apply_zoom_from_label(self):
        """Apply the zoom level from the scale label."""
        try:
            zoom_value = self.get_zoom_value()
            if zoom_value < 1:
                zoom_value = 1
            elif zoom_value > 10000:
                zoom_value = 10000
            GridInfo.set_zoom(self.view, zoom_value)
            self.scale_label.setText(str(zoom_value))
        except ValueError:
            # Reset to current zoom if invalid input
            current_zoom = GridInfo.get_zoom(self.view)
            self.scale_label.setText(str(int(current_zoom)))

        # Make the label read-only again
        self.scale_label.setReadOnly(True)

    def _update_scale_label(self):
        """Update the scale percentage label."""
        zoom = GridInfo.get_zoom(self.view)
        self.scale_label.setText(str(int(zoom)))
