"""
G-Code Backtracer Dialog

This module provides a dialog for analyzing and visualizing G-code files.
"""

import os
from typing import Optional, Dict
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QTextEdit, QGroupBox, QScrollArea, QWidget,
    QGraphicsView, QGraphicsScene, QGraphicsPathItem, QGraphicsItem,
    QGraphicsEllipseItem, QComboBox
)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath, QBrush

from ...mlcnc.gcode_backtracer import GCodeBacktracer, GCodeCommand


class ToolPathView(QGraphicsView):
    """Graphics view for displaying G-code tool paths."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setBackgroundBrush(QColor(240, 240, 240))

    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming."""
        zoom_factor = 1.15
        if event.angleDelta().y() < 0:
            zoom_factor = 1.0 / zoom_factor
        self.scale(zoom_factor, zoom_factor)


class GCodeBacktracerDialog(QDialog):
    """Dialog for analyzing and visualizing G-code files."""

    # Tool colors for different tools
    TOOL_COLORS = [
        QColor(0, 0, 255),    # Blue
        QColor(0, 128, 0),    # Green
        QColor(255, 0, 0),    # Red
        QColor(128, 0, 128),  # Purple
        QColor(0, 128, 128),  # Teal
        QColor(128, 128, 0),  # Olive
        QColor(255, 128, 0),  # Orange
        QColor(128, 0, 0),    # Maroon
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("G-Code Backtracer")
        self.setMinimumSize(1000, 800)
        self.backtracer = GCodeBacktracer()
        self._setup_ui()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QHBoxLayout()

        # Left panel
        left_panel = QVBoxLayout()

        # File selection
        file_group = QGroupBox("G-Code File")
        file_layout = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self._browse_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.browse_button)
        file_group.setLayout(file_layout)
        left_panel.addWidget(file_group)

        # Statistics
        stats_group = QGroupBox("Program Statistics")
        stats_layout = QVBoxLayout()
        self.bounds_label = QLabel("Bounds: Not loaded")
        self.tool_changes_label = QLabel("Tool Changes: Not loaded")
        self.machining_time_label = QLabel("Estimated Time: Not loaded")
        stats_layout.addWidget(self.bounds_label)
        stats_layout.addWidget(self.tool_changes_label)
        stats_layout.addWidget(self.machining_time_label)
        stats_group.setLayout(stats_layout)
        left_panel.addWidget(stats_group)

        # Z-level selection
        z_group = QGroupBox("Z-Level")
        z_layout = QVBoxLayout()
        self.z_combo = QComboBox()
        self.z_combo.currentIndexChanged.connect(self._on_z_level_changed)
        z_layout.addWidget(self.z_combo)
        z_group.setLayout(z_layout)
        left_panel.addWidget(z_group)

        # G-code preview
        preview_group = QGroupBox("G-Code Preview")
        preview_layout = QVBoxLayout()
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)
        preview_group.setLayout(preview_layout)
        left_panel.addWidget(preview_group)

        # Buttons
        button_layout = QHBoxLayout()
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        left_panel.addLayout(button_layout)

        # Add left panel to main layout
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMaximumWidth(400)
        layout.addWidget(left_widget)

        # Right panel - Tool path visualization
        right_panel = QVBoxLayout()
        path_group = QGroupBox("Tool Path Visualization")
        path_layout = QVBoxLayout()

        # Create graphics scene and view
        self.scene = QGraphicsScene()
        self.view = ToolPathView()
        self.view.setScene(self.scene)
        path_layout.addWidget(self.view)

        path_group.setLayout(path_layout)
        right_panel.addWidget(path_group)

        # Add right panel to main layout
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        layout.addWidget(right_widget)

        self.setLayout(layout)

    def _browse_file(self):
        """Open file dialog to select G-code file."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open G-Code File",
            "",
            "G-Code Files (*.gcode *.nc *.cnc *.tap);;All Files (*.*)"
        )
        if filename:
            self._load_file(filename)

    def _load_file(self, filename: str):
        """Load and analyze G-code file."""
        try:
            # Load file
            self.backtracer.parse_file(filename)
            self.file_label.setText(os.path.basename(filename))

            # Update statistics
            bounds = self.backtracer.get_bounds()
            self.bounds_label.setText(
                f"Bounds: X({bounds['min_x']:.3f}, {bounds['max_x']:.3f}) "
                f"Y({bounds['min_y']:.3f}, {bounds['max_y']:.3f}) "
                f"Z({bounds['min_z']:.3f}, {bounds['max_z']:.3f})"
            )

            tool_changes = self.backtracer.get_tool_changes()
            self.tool_changes_label.setText(
                f"Tool Changes: {len(tool_changes)}"
            )

            machining_time = self.backtracer.get_machining_time()
            self.machining_time_label.setText(
                f"Estimated Time: {machining_time:.1f} minutes"
            )

            # Update Z-level combo box
            self.z_combo.clear()
            for z in self.backtracer.get_z_levels():
                self.z_combo.addItem(f"Z = {z:.3f}", z)

            # Load preview
            with open(filename, 'r') as f:
                self.preview_text.setText(f.read())

            # Draw tool path
            self._draw_tool_path()

        except Exception as e:
            self.file_label.setText("Error loading file")
            self.bounds_label.setText("Bounds: Error")
            self.tool_changes_label.setText("Tool Changes: Error")
            self.machining_time_label.setText("Estimated Time: Error")
            self.preview_text.setText(f"Error loading file: {str(e)}")

    def _on_z_level_changed(self, index: int):
        """Handle Z-level selection change."""
        if index >= 0:
            self._draw_tool_path()

    def _get_tool_color(self, tool_number: int) -> QColor:
        """Get color for a tool number."""
        return self.TOOL_COLORS[tool_number % len(self.TOOL_COLORS)]

    def _draw_tool_path(self):
        """Draw the tool path in the graphics view."""
        self.scene.clear()

        # Get current Z-level
        current_z = self.z_combo.currentData()
        if current_z is None:
            return

        # Create paths for each tool
        tool_paths: Dict[int, QPainterPath] = {}
        tool_feed_rates: Dict[int, float] = {}

        # Track current position and tool
        current_x = 0.0
        current_y = 0.0
        current_z = 0.0
        current_tool = 0

        # Draw each operation
        for op in self.backtracer.get_operations():
            if op.command in [GCodeCommand.RAPID_MOVE,
                            GCodeCommand.LINEAR_MOVE,
                            GCodeCommand.ARC_CW,
                            GCodeCommand.ARC_CCW]:
                # Update current position
                if op.point.x is not None:
                    current_x = op.point.x
                if op.point.y is not None:
                    current_y = op.point.y
                if op.point.z is not None:
                    current_z = op.point.z

                # Update current tool
                if op.tool_number is not None:
                    current_tool = op.tool_number

                # Only draw moves at current Z-level
                if abs(current_z - self.z_combo.currentData()) < 0.001:
                    # Get or create path for current tool
                    if current_tool not in tool_paths:
                        tool_paths[current_tool] = QPainterPath()
                        tool_paths[current_tool].setFillRule(Qt.FillRule.OddEvenFill)

                    # Add to path
                    if tool_paths[current_tool].isEmpty():
                        tool_paths[current_tool].moveTo(current_x, current_y)
                    else:
                        if op.command == GCodeCommand.RAPID_MOVE:
                            # Draw rapid move line
                            tool_paths[current_tool].moveTo(current_x, current_y)
                        else:
                            # Draw cutting move line
                            tool_paths[current_tool].lineTo(current_x, current_y)
                            # Store feed rate for this tool
                            if op.feed_rate is not None:
                                tool_feed_rates[current_tool] = op.feed_rate

        # Create path items for each tool
        for tool, path in tool_paths.items():
            # Create path item
            path_item = QGraphicsPathItem(path)
            color = self._get_tool_color(tool)

            # Set pen based on feed rate
            feed_rate = tool_feed_rates.get(tool, 0.0)
            pen_width = 1.0 + (feed_rate / 1000.0)  # Scale pen width with feed rate
            path_item.setPen(QPen(color, pen_width))

            self.scene.addItem(path_item)

        # Draw tool change markers
        for tool, line_num, z in self.backtracer.get_tool_changes():
            if abs(z - self.z_combo.currentData()) < 0.001:
                # Find the operation at this line number
                for op in self.backtracer.get_operations():
                    if op.line_number == line_num:
                        # Draw tool change marker
                        marker = QGraphicsEllipseItem(
                            op.point.x - 2, op.point.y - 2, 4, 4
                        )
                        marker.setBrush(QBrush(self._get_tool_color(tool)))
                        marker.setPen(QPen(Qt.PenStyle.NoPen))
                        self.scene.addItem(marker)
                        break

        # Fit view to scene
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)