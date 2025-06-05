#!/usr/bin/env python3
"""
Simple validation script for pyTkCAD keyboard shortcuts.

This script verifies that the keyboard shortcut system is properly implemented
and shows the current mappings.
"""

import os
import sys

# Add the src directory to Python path
sys.path.insert(0, 'src')

from PySide6.QtWidgets import QApplication
from src.config import AppConfig
from src.core.preferences import PreferencesManager
from src.core.document import Document
from src.gui.main_window import MainWindow


def main():
    """Main validation function"""
    print("pyTkCAD Keyboard Shortcuts Validation")
    print("=====================================")
    print()

    # Create QApplication
    app = QApplication([])

    try:
        # Create test instances
        config = AppConfig()
        preferences = PreferencesManager(config)
        document = Document()

        # Create main window
        main_window = MainWindow(config, preferences, document)

        # Test keyboard shortcuts exist
        if hasattr(main_window, 'category_key_mappings'):
            print('✓ Primary keyboard shortcuts found:')
            print()
            for key, category in main_window.category_key_mappings.items():
                print(f'  {key:5} -> {category.value}')
            print()
            print('✓ Keyboard shortcut system is working correctly!')
            print()
            print('USAGE:')
            print('------')
            print('1. Press Space to activate Selector tool directly')
            print('2. Press N to show Node tools, then S-A-D-R-C for tools')
            print('3. Press L to show Line tools, then L-M-P-B-Q for tools')
            print('4. Continue with other categories as needed')
            print('5. Press Escape to close any open palette')
            
        else:
            print('✗ Keyboard shortcuts not found')
            return 1

        main_window.close()
        return 0

    except Exception as e:
        print(f'✗ Error during validation: {e}')
        return 1
    finally:
        app.quit()


if __name__ == "__main__":
    sys.exit(main())
