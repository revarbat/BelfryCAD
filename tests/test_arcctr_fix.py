"""
Test to verify the ARCCTR secondary key fix works correctly.
"""

import sys
import os
# Adjust import path to work from the tests directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent

from BelfryCAD.tools.base import ToolCategory
from BelfryCAD.gui.tool_palette import ToolPalette
from BelfryCAD.tools import available_tools


class ARCCTRTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ARCCTR Secondary Key Fix Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create status label
        self.status_label = QLabel("Testing ARCCTR secondary key fix...")
        layout.addWidget(self.status_label)
        
        # Get available tools and create arc tool definitions
        arc_tool_definitions = []
        for tool_class in available_tools:
            try:
                temp_tool = tool_class(None, None, None)
                for definition in temp_tool.definitions:
                    if definition.category == ToolCategory.ARCS:
                        arc_tool_definitions.append(definition)
            except:
                pass  # Skip tools that can't be instantiated without proper params
        
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
        
        print(f"\nARCS palette secondary key mappings: {self.arc_palette.secondary_key_mappings}")
        
        # Position and show palette
        center_pos = self.mapToGlobal(self.rect().center())
        self.arc_palette.show_at_position(center_pos)
        
        print("\n" + "=" * 60)
        print("TESTING INSTRUCTIONS:")
        print("1. Press 'c' (lowercase) to test ARCCTR selection")
        print("2. Press 'C' (uppercase) to test ARCCTR selection")  
        print("3. Press 't' (lowercase) to test ARCTAN selection")
        print("4. Press '3' to test ARC3PT selection")
        print("5. Check console output for results")
        print("=" * 60)
        
    def dummy_icon_loader(self, icon_name):
        """Dummy icon loader for testing"""
        from PySide6.QtGui import QIcon
        return QIcon()
    
    def on_tool_selected(self, tool_token):
        """Handle tool selection"""
        message = f"✅ SUCCESS: Tool '{tool_token}' selected!"
        self.status_label.setText(message)
        print(f"\n{message}")
        
        # Also test the specific case we're fixing
        if tool_token == 'ARCCTR':
            print("🎉 ARCCTR secondary key 'C' is now working correctly!")
        
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events and forward to palette"""
        key_text = event.text()
        print(f"\nKey pressed: '{key_text}' (event.text())")
        print(f"Key pressed: '{key_text.upper()}' (event.text().upper())")
        print(f"Palette visible: {self.arc_palette.isVisible()}")
        print(f"Palette has focus: {self.arc_palette.hasFocus()}")
        
        # Forward the event to the palette if it's visible
        if self.arc_palette.isVisible():
            print("Forwarding key event to palette...")
            self.arc_palette.keyPressEvent(event)
        
        super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)
    
    window = ARCCTRTestWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()