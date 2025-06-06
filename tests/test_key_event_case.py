#!/usr/bin/env python3
"""
Test to verify if the key event case is the issue with ARCCTR secondary key.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent

from BelfryCAD.tools.base import ToolCategory
from BelfryCAD.gui.tool_palette import ToolPalette
from BelfryCAD.tools import available_tools


class KeyCaseTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Key Event Case Test")
        self.setGeometry(100, 100, 600, 400)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create status label
        self.status_label = QLabel("Testing key event case handling...")
        layout.addWidget(self.status_label)

        # Get available tools
        self.available_tools = available_tools

        # Create tool definitions by instantiating tools temporarily
        arc_tool_definitions = []
        for tool_class in self.available_tools:
            try:
                temp_tool = tool_class(None, None, None)
                for definition in temp_tool.definitions:
                    if definition.category == ToolCategory.ARCS:
                        arc_tool_definitions.append(definition)
            except:
                pass  # Skip tools that can't be instantiated without proper params

        print(f"Found {len(arc_tool_definitions)} ARC tool definitions")

        # Create tool palette for ARCS
        self.arc_palette = ToolPalette(
            ToolCategory.ARCS,
            arc_tool_definitions,
            self.dummy_icon_loader
        )

        print(f"ARCS palette secondary key mappings: {self.arc_palette.secondary_key_mappings}")

        # Position palette
        self.arc_palette.show_at_position(self.mapToGlobal(self.rect().center()))

    def dummy_icon_loader(self, icon_name):
        """Dummy icon loader for testing"""
        from PySide6.QtGui import QIcon
        return QIcon()

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events and test case sensitivity"""
        key_text = event.text()
        key_text_upper = event.text().upper()

        print(f"Key pressed:")
        print(f"  event.text(): '{key_text}'")
        print(f"  event.text().upper(): '{key_text_upper}'")
        print(f"  event.key(): {event.key()}")
        print(f"  Qt key name: {Qt.Key(event.key()).name if hasattr(Qt.Key, 'name') else 'Unknown'}")

        # Test if the palette has focus
        print(f"  Palette has focus: {self.arc_palette.hasFocus()}")
        print(f"  Palette is visible: {self.arc_palette.isVisible()}")

        # Test if key is in mappings (case sensitive vs case insensitive)
        mappings = self.arc_palette.secondary_key_mappings
        print(f"  Key '{key_text}' in mappings: {key_text in mappings}")
        print(f"  Key '{key_text_upper}' in mappings: {key_text_upper in mappings}")

        if key_text_upper in mappings:
            tool_token = mappings[key_text_upper]
            print(f"  Would map to tool: {tool_token}")

        print("-" * 50)

        # Pass event to parent and palette
        if self.arc_palette.isVisible() and self.arc_palette.hasFocus():
            # Manually call the palette's key handler to test
            print("Manually calling palette keyPressEvent...")
            self.arc_palette.keyPressEvent(event)

        super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)

    window = KeyCaseTestWindow()
    window.show()

    print("Key case test window created.")
    print("Instructions:")
    print("1. Press 'C' (uppercase) to test")
    print("2. Press 'c' (lowercase) to test")
    print("3. Check console output for key event details")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
