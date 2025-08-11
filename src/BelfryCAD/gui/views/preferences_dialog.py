"""
Preferences Dialog View for BelfryCAD.

This is a pure view that delegates all logic to the PreferencesViewModel,
following the MVVM design pattern.
"""

from typing import Dict, Any, Optional, Union
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QLineEdit, QPushButton, QCheckBox, QSpinBox,
    QDoubleSpinBox, QComboBox, QColorDialog, QFileDialog, QDialogButtonBox,
    QMessageBox, QApplication, QScrollArea, QGroupBox, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from ..viewmodels.preferences_viewmodel import PreferencesViewModel


class PreferenceControlWidget(QWidget):
    """Base class for preference control widgets."""

    valueChanged = Signal()

    def __init__(self, pref_key: str, pref_name: str, parent=None):
        super().__init__(parent)
        self.pref_key = pref_key
        self.pref_name = pref_name
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


class BoolPreferenceControl(PreferenceControlWidget):
    """Checkbox for boolean preferences."""

    def _create_widget(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.checkbox = QCheckBox(self.pref_name)
        self.checkbox.stateChanged.connect(self.valueChanged.emit)

        layout.addWidget(self.checkbox)
        layout.addStretch()

    def get_value(self) -> bool:
        return self.checkbox.isChecked()

    def set_value(self, value: bool):
        self.checkbox.setChecked(bool(value))


class IntPreferenceControl(PreferenceControlWidget):
    """Spinbox for integer preferences."""

    def __init__(self, pref_key: str, pref_name: str, minimum=0, maximum=10000, parent=None):
        self.minimum = minimum
        self.maximum = maximum
        super().__init__(pref_key, pref_name, parent)

    def _create_widget(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(self.pref_name + ":")
        label.setMinimumWidth(150)
        layout.addWidget(label)

        self.spinbox = QSpinBox()
        self.spinbox.setMinimum(self.minimum)
        self.spinbox.setMaximum(self.maximum)
        self.spinbox.valueChanged.connect(self.valueChanged.emit)

        layout.addWidget(self.spinbox)
        layout.addStretch()

    def get_value(self) -> int:
        return self.spinbox.value()

    def set_value(self, value: int):
        self.spinbox.setValue(int(value))


class StringPreferenceControl(PreferenceControlWidget):
    """Line edit for string preferences."""

    def _create_widget(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(self.pref_name + ":")
        label.setMinimumWidth(150)
        layout.addWidget(label)

        self.lineedit = QLineEdit()
        self.lineedit.textChanged.connect(self.valueChanged.emit)

        layout.addWidget(self.lineedit)

    def get_value(self) -> str:
        return self.lineedit.text()

    def set_value(self, value: str):
        self.lineedit.setText(str(value))


class ComboPreferenceControl(PreferenceControlWidget):
    """Combobox for choice preferences."""

    def __init__(self, pref_key: str, pref_name: str, choices=None, parent=None):
        self.choices = choices or []
        super().__init__(pref_key, pref_name, parent)

    def _create_widget(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(self.pref_name + ":")
        label.setMinimumWidth(150)
        layout.addWidget(label)

        self.combobox = QComboBox()
        self.combobox.addItems(self.choices)
        self.combobox.currentTextChanged.connect(self.valueChanged.emit)

        layout.addWidget(self.combobox)
        layout.addStretch()

    def get_value(self) -> str:
        return self.combobox.currentText()

    def set_value(self, value: str):
        index = self.combobox.findText(str(value))
        if index >= 0:
            self.combobox.setCurrentIndex(index)


class ColorPreferenceControl(PreferenceControlWidget):
    """Color picker for color preferences."""

    def _create_widget(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(self.pref_name + ":")
        label.setMinimumWidth(150)
        layout.addWidget(label)

        self.color_button = QPushButton()
        self.color_button.setFixedSize(80, 30)
        self.color_button.clicked.connect(self._pick_color)

        layout.addWidget(self.color_button)
        layout.addStretch()

        self._current_color = "#ffffff"

    def _pick_color(self):
        """Open color picker dialog."""
        color = QColorDialog.getColor(QColor(self._current_color), self)
        if color.isValid():
            self._current_color = color.name()
            self._update_button_color()
            self.valueChanged.emit()

    def _update_button_color(self):
        """Update button background color."""
        self.color_button.setStyleSheet(f"background-color: {self._current_color}")

    def get_value(self) -> str:
        return self._current_color

    def set_value(self, value: str):
        self._current_color = str(value)
        self._update_button_color()


class RecentFilesPreferenceControl(PreferenceControlWidget):
    """Recent files preference control widget."""

    def _create_widget(self):
        """Create the recent files widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Label
        self.label = QLabel(self.pref_name + ":")
        layout.addWidget(self.label)

        # List widget for recent files
        self.list_widget = QListWidget()
        self.list_widget.setMaximumHeight(150)
        layout.addWidget(self.list_widget)

        # Buttons layout
        button_layout = QHBoxLayout()
        
        # Clear button
        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self._clear_recent_files)
        button_layout.addWidget(self.clear_button)
        
        # Remove selected button
        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self._remove_selected)
        button_layout.addWidget(self.remove_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Initialize internal state
        self._recent_files = []
        self._update_list()

    def _update_list(self):
        """Update the recent files list."""
        self.list_widget.clear()
        
        # Filter out non-existent files
        valid_files = []
        for file_path in self._recent_files:
            if file_path and len(file_path) > 0:
                # Check if file exists
                if Path(file_path).exists():
                    valid_files.append(file_path)
                # If file doesn't exist, it's automatically removed from the list
        
        # Update internal list if any files were removed
        if len(valid_files) != len(self._recent_files):
            self._recent_files = valid_files
            self.valueChanged.emit()
        
        # Display valid files
        for file_path in valid_files:
            # Show just the filename, not the full path
            filename = file_path.split('/')[-1] if '/' in file_path else file_path
            filename = filename.split('\\')[-1] if '\\' in filename else filename
            
            item = QListWidgetItem(f"{filename}")
            item.setToolTip(file_path)  # Show full path in tooltip
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            self.list_widget.addItem(item)

    def _clear_recent_files(self):
        """Clear all recent files."""
        self._recent_files = []
        self._update_list()
        self.valueChanged.emit()

    def _remove_selected(self):
        """Remove selected files from recent files list."""
        selected_items = self.list_widget.selectedItems()
        
        for item in selected_items:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path in self._recent_files:
                self._recent_files.remove(file_path)
        
        self._update_list()
        self.valueChanged.emit()

    def get_value(self) -> list:
        """Get the current recent files list."""
        return self._recent_files.copy()

    def set_value(self, value: list):
        """Set the recent files list."""
        self._recent_files = value.copy() if value else []
        self._update_list()


class PreferencesDialog(QDialog):
    """
    Pure View preferences dialog that delegates to PreferencesViewModel.
    
    This dialog contains only UI logic and delegates all business logic
    to the ViewModel.
    """

    def __init__(self, preferences_viewmodel: PreferencesViewModel, parent=None):
        super().__init__(parent)
        self.viewmodel = preferences_viewmodel
        self.controls: Dict[str, PreferenceControlWidget] = {}
        
        self._setup_ui()
        self._connect_viewmodel_signals()
        self._load_preferences()

    def _setup_ui(self):
        """Set up the UI components."""
        self.setWindowTitle("Preferences")
        self.setModal(True)
        self.resize(600, 500)

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
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.RestoreDefaults
        )
        
        # Connect button signals
        self.button_box.accepted.connect(self._ok_clicked)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._apply_clicked)
        self.button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self._reset_clicked)
        
        # Disable Apply initially
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).setEnabled(False)

        layout.addWidget(self.button_box)

    def _create_tabs(self):
        """Create preference tabs."""
        # Define preference controls for each category
        preference_controls = {
            'display': {
                'grid_visible': ('bool', 'Show Grid'),
                'show_rulers': ('bool', 'Show Rulers'),
                'canvas_bg_color': ('color', 'Background Color'),
                'grid_color': ('color', 'Grid Color'),
                'selection_color': ('color', 'Selection Color'),
            },
            'snap': {
                'snap_to_grid': ('bool', 'Snap to Grid'),
            },
            'file': {
                'auto_save': ('bool', 'Enable Auto-save'),
                'auto_save_interval': ('int', 'Auto-save Interval (seconds)', 30, 3600),
                'recent_files_count': ('int', 'Recent Files Count', 1, 50),
                'recent_files': ('recent_files', 'Recent Files'),
            },
            'units': {
                'units': ('combo', 'Default Units', ['inches', 'mm']),
                'precision': ('int', 'Decimal Precision', 0, 10),
            },
            'window': {
                'window_geometry': ('string', 'Window Geometry'),
            }
        }

        for category in self.viewmodel.get_categories():
            if category in preference_controls:
                self._create_tab(category, preference_controls[category])

    def _create_tab(self, category: str, controls_spec: Dict[str, tuple]):
        """Create a preferences tab."""
        # Create tab widget
        tab_widget = QWidget()
        self.tab_widget.addTab(tab_widget, category.title())

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Create content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # Create group box for category
        group_box = QGroupBox(self.viewmodel.get_category_description(category))
        group_layout = QVBoxLayout(group_box)

        # Create controls
        for pref_key, control_spec in controls_spec.items():
            control = self._create_control(pref_key, control_spec)
            if control:
                self.controls[pref_key] = control
                group_layout.addWidget(control)

        content_layout.addWidget(group_box)
        content_layout.addStretch()

        # Set up scroll area
        scroll_area.setWidget(content_widget)

        # Set up tab layout
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.addWidget(scroll_area)

    def _create_control(self, pref_key: str, control_spec: tuple) -> Optional[PreferenceControlWidget]:
        """Create a preference control widget."""
        control_type = control_spec[0]
        pref_name = control_spec[1]

        try:
            if control_type == 'bool':
                control = BoolPreferenceControl(pref_key, pref_name)
            elif control_type == 'int':
                minimum = control_spec[2] if len(control_spec) > 2 else 0
                maximum = control_spec[3] if len(control_spec) > 3 else 10000
                control = IntPreferenceControl(pref_key, pref_name, minimum, maximum)
            elif control_type == 'string':
                control = StringPreferenceControl(pref_key, pref_name)
            elif control_type == 'combo':
                choices = control_spec[2] if len(control_spec) > 2 else []
                control = ComboPreferenceControl(pref_key, pref_name, choices)
            elif control_type == 'color':
                control = ColorPreferenceControl(pref_key, pref_name)
            elif control_type == 'recent_files':
                control = RecentFilesPreferenceControl(pref_key, pref_name)
            else:
                return None

            # Connect change signal
            control.valueChanged.connect(self._on_control_changed)
            return control

        except Exception as e:
            print(f"Error creating control for {pref_key}: {e}")
            return None

    def _connect_viewmodel_signals(self):
        """Connect to ViewModel signals."""
        self.viewmodel.preference_changed.connect(self._on_preference_changed)
        self.viewmodel.preferences_saved.connect(self._on_preferences_saved)
        self.viewmodel.preferences_reset.connect(self._on_preferences_reset)

    def _load_preferences(self):
        """Load preferences from ViewModel into controls."""
        for pref_key, control in self.controls.items():
            value = self.viewmodel.get(pref_key)
            if value is not None:
                control.set_value(value)

    def _on_control_changed(self):
        """Handle control value changes."""
        # Enable Apply button
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).setEnabled(True)

    def _on_preference_changed(self, key: str, value):
        """Handle preference changes from ViewModel."""
        if key in self.controls:
            # Update control if value changed externally
            control = self.controls[key]
            if control.get_value() != value:
                control.set_value(value)

    def _on_preferences_saved(self):
        """Handle preferences saved signal."""
        # Disable Apply button
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).setEnabled(False)

    def _on_preferences_reset(self):
        """Handle preferences reset signal."""
        self._load_preferences()

    def _collect_values(self) -> Dict[str, Any]:
        """Collect values from all controls."""
        values = {}
        for pref_key, control in self.controls.items():
            values[pref_key] = control.get_value()
        return values

    def _apply_changes(self) -> bool:
        """Apply changes to ViewModel."""
        try:
            values = self._collect_values()
            self.viewmodel.set_multiple(values)
            return self.viewmodel.save_preferences()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save preferences:\n{str(e)}"
            )
            return False

    def _ok_clicked(self):
        """Handle OK button click."""
        if self._apply_changes():
            self.accept()

    def _apply_clicked(self):
        """Handle Apply button click."""
        self._apply_changes()

    def _reset_clicked(self):
        """Handle Reset button click."""
        reply = QMessageBox.question(
            self,
            "Reset Preferences",
            "Are you sure you want to reset all preferences to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.viewmodel.reset_all_to_defaults()

    @classmethod
    def show_preferences(cls, preferences_viewmodel: PreferencesViewModel, parent=None):
        """Convenience method to show preferences dialog."""
        dialog = cls(preferences_viewmodel, parent)
        return dialog.exec() 