from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QMessageBox, QAbstractItemView
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox

from ...utils.cad_expression import CadExpression
from ..widgets.cad_expression_edit import CadExpressionEdit

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
        layout.addWidget(self.table)

        # Add/Delete buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("+")
        self.add_btn.setToolTip("Add Parameter")
        self.delete_btn = QPushButton("-")
        self.delete_btn.setToolTip("Delete Parameter")
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.add_btn.clicked.connect(self._add_param)
        self.delete_btn.clicked.connect(self._delete_param)
        self.table.cellDoubleClicked.connect(self._edit_param)

    def refresh(self):
        self.table.setRowCount(0)
        for i, (name, expr_str) in enumerate(self.cad_expression.expressions.items()):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(str(name)))
            expr_item = QTableWidgetItem(str(expr_str))
            # Add tooltip with evaluated value
            try:
                value = self.cad_expression.get_variable(name)
                expr_item.setToolTip(f"Value: {value}")
            except Exception as e:
                expr_item.setToolTip(f"Error: {e}")
            self.table.setItem(i, 1, expr_item)

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
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Select a parameter to delete.")
            return
        name = self.table.item(row, 0).text() # type: ignore
        reply = QMessageBox.question(self, "Delete Parameter", f"Delete parameter '{name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            del self.cad_expression.expressions[name]
            self.refresh()
            self.parameter_changed.emit()
