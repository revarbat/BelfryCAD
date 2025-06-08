#!/usr/bin/env python3
"""
Comprehensive test script to verify all cursor types are mapped correctly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor

from BelfryCAD.tools.base import ToolDefinition, Tool


class TestTool(Tool):
    """Test tool for cursor testing"""

    def __init__(self, scene, cursor_name):
        self.cursor_name = cursor_name
        super().__init__(scene, None, None)

    def _get_definition(self):
        return [ToolDefinition(
            token="TEST",
            name="Test Tool",
            category=None,
            cursor=self.cursor_name
        )]


def test_all_cursors():
    """Test various cursor types"""
    app = QApplication(sys.argv)

    scene = QGraphicsScene()
    view = QGraphicsView(scene)

    # Test different cursor types
    cursor_tests = [
        ("arrow", Qt.CursorShape.ArrowCursor),
        ("crosshair", Qt.CursorShape.CrossCursor),
        ("text", Qt.CursorShape.IBeamCursor),  # "text" should map to IBeamCursor
        ("pointing", Qt.CursorShape.PointingHandCursor),
        ("wait", Qt.CursorShape.WaitCursor),
        ("invalid_cursor", Qt.CursorShape.CrossCursor),  # Should fallback to default
    ]

    print("Testing cursor mappings...")
    print("=" * 50)

    for cursor_name, expected_shape in cursor_tests:
        tool = TestTool(scene, cursor_name)
        tool.activate()

        actual_shape = view.cursor().shape()
        status = "✓ PASS" if actual_shape == expected_shape else "✗ FAIL"

        print(f"{status} Cursor '{cursor_name}': {actual_shape} (expected: {expected_shape})")

        tool.deactivate()

    print("=" * 50)
    print("Cursor mapping test completed!")


if __name__ == "__main__":
    test_all_cursors()
