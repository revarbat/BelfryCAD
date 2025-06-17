"""
Qt-based Preferences Dialog for PyTkCAD.

This module provides a PySide6/Qt GUI dialog for managing application
preferences, compatible with the main Qt-based application framework.
"""

from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QLineEdit, QPushButton, QCheckBox, QSpinBox,
    QDoubleSpinBox, QComboBox, QColorDialog, QFileDialog, QDialogButtonBox,
    QMessageBox, QApplication, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor


try:
    from ..core.preferences import PreferencesManager
    from ..config import AppConfig
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from core.preferences import PreferencesManager
    from config import AppConfig


class ColorButton(QPushButton):
    """Custom button for color selection."""

    colorChanged = Signal(str)

    def __init__(self, color="#ffffff", parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(50, 30)
        self.clicked.connect(self._choose_color)
        self._update_color()

    def _update_color(self):
        """Update button appearance to show current color."""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color};
                border: 2px solid #888;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border: 2px solid #555;
            }}
        """)

    def _choose_color(self):
        """Open color dialog to choose new color."""
        color = QColorDialog.getColor(
            QColor(self._color), self, "Choose Color"
        )
        if color.isValid():
            self.set_color(color.name())

    def set_color(self, color: str):
        """Set the current color."""
        self._color = color
        self._update_color()
        self.colorChanged.emit(color)

    def get_color(self) -> str:
        """Get the current color."""
        return self._color


class PreferenceWidget(QWidget):
    """Base class for preference widgets."""

    valueChanged = Signal()

    def __init__(self, pref_name: str, pref_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.pref_name = pref_name
        self.pref_data = pref_data
        self._create_widget()

    def _create_widget(self):
        """Create the widget. Must be implemented by subclasses."""
        raise NotImplementedError

    def get_value(self):
        """Get the current value from the widget."""
        raise NotImplementedError

    def set_value(self, value):
        """Set the value in the widget."""
        raise NotImplementedError


class BoolPreferenceWidget(PreferenceWidget):
    """Checkbox widget for boolean preferences."""

    def _create_widget(self):
        layout = QHBoxLayout(self)

        self.checkbox = QCheckBox(self.pref_data.get('desc', self.pref_name))
        self.checkbox.stateChanged.connect(self.valueChanged.emit)

        layout.addWidget(self.checkbox)
        layout.addStretch()

    def get_value(self) -> bool:
        return self.checkbox.isChecked()

    def set_value(self, value: bool):
        self.checkbox.setChecked(bool(value))


class IntPreferenceWidget(PreferenceWidget):
    """Spinbox widget for integer preferences."""

    def _create_widget(self):
        layout = QHBoxLayout(self)

        label = QLabel(self.pref_data.get('desc', self.pref_name) + ":")
        layout.addWidget(label)

        self.spinbox = QSpinBox()
        self.spinbox.setMinimum(self.pref_data.get('min', 0))
        self.spinbox.setMaximum(self.pref_data.get('max', 1000))
        self.spinbox.valueChanged.connect(self.valueChanged.emit)

        layout.addWidget(self.spinbox)
        layout.addStretch()

    def get_value(self) -> int:
        return self.spinbox.value()

    def set_value(self, value: int):
        self.spinbox.setValue(int(value))


class FloatPreferenceWidget(PreferenceWidget):
    """Double spinbox widget for float preferences."""

    def _create_widget(self):
        layout = QHBoxLayout(self)

        label = QLabel(self.pref_data.get('desc', self.pref_name) + ":")
        layout.addWidget(label)

        self.spinbox = QDoubleSpinBox()
        self.spinbox.setMinimum(self.pref_data.get('min', 0.0))
        self.spinbox.setMaximum(self.pref_data.get('max', 1000.0))
        self.spinbox.setDecimals(self.pref_data.get('decimals', 2))
        self.spinbox.valueChanged.connect(self.valueChanged.emit)

        layout.addWidget(self.spinbox)
        layout.addStretch()

    def get_value(self) -> float:
        return self.spinbox.value()

    def set_value(self, value: float):
        self.spinbox.setValue(float(value))


class StringPreferenceWidget(PreferenceWidget):
    """Line edit widget for string preferences."""

    def _create_widget(self):
        layout = QHBoxLayout(self)

        label = QLabel(self.pref_data.get('desc', self.pref_name) + ":")
        layout.addWidget(label)

        self.lineedit = QLineEdit()
        self.lineedit.textChanged.connect(self.valueChanged.emit)

        layout.addWidget(self.lineedit)

    def get_value(self) -> str:
        return self.lineedit.text()

    def set_value(self, value: str):
        self.lineedit.setText(str(value))


class ComboPreferenceWidget(PreferenceWidget):
    """Combobox widget for choice preferences."""

    def _create_widget(self):
        layout = QHBoxLayout(self)

        label = QLabel(self.pref_data.get('desc', self.pref_name) + ":")
        layout.addWidget(label)

        self.combobox = QComboBox()
        values = self.pref_data.get('values', [])
        self.combobox.addItems(values)
        self.combobox.currentTextChanged.connect(self.valueChanged.emit)

        layout.addWidget(self.combobox)
        layout.addStretch()

    def get_value(self) -> str:
        return self.combobox.currentText()

    def set_value(self, value: str):
        index = self.combobox.findText(str(value))
        if index >= 0:
            self.combobox.setCurrentIndex(index)


class ColorPreferenceWidget(PreferenceWidget):
    """Color picker widget for color preferences."""

    def _create_widget(self):
        layout = QHBoxLayout(self)

        label = QLabel(self.pref_data.get('desc', self.pref_name) + ":")
        layout.addWidget(label)

        self.color_button = ColorButton()
        self.color_button.colorChanged.connect(self.valueChanged.emit)

        layout.addWidget(self.color_button)
        layout.addStretch()

    def get_value(self) -> str:
        return self.color_button.get_color()

    def set_value(self, value: str):
        self.color_button.set_color(str(value))


class FilePreferenceWidget(PreferenceWidget):
    """File/directory picker widget for file preferences."""

    def _create_widget(self):
        layout = QHBoxLayout(self)

        label = QLabel(self.pref_data.get('desc', self.pref_name) + ":")
        layout.addWidget(label)

        self.lineedit = QLineEdit()
        self.lineedit.textChanged.connect(self.valueChanged.emit)

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse)

        layout.addWidget(self.lineedit)
        layout.addWidget(browse_button)

    def _browse(self):
        """Open file/directory dialog."""
        if self.pref_data.get('type') == 'directory':
            path = QFileDialog.getExistingDirectory(
                self, "Select Directory", self.lineedit.text()
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, "Select File", self.lineedit.text()
            )

        if path:
            self.lineedit.setText(path)

    def get_value(self) -> str:
        return self.lineedit.text()

    def set_value(self, value: str):
        self.lineedit.setText(str(value))


class PreferencesDialog(QDialog):
    """Main preferences dialog window."""

    # Preference definitions matching AppConfig.default_prefs
    PREFERENCE_DEFINITIONS = {
        'General': {
            'antialiasing': {
                'type': 'bool',
                'desc': 'Enable antialiasing',
                'default': True
            },
            'auto_save': {
                'type': 'bool',
                'desc': 'Enable auto-save',
                'default': True
            },
            'auto_save_interval': {
                'type': 'int',
                'desc': 'Auto-save interval (seconds)',
                'min': 30,
                'max': 3600,
                'default': 300
            },
            'recent_files_count': {
                'type': 'int',
                'desc': 'Number of recent files to remember',
                'min': 1,
                'max': 20,
                'default': 10
            },
            'precision': {
                'type': 'int',
                'desc': 'Decimal precision',
                'min': 0,
                'max': 10,
                'default': 3
            }
        },
        'Display': {
            'grid_visible': {
                'type': 'bool',
                'desc': 'Show grid',
                'default': True
            },
            'snap_to_grid': {
                'type': 'bool',
                'desc': 'Snap to grid',
                'default': True
            },
            'show_rulers': {
                'type': 'bool',
                'desc': 'Show rulers',
                'default': True
            },
            'canvas_bg_color': {
                'type': 'color',
                'desc': 'Canvas background color',
                'default': '#ffffff'
            },
            'grid_color': {
                'type': 'color',
                'desc': 'Grid color',
                'default': '#cccccc'
            },
            'selection_color': {
                'type': 'color',
                'desc': 'Selection color',
                'default': '#0080ff'
            }
        },
        'Units': {
            'units': {
                'type': 'combo',
                'desc': 'Default units',
                'values': ['inches', 'mm'],
                'default': 'inches'
            }
        }
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        # Get preferences manager
        try:
            # Try to get config from parent if it has one
            if parent and hasattr(parent, 'config'):
                config = parent.config
            else:
                config = AppConfig()
        except Exception:
            config = AppConfig()

        self.prefs_manager = PreferencesManager(config)
        self.widgets = {}
        self.original_values = {}
        self.has_changes = False

        self._setup_ui()
        self._load_preferences()

    def _setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Preferences")
        self.setMinimumSize(600, 500)
        self.resize(700, 600)

        # Make dialog modal
        self.setModal(True)

        # Main layout
        layout = QVBoxLayout(self)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs
        self._create_tabs()

        # Create button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        self.button_box.accepted.connect(self._ok_clicked)
        self.button_box.rejected.connect(self._cancel_clicked)
        apply_btn = self.button_box.button(
            QDialogButtonBox.StandardButton.Apply)
        apply_btn.clicked.connect(self._apply_clicked)

        # Initially disable Apply button
        self.button_box.button(
            QDialogButtonBox.StandardButton.Apply).setEnabled(False)

        layout.addWidget(self.button_box)

        # Center dialog on parent or screen
        if self.parent():
            # Center on parent
            parent_geom = self.parent().geometry()
            x = parent_geom.x() + (parent_geom.width() - self.width()) // 2
            y = parent_geom.y() + (parent_geom.height() - self.height()) // 2
            self.move(x, y)

    def _create_tabs(self):
        """Create preference tabs."""
        for tab_name, prefs in self.PREFERENCE_DEFINITIONS.items():
            # Create tab widget
            tab_widget = QWidget()
            self.tab_widget.addTab(tab_widget, tab_name)

            # Create scroll area for the tab
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll_area.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded)

            # Create content widget
            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

            # Create preference widgets
            self._create_preference_widgets(content_widget, tab_name, prefs)

            # Set up scroll area
            scroll_area.setWidget(content_widget)

            # Set up tab layout
            tab_layout = QVBoxLayout(tab_widget)
            tab_layout.addWidget(scroll_area)

    def _create_preference_widgets(self, parent: QWidget, tab_name: str,
                                   prefs: Dict[str, Any]):
        """Create widgets for preferences in a tab."""
        if tab_name not in self.widgets:
            self.widgets[tab_name] = {}

        layout = parent.layout()
        if layout is None:
            layout = QVBoxLayout(parent)

        for pref_name, pref_data in prefs.items():
            # Create widget based on type
            widget_type = pref_data.get('type', 'str')

            if widget_type == 'bool':
                widget = BoolPreferenceWidget(pref_name, pref_data)
            elif widget_type == 'int':
                widget = IntPreferenceWidget(pref_name, pref_data)
            elif widget_type == 'float':
                widget = FloatPreferenceWidget(pref_name, pref_data)
            elif widget_type == 'combo':
                widget = ComboPreferenceWidget(pref_name, pref_data)
            elif widget_type in ('file', 'directory'):
                widget = FilePreferenceWidget(pref_name, pref_data)
            elif widget_type == 'color':
                widget = ColorPreferenceWidget(pref_name, pref_data)
            else:
                widget = StringPreferenceWidget(pref_name, pref_data)

            # Connect change signal
            widget.valueChanged.connect(self._on_value_changed)

            # Add to layout
            layout.addWidget(widget)

            # Store widget reference
            self.widgets[tab_name][pref_name] = widget

    def _on_value_changed(self):
        """Handle value changes in preference widgets."""
        self.has_changes = True
        self.button_box.button(
            QDialogButtonBox.StandardButton.Apply).setEnabled(True)

    def _load_preferences(self):
        """Load current preferences into widgets."""
        # Load preferences from file
        self.prefs_manager.load()

        for tab_name, tab_widgets in self.widgets.items():
            for pref_name, widget in tab_widgets.items():
                # Get current value or default
                pref_def = self.PREFERENCE_DEFINITIONS[tab_name][pref_name]
                value = self.prefs_manager.get(
                    pref_name, pref_def.get('default')
                )

                # Store original value
                self.original_values[pref_name] = value

                # Set widget value
                widget.set_value(value)

    def _apply_changes(self) -> bool:
        """Apply preference changes."""
        try:
            # Collect all values from widgets
            for tab_name, tab_widgets in self.widgets.items():
                for pref_name, widget in tab_widgets.items():
                    new_value = widget.get_value()
                    self.prefs_manager.set(pref_name, new_value)

            # Save preferences to file
            self.prefs_manager.save()

            # Update original values
            for tab_name, tab_widgets in self.widgets.items():
                for pref_name, widget in tab_widgets.items():
                    self.original_values[pref_name] = widget.get_value()

            # Disable Apply button
            self.has_changes = False
            self.button_box.button(
                QDialogButtonBox.StandardButton.Apply).setEnabled(False)

            return True

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save preferences:\n{str(e)}"
            )
            return False

    def _ok_clicked(self):
        """Handle OK button click."""
        if self.has_changes:
            if self._apply_changes():
                self.accept()
        else:
            self.accept()

    def _cancel_clicked(self):
        """Handle Cancel button click."""
        if self.has_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save them?",
                (QMessageBox.StandardButton.Yes |
                 QMessageBox.StandardButton.No |
                 QMessageBox.StandardButton.Cancel)
            )

            if reply == QMessageBox.StandardButton.Yes:
                if self._apply_changes():
                    self.reject()
            elif reply == QMessageBox.StandardButton.No:
                self.reject()
            # Cancel - do nothing, stay open
        else:
            self.reject()

    def _apply_clicked(self):
        """Handle Apply button click."""
        self._apply_changes()


def show_preferences_dialog(parent=None) -> Optional[PreferencesDialog]:
    """Convenience function to show preferences dialog."""
    dialog = PreferencesDialog(parent)
    dialog.exec()
    return dialog


# Test/demo code
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # Test the preferences dialog
    dialog = PreferencesDialog()
    result = dialog.exec()

    print(f"Dialog result: {result}")
    if result == QDialog.DialogCode.Accepted:
        print("Preferences were saved")
    else:
        print("Preferences were cancelled")

    sys.exit()
