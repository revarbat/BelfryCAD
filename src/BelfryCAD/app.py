"""
Main application class for BelfryCAD.
"""

from PySide6.QtWidgets import QApplication, QMessageBox, QFileDialog
from typing import Optional
from PySide6.QtCore import Qt

from .config import AppConfig
from .gui.document_window import DocumentWindow
from .models.preferences import PreferencesModel
from .gui.viewmodels.preferences_viewmodel import PreferencesViewModel
from .models.document import Document
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

        # Initialize core components with MVVM preferences
        self.preferences_model = PreferencesModel(config)
        self.preferences_viewmodel = PreferencesViewModel(self.preferences_model)
        self.document = Document()
        self.document_window: Optional[DocumentWindow] = None

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
            self.app.setOrganizationName("BelfrySCAD")

    def run(self):
        """Run the main application."""
        try:
            # Load preferences using MVVM system
            self.preferences_viewmodel.load_preferences()
            self.logger.info("Preferences loaded")

            # Create the document window
            self.logger.info("Creating document window...")
            self.document_window = DocumentWindow(
                self.config, self.preferences_viewmodel, self.document)
            self.logger.info("Document window created")

            # Show the window
            self.logger.info("Showing document window...")
            self.document_window.show()
            self.logger.info("Document window shown")

            self.logger.info("Application started successfully")

            # Start the main event loop
            self.logger.info("Starting Qt event loop...")
            result = self.app.exec()  # type: ignore
            self.logger.info(f"Qt event loop exited with code: {result}")
            return result

        except Exception as e:
            self.logger.error(f"Error in main application loop: {e}")
            raise

    def cleanup(self):
        """Clean up application resources before exit."""
        try:
            # Save window geometry
            if self.document_window:
                geometry = self.document_window.geometry()
                geometry_str = (f"{geometry.width()}x{geometry.height()}+"
                               f"{max(0,geometry.x())}+{max(0,geometry.y()-28)}")
                self.preferences_viewmodel.set("window_geometry", geometry_str)
                self.logger.info("Window geometry saved")

            # Save preferences
            if self.preferences_viewmodel:
                self.preferences_viewmodel.save_preferences()
                self.logger.info("Preferences saved")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def show_error_dialog(self, title: str, message: str):
        """Show an error dialog to the user."""
        try:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle(title)
            msg.setText(message)
            msg.setParent(self.document_window)
            msg.exec()
        except Exception as e:
            self.logger.error(f"Error showing error dialog: {e}")

    def show_info_dialog(self, title: str, message: str):
        """Show an info dialog to the user."""
        try:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle(title)
            msg.setText(message)
            msg.setParent(self.document_window)
            msg.exec()
        except Exception as e:
            self.logger.error(f"Error showing info dialog: {e}")

    def update_title(self):
        """Update the document window title."""
        if self.document_window:
            self.document_window.update_title()

    def show_file_dialog(self, title: str, filter: str, save_mode: bool = False) -> Optional[str]:
        """Show a file dialog and return the selected file path."""
        try:
            if save_mode:
                file_path, _ = QFileDialog.getSaveFileName(
                    self.document_window, title, "", filter)
            else:
                file_path, _ = QFileDialog.getOpenFileName(
                    self.document_window, title, "", filter)
            return file_path if file_path else None
        except Exception as e:
            self.logger.error(f"Error showing file dialog: {e}")
            return None
