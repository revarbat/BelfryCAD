"""
Progress Window for PyTkCAD.

This module provides a PySide6/Qt GUI progress window for displaying operation
progress with a progress bar. It's a direct translation of the original TCL
progwin.tcl functionality.
"""

import time
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, QApplication, QWidget
)
from PySide6.QtCore import Qt, Signal


class ProgressWindowInfo:
    """Global progress window information storage."""

    def __init__(self):
        self.last_update = 0
        self.update_interval = 125  # milliseconds


# Global instance
progwin_info = ProgressWindowInfo()


class ProgressWindow(QDialog):
    """
    Progress window for displaying operation progress.
    """

    # Signals
    cancelled = Signal()  # Emitted if user tries to close (blocked

    def __init__(
            self,
            title: str,
            caption: str,
            parent: Optional[QWidget] = None
    ):
        """
        Initialize the progress window.

        Args:
            title: Window title
            caption: Caption text to display above progress bar
            parent: Parent widget, if any
        """
        super().__init__(parent)
        self.title = title
        self.caption = caption
        self.max_value = 100
        self.current_value = 0
        self._init_ui()
        self._setup_window()

        # Initialize timing
        progwin_info.last_update = int(time.time() * 1000)

    def _init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(self.title)
        self.setFixedSize(220, 80)

        # Create main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create caption label
        self.caption_label = QLabel(self.caption)
        self.caption_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.caption_label)

        # Create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedSize(200, 20)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        # Style the progress bar to match the original blue4 color
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #666;
                border-radius: 0px;
                text-align: center;
                background-color: white;
            }
            QProgressBar::chunk {
                background-color: #00008B;  /* blue4 equivalent */
                border-radius: 0px;
            }
        """)

        layout.addWidget(self.progress_bar)

    def _setup_window(self):
        """Setup window properties."""
        # Make window non-resizable
        self.setFixedSize(self.size())

        # Make window modal
        self.setModal(True)

        # Disable close button functionality (like the original TCL version)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.CustomizeWindowHint
        )

        # Show and raise the window
        self.show()
        self.raise_()

        # Force window to be visible and update
        QApplication.processEvents()

    def closeEvent(self, event):
        """
        Override close event to prevent closing (like original TCL version).
        """
        # In the original TCL, WM_DELETE_WINDOW was set to "string tolower 0"
        # which effectively prevents closing. We'll ignore the close event.
        event.ignore()
        self.cancelled.emit()

    def update_progress(self, max_val: int, curr_val: int):
        """
        Update the progress bar.

        Args:
            max_val: Maximum value for progress
            curr_val: Current progress value
        """
        if not self.isVisible():
            return

        now = int(time.time() * 1000)
        time_delta = now - progwin_info.last_update

        # Only update if enough time has passed (throttle updates)
        if time_delta > progwin_info.update_interval:
            progwin_info.last_update = now

            # Calculate percentage
            if max_val > 0:
                percentage = int(round(100.0 * curr_val / max_val))
                percentage = max(0, min(100, percentage))  # Clamp to 0-100
            else:
                percentage = 0

            self.progress_bar.setValue(percentage)

            # Store values for potential external access
            self.max_value = max_val
            self.current_value = curr_val

            # Force immediate update
            QApplication.processEvents()

    def set_caption(self, caption: str):
        """
        Update the caption text.

        Args:
            caption: New caption text
        """
        self.caption = caption
        self.caption_label.setText(caption)

    def get_progress(self) -> tuple[int, int]:
        """
        Get current progress values.

        Returns:
            Tuple of (current_value, max_value)
        """
        return (self.current_value, self.max_value)

    def destroy_window(self):
        """
        Destroy the progress window.
        """
        if self.isVisible():
            self.hide()
            self.close()
            # Reset timing info
            progwin_info.last_update = 0


def create_progress_window(title: str, caption: str,
                           parent: Optional[QWidget] = None) -> ProgressWindow:
    """
    Create and return a new progress window.

    Args:
        title: Window title
        caption: Caption text to display
        parent: Parent widget for the new window

    Returns:
        A new ProgressWindow instance
    """
    return ProgressWindow(title, caption, parent)


def progress_callback(window: ProgressWindow, max_val: int, curr_val: int):
    """
    Callback function to update progress window.

    Args:
        window: The progress window to update
        max_val: Maximum progress value
        curr_val: Current progress value
    """
    if window:
        window.update_progress(max_val, curr_val)


def destroy_progress_window(window: ProgressWindow):
    """
    Destroy a progress window.

    Args:
        window: The progress window to destroy
    """
    if window:
        window.destroy_window()


class ProgressContext:
    """
    Context manager for progress windows.

    Usage:
        with ProgressContext("Processing", "Loading files...") as progress:
            for i in range(100):
                # Do work
                progress.update(100, i)
                time.sleep(0.1)
    """

    def __init__(
            self,
            title: str,
            caption: str,
            parent: Optional[QWidget] = None
    ):
        """
        Initialize progress context.

        Args:
            title: Window title
            caption: Caption text
            parent: Parent widget
        """
        self.title = title
        self.caption = caption
        self.parent = parent
        self.window = None

    def __enter__(self) -> 'ProgressContext':
        """Enter context - create progress window."""
        self.window = create_progress_window(
            self.title, self.caption, self.parent)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - destroy progress window."""
        if self.window:
            destroy_progress_window(self.window)
            self.window = None

    def update(self, max_val: int, curr_val: int):
        """
        Update progress.

        Args:
            max_val: Maximum value
            curr_val: Current value
        """
        if self.window:
            self.window.update_progress(max_val, curr_val)

    def set_caption(self, caption: str):
        """
        Update caption text.

        Args:
            caption: New caption text
        """
        if self.window:
            self.window.set_caption(caption)


if __name__ == "__main__":
    """Test the progress window independently."""
    import sys
    from PySide6.QtWidgets import (
        QMainWindow, QPushButton, QWidget
    )
    import threading

    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Progress Window Test")
            self.setGeometry(100, 100, 300, 200)

            central_widget = QWidget()
            self.setCentralWidget(central_widget)

            layout = QVBoxLayout()
            central_widget.setLayout(layout)

            # Test button
            test_btn = QPushButton("Test Progress Window")
            test_btn.clicked.connect(self.test_progress)
            layout.addWidget(test_btn)

            # Test context manager button
            context_btn = QPushButton("Test Progress Context")
            context_btn.clicked.connect(self.test_context)
            layout.addWidget(context_btn)

        def test_progress(self):
            """Test basic progress window functionality."""
            progress = create_progress_window(
                "Test Progress", "Processing items...")

            def update_progress():
                for i in range(101):
                    progress.update_progress(100, i)
                    time.sleep(0.05)
                destroy_progress_window(progress)

            # Run in thread to avoid blocking UI
            thread = threading.Thread(target=update_progress)
            thread.daemon = True
            thread.start()

        def test_context(self):
            """Test progress context manager."""
            def run_with_context():
                with ProgressContext(
                    "Context Test", "Using context manager..."
                ) as progress:
                    for i in range(101):
                        progress.update(100, i)
                        if i == 50:
                            progress.set_caption("Halfway done...")
                        time.sleep(0.05)

            # Run in thread to avoid blocking UI
            thread = threading.Thread(target=run_with_context)
            thread.daemon = True
            thread.start()

    app = QApplication(sys.argv)

    # Create test window
    test_window = TestWindow()
    test_window.show()

    sys.exit(app.exec())
