"""
Main application class for BelfryCAD.
"""

from PySide6.QtWidgets import QApplication, QMessageBox, QFileDialog
from PySide6.QtCore import Qt
from typing import Optional

from .config import AppConfig
from .gui.main_window import MainWindow
from .core.preferences import PreferencesManager
from .core.document import Document
from .utils.logger import get_logger


class BelfryCadApplication:
    """Main application class for BelfryCAD."""

    def __init__(self, config: AppConfig):
        """Initialize the BelfryCAD application.

        Args:
            config: Application configuration object
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)

        # Initialize core components
        self.preferences = PreferencesManager(config)
        self.document = Document()
        self.main_window: Optional[MainWindow] = None

        # Create the QApplication
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])

        self.setup_application()

    def setup_application(self):
        """Set up the application properties."""
        if self.app is not None:
            self.app.setApplicationName(self.config.APP_NAME)
            self.app.setApplicationVersion(self.config.VERSION)
            self.app.setOrganizationName("BelfryCad")

    def run(self):
        """Run the main application."""
        try:
            # Load preferences
            self.preferences.load()
            self.logger.info("Preferences loaded")

            # Create the main window
            self.logger.info("Creating main window...")
            self.main_window = MainWindow(
                self.config, self.preferences, self.document)
            self.logger.info("Main window created")

            # Show the window
            self.logger.info("Showing main window...")
            self.main_window.show()
            self.logger.info("Main window shown")

            self.logger.info("Application started successfully")

            # Start the main event loop
            self.logger.info("Starting Qt event loop...")
            result = self.app.exec()
            self.logger.info(f"Qt event loop exited with code: {result}")
            return result

        except Exception as e:
            self.logger.error(f"Error in main application loop: {e}")
            raise

    def on_closing(self):
        """Handle application closing."""
        try:
            # Check if document has unsaved changes
            if self.document and self.document.is_modified():
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Question)
                msg.setWindowTitle("Unsaved Changes")
                msg.setText("You have unsaved changes. Do you want to save before closing?")
                msg.setStandardButtons(
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
                )
                msg.setDefaultButton(QMessageBox.Yes)

                result = msg.exec()

                if result == QMessageBox.Cancel:
                    return False
                elif result == QMessageBox.Yes:
                    if not self.save_document():
                        return False  # Save was cancelled or failed

            # Save preferences
            if self.main_window:
                # Update window geometry in preferences
                geometry = self.main_window.geometry()
                self.preferences.set("window_geometry",
                                     f"{geometry.width()}x{geometry.height()}+"
                                     f"{geometry.x()}+{geometry.y()}")

            self.preferences.save()

            self.logger.info("Application closing normally")
            return True

        except Exception as e:
            self.logger.error(f"Error during application shutdown: {e}")
            return True

    def save_document(self) -> bool:
        """Save the current document.

        Returns:
            True if saved successfully, False if cancelled or failed
        """
        try:
            if not self.document.filename:
                # No filename set, show save dialog
                filename, _ = QFileDialog.getSaveFileName(
                    self.main_window,
                    "Save Document",
                    "",
                    "BelfryCad files (*.tkcad);;SVG files (*.svg);;"
                    "DXF files (*.dxf);;All files (*.*)"
                )

                if not filename:
                    return False  # User cancelled

                self.document.filename = filename

            # Save the document
            self.document.save()

            if self.main_window:
                self.main_window.update_title()

            return True

        except Exception as e:
            self.logger.error(f"Error saving document: {e}")
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Save Error")
            msg.setText(f"Failed to save document:\n{str(e)}")
            msg.setParent(self.main_window)
            msg.exec()
            return False
