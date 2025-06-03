"""
Preferences dialog for PyTkCAD - Python translation of prefs.tcl

This module provides a comprehensive preferences management system with GUI dialog
creation, similar to the original Tcl implementation.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Callable
import platform

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget,
    QWidget, QLabel, QLineEdit, QPushButton, QCheckBox, QSpinBox,
    QComboBox, QColorDialog, QFileDialog, QDialogButtonBox,
    QGroupBox, QFormLayout, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from ..core.preferences import PreferencesManager


class PreferenceTypes:
    """Enumeration of preference types."""
    BOOL = "bool"
    INT = "int"
    STR = "str"
    COMBO = "combo"
    MULTI = "multi"
    CUSTOM = "cust"
    COLOR = "color"
    FILE = "file"
    DIR = "dir"


class PreferenceSpec:
    """Specification for a single preference."""
    
    def __init__(self, name: str, pref_type: str, label: str = None, 
                 default: Any = None, choices: List[str] = None,
                 min_val: float = None, max_val: float = None,
                 validation: Callable = None, help_text: str = None):
        self.name = name
        self.type = pref_type
        self.label = label or name.replace('_', ' ').title()
        self.default = default
        self.choices = choices or []
        self.min_val = min_val
        self.max_val = max_val
        self.validation = validation
        self.help_text = help_text


class PreferencesDialog:
    """Main preferences dialog class - Python equivalent of prefs.tcl"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.root = None
        self.notebook = None
        self.widgets = {}  # Dictionary to store widget references
        self.modified_prefs = {}  # Track modifications
        self.prefs_manager = PreferencesManager()
        self.current_values = {}
        self.apply_button = None
        
        # Define preference specifications similar to Tcl version
        self.preference_specs = self._define_preference_specs()
        self.tab_specs = self._define_tab_specs()
        
    def _define_preference_specs(self) -> Dict[str, PreferenceSpec]:
        """Define all preference specifications."""
        specs = {}
        
        # General preferences
        specs['antialiasing'] = PreferenceSpec(
            'antialiasing', PreferenceTypes.BOOL, 'Enable Antialiasing', True,
            help_text='Enable smooth rendering of lines and curves'
        )
        specs['grid_visible'] = PreferenceSpec(
            'grid_visible', PreferenceTypes.BOOL, 'Show Grid', True,
            help_text='Display construction grid'
        )
        specs['snap_to_grid'] = PreferenceSpec(
            'snap_to_grid', PreferenceTypes.BOOL, 'Snap to Grid', True,
            help_text='Automatically snap objects to grid points'
        )
        specs['show_rulers'] = PreferenceSpec(
            'show_rulers', PreferenceTypes.BOOL, 'Show Rulers', True,
            help_text='Display measurement rulers'
        )
        
        # Units and precision  
        specs['units'] = PreferenceSpec(
            'units', PreferenceTypes.COMBO, 'Units', 'inches',
            choices=['inches', 'mm', 'cm', 'points'],
            help_text='Default measurement units'
        )
        specs['precision'] = PreferenceSpec(
            'precision', PreferenceTypes.INT, 'Decimal Precision', 3,
            min_val=0, max_val=10,
            help_text='Number of decimal places for measurements'
        )
        
        # Colors
        specs['canvas_bg_color'] = PreferenceSpec(
            'canvas_bg_color', PreferenceTypes.COLOR, 'Canvas Background', '#ffffff',
            help_text='Background color of the drawing canvas'
        )
        specs['grid_color'] = PreferenceSpec(
            'grid_color', PreferenceTypes.COLOR, 'Grid Color', '#cccccc',
            help_text='Color of the construction grid'
        )
        specs['selection_color'] = PreferenceSpec(
            'selection_color', PreferenceTypes.COLOR, 'Selection Color', '#0080ff',
            help_text='Color for selected objects'
        )
        
        # Auto-save settings
        specs['auto_save'] = PreferenceSpec(
            'auto_save', PreferenceTypes.BOOL, 'Enable Auto-save', True,
            help_text='Automatically save work at regular intervals'
        )
        specs['auto_save_interval'] = PreferenceSpec(
            'auto_save_interval', PreferenceTypes.INT, 'Auto-save Interval (seconds)', 300,
            min_val=30, max_val=3600,
            help_text='Time between automatic saves'
        )
        
        # File handling
        specs['recent_files_count'] = PreferenceSpec(
            'recent_files_count', PreferenceTypes.INT, 'Recent Files Count', 10,
            min_val=1, max_val=50,
            help_text='Number of recent files to remember'
        )
        
        # Window settings
        specs['window_geometry'] = PreferenceSpec(
            'window_geometry', PreferenceTypes.STR, 'Default Window Size', '1200x800+100+100',
            help_text='Default window size and position'
        )
        
        return specs
    
    def _define_tab_specs(self) -> Dict[str, List[str]]:
        """Define which preferences belong to which tabs."""
        return {
            'General': [
                'antialiasing', 'grid_visible', 'snap_to_grid', 'show_rulers'
            ],
            'Units & Precision': [
                'units', 'precision'
            ],
            'Colors': [
                'canvas_bg_color', 'grid_color', 'selection_color'
            ],
            'Files': [
                'auto_save', 'auto_save_interval', 'recent_files_count'
            ],
            'Window': [
                'window_geometry'
            ]
        }
    
    def show_dialog(self):
        """Show the preferences dialog - equivalent to prefs:edit in Tcl."""
        if self.root and self.root.winfo_exists():
            # Dialog already open, bring to front
            self.root.lift()
            self.root.focus_force()
            return
            
        self._create_dialog()
        self._load_current_values()
        self._populate_widgets()
        
        # Center the dialog
        self._center_dialog()
        
        # Make dialog modal
        self.root.transient(self.parent)
        self.root.grab_set()
        
        # Focus on OK button
        self.ok_button.focus_set()
    
    def _create_dialog(self):
        """Create the main dialog window."""
        self.root = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        self.root.title("Preferences")
        self.root.resizable(True, True)
        
        # Set minimum size
        self.root.minsize(500, 400)
        
        # Create main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(0, 10))
        
        # Create tabs
        self._create_tabs()
        
        # Create buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, sticky="e")
        
        self.ok_button = ttk.Button(button_frame, text="OK", command=self._on_ok)
        self.ok_button.grid(row=0, column=0, padx=(0, 5))
        
        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self._on_cancel)
        self.cancel_button.grid(row=0, column=1, padx=5)
        
        self.apply_button = ttk.Button(button_frame, text="Apply", command=self._on_apply, state="disabled")
        self.apply_button.grid(row=0, column=2, padx=(5, 0))
        
        # Bind keyboard shortcuts
        self.root.bind('<Return>', lambda e: self._on_ok())
        self.root.bind('<Escape>', lambda e: self._on_cancel())
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_cancel)
    
    def _create_tabs(self):
        """Create all preference tabs."""
        for tab_name, pref_names in self.tab_specs.items():
            tab_frame = ttk.Frame(self.notebook, padding="10")
            self.notebook.add(tab_frame, text=tab_name)
            self._create_tab_content(tab_frame, pref_names)
    
    def _create_tab_content(self, parent: ttk.Frame, pref_names: List[str]):
        """Create content for a specific tab."""
        row = 0
        
        for pref_name in pref_names:
            if pref_name not in self.preference_specs:
                continue
                
            spec = self.preference_specs[pref_name]
            
            # Create label
            label = ttk.Label(parent, text=spec.label + ":")
            label.grid(row=row, column=0, sticky="w", padx=(0, 10), pady=2)
            
            # Create widget based on type
            widget = self._create_preference_widget(parent, spec)
            if widget:
                widget.grid(row=row, column=1, sticky="ew", pady=2)
                self.widgets[pref_name] = widget
                
                # Add help text as tooltip if available
                if spec.help_text:
                    self._create_tooltip(widget, spec.help_text)
            
            row += 1
        
        # Configure column weights
        parent.grid_columnconfigure(1, weight=1)
    
    def _create_preference_widget(self, parent: ttk.Frame, spec: PreferenceSpec):
        """Create appropriate widget for preference type."""
        if spec.type == PreferenceTypes.BOOL:
            var = tk.BooleanVar()
            widget = ttk.Checkbutton(parent, variable=var, command=self._on_value_changed)
            widget._var = var
            return widget
            
        elif spec.type == PreferenceTypes.INT:
            var = tk.StringVar()
            widget = ttk.Spinbox(parent, from_=spec.min_val or 0, to=spec.max_val or 100,
                               textvariable=var, validate='key',
                               validatecommand=(parent.register(self._validate_int), '%P'))
            widget._var = var
            var.trace('w', lambda *args: self._on_value_changed())
            return widget
            
        elif spec.type == PreferenceTypes.STR:
            var = tk.StringVar()
            widget = ttk.Entry(parent, textvariable=var)
            widget._var = var
            var.trace('w', lambda *args: self._on_value_changed())
            return widget
            
        elif spec.type == PreferenceTypes.COMBO:
            var = tk.StringVar()
            widget = ttk.Combobox(parent, textvariable=var, values=spec.choices, state="readonly")
            widget._var = var
            widget.bind('<<ComboboxSelected>>', lambda e: self._on_value_changed())
            return widget
            
        elif spec.type == PreferenceTypes.COLOR:
            frame = ttk.Frame(parent)
            var = tk.StringVar()
            entry = ttk.Entry(frame, textvariable=var, width=10)
            entry.pack(side=tk.LEFT, padx=(0, 5))
            
            def choose_color():
                color = colorchooser.askcolor(color=var.get())[1]
                if color:
                    var.set(color)
                    self._on_value_changed()
                    
            button = ttk.Button(frame, text="Choose...", command=choose_color)
            button.pack(side=tk.LEFT)
            
            frame._var = var
            var.trace('w', lambda *args: self._on_value_changed())
            return frame
            
        return None
    
    def _validate_int(self, value: str) -> bool:
        """Validate integer input."""
        if value == "":
            return True
        try:
            int(value)
            return True
        except ValueError:
            return False
    
    def _create_tooltip(self, widget, text: str):
        """Create a simple tooltip for a widget."""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, background="lightyellow",
                           relief="solid", borderwidth=1, font=("TkDefaultFont", "8"))
            label.pack()
            
            def hide_tooltip():
                tooltip.destroy()
                
            tooltip.after(3000, hide_tooltip)  # Auto-hide after 3 seconds
            widget._tooltip = tooltip
            
        def hide_tooltip(event):
            if hasattr(widget, '_tooltip'):
                widget._tooltip.destroy()
                
        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)
    
    def _load_current_values(self):
        """Load current preference values."""
        all_prefs = self.prefs_manager.get_all_preferences()
        self.current_values = {}
        
        for pref_name, spec in self.preference_specs.items():
            if pref_name in all_prefs:
                self.current_values[pref_name] = all_prefs[pref_name]
            else:
                self.current_values[pref_name] = spec.default
    
    def _populate_widgets(self):
        """Populate widgets with current values."""
        for pref_name, widget in self.widgets.items():
            if pref_name in self.current_values:
                value = self.current_values[pref_name]
                if hasattr(widget, '_var'):
                    widget._var.set(value)
    
    def _on_value_changed(self):
        """Called when any preference value changes."""
        if self.apply_button:
            self.apply_button.config(state="normal")
    
    def _collect_values(self) -> Dict[str, Any]:
        """Collect current values from all widgets."""
        values = {}
        
        for pref_name, widget in self.widgets.items():
            if hasattr(widget, '_var'):
                value = widget._var.get()
                
                # Convert based on preference type
                spec = self.preference_specs[pref_name]
                if spec.type == PreferenceTypes.INT:
                    try:
                        value = int(value) if value else spec.default
                    except ValueError:
                        value = spec.default
                elif spec.type == PreferenceTypes.BOOL:
                    value = bool(value)
                    
                values[pref_name] = value
                
        return values
    
    def _apply_changes(self):
        """Apply preference changes."""
        try:
            new_values = self._collect_values()
            
            # Update preferences
            for pref_name, value in new_values.items():
                self.prefs_manager.set_preference(pref_name, value)
            
            # Save preferences
            self.prefs_manager.save_preferences()
            
            # Update current values
            self.current_values = new_values.copy()
            
            # Disable apply button
            if self.apply_button:
                self.apply_button.config(state="disabled")
                
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save preferences: {str(e)}")
            return False
    
    def _center_dialog(self):
        """Center the dialog on the parent window or screen."""
        self.root.update_idletasks()
        
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        if self.parent:
            parent_x = self.parent.winfo_rootx()
            parent_y = self.parent.winfo_rooty()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()
            
            x = parent_x + (parent_width - width) // 2
            y = parent_y + (parent_height - height) // 2
        else:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _on_ok(self):
        """Handle OK button click."""
        if self._apply_changes():
            self._close_dialog()
    
    def _on_cancel(self):
        """Handle Cancel button click."""
        self._close_dialog()
    
    def _on_apply(self):
        """Handle Apply button click."""
        self._apply_changes()
    
    def _close_dialog(self):
        """Close the preferences dialog."""
        if self.root:
            self.root.grab_release()
            self.root.destroy()
            self.root = None


# Platform-specific integration
def setup_mac_preferences_menu():
    """Set up macOS-specific preferences menu integration."""
    if platform.system() == "Darwin":
        try:
            import tkinter.dnd  # This will fail on some systems, that's OK
            # On macOS, we should integrate with the system preferences menu
            # This would be more complex in a real implementation
            pass
        except ImportError:
            pass


def show_preferences_dialog(parent=None):
    """Convenience function to show preferences dialog."""
    dialog = PreferencesDialog(parent)
    dialog.show_dialog()


# Module initialization
if __name__ == "__main__":
    # Test the preferences dialog
    root = tk.Tk()
    root.title("Test Application")
    
    def show_prefs():
        show_preferences_dialog(root)
    
    ttk.Button(root, text="Show Preferences", command=show_prefs).pack(pady=20)
    
    root.mainloop()
