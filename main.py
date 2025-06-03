#!/usr/bin/env python3
"""
PyTkCAD - A CAD application using Python and PySide6
Translated from TCL TkCAD codebase

This is the main entry point for the application.
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox
import traceback

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import main application modules
from src.app import TkCADApplication
from src.config import AppConfig
from src.utils.logger import setup_logger

def main():
    """Main entry point for PyTkCAD application."""
    try:
        # Set up logging
        logger = setup_logger()
        logger.info("Starting PyTkCAD application...")

        # Initialize application configuration
        config = AppConfig()

        # Create and run the main application
        app = TkCADApplication(config)
        app.run()

    except Exception as e:
        # Show error dialog if application fails to start
        error_msg = (f"Failed to start PyTkCAD:\n\n{str(e)}\n\n"
                     f"{traceback.format_exc()}")
        try:
            # Try to show PySide6 message box
            app = QApplication(sys.argv)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("PyTkCAD Error")
            msg.setText(error_msg)
            msg.exec()
        except Exception:
            # Fall back to console output
            print(f"ERROR: {error_msg}", file=sys.stderr)

        sys.exit(1)

if __name__ == "__main__":
    main()
