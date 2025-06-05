#!/usr/bin/env python3
"""Test script for the palette system integration."""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from PySide6.QtWidgets import QApplication, QMainWindow, QTextEdit
from PySide6.QtCore import QObject, Signal

# Mock preferences class for testing
class MockPreferences(QObject):
    def __init__(self):
        super().__init__()
        self._data = {
            "show_info_panel": True,
            "show_properties": True,
            "show_layers": True,
            "show_snap_settings": False
        }
    
    def get(self, key, default=None):
        return self._data.get(key, default)
    
    def set(self, key, value):
        self._data[key] = value
        print(f"Preference set: {key} = {value}")

# Mock main menu with minimal palette signals
class MockMainMenuBar(QObject):
    show_info_panel_toggled = Signal(bool)
    show_properties_toggled = Signal(bool)
    show_layers_toggled = Signal(bool)
    show_snap_settings_toggled = Signal(bool)
    
    def __init__(self, parent, preferences):
        super().__init__()
        self.parent_window = parent
        self.preferences = preferences
        
    def sync_palette_menu_states(self, palette_manager):
        print("Menu states synced with palette manager")

# Simple test window
class TestMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.preferences = MockPreferences()
        self.setWindowTitle("Palette System Test")
        self.resize(1024, 768)
        
        # Add central widget
        central_widget = QTextEdit()
        central_widget.setText(
            "Palette System Test\\n\\n"
            "The palettes should be visible and dockable.\\n"
            "Try closing them with the X button to test visibility sync."
        )
        self.setCentralWidget(central_widget)
        
        # Create mock menu
        self.main_menu = MockMainMenuBar(self, self.preferences)
        
        # Setup palettes
        self._setup_palettes()
        
    def _setup_palettes(self):
        """Setup the palette system."""
        from src.gui.palette_system import create_default_palettes
        
        # Create palette manager
        self.palette_manager = create_default_palettes(self)
        
        # Connect visibility changes
        self.palette_manager.palette_visibility_changed.connect(
            self._on_palette_visibility_changed
        )
        
        print("Palette system initialized successfully!")
        
    def _on_palette_visibility_changed(self, palette_id: str, visible: bool):
        """Handle palette visibility changes."""
        print(f"Palette visibility changed: {palette_id} = {visible}")
        
        # Update preferences
        if palette_id == "info_pane":
            self.preferences.set("show_info_panel", visible)
        elif palette_id == "config_pane":
            self.preferences.set("show_properties", visible)
        elif palette_id == "layer_window":
            self.preferences.set("show_layers", visible)
        elif palette_id == "snap_window":
            self.preferences.set("show_snap_settings", visible)
        
        # Sync menu (mock)
        self.main_menu.sync_palette_menu_states(self.palette_manager)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = TestMainWindow()
    window.show()
    
    print("Test started! Try closing palettes with the X button.")
    print("Check terminal output for visibility change events.")
    
    sys.exit(app.exec())
