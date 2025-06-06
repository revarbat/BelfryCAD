#!/usr/bin/env python3
"""
Debug script to test ARCCTR secondary key functionality.
This script will create a minimal test to verify the key event handling.
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


class DebugWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ARCCTR Secondary Key Debug")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create status label
        self.status_label = QLabel("Press 'A' to show ARCS palette, then 'C' for ARCCTR")
        layout.addWidget(self.status_label)

        # Get available tools
        self.available_tools = available_tools

        # Create tool definitions by instantiating tools temporarily
        arc_tool_definitions = []
        for tool_class in self.available_tools:
            # Create a temporary instance to get definitions
            temp_tool = tool_class(None, None, None)
            for definition in temp_tool.definitions:
                if definition.category == ToolCategory.ARCS:
                    arc_tool_definitions.append(definition)

        print(f"Found {len(arc_tool_definitions)} ARC tool definitions:")
        for definition in arc_tool_definitions:
            print(f"  - {definition.token}: {definition.name}")

        # Create tool palette for ARCS
        self.arc_palette = ToolPalette(
            ToolCategory.ARCS,
            arc_tool_definitions,
            self.dummy_icon_loader
        )

        # Connect palette signal
        self.arc_palette.tool_selected.connect(self.on_tool_selected)

        print(f"ARCS palette secondary key mappings: {self.arc_palette.secondary_key_mappings}")

    def dummy_icon_loader(self, icon_name):
        """Dummy icon loader for testing"""
        from PySide6.QtGui import QIcon
        return QIcon()

    def on_tool_selected(self, tool_token):
        """Handle tool selection"""
        self.status_label.setText(f"Tool selected: {tool_token}")
        print(f"Tool selected: {tool_token}")

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events"""
        key_text = event.text().upper()
        print(f"Key pressed: '{key_text}' (Qt key: {event.key()})")

        if key_text == 'A':
            # Show ARCS palette
            print("Showing ARCS palette")
            self.status_label.setText("ARCS palette shown - Press 'C' for ARCCTR")

            # Position palette at center of window
            center = self.rect().center()
            global_pos = self.mapToGlobal(center)
            self.arc_palette.show_at_position(global_pos)

            # Give focus to the palette
            self.arc_palette.setFocus()
            print(f"Palette focus: {self.arc_palette.hasFocus()}")

        elif key_text == 'C' and self.arc_palette.isVisible():
            # Test direct key handling
            print("Testing direct 'C' key for ARCCTR")
            if 'C' in self.arc_palette.secondary_key_mappings:
                tool_token = self.arc_palette.secondary_key_mappings['C']
                print(f"'C' maps to: {tool_token}")
                self.on_tool_selected(tool_token)
            else:
                print("'C' not found in secondary key mappings")

        # Pass event to parent
        super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)

    window = DebugWindow()
    window.show()

    print("Debug window created. Instructions:")
    print("1. Press 'A' to show ARCS palette")
    print("2. Press 'C' to select ARCCTR tool")
    print("3. Check console output for debugging info")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
