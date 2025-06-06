"""
Configuration Pane for PyTkCAD.

This module provides a PySide6/Qt GUI configuration pane system for editing
CAD object properties. It's a direct translation of the original TCL confpane.tcl
functionality with validation, field management, and dynamic UI generation.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QSpinBox, QDoubleSpinBox, QComboBox, QFrame,
    QColorDialog, QFontComboBox, QApplication, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPalette, QValidator, QDoubleValidator, QIntValidator

from typing import Dict, Any, Optional, List, Callable, Union
import math
import re


class ConfigPaneInfo:
    """Global configuration pane information storage."""

    def __init__(self):
        self.no_validate = False
        self.persist_vals = {}
        self.persists = {}
        self.font_combos = {}
        self.size_spins = {}
        self.bold_checks = {}
        self.italic_checks = {}
        self.exec_buttons = {}
        self.focus_field = ""
        self.populate_timer_id = None
        self.prev_fields = {}


# Global instance
confpane_info = ConfigPaneInfo()


class ConfigPaneValidator(QValidator):
    """Custom validator for configuration pane fields."""

    def __init__(self, validate_func: Callable, parent=None):
        super().__init__(parent)
        self.validate_func = validate_func

    def validate(self, input_str: str, pos: int) -> tuple:
        """Validate input using the provided validation function."""
        if self.validate_func(input_str):
            return (QValidator.Acceptable, input_str, pos)
        return (QValidator.Invalid, input_str, pos)


class ConfigPane(QWidget):
    """
    Configuration pane widget for editing CAD object properties.
    """

    # Signals
    field_changed = Signal(str, str, object)  # field_name, datum, value
    execute_requested = Signal(str)  # field_name

    def __init__(self, canvas=None, parent: Optional[QWidget] = None):
        """
        Initialize the configuration pane.

        Args:
            canvas: Canvas object reference
            parent: Parent widget, if any
        """
        super().__init__(parent)
        self.canvas = canvas
        self.fields = []
        self.field_widgets = {}
        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface."""
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

    def validate_combobox(self, combo: QComboBox):
        """Validate combobox input."""
        text = combo.currentText()
        # Implementation would depend on specific validation needs
        pass

    def invalid_cmd(self, canvas, name: str, datum: str, val_get_cb: Optional[Callable],
                   default: Any, var_name: str):
        """Handle invalid input by reverting to old value."""
        QApplication.beep()
        old_val = self.get_datum(canvas, name, datum, val_get_cb, default)
        # Schedule restoration of old value
        QTimer.singleShot(0, lambda: self._restore_value(var_name, old_val))

    def invalid_cmd_point(self, canvas, name: str, datum: str, val_get_cb: Optional[Callable],
                         default: Any, coord_num: int, var_name: str):
        """Handle invalid point input."""
        QApplication.beep()
        old_val = self.get_datum(canvas, name, datum, val_get_cb, default)
        if isinstance(old_val, (list, tuple)) and len(old_val) > coord_num:
            old_val = old_val[coord_num]
        QTimer.singleShot(0, lambda: self._restore_value(var_name, old_val))

    def invalid_cmd_fontsize(self, canvas, name: str, datum: str, val_get_cb: Optional[Callable],
                           default: Any, var_name: str):
        """Handle invalid font size input."""
        QApplication.beep()
        old_val = self.get_datum(canvas, name, datum, val_get_cb, default)
        if isinstance(old_val, (list, tuple)) and len(old_val) > 1:
            old_val = old_val[1]
        QTimer.singleShot(0, lambda: self._restore_value(var_name, old_val))

    def _restore_value(self, var_name: str, value: Any):
        """Restore a widget's value."""
        if var_name in self.field_widgets:
            widget = self.field_widgets[var_name]
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QSpinBox):
                widget.setValue(int(value))
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(float(value))
            elif isinstance(widget, QComboBox):
                widget.setCurrentText(str(value))

    def validate_str(self, canvas, name: str, datum: str, val_set_cb: Optional[Callable],
                    validate_cb: Optional[Callable], value: str) -> bool:
        """Validate string input."""
        if confpane_info.no_validate:
            return True

        if value == "":
            return True

        if validate_cb and not validate_cb(value):
            return False

        self.set_datum(canvas, name, datum, val_set_cb, value)
        return True

    def validate_int(self, canvas, name: str, datum: str, min_val: int, max_val: int,
                    val_set_cb: Optional[Callable], validate_cb: Optional[Callable],
                    value: str) -> bool:
        """Validate integer input."""
        if confpane_info.no_validate:
            return True

        if value == "":
            return True

        try:
            int_val = int(value)
        except ValueError:
            return False

        if int_val < min_val or int_val > max_val:
            return False

        if validate_cb and not validate_cb(int_val):
            return False

        self.set_datum(canvas, name, datum, val_set_cb, int_val)
        return True

    def validate_float(self, canvas, name: str, datum: str, min_val: float, max_val: float,
                      val_set_cb: Optional[Callable], validate_cb: Optional[Callable],
                      is_length: bool, value: str) -> bool:
        """Validate float input."""
        if confpane_info.no_validate:
            return True

        if value == "":
            return True

        try:
            if is_length:
                # Handle unit conversion if needed
                float_val = self._parse_length_value(value)
            else:
                float_val = float(value)
        except (ValueError, TypeError):
            return False

        if float_val < min_val or float_val > max_val:
            return False

        if validate_cb and not validate_cb(float_val):
            return False

        self.set_datum(canvas, name, datum, val_set_cb, float_val)
        return True

    def validate_point(self, canvas, name: str, datum: str, val_set_cb: Optional[Callable],
                      coord_num: int, value: str) -> bool:
        """Validate point coordinate input."""
        if confpane_info.no_validate:
            return True

        if value == "":
            return True

        try:
            float_val = self._parse_length_value(value)
        except (ValueError, TypeError):
            return False

        self.set_point_val(canvas, name, datum, val_set_cb, coord_num, float_val)
        return True

    def validate_fontsize(self, canvas, name: str, datum: str, val_set_cb: Optional[Callable],
                         base_widget: QWidget, value: str) -> bool:
        """Validate font size input."""
        if confpane_info.no_validate:
            return True

        if value == "":
            return True

        try:
            size_val = int(value)
        except ValueError:
            return False

        if size_val < 1:
            return False

        self.set_font_datum(canvas, name, datum, val_set_cb, base_widget)
        return True

    def clear_color(self, canvas, name: str, datum: str, val_set_cb: Optional[Callable],
                   color_button: QPushButton):
        """Clear color selection."""
        color_button.setStyleSheet("background-color: white; color: black;")
        color_button.setText("None")
        self.set_datum(canvas, name, datum, val_set_cb, "none")

    def edit_color(self, canvas, name: str, datum: str, val_set_cb: Optional[Callable],
                  color_button: QPushButton):
        """Open color selection dialog."""
        current_color = color_button.palette().color(QPalette.Button)
        color = QColorDialog.getColor(current_color, self, "Choose a new color")

        if color.isValid():
            color_button.setStyleSheet(f"background-color: {color.name()}; color: {color.name()};")
            color_button.setText("")
            self.set_datum(canvas, name, datum, val_set_cb, color.name())

    def inc_datum(self, canvas, name: str, datum: str, min_val: float, max_val: float,
                 val_set_cb: Optional[Callable], is_length: bool, fmt: str,
                 spin_box: QDoubleSpinBox, direction: str):
        """Increment or decrement datum value."""
        increment = spin_box.singleStep()
        current_val = spin_box.value()

        if direction == "up":
            if current_val + increment >= max_val - 1e-6:
                return
            new_val = current_val + increment
        else:
            if current_val - increment <= min_val + 1e-6:
                return
            new_val = current_val - increment

        spin_box.setValue(new_val)
        self.set_datum(canvas, name, datum, val_set_cb, new_val)

    def set_font_datum(self, canvas, name: str, datum: str, val_set_cb: Optional[Callable],
                      base_widget: QWidget, *args):
        """Set font datum from font controls."""
        # Get font control values
        family_key = f"FONTMB-{canvas}-{name}"
        size_key = f"SIZESP-{canvas}-{name}"
        bold_key = f"BOLDCB-{canvas}-{name}"
        italic_key = f"ITALCB-{canvas}-{name}"

        family = confpane_info.font_combos.get(family_key, "")
        size = confpane_info.size_spins.get(size_key, 12)
        bold = confpane_info.bold_checks.get(bold_key, False)
        italic = confpane_info.italic_checks.get(italic_key, False)

        # Create font specification
        font_spec = [family, size]
        if bold:
            font_spec.append("bold")
        if italic:
            font_spec.append("italic")

        self.set_datum(canvas, name, datum, val_set_cb, font_spec)

    def set_point_val(self, canvas, name: str, datum: str, val_set_cb: Optional[Callable],
                     coord_num: int, value: float):
        """Set point coordinate value."""
        # Implementation would depend on tool/object system integration
        self.field_changed.emit(name, datum, {"coord_num": coord_num, "value": value})

    def get_persistent(self, canvas, datum: str, default: Any) -> Any:
        """Get persistent value for datum."""
        key = f"{canvas}-{datum}"
        if key not in confpane_info.persist_vals:
            confpane_info.persist_vals[key] = default
            if canvas not in confpane_info.persists:
                confpane_info.persists[canvas] = []
            confpane_info.persists[canvas].append(datum)
        return confpane_info.persist_vals[key]

    def get_datum(self, canvas, name: str, datum: str, val_get_cb: Optional[Callable],
                 default: Any = "") -> Any:
        """Get datum value from selected objects or tool."""
        # This would integrate with the CAD object system
        # For now, return default or persistent value
        if datum in confpane_info.persists.get(canvas, []):
            return self.get_persistent(canvas, datum, default)
        return default

    def set_datum(self, canvas, name: str, datum: str, val_set_cb: Optional[Callable], value: Any):
        """Set datum value on selected objects or tool."""
        # Store persistent value
        key = f"{canvas}-{datum}"
        confpane_info.persist_vals[key] = value

        # Emit signal for integration with CAD system
        self.field_changed.emit(name, datum, value)

    def invoke_exec(self, canvas, do_invoke: bool, dummy=None):
        """Execute current tool operation."""
        if do_invoke:
            exec_key = f"EXECBTN-{canvas}"
            if exec_key in confpane_info.exec_buttons:
                button = confpane_info.exec_buttons[exec_key]
                QTimer.singleShot(10, button.click)

    def execute(self, canvas, name: str):
        """Execute tool operation."""
        self.execute_requested.emit(name)

    def populate_font_menu(self, menu, command: Callable, variable: str):
        """Populate font family menu."""
        # This would be implemented based on the menu system used
        pass

    def focus_field(self, field_name: str):
        """Focus on specific field."""
        confpane_info.focus_field = field_name

    def populate(self):
        """Schedule population of configuration pane."""
        if confpane_info.populate_timer_id is None:
            confpane_info.populate_timer_id = QTimer.singleShot(50, self.populate_really)
            confpane_info.focus_field = ""

    def populate_really(self):
        """Actually populate the configuration pane with current field data."""
        confpane_info.populate_timer_id = None
        confpane_info.no_validate = True

        try:
            # Clear existing widgets
            self._clear_widgets()

            # Get field definitions
            fields = self._get_current_fields()

            # Create widgets for fields
            self._create_field_widgets(fields)

        finally:
            confpane_info.no_validate = False

    def _clear_widgets(self):
        """Clear all existing widgets."""
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.field_widgets.clear()

    def _get_current_fields(self) -> List[Dict[str, Any]]:
        """Get current field definitions based on selected objects/tool."""
        # This would integrate with the CAD object/tool system
        # Return common fields for now
        common_fields = [
            {
                'pane': 'STROKE',
                'type': 'COLOR',
                'name': 'LINECOLOR',
                'title': 'Stroke Color',
                'default': 'black',
                'persist': True
            },
            {
                'pane': 'STROKE',
                'type': 'COLOR',
                'name': 'FILLCOLOR',
                'title': 'Fill Color',
                'default': 'none',
                'persist': True
            },
            {
                'pane': 'STROKE',
                'type': 'FLOAT',
                'name': 'LINEWIDTH',
                'title': 'Stroke Width',
                'fmt': '%.4f',
                'width': 8,
                'min': 0.0,
                'max': 10.0,
                'increment': 0.001,
                'default': 0.0050,
                'persist': True,
                'islength': True
            }
        ]
        return common_fields

    def _create_field_widgets(self, fields: List[Dict[str, Any]]):
        """Create widgets for field definitions."""
        row = 0

        for field in fields:
            field_type = field.get('type', '')
            name = field.get('name', '')
            title = field.get('title', name)

            if field_type == 'COLOR':
                self._create_color_field(row, field)
            elif field_type == 'FLOAT':
                self._create_float_field(row, field)
            elif field_type == 'INT':
                self._create_int_field(row, field)
            elif field_type == 'STRING':
                self._create_string_field(row, field)
            elif field_type == 'BOOLEAN':
                self._create_boolean_field(row, field)
            elif field_type == 'OPTIONS':
                self._create_options_field(row, field)
            elif field_type == 'FONT':
                self._create_font_field(row, field)
            elif field_type == 'BUTTON':
                self._create_button_field(row, field)

            row += 1

    def _create_color_field(self, row: int, field: Dict[str, Any]):
        """Create color selection field."""
        name = field['name']
        title = field['title']
        default = field.get('default', 'black')

        label = QLabel(title)
        button = QPushButton()
        button.setFixedSize(60, 25)

        # Set initial color
        if default == 'none':
            button.setStyleSheet("background-color: white; color: black;")
            button.setText("None")
        else:
            button.setStyleSheet(f"background-color: {default}; color: {default};")
            button.setText("")

        button.clicked.connect(
            lambda: self.edit_color(self.canvas, name, name, None, button)
        )

        # Add clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(
            lambda: self.clear_color(self.canvas, name, name, None, button)
        )

        # Layout
        widget = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(button)
        layout.addWidget(clear_btn)
        layout.addStretch()
        widget.setLayout(layout)

        self.layout.addWidget(widget)
        self.field_widgets[name] = button

    def _create_float_field(self, row: int, field: Dict[str, Any]):
        """Create float input field."""
        name = field['name']
        title = field['title']
        min_val = field.get('min', 0.0)
        max_val = field.get('max', 100.0)
        increment = field.get('increment', 0.1)
        default = field.get('default', 0.0)

        label = QLabel(title)
        spinbox = QDoubleSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setSingleStep(increment)
        spinbox.setValue(default)
        spinbox.setDecimals(4)

        spinbox.valueChanged.connect(
            lambda val: self.set_datum(self.canvas, name, name, None, val)
        )

        # Layout
        widget = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(spinbox)
        layout.addStretch()
        widget.setLayout(layout)

        self.layout.addWidget(widget)
        self.field_widgets[name] = spinbox

    def _create_int_field(self, row: int, field: Dict[str, Any]):
        """Create integer input field."""
        name = field['name']
        title = field['title']
        min_val = field.get('min', 0)
        max_val = field.get('max', 100)
        default = field.get('default', 0)

        label = QLabel(title)
        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(default)

        spinbox.valueChanged.connect(
            lambda val: self.set_datum(self.canvas, name, name, None, val)
        )

        # Layout
        widget = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(spinbox)
        layout.addStretch()
        widget.setLayout(layout)

        self.layout.addWidget(widget)
        self.field_widgets[name] = spinbox

    def _create_string_field(self, row: int, field: Dict[str, Any]):
        """Create string input field."""
        name = field['name']
        title = field['title']
        default = field.get('default', '')

        label = QLabel(title)
        lineedit = QLineEdit()
        lineedit.setText(default)

        lineedit.textChanged.connect(
            lambda text: self.set_datum(self.canvas, name, name, None, text)
        )

        # Layout
        widget = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(lineedit)
        layout.addStretch()
        widget.setLayout(layout)

        self.layout.addWidget(widget)
        self.field_widgets[name] = lineedit

    def _create_boolean_field(self, row: int, field: Dict[str, Any]):
        """Create boolean checkbox field."""
        name = field['name']
        title = field['title']
        default = field.get('default', False)

        checkbox = QCheckBox(title)
        checkbox.setChecked(default)

        checkbox.toggled.connect(
            lambda checked: self.set_datum(self.canvas, name, name, None, checked)
        )

        self.layout.addWidget(checkbox)
        self.field_widgets[name] = checkbox

    def _create_options_field(self, row: int, field: Dict[str, Any]):
        """Create options combobox field."""
        name = field['name']
        title = field['title']
        values = field.get('values', [])
        default = field.get('default', '')

        label = QLabel(title)
        combobox = QComboBox()

        # Add options (values list alternates between display text and value)
        for i in range(0, len(values), 2):
            if i + 1 < len(values):
                display_text = values[i]
                value = values[i + 1]
                combobox.addItem(display_text, value)

        # Set default
        if default:
            index = combobox.findData(default)
            if index >= 0:
                combobox.setCurrentIndex(index)

        combobox.currentTextChanged.connect(
            lambda text: self.set_datum(self.canvas, name, name, None,
                                       combobox.currentData())
        )

        # Layout
        widget = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(combobox)
        layout.addStretch()
        widget.setLayout(layout)

        self.layout.addWidget(widget)
        self.field_widgets[name] = combobox

    def _create_font_field(self, row: int, field: Dict[str, Any]):
        """Create font selection field."""
        name = field['name']
        title = field['title']

        label = QLabel(title)

        # Font family combo
        font_combo = QFontComboBox()
        confpane_info.font_combos[f"FONTMB-{self.canvas}-{name}"] = font_combo

        # Font size spin
        size_spin = QSpinBox()
        size_spin.setRange(6, 72)
        size_spin.setValue(12)
        confpane_info.size_spins[f"SIZESP-{self.canvas}-{name}"] = size_spin

        # Bold checkbox
        bold_check = QCheckBox("Bold")
        confpane_info.bold_checks[f"BOLDCB-{self.canvas}-{name}"] = bold_check

        # Italic checkbox
        italic_check = QCheckBox("Italic")
        confpane_info.italic_checks[f"ITALCB-{self.canvas}-{name}"] = italic_check

        # Connect signals
        font_combo.currentTextChanged.connect(
            lambda: self.set_font_datum(self.canvas, name, name, None, None)
        )
        size_spin.valueChanged.connect(
            lambda: self.set_font_datum(self.canvas, name, name, None, None)
        )
        bold_check.toggled.connect(
            lambda: self.set_font_datum(self.canvas, name, name, None, None)
        )
        italic_check.toggled.connect(
            lambda: self.set_font_datum(self.canvas, name, name, None, None)
        )

        # Layout
        widget = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(font_combo)
        layout.addWidget(size_spin)
        layout.addWidget(bold_check)
        layout.addWidget(italic_check)
        layout.addStretch()
        widget.setLayout(layout)

        self.layout.addWidget(widget)
        self.field_widgets[name] = font_combo

    def _create_button_field(self, row: int, field: Dict[str, Any]):
        """Create button field."""
        name = field['name']
        title = field['title']

        button = QPushButton(title)
        button.clicked.connect(lambda: self.execute(self.canvas, name))

        if field.get('type') == 'EXEC':
            confpane_info.exec_buttons[f"EXECBTN-{self.canvas}"] = button

        self.layout.addWidget(button)
        self.field_widgets[name] = button

    def _parse_length_value(self, value: str) -> float:
        """Parse length value with unit conversion."""
        # Simple implementation - would need to integrate with unit system
        try:
            return float(value)
        except ValueError:
            # Try to extract numeric part
            match = re.match(r'^([+-]?\d*\.?\d+)', value)
            if match:
                return float(match.group(1))
            raise ValueError(f"Cannot parse length value: {value}")


def create_config_pane(canvas=None, parent: Optional[QWidget] = None) -> ConfigPane:
    """
    Create and return a new configuration pane.

    Args:
        canvas: Canvas object reference
        parent: Parent widget for the new pane

    Returns:
        A new ConfigPane instance
    """
    return ConfigPane(canvas, parent)


if __name__ == "__main__":
    """Test the configuration pane independently."""
    import sys

    app = QApplication(sys.argv)

    # Create and show the configuration pane
    config_pane = create_config_pane()
    config_pane.show()

    # Test population
    config_pane.populate()

    sys.exit(app.exec())
