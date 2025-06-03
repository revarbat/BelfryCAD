"""
Preferences Dialog for PyTkCAD.

This module provides a GUI dialog for managing application preferences,
translating the functionality from the original prefs.tcl file.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
from typing import Dict, Any
import os
import platform

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


class PreferenceWidget:
    """Base class for preference widgets."""

    def __init__(self, parent, pref_name: str, pref_data: Dict[str, Any]):
        self.parent = parent
        self.pref_name = pref_name
        self.pref_data = pref_data
        self.widget = None
        self.var = None

    def create_widget(self):
        """Create the widget. Must be implemented by subclasses."""
        raise NotImplementedError

    def get_value(self):
        """Get the current value from the widget."""
        raise NotImplementedError

    def set_value(self, value):
        """Set the value in the widget."""
        raise NotImplementedError


class BoolWidget(PreferenceWidget):
    """Checkbox widget for boolean preferences."""

    def create_widget(self):
        self.var = tk.BooleanVar()
        self.widget = ttk.Checkbutton(
            self.parent,
            text=self.pref_data.get('desc', self.pref_name),
            variable=self.var
        )
        return self.widget

    def get_value(self):
        return self.var.get()

    def set_value(self, value):
        self.var.set(bool(value))


class IntWidget(PreferenceWidget):
    """Spinbox widget for integer preferences."""

    def create_widget(self):
        frame = ttk.Frame(self.parent)

        label_text = self.pref_data.get('desc', self.pref_name)
        ttk.Label(frame, text=label_text).pack(side=tk.LEFT)

        self.var = tk.IntVar()
        self.widget = ttk.Spinbox(
            frame,
            from_=self.pref_data.get('min', 0),
            to=self.pref_data.get('max', 100),
            textvariable=self.var,
            width=10
        )
        self.widget.pack(side=tk.RIGHT)

        return frame

    def get_value(self):
        return self.var.get()

    def set_value(self, value):
        self.var.set(int(value))


class FloatWidget(PreferenceWidget):
    """Entry widget for float preferences."""

    def create_widget(self):
        frame = ttk.Frame(self.parent)

        label_text = self.pref_data.get('desc', self.pref_name)
        ttk.Label(frame, text=label_text).pack(side=tk.LEFT)

        self.var = tk.DoubleVar()
        self.widget = ttk.Entry(frame, textvariable=self.var, width=10)
        self.widget.pack(side=tk.RIGHT)

        return frame

    def get_value(self):
        return self.var.get()

    def set_value(self, value):
        self.var.set(float(value))


class StringWidget(PreferenceWidget):
    """Entry widget for string preferences."""

    def create_widget(self):
        frame = ttk.Frame(self.parent)

        label_text = self.pref_data.get('desc', self.pref_name)
        ttk.Label(frame, text=label_text).pack(side=tk.LEFT)

        self.var = tk.StringVar()
        self.widget = ttk.Entry(frame, textvariable=self.var, width=30)
        self.widget.pack(side=tk.RIGHT)

        return frame

    def get_value(self):
        return self.var.get()

    def set_value(self, value):
        self.var.set(str(value))


class ComboWidget(PreferenceWidget):
    """Combobox widget for choice preferences."""

    def create_widget(self):
        frame = ttk.Frame(self.parent)

        label_text = self.pref_data.get('desc', self.pref_name)
        ttk.Label(frame, text=label_text).pack(side=tk.LEFT)

        self.var = tk.StringVar()
        values = self.pref_data.get('values', [])
        self.widget = ttk.Combobox(
            frame,
            textvariable=self.var,
            values=values,
            state='readonly',
            width=20
        )
        self.widget.pack(side=tk.RIGHT)

        return frame

    def get_value(self):
        return self.var.get()

    def set_value(self, value):
        self.var.set(str(value))


class FileWidget(PreferenceWidget):
    """File/directory chooser widget."""

    def create_widget(self):
        frame = ttk.Frame(self.parent)

        label_text = self.pref_data.get('desc', self.pref_name)
        ttk.Label(frame, text=label_text).pack(side=tk.LEFT)

        self.var = tk.StringVar()
        self.widget = ttk.Entry(frame, textvariable=self.var, width=25)
        self.widget.pack(side=tk.LEFT, padx=(5, 0))

        button = ttk.Button(frame, text="Browse...", command=self._browse)
        button.pack(side=tk.RIGHT)

        return frame

    def _browse(self):
        if self.pref_data.get('type') == 'directory':
            path = filedialog.askdirectory(initialdir=self.var.get())
        else:
            default_filetypes = [('All Files', '*.*')]
            filetypes = self.pref_data.get('filetypes', default_filetypes)
            path = filedialog.askopenfilename(
                initialdir=os.path.dirname(self.var.get() or ''),
                filetypes=filetypes
            )
        if path:
            self.var.set(path)

    def get_value(self):
        return self.var.get()

    def set_value(self, value):
        self.var.set(str(value))


class ColorWidget(PreferenceWidget):
    """Color chooser widget."""

    def create_widget(self):
        frame = ttk.Frame(self.parent)

        label_text = self.pref_data.get('desc', self.pref_name)
        ttk.Label(frame, text=label_text).pack(side=tk.LEFT)

        self.var = tk.StringVar()
        self.widget = ttk.Entry(frame, textvariable=self.var, width=10)
        self.widget.pack(side=tk.LEFT, padx=(5, 0))

        self.color_button = tk.Button(frame, width=3,
                                      command=self._choose_color)
        self.color_button.pack(side=tk.RIGHT)

        return frame

    def _choose_color(self):
        color = colorchooser.askcolor(color=self.var.get())[1]
        if color:
            self.var.set(color)
            self.color_button.configure(bg=color)

    def get_value(self):
        return self.var.get()

    def set_value(self, value):
        self.var.set(str(value))
        try:
            self.color_button.configure(bg=value)
        except tk.TclError:
            pass


class PreferencesDialog:
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
        self.parent = parent
        try:
            # Try to get config from parent if it has one
            if hasattr(parent, 'config'):
                config = parent.config
            else:
                config = AppConfig()
        except Exception:
            config = AppConfig()
        
        self.prefs_manager = PreferencesManager(config)
        self.dialog = None
        self.notebook = None
        self.widgets = {}
        self.original_values = {}
        self.has_changes = False

    def show(self):
        """Show the preferences dialog."""
        if self.dialog:
            self.dialog.lift()
            return

        self._create_dialog()
        self._load_preferences()

    def _create_dialog(self):
        """Create the main dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Preferences")
        self.dialog.geometry("600x500")
        self.dialog.resizable(True, True)

        # Make dialog modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"600x500+{x}+{y}")

        # Create main frame
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create tabs
        self._create_tabs()

        # Create button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        # Create buttons
        self.ok_button = ttk.Button(
            button_frame,
            text="OK",
            command=self._ok_clicked,
            width=10
        )
        self.ok_button.pack(side=tk.RIGHT, padx=(5, 0))

        self.cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel_clicked,
            width=10
        )
        self.cancel_button.pack(side=tk.RIGHT)

        self.apply_button = ttk.Button(
            button_frame,
            text="Apply",
            command=self._apply_clicked,
            width=10,
            state=tk.DISABLED
        )
        self.apply_button.pack(side=tk.RIGHT, padx=(0, 5))

        # Bind events
        self.dialog.bind('<Return>', lambda e: self._ok_clicked())
        self.dialog.bind('<Escape>', lambda e: self._cancel_clicked())
        self.dialog.protocol("WM_DELETE_WINDOW", self._cancel_clicked)

        # Focus on OK button
        self.ok_button.focus_set()

    def _create_tabs(self):
        """Create preference tabs."""
        for tab_name, prefs in self.PREFERENCE_DEFINITIONS.items():
            # Create tab frame
            tab_frame = ttk.Frame(self.notebook)
            self.notebook.add(tab_frame, text=tab_name)

            # Create scrollable frame
            canvas = tk.Canvas(tab_frame)
            scrollbar = ttk.Scrollbar(tab_frame, orient=tk.VERTICAL,
                                      command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Create preference widgets
            self._create_preference_widgets(scrollable_frame, tab_name, prefs)

            # Bind mousewheel to canvas
            def _on_mousewheel(event, canvas=canvas):
                delta = int(-1 * (event.delta / 120))
                canvas.yview_scroll(delta, "units")
            canvas.bind("<MouseWheel>", _on_mousewheel)

    def _create_preference_widgets(self, parent, tab_name: str,
                                   prefs: Dict[str, Any]):
        """Create widgets for preferences in a tab."""
        if tab_name not in self.widgets:
            self.widgets[tab_name] = {}

        for pref_name, pref_data in prefs.items():
            # Create widget based on type
            widget_type = pref_data.get('type', 'str')

            if widget_type == 'bool':
                widget = BoolWidget(parent, pref_name, pref_data)
            elif widget_type == 'int':
                widget = IntWidget(parent, pref_name, pref_data)
            elif widget_type == 'float':
                widget = FloatWidget(parent, pref_name, pref_data)
            elif widget_type == 'combo':
                widget = ComboWidget(parent, pref_name, pref_data)
            elif widget_type in ('file', 'directory'):
                widget = FileWidget(parent, pref_name, pref_data)
            elif widget_type == 'color':
                widget = ColorWidget(parent, pref_name, pref_data)
            else:
                widget = StringWidget(parent, pref_name, pref_data)

            # Create and pack the widget
            widget_frame = widget.create_widget()
            widget_frame.pack(fill=tk.X, padx=10, pady=5)

            # Store widget reference
            self.widgets[tab_name][pref_name] = widget

            # Bind change events
            self._bind_change_events(widget)

    def _bind_change_events(self, widget):
        """Bind change events to enable/disable Apply button."""
        def on_change(*args):
            self.has_changes = True
            self.apply_button.configure(state=tk.NORMAL)

        if hasattr(widget, 'var') and widget.var:
            widget.var.trace('w', on_change)

    def _load_preferences(self):
        """Load current preferences into widgets."""
        # Load preferences from file
        self.prefs_manager.load()
        
        for tab_name, tab_widgets in self.widgets.items():
            for pref_name, widget in tab_widgets.items():
                # Get current value or default
                pref_def = self.PREFERENCE_DEFINITIONS[tab_name][pref_name]
                value = self.prefs_manager.get(pref_name, pref_def.get('default'))
                
                # Store original value
                self.original_values[pref_name] = value
                
                # Set widget value
                widget.set_value(value)

    def _apply_changes(self):
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
            self.apply_button.configure(state=tk.DISABLED)

            return True

        except Exception as e:
            error_msg = f"Failed to save preferences:\n{str(e)}"
            messagebox.showerror("Error", error_msg)
            return False

    def _ok_clicked(self):
        """Handle OK button click."""
        if self.has_changes:
            if self._apply_changes():
                self._close_dialog()
        else:
            self._close_dialog()

    def _cancel_clicked(self):
        """Handle Cancel button click."""
        if self.has_changes:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save them?"
            )
            if result is True:  # Yes - save and close
                if self._apply_changes():
                    self._close_dialog()
            elif result is False:  # No - close without saving
                self._close_dialog()
            # None - cancel, don't close
        else:
            self._close_dialog()

    def _apply_clicked(self):
        """Handle Apply button click."""
        self._apply_changes()

    def _close_dialog(self):
        """Close the dialog."""
        if self.dialog:
            self.dialog.grab_release()
            self.dialog.destroy()
            self.dialog = None


def show_preferences(parent=None):
    """Convenience function to show preferences dialog."""
    dialog = PreferencesDialog(parent)
    dialog.show()


# Platform-specific integration
if platform.system() == "Darwin":
    # macOS-specific preferences integration
    def setup_macos_preferences_menu(app):
        """Set up macOS preferences menu integration."""
        try:
            cmd = 'tk::mac::ShowPreferences'
            app.createcommand(cmd, lambda: show_preferences(app))
        except Exception:
            pass