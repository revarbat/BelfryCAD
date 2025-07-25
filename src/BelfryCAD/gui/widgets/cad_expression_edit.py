from PySide6.QtWidgets import QLineEdit, QCompleter
from PySide6.QtGui import QTextCharFormat, QColor, QKeyEvent, QPainter, QPen
from PySide6.QtCore import Qt, QStringListModel
from BelfryCAD.utils.cad_expression import CadExpression
import re

class CadExpressionEdit(QLineEdit):
    """
    Drop-in replacement for QLineEdit for editing CadExpression expressions.
    - Live syntax error underlining (red squiggle) (custom paint)
    - Tab completion for function names and variables
    - Accepts a CadExpression instance for parsing and completion
    - Uses CadExpression for parsing
    """
    def __init__(self, expression: CadExpression, parent=None):
        super().__init__(parent)
        self._expression = expression
        self._functions = list(CadExpression._FUNCTIONS.keys())
        self._completer = QCompleter(self)
        self._update_completer()
        self.setCompleter(self._completer)
        self._error = None
        self._error_region = None
        self.textChanged.connect(self._on_text_changed)
        self.setPlaceholderText("Enter expression (e.g. $radius * pi)")

    def _on_text_changed(self, text):
        self._error = None
        self._error_region = None
        expr = self._expression
        try:
            expr.evaluate(text)
        except Exception as e:
            self._error = str(e)
            # Try to extract error position from message (if possible)
            m = re.search(r'position (\d+)', self._error)
            if m:
                pos = int(m.group(1))
                self._error_region = (pos, min(pos + 1, len(text)))
            else:
                # Underline the whole text if position is unknown
                self._error_region = (0, len(text))
        self.update()  # Trigger repaint for underline

    def get_error(self):
        """Return the current syntax error message, or None if valid."""
        return self._error

    def set_expression(self, expression: CadExpression):
        """Set the CadExpression instance and refresh completion."""
        self._expression = expression
        self._update_completer()

    def set_functions(self, functions):
        """Set the list of function names for completion."""
        self._functions = functions
        self._update_completer()

    def _update_completer(self):
        # Variables are completed with $ prefix
        var_items = [f"${v}" for v in self._expression.expressions.keys()]
        items = var_items + self._functions
        model = QStringListModel(items, self._completer)
        self._completer.setModel(model)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseSensitive)
        self._completer.setFilterMode(Qt.MatchFlag.MatchStartsWith)

    def keyPressEvent(self, event: QKeyEvent):
        # Tab completion for variables and functions
        if event.key() == Qt.Key.Key_Tab:
            if self._completer.popup().isVisible():
                self._completer.popup().setCurrentIndex(self._completer.popup().model().index(0, 0))
                self._completer.complete()
                return
            else:
                self._completer.complete()
                return
        super().keyPressEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        # Custom red squiggle underline for syntax errors
        if self._error_region and self._error_region[1] > self._error_region[0]:
            start, end = self._error_region
            text = self.text()
            font_metrics = self.fontMetrics()
            # Calculate x positions for start and end
            x0 = self.contentsRect().left() + font_metrics.horizontalAdvance(text[:start])
            x1 = self.contentsRect().left() + font_metrics.horizontalAdvance(text[:end])
            y = self.height() - 4
            painter = QPainter(self)
            pen = QPen(QColor('red'))
            pen.setWidth(2)
            painter.setPen(pen)
            # Draw a squiggle underline
            step = 4
            amplitude = 2
            x = x0
            up = True
            while x < x1:
                next_x = min(x + step, x1)
                y_offset = amplitude if up else -amplitude
                painter.drawLine(int(x), y + y_offset, int(next_x), y - y_offset)
                x = next_x
                up = not up
            painter.end() 