"""
Main application class for PyTkCAD.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Optional

from .config import AppConfig
from .gui.main_window import MainWindow
from .core.preferences import PreferencesManager
from .core.document import Document
from .utils.logger import get_logger


class TkCADApplication:
    """Main application class for PyTkCAD."""

    def __init__(self, config: AppConfig):
        """Initialize the TkCAD application.

        Args:
            config: Application configuration object
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)

        # Initialize core components
        self.preferences = PreferencesManager(config)
        self.document = Document()
        self.main_window: Optional[MainWindow] = None

        # Create the root window
        self.root = tk.Tk()
        self.setup_root_window()

    def setup_root_window(self):
        """Set up the root window properties."""
        self.root.title(f"{self.config.APP_NAME} v{self.config.VERSION}")

        # Load window geometry from preferences
        geometry = self.preferences.get("window_geometry", "1200x800+100+100")
        self.root.geometry(geometry)

        # Set up window close protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Platform-specific configurations
        if self.config.windowing_system == "aqua":
            # macOS specific settings
            self.root.createcommand('::tk::mac::Quit', self.on_closing)

    def run(self):
        """Run the main application."""
        try:
            # Load preferences
            self.preferences.load()

            # Create the main window
            self.main_window = MainWindow(
                self.root, self.config, self.preferences, self.document)

            # Show the window (it might be withdrawn initially)
            self.root.deiconify()

            self.logger.info("Application started successfully")

            # Start the main event loop
            self.root.mainloop()

        except Exception as e:
            self.logger.error(f"Error in main application loop: {e}")
            raise

    def on_closing(self):
        """Handle application closing."""
        try:
            # Check if document has unsaved changes
            if self.document and self.document.is_modified():
                result = messagebox.askyesnocancel(
                    "Unsaved Changes",
                    "You have unsaved changes." +
                    " Do you want to save before closing?",
                    parent=self.root
                )

                if result is None:  # Cancel
                    return
                elif result:  # Yes, save
                    if not self.save_document():
                        return  # Save was cancelled or failed

            # Save preferences
            if self.main_window:
                # Update window geometry in preferences
                self.preferences.set("window_geometry", self.root.geometry())

            self.preferences.save()

            self.logger.info("Application closing normally")

        except Exception as e:
            self.logger.error(f"Error during application shutdown: {e}")

        finally:
            # Destroy the root window
            self.root.destroy()

    def save_document(self) -> bool:
        """Save the current document.

        Returns:
            True if saved successfully, False if cancelled or failed
        """
        try:
            if not self.document.filename:
                # No filename set, show save dialog
                filename = filedialog.asksaveasfilename(
                    parent=self.root,
                    title="Save Document",
                    defaultextension=".tkcad",
                    filetypes=[
                        ("TkCAD files", "*.tkcad"),
                        ("SVG files", "*.svg"),
                        ("DXF files", "*.dxf"),
                        ("All files", "*.*")
                    ]
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
            messagebox.showerror(
                "Save Error",
                f"Failed to save document:\n{str(e)}",
                parent=self.root
            )
            return False
