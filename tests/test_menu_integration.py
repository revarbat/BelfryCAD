#!/usr/bin/env python3
"""
Test script to verify the menu system integration in PyTkCAD.

This script tests that the new comprehensive menu system is properly integrated
and working as expected.
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Add the src directory to the path so we can import from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from BelfryCAD.config import AppConfig
from BelfryCAD.core.preferences import PreferencesManager
from BelfryCAD.core.document import Document
from BelfryCAD.gui.main_window import MainWindow


def test_menu_system():
    """Test the menu system functionality."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Initialize components
    config = AppConfig()
    preferences = PreferencesManager(config)
    document = Document()

    # Create main window
    main_window = MainWindow(config, preferences, document)
    main_window.show()

    # Test that the menu bar exists and has the expected menus
    menubar = main_window.menuBar()
    menu_actions = menubar.actions()
    menu_titles = [action.text() for action in menu_actions]

    print("Menu System Integration Test")
    print("=" * 40)

    # Expected menus from our comprehensive menu system
    expected_menus = ["&File", "&Edit", "&View", "&CAM", "&Window"]

    print(f"Found menus: {menu_titles}")
    print(f"Expected menus: {expected_menus}")

    # Check if all expected menus are present
    all_present = all(menu in menu_titles for menu in expected_menus)
    print(f"All expected menus present: {all_present}")

    # Test the MainMenuBar integration
    if hasattr(main_window, 'main_menu'):
        print("✓ MainMenuBar instance found")

        # Test recent files manager
        if hasattr(main_window.main_menu, 'recent_files_manager'):
            print("✓ Recent files manager found")
        else:
            print("✗ Recent files manager not found")

        # Test signal connections
        signals_to_test = [
            'new_triggered', 'open_triggered', 'save_triggered', 'save_as_triggered',
            'redraw_triggered', 'show_origin_toggled', 'show_grid_toggled'
        ]

        for signal_name in signals_to_test:
            if hasattr(main_window.main_menu, signal_name):
                print(f"✓ Signal {signal_name} found")
            else:
                print(f"✗ Signal {signal_name} not found")
    else:
        print("✗ MainMenuBar instance not found")

    # Test specific menu items
    file_menu = None
    for action in menu_actions:
        if action.text() == "&File":
            file_menu = action.menu()
            break

    if file_menu:
        file_actions = file_menu.actions()
        file_action_texts = [action.text() for action in file_actions if action.text()]
        print(f"File menu items: {file_action_texts}")

        # Check for expected file menu items
        expected_file_items = ["&New", "&Open...", "&Save", "Save &As..."]
        file_items_present = any(item in file_action_texts for item in expected_file_items)
        print(f"Expected file menu items present: {file_items_present}")

    # Test keyboard shortcuts
    print("\nTesting keyboard shortcuts...")
    new_actions = [action for action in menubar.findChildren(type(menu_actions[0])) if action.text() == "&New"]
    if new_actions:
        shortcut = new_actions[0].shortcut()
        print(f"New file shortcut: {shortcut.toString()}")

    print("\n" + "=" * 40)
    print("Menu system integration test completed!")

    # Close the application after a short delay
    QTimer.singleShot(2000, app.quit)

    return main_window


if __name__ == "__main__":
    test_menu_system()
    app = QApplication.instance()
    if app:
        sys.exit(app.exec())
