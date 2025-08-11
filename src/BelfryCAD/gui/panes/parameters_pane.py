from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QMessageBox, QAbstractItemView, QToolBar, QSizePolicy
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox
from PySide6.QtGui import QAction
from PySide6.QtCore import QSize
from PySide6.QtGui import QColor

from ...utils.cad_expression import CadExpression
from ..widgets.cad_expression_edit import CadExpressionEdit
from ..icon_manager import get_icon

class ParametersPane(QWidget):
    """
    Pane for adding, deleting, listing, and editing parameters (variables) in a
    CadExpression instance. Emits parameter_changed signal when parameters are
    updated. Shows both the expression and the current evaluated value.
    """
    parameter_changed = Signal()

    def __init__(self, cad_expression: CadExpression, parent=None):
        super().__init__(parent)
        self.cad_expression = cad_expression
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Table for parameters
        self.table = QTableWidget(0, 2, self)
        self.table.setHorizontalHeaderLabels(["Name", "Expression"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)  # Allow user resizing
        header.setStretchLastSection(True)
        # Set the default width of the first column to fit about 10 letters
        self.table.setColumnWidth(0, 90)
        self.table.setColumnWidth(2, 50)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setDropIndicatorShown(False)
        self.table.setDragEnabled(False)
        self.table.setAcceptDrops(False)
        self.table.viewport().setAcceptDrops(False)
        self.table.model().rowsMoved.connect(self._on_rows_moved)
        layout.addWidget(self.table)

        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(16, 16))
        self.toolbar.setMovable(False)
        layout.addWidget(self.toolbar)

        # Add new parameter action
        add_param_action = QAction(self)
        add_param_action.setIcon(get_icon("item-add"))
        add_param_action.setToolTip("Add Parameter")
        add_param_action.triggered.connect(self._add_param)
        self.toolbar.addAction(add_param_action)

        # Add delete parameter action
        self.delete_param_action = QAction(self)
        self.delete_param_action.setIcon(get_icon("item-delete"))
        self.delete_param_action.setToolTip("Delete Parameter")
        self.delete_param_action.triggered.connect(self._delete_param)
        self.toolbar.addAction(self.delete_param_action)
        self.delete_param_action.setEnabled(False)

        # Add spacer to push move actions to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer)

        # Add move up action
        self.move_up_action = QAction("↑", self)
        self.move_up_action.setToolTip("Move Up")
        self.move_up_action.triggered.connect(self._move_param_up)
        self.toolbar.addAction(self.move_up_action)
        self.move_up_action.setEnabled(False)

        # Add move down action
        self.move_down_action = QAction("↓", self)
        self.move_down_action.setToolTip("Move Down")
        self.move_down_action.triggered.connect(self._move_param_down)
        self.toolbar.addAction(self.move_down_action)
        self.move_down_action.setEnabled(False)

        self.table.cellDoubleClicked.connect(self._edit_param)
        self.table.selectionModel().selectionChanged.connect(self._update_delete_action_enabled)
        self.table.selectionModel().selectionChanged.connect(self._update_move_actions_enabled)

    def _on_rows_moved(self, parent, start, end, dest, dest_row):
        # Update the order of self.cad_expression.expressions to match the new table order
        new_order = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is not None:
                new_order.append(item.text())
        # Rebuild the expressions dict in the new order
        new_expressions = {name: self.cad_expression.expressions[name] for name in new_order if name in self.cad_expression.expressions}
        self.cad_expression.expressions = new_expressions
        self.refresh()
        self.parameter_changed.emit()

    def refresh(self):
        self.table.setRowCount(0)
        for i, (name, expr_str) in enumerate(self.cad_expression.expressions.items()):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(str(name)))
            expr_item = QTableWidgetItem(str(expr_str))
            # Add tooltip with both expression and evaluated value (but not for simple numbers)
            try:
                value = self.cad_expression.get_variable(name)
                # Check if expression is just a number (no tooltip needed)
                try:
                    float(expr_str.strip())
                    # Expression is just a number, no tooltip needed
                except ValueError:
                    # Expression is not just a number, set tooltip
                    expr_item.setToolTip(f"{expr_str}\n= {value}")
                # Check if parameter is valid (can be evaluated)
                if not self._is_parameter_valid(name):
                    expr_item.setForeground(QColor(255, 0, 0))  # Red for invalid
            except Exception as e:
                # Always show tooltip for errors, even if expression is just a number
                expr_item.setToolTip(f"{expr_str}\nError: {e}")
                expr_item.setForeground(QColor(255, 0, 0))  # Red for invalid
            self.table.setItem(i, 1, expr_item)

    def _is_parameter_valid(self, name: str) -> bool:
        """Check if a parameter can be evaluated without errors."""
        try:
            self.cad_expression.get_variable(name)
            return True
        except Exception:
            return False

    def _add_param(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Parameter")
        layout = QVBoxLayout(dialog)
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("Parameter name (no $)")
        expr_edit = CadExpressionEdit(self.cad_expression)
        expr_edit.setPlaceholderText("Expression (e.g. 5.3, or 2 * $foo)")
        expr_edit.setMinimumWidth(200)
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(name_edit)
        layout.addWidget(QLabel("Expression:"))
        layout.addWidget(expr_edit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = name_edit.text().strip()
            expr_str = expr_edit.text().strip()
            if not name or not expr_str:
                QMessageBox.warning(self, "Invalid Input", "Name and expression are required.")
                return
            if name in self.cad_expression.expressions:
                QMessageBox.warning(self, "Duplicate Name", f"Parameter '{name}' already exists.")
                return
            # Try evaluating to check for errors, but store the expression string
            try:
                self.cad_expression.evaluate(expr_str)
            except Exception as e:
                QMessageBox.warning(self, "Invalid Expression", f"Error evaluating expression: {e}")
                return
            self.cad_expression.set_variable(name, expr_str)
            self.refresh()
            self.parameter_changed.emit()

    def _edit_param(self, row, column=None):
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Select a parameter to edit.")
            return
        name = self.table.item(row, 0).text() # type: ignore
        old_expr = self.cad_expression.expressions[name]
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Parameter: {name}")
        layout = QVBoxLayout(dialog)
        expr_edit = CadExpressionEdit(self.cad_expression)
        expr_edit.setText(str(old_expr))
        expr_edit.setMinimumWidth(200)
        layout.addWidget(QLabel(f"Expression for {name}:"))
        layout.addWidget(expr_edit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            expr_str = expr_edit.text().strip()
            if not expr_str:
                QMessageBox.warning(self, "Invalid Input", "Expression is required.")
                return
            # Try evaluating to check for errors, but store the expression string
            try:
                self.cad_expression.evaluate(expr_str)
            except Exception as e:
                QMessageBox.warning(self, "Invalid Expression", f"Error evaluating expression: {e}")
                return
            self.cad_expression.set_variable(name, expr_str)
            self.refresh()
            self.parameter_changed.emit()

    def _delete_param(self):
        selection = self.table.selectionModel().selectedRows()
        names = []
        for row in selection:
            item = self.table.item(row.row(), 0)
            if item is not None:
                names.append(item.text())
        if not names:
            QMessageBox.warning(self, "No Selection", "Select a parameter to delete.")
            return
        if len(names) == 1:
            msg = f"Delete parameter '{names[0]}'?"
        else:
            msg = f"Delete parameters: {', '.join(names)}?"
        reply = QMessageBox.question(self, "Delete Parameter(s)", msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            for name in names:
                if name in self.cad_expression.expressions:
                    del self.cad_expression.expressions[name]
            self.refresh()
            self.parameter_changed.emit()

    def _update_delete_action_enabled(self, *args):
        selected = self.table.selectionModel().hasSelection() and self.table.currentRow() >= 0
        self.delete_param_action.setEnabled(selected)

    def _update_move_actions_enabled(self, *args):
        selected_rows = sorted([idx.row() for idx in self.table.selectionModel().selectedRows()])
        row_count = self.table.rowCount()
        if not selected_rows:
            self.move_up_action.setEnabled(False)
            self.move_down_action.setEnabled(False)
            return
        self.move_up_action.setEnabled(selected_rows[0] > 0)
        self.move_down_action.setEnabled(selected_rows[-1] < row_count - 1)

    def _move_param_up(self):
        selected_rows = sorted([idx.row() for idx in self.table.selectionModel().selectedRows()])
        if not selected_rows or selected_rows[0] == 0:
            return
        for row in selected_rows:
            if row == 0:
                continue
            self._swap_rows(row, row - 1)
        self._update_expressions_order()
        self._reselect_rows([r - 1 for r in selected_rows])

    def _move_param_down(self):
        selected_rows = sorted([idx.row() for idx in self.table.selectionModel().selectedRows()], reverse=True)
        row_count = self.table.rowCount()
        if not selected_rows or selected_rows[0] == row_count - 1:
            return
        for row in selected_rows:
            if row == row_count - 1:
                continue
            self._swap_rows(row, row + 1)
        self._update_expressions_order()
        self._reselect_rows([r + 1 for r in selected_rows])

    def _swap_rows(self, row1, row2):
        for col in range(self.table.columnCount()):
            item1 = self.table.takeItem(row1, col)
            item2 = self.table.takeItem(row2, col)
            self.table.setItem(row1, col, item2)
            self.table.setItem(row2, col, item1)

    def _update_expressions_order(self):
        new_order = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is not None:
                new_order.append(item.text())
        new_expressions = {name: self.cad_expression.expressions[name] for name in new_order if name in self.cad_expression.expressions}
        self.cad_expression.expressions = new_expressions
        self.refresh()
        self.parameter_changed.emit()

    def _reselect_rows(self, rows):
        self.table.clearSelection()
        for row in rows:
            self.table.selectRow(row)
