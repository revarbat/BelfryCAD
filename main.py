#!/usr/bin/env python3
"""
BelfryCAD - A CAD application using Python and PySide6

This is the main entry point for the application.
"""

import sys
from PySide6.QtWidgets import QApplication, QMessageBox
import traceback

# Import main application modules
from BelfryCAD.app import BelfryCadApplication
from BelfryCAD.config import AppConfig
from BelfryCAD.utils.logger import setup_logger


def main():
    """Main entry point for BelfryCAD application."""
    try:
        # Set up logging
        logger = setup_logger()
        logger.info("Starting BelfryCAD application...")

        # Initialize application configuration
        config = AppConfig()

        # Create and run the main application
        app = BelfryCadApplication(config)
        app.run()

    except Exception as e:
        # Show error dialog if application fails to start
        error_msg = (f"Failed to start BelfryCAD:\n\n{str(e)}\n\n"
                     f"{traceback.format_exc()}")
        try:
            # Try to show PySide6 message box
            app = QApplication(sys.argv)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("BelfryCAD Error")
            msg.setText(error_msg)
            msg.exec()
        except Exception:
            # Fall back to console output
            print(f"ERROR: {error_msg}", file=sys.stderr)

        sys.exit(1)


if __name__ == "__main__":
    main()
