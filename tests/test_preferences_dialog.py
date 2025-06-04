#!/usr/bin/env python3
"""
Test script for the preferences dialog.

This script tests the functionality of the translated preferences dialog
to ensure it works correctly with the existing preferences system.
"""

import sys
import os
import tkinter as tk
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import with corrected paths
try:
    from gui.preferences_dialog import show_preferences, setup_macos_preferences_menu
    from core.preferences import PreferencesManager
except ImportError:
    # Alternative import method
    import importlib.util
    
    # Load preferences_dialog module
    spec = importlib.util.spec_from_file_location(
        "preferences_dialog", 
        Path(__file__).parent / "src" / "gui" / "preferences_dialog.py"
    )
    preferences_dialog = importlib.util.module_from_spec(spec)
    
    # Load preferences module first
    prefs_spec = importlib.util.spec_from_file_location(
        "preferences", 
        Path(__file__).parent / "src" / "core" / "preferences.py"
    )
    preferences = importlib.util.module_from_spec(prefs_spec)
    sys.modules['preferences'] = preferences
    prefs_spec.loader.exec_module(preferences)
    
    # Now load preferences_dialog
    sys.modules['preferences_dialog'] = preferences_dialog
    spec.loader.exec_module(preferences_dialog)
    
    show_preferences = preferences_dialog.show_preferences
    setup_macos_preferences_menu = preferences_dialog.setup_macos_preferences_menu
    PreferencesManager = preferences.PreferencesManager


def test_preferences_dialog():
    """Test the preferences dialog functionality."""
    # Create main window
    root = tk.Tk()
    root.title("PyTkCAD Preferences Test")
    root.geometry("400x300")
    
    # Set up macOS preferences menu if on macOS
    try:
        setup_macos_preferences_menu(root)
    except Exception as e:
        print(f"Note: macOS preferences menu setup failed: {e}")
    
    # Create a simple interface for testing
    frame = tk.Frame(root)
    frame.pack(expand=True, fill='both', padx=20, pady=20)
    
    tk.Label(frame, text="PyTkCAD Preferences Dialog Test", 
             font=('Arial', 16, 'bold')).pack(pady=10)
    
    tk.Label(frame, text="Click the button below to open the preferences dialog:").pack(pady=5)
    
    # Button to open preferences
    prefs_button = tk.Button(
        frame,
        text="Open Preferences Dialog",
        command=lambda: show_preferences(root),
        font=('Arial', 12),
        padx=20,
        pady=10,
        bg='lightblue'
    )
    prefs_button.pack(pady=10)
    
    # Show current preferences
    tk.Label(frame, text="Current Preferences:", font=('Arial', 12, 'bold')).pack(pady=(20, 5))
    
    prefs_manager = PreferencesManager()
    current_prefs = prefs_manager.get_all_preferences()
    
    prefs_text = tk.Text(frame, height=8, width=50)
    prefs_text.pack(pady=5)
    
    # Display current preferences
    for key, value in sorted(current_prefs.items()):
        prefs_text.insert(tk.END, f"{key}: {value}\n")
    
    prefs_text.config(state=tk.DISABLED)
    
    # Button to refresh preferences display
    def refresh_prefs():
        prefs_text.config(state=tk.NORMAL)
        prefs_text.delete(1.0, tk.END)
        current_prefs = prefs_manager.get_all_preferences()
        for key, value in sorted(current_prefs.items()):
            prefs_text.insert(tk.END, f"{key}: {value}\n")
        prefs_text.config(state=tk.DISABLED)
    
    refresh_button = tk.Button(
        frame,
        text="Refresh Preferences Display",
        command=refresh_prefs,
        font=('Arial', 10)
    )
    refresh_button.pack(pady=5)
    
    # Instructions
    instructions = tk.Label(
        frame,
        text="Instructions:\n1. Open the preferences dialog\n2. Change some settings\n3. Click Apply or OK\n4. Refresh the display to see changes",
        justify=tk.LEFT,
        font=('Arial', 9),
        fg='gray'
    )
    instructions.pack(pady=10)
    
    # Start the GUI
    root.mainloop()


if __name__ == "__main__":
    test_preferences_dialog()
