#!/usr/bin/env python3
"""
Test script for ArrowLineItem with various arrowhead configurations.

This script demonstrates the ArrowLineItem class with:
- Different arrowhead combinations (none, start, end, both)
- Various line widths and colors
- Different line orientations
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox,
    QColorDialog, QGraphicsEllipseItem, QScrollArea, QTextEdit
)
from PySide6.QtCore import Qt, QPointF, QLineF, QRectF
from PySide6.QtGui import QPen, QBrush, QColor, QPainter, QFont

from BelfryCAD.gui.graphics_items.arrow_line_item import ArrowLineItem


class ArrowLineTestWindow(QMainWindow):
    """Test window for ArrowLineItem with various configurations."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ArrowLineItem Test")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        # Create graphics view and scene
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        
        # Set up the scene
        self.scene.setSceneRect(-100, -100, 200, 200)
        self.view.resetTransform()
        self.view.scale(1.0, -1.0)
        self.view.centerOn(0, 0)
        
        # Create control panel
        control_panel = self.create_control_panel()
        
        # Add widgets to layout
        layout.addWidget(self.view, 3)
        layout.addWidget(control_panel, 1)
        
        # Initialize test data
        self.arrow_lines = []
        self.endpoint_markers = []  # Store endpoint markers
        self.boundary_rect_item = None  # Store boundary rectangle display
        self.shape_outline_item = None  # Store shape outline display
        self.current_line = None
        
        # Create initial test lines
        self.create_test_lines()
        
        # Connect signals
        self.connect_signals()
    
    def create_control_panel(self):
        """Create the control panel for testing different configurations."""
        # Create scroll area for the control panel
        scroll_area = QScrollArea()
        scroll_area.setMaximumWidth(350)
        scroll_area.setWidgetResizable(True)
        
        # Create the main panel widget
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Title
        title = QLabel("Arrow Line Controls")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Arrow configuration
        arrow_group = QGroupBox("Arrow Configuration")
        arrow_layout = QVBoxLayout(arrow_group)
        
        self.start_arrow_check = QCheckBox("Start Arrow")
        arrow_layout.addWidget(self.start_arrow_check)
        
        self.end_arrow_check = QCheckBox("End Arrow")
        self.end_arrow_check.setChecked(True)
        arrow_layout.addWidget(self.end_arrow_check)
        
        layout.addWidget(arrow_group)
        
        # Line properties
        line_group = QGroupBox("Line Properties")
        line_layout = QVBoxLayout(line_group)
        
        # Line width
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Line Width:"))
        self.line_width_spin = QDoubleSpinBox()
        self.line_width_spin.setRange(0.1, 10.0)
        self.line_width_spin.setValue(2.0)
        self.line_width_spin.setSingleStep(0.1)
        self.line_width_spin.setSuffix(" px")
        width_layout.addWidget(self.line_width_spin)
        line_layout.addLayout(width_layout)
        
        # Line color
        self.line_color_button = QPushButton("Line Color")
        self.line_color_button.clicked.connect(self.choose_line_color)
        line_layout.addWidget(self.line_color_button)
        
        # Arrow color
        self.arrow_color_button = QPushButton("Arrow Color")
        self.arrow_color_button.clicked.connect(self.choose_arrow_color)
        line_layout.addWidget(self.arrow_color_button)
        
        # Line style
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("Line Style:"))
        self.line_style_combo = QComboBox()
        self.line_style_combo.addItems(["Solid", "Dash", "Dot", "DashDot", "DashDotDot"])
        style_layout.addWidget(self.line_style_combo)
        line_layout.addLayout(style_layout)
        
        # Dash pattern
        dash_layout = QHBoxLayout()
        dash_layout.addWidget(QLabel("Dash Pattern:"))
        self.dash_pattern_spin = QDoubleSpinBox()
        self.dash_pattern_spin.setRange(1.0, 20.0)
        self.dash_pattern_spin.setValue(5.0)
        self.dash_pattern_spin.setSuffix(" px")
        dash_layout.addWidget(self.dash_pattern_spin)
        line_layout.addLayout(dash_layout)
        
        layout.addWidget(line_group)
        
        # Line position
        position_group = QGroupBox("Line Position")
        position_layout = QVBoxLayout(position_group)
        
        # Start X
        start_x_layout = QHBoxLayout()
        start_x_layout.addWidget(QLabel("Start X:"))
        self.start_x_spin = QDoubleSpinBox()
        self.start_x_spin.setRange(-80, 80)
        self.start_x_spin.setValue(-50)
        start_x_layout.addWidget(self.start_x_spin)
        position_layout.addLayout(start_x_layout)
        
        # Start Y
        start_y_layout = QHBoxLayout()
        start_y_layout.addWidget(QLabel("Start Y:"))
        self.start_y_spin = QDoubleSpinBox()
        self.start_y_spin.setRange(-80, 80)
        self.start_y_spin.setValue(0)
        start_y_layout.addWidget(self.start_y_spin)
        position_layout.addLayout(start_y_layout)
        
        # End X
        end_x_layout = QHBoxLayout()
        end_x_layout.addWidget(QLabel("End X:"))
        self.end_x_spin = QDoubleSpinBox()
        self.end_x_spin.setRange(-80, 80)
        self.end_x_spin.setValue(50)
        end_x_layout.addWidget(self.end_x_spin)
        position_layout.addLayout(end_x_layout)
        
        # End Y
        end_y_layout = QHBoxLayout()
        end_y_layout.addWidget(QLabel("End Y:"))
        self.end_y_spin = QDoubleSpinBox()
        self.end_y_spin.setRange(-80, 80)
        self.end_y_spin.setValue(0)
        end_y_layout.addWidget(self.end_y_spin)
        position_layout.addLayout(end_y_layout)
        
        layout.addWidget(position_group)
        
        # Zoom controls
        zoom_group = QGroupBox("Zoom")
        zoom_layout = QVBoxLayout(zoom_group)
        
        # Zoom buttons
        zoom_buttons_layout = QHBoxLayout()
        
        self.zoom_in_button = QPushButton("Zoom In")
        self.zoom_in_button.clicked.connect(self.zoom_in)
        zoom_buttons_layout.addWidget(self.zoom_in_button)
        
        self.zoom_out_button = QPushButton("Zoom Out")
        self.zoom_out_button.clicked.connect(self.zoom_out)
        zoom_buttons_layout.addWidget(self.zoom_out_button)
        
        zoom_layout.addLayout(zoom_buttons_layout)
        
        # Reset zoom button
        self.reset_zoom_button = QPushButton("Reset Zoom")
        self.reset_zoom_button.clicked.connect(self.reset_zoom)
        zoom_layout.addWidget(self.reset_zoom_button)
        
        layout.addWidget(zoom_group)
        
        # Boundary and Shape Display
        info_group = QGroupBox("Item Information")
        info_layout = QVBoxLayout(info_group)
        
        # Show boundary button
        self.show_boundary_button = QPushButton("Show Boundary Rect")
        self.show_boundary_button.clicked.connect(self.show_boundary_rect)
        info_layout.addWidget(self.show_boundary_button)
        
        # Hide boundary button
        self.hide_boundary_button = QPushButton("Hide Boundary Rect")
        self.hide_boundary_button.clicked.connect(self.hide_boundary_rect)
        info_layout.addWidget(self.hide_boundary_button)
        
        # Show shape button
        self.show_shape_button = QPushButton("Show Shape")
        self.show_shape_button.clicked.connect(self.show_shape)
        info_layout.addWidget(self.show_shape_button)
        
        # Hide shape button
        self.hide_shape_button = QPushButton("Hide Shape")
        self.hide_shape_button.clicked.connect(self.hide_shape)
        info_layout.addWidget(self.hide_shape_button)
        
        layout.addWidget(info_group)
        
        # Action buttons
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        self.create_button = QPushButton("Create New Line")
        self.create_button.clicked.connect(self.create_new_line)
        actions_layout.addWidget(self.create_button)
        
        self.update_button = QPushButton("Update Current Line")
        self.update_button.clicked.connect(self.update_current_line)
        actions_layout.addWidget(self.update_button)
        
        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self.clear_all_lines)
        actions_layout.addWidget(self.clear_button)
        
        self.test_all_button = QPushButton("Test All Configurations")
        self.test_all_button.clicked.connect(self.test_all_configurations)
        actions_layout.addWidget(self.test_all_button)
        
        layout.addWidget(actions_group)
        
        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: green;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Set the panel as the scroll area widget
        scroll_area.setWidget(panel)
        return scroll_area
    
    def create_endpoint_markers(self, start_point: QPointF, end_point: QPointF, color: str = "red"):
        """Create small dots at the start and end points of a line."""
        marker_size = 3.0  # Size of the marker dots
        
        # Create start point marker
        start_marker = QGraphicsEllipseItem(
            start_point.x() - marker_size/2,
            start_point.y() - marker_size/2,
            marker_size, marker_size
        )
        start_marker.setBrush(QBrush(QColor(color)))
        start_marker.setPen(QPen(QColor("black"), 0.5))
        start_marker.setZValue(10)  # Ensure markers are on top
        self.scene.addItem(start_marker)
        
        # Create end point marker
        end_marker = QGraphicsEllipseItem(
            end_point.x() - marker_size/2,
            end_point.y() - marker_size/2,
            marker_size, marker_size
        )
        end_marker.setBrush(QBrush(QColor(color)))
        end_marker.setPen(QPen(QColor("black"), 0.5))
        end_marker.setZValue(10)  # Ensure markers are on top
        self.scene.addItem(end_marker)
        
        return [start_marker, end_marker]
    
    def connect_signals(self):
        """Connect control signals to update functions."""
        self.start_arrow_check.toggled.connect(self.update_current_line)
        self.end_arrow_check.toggled.connect(self.update_current_line)
        self.line_width_spin.valueChanged.connect(self.update_current_line)
        self.line_style_combo.currentTextChanged.connect(self.update_current_line)
        self.dash_pattern_spin.valueChanged.connect(self.update_current_line)
        self.start_x_spin.valueChanged.connect(self.update_current_line)
        self.start_y_spin.valueChanged.connect(self.update_current_line)
        self.end_x_spin.valueChanged.connect(self.update_current_line)
        self.end_y_spin.valueChanged.connect(self.update_current_line)
    
    def create_test_lines(self):
        """Create initial test arrow lines."""
        # Test line 1: Horizontal with end arrow
        start1, end1 = QPointF(-60, -40), QPointF(60, -40)
        line1 = ArrowLineItem(
            line=QLineF(start1, end1),
            start_arrow=False,
            end_arrow=True,
            pen=QPen(QColor("black"), 2.0)
        )
        self.scene.addItem(line1)
        self.arrow_lines.append(line1)
        markers1 = self.create_endpoint_markers(start1, end1, "black")
        self.endpoint_markers.extend(markers1)
        
        # Test line 2: Vertical with start arrow
        start2, end2 = QPointF(-40, -60), QPointF(-40, 60)
        line2 = ArrowLineItem(
            line=QLineF(start2, end2),
            start_arrow=True,
            end_arrow=False,
            pen=QPen(QColor("blue"), 1.5)
        )
        self.scene.addItem(line2)
        self.arrow_lines.append(line2)
        markers2 = self.create_endpoint_markers(start2, end2, "blue")
        self.endpoint_markers.extend(markers2)
        
        # Test line 3: Diagonal with both arrows
        start3, end3 = QPointF(-50, 50), QPointF(50, -50)
        line3 = ArrowLineItem(
            line=QLineF(start3, end3),
            start_arrow=True,
            end_arrow=True,
            pen=QPen(QColor("red"), 3.0)
        )
        self.scene.addItem(line3)
        self.arrow_lines.append(line3)
        markers3 = self.create_endpoint_markers(start3, end3, "red")
        self.endpoint_markers.extend(markers3)
        
        # Test line 4: No arrows
        start4, end4 = QPointF(-30, 30), QPointF(30, 30)
        line4 = ArrowLineItem(
            line=QLineF(start4, end4),
            start_arrow=False,
            end_arrow=False,
            pen=QPen(QColor("green"), 1.0)
        )
        self.scene.addItem(line4)
        self.arrow_lines.append(line4)
        markers4 = self.create_endpoint_markers(start4, end4, "green")
        self.endpoint_markers.extend(markers4)
        
        self.current_line = line1
        self.update_controls_from_line(line1)
        self.status_label.setText(f"Created {len(self.arrow_lines)} test lines")
    
    def update_controls_from_line(self, line: ArrowLineItem):
        """Update controls to reflect the current line's properties."""
        if not line:
            return
        
        # Update position controls
        line_geom = line.line()
        self.start_x_spin.setValue(line_geom.p1().x())
        self.start_y_spin.setValue(line_geom.p1().y())
        self.end_x_spin.setValue(line_geom.p2().x())
        self.end_y_spin.setValue(line_geom.p2().y())
        
        # Update arrow controls
        self.start_arrow_check.setChecked(line._start_arrow)
        self.end_arrow_check.setChecked(line._end_arrow)
        
        # Update line width
        self.line_width_spin.setValue(line.pen().widthF())
        
        # Update line style
        pen = line.pen()
        if pen.style() == Qt.PenStyle.SolidLine:
            self.line_style_combo.setCurrentText("Solid")
        elif pen.style() == Qt.PenStyle.DashLine:
            self.line_style_combo.setCurrentText("Dash")
        elif pen.style() == Qt.PenStyle.DotLine:
            self.line_style_combo.setCurrentText("Dot")
        elif pen.style() == Qt.PenStyle.DashDotLine:
            self.line_style_combo.setCurrentText("DashDot")
        elif pen.style() == Qt.PenStyle.DashDotDotLine:
            self.line_style_combo.setCurrentText("DashDotDot")
        
        # Update dash pattern (use first dash value if available)
        dash_pattern = pen.dashPattern()
        if dash_pattern:
            self.dash_pattern_spin.setValue(dash_pattern[0])
        else:
            self.dash_pattern_spin.setValue(5.0)
    
    def create_new_line(self):
        """Create a new arrow line with current settings."""
        # Calculate position for new line
        offset = len(self.arrow_lines) * 10
        start = QPointF(-30 + offset, 60 + offset)
        end = QPointF(30 + offset, 60 + offset)
        
        # Create new line
        new_line = ArrowLineItem(
            line=QLineF(start, end),
            start_arrow=self.start_arrow_check.isChecked(),
            end_arrow=self.end_arrow_check.isChecked(),
            pen=QPen(QColor("purple"), self.line_width_spin.value())
        )
        
        self.scene.addItem(new_line)
        self.arrow_lines.append(new_line)
        
        # Add endpoint markers
        markers = self.create_endpoint_markers(start, end, "purple")
        self.endpoint_markers.extend(markers)
        
        self.current_line = new_line
        
        self.status_label.setText(f"Created new line (total: {len(self.arrow_lines)})")
    
    def update_current_line(self):
        """Update the current line with new settings."""
        if not self.current_line:
            return
        
        # Get current settings
        start_arrow = self.start_arrow_check.isChecked()
        end_arrow = self.end_arrow_check.isChecked()
        line_width = self.line_width_spin.value()
        line_style = self.line_style_combo.currentText()
        dash_pattern = self.dash_pattern_spin.value()
        start_x = self.start_x_spin.value()
        start_y = self.start_y_spin.value()
        end_x = self.end_x_spin.value()
        end_y = self.end_y_spin.value()
        
        # Create pen with appropriate style
        pen = QPen(self.current_line.pen().color(), line_width)
        
        # Set line style
        if line_style == "Solid":
            pen.setStyle(Qt.PenStyle.SolidLine)
        elif line_style == "Dash":
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setDashPattern([dash_pattern, dash_pattern])
        elif line_style == "Dot":
            pen.setStyle(Qt.PenStyle.DotLine)
            pen.setDashPattern([1.0, dash_pattern])
        elif line_style == "DashDot":
            pen.setStyle(Qt.PenStyle.DashDotLine)
            pen.setDashPattern([dash_pattern, dash_pattern, 1.0, dash_pattern])
        elif line_style == "DashDotDot":
            pen.setStyle(Qt.PenStyle.DashDotDotLine)
            pen.setDashPattern([dash_pattern, dash_pattern, 1.0, dash_pattern, 1.0, dash_pattern])
        
        # Update the line
        self.current_line.setArrows(start_arrow, end_arrow)
        self.current_line.setPen(pen)
        self.current_line.setLine(QLineF(start_x, start_y, end_x, end_y))
        
        self.status_label.setText("Updated current line")
    
    def choose_line_color(self):
        """Open color dialog to choose line color."""
        if not self.current_line:
            return
        
        color = QColorDialog.getColor(self.current_line.pen().color(), self)
        if color.isValid():
            pen = self.current_line.pen()
            pen.setColor(color)
            self.current_line.setPen(pen)
            self.status_label.setText("Updated line color")
    
    def choose_arrow_color(self):
        """Open color dialog to choose arrow color."""
        if not self.current_line:
            return
        
        color = QColorDialog.getColor(self.current_line._arrow_brush.color(), self)
        if color.isValid():
            self.current_line.setArrowColor(color)
            self.status_label.setText("Updated arrow color")
    
    def zoom_in(self):
        """Zoom in on the graphics view."""
        self.view.scale(1.2, 1.2)
        self.status_label.setText("Zoomed in")
    
    def zoom_out(self):
        """Zoom out on the graphics view."""
        self.view.scale(0.833, 0.833)  # 1/1.2
        self.status_label.setText("Zoomed out")
    
    def reset_zoom(self):
        """Reset zoom to fit all items."""
        self.view.resetTransform()
        self.view.centerOn(0, 0)
        self.status_label.setText("Reset zoom")
    
    def show_boundary_rect(self):
        """Display the boundary rectangle of the current line visually."""
        if not self.current_line:
            self.status_label.setText("No line selected")
            return
        
        # Remove existing boundary display
        self.hide_boundary_rect()
        
        # Get the boundary rectangle
        boundary = self.current_line.boundingRect()
        
        # Create a rectangle item to display the boundary
        from PySide6.QtWidgets import QGraphicsRectItem
        self.boundary_rect_item = QGraphicsRectItem(boundary)
        self.boundary_rect_item.setPen(QPen(QColor("red"), 2.0, Qt.PenStyle.DashLine))
        self.boundary_rect_item.setBrush(QBrush(QColor(255, 0, 0, 30)))  # Semi-transparent red
        self.boundary_rect_item.setZValue(5)  # Above lines but below markers
        
        # Position the rectangle relative to the line
        self.boundary_rect_item.setPos(self.current_line.pos())
        
        self.scene.addItem(self.boundary_rect_item)
        self.status_label.setText("Displayed boundary rectangle")
    
    def hide_boundary_rect(self):
        """Hide the boundary rectangle display."""
        if self.boundary_rect_item:
            self.scene.removeItem(self.boundary_rect_item)
            self.boundary_rect_item = None
            self.status_label.setText("Hidden boundary rectangle")
    
    def show_shape(self):
        """Display the shape outline of the current line visually."""
        if not self.current_line:
            self.status_label.setText("No line selected")
            return
        
        # Remove existing shape display
        self.hide_shape()
        
        # Get the shape
        shape = self.current_line.shape()
        
        # Create a path item to display the shape
        from PySide6.QtWidgets import QGraphicsPathItem
        self.shape_outline_item = QGraphicsPathItem(shape)
        self.shape_outline_item.setPen(QPen(QColor("blue"), 1.5, Qt.PenStyle.DotLine))
        self.shape_outline_item.setBrush(QBrush(QColor(0, 0, 255, 20)))  # Semi-transparent blue
        self.shape_outline_item.setZValue(4)  # Above lines but below boundary rect
        
        # Position the shape relative to the line
        self.shape_outline_item.setPos(self.current_line.pos())
        
        self.scene.addItem(self.shape_outline_item)
        self.status_label.setText("Displayed shape outline")
    
    def hide_shape(self):
        """Hide the shape outline display."""
        if self.shape_outline_item:
            self.scene.removeItem(self.shape_outline_item)
            self.shape_outline_item = None
            self.status_label.setText("Hidden shape outline")
    
    def clear_all_lines(self):
        """Clear all arrow lines from the scene."""
        for line in self.arrow_lines:
            self.scene.removeItem(line)
        self.arrow_lines.clear()
        
        # Clear endpoint markers
        for marker in self.endpoint_markers:
            self.scene.removeItem(marker)
        self.endpoint_markers.clear()
        
        # Clear visual displays
        self.hide_boundary_rect()
        self.hide_shape()
        
        self.current_line = None
        self.status_label.setText("Cleared all lines")
    
    def test_all_configurations(self):
        """Test all arrow configurations."""
        self.clear_all_lines()
        
        # Test configurations
        test_configs = [
            # (start, end, start_arrow, end_arrow, color, width, style, description)
            (QPointF(-60, -60), QPointF(60, -60), False, False, "black", 1.0, "Solid", "No arrows"),
            (QPointF(-60, -40), QPointF(60, -40), True, False, "blue", 1.5, "Solid", "Start arrow only"),
            (QPointF(-60, -20), QPointF(60, -20), False, True, "red", 2.0, "Dash", "End arrow only"),
            (QPointF(-60, 0), QPointF(60, 0), True, True, "green", 2.5, "Dot", "Both arrows"),
            (QPointF(-60, 20), QPointF(60, 20), False, False, "purple", 3.0, "DashDot", "Thick line"),
            (QPointF(-60, 40), QPointF(60, 40), True, True, "orange", 0.5, "DashDotDot", "Thin line"),
        ]
        
        for i, (start, end, start_arrow, end_arrow, color, width, style, desc) in enumerate(test_configs):
            # Create pen with appropriate style
            pen = QPen(QColor(color), width)
            
            # Set line style
            if style == "Solid":
                pen.setStyle(Qt.PenStyle.SolidLine)
            elif style == "Dash":
                pen.setStyle(Qt.PenStyle.DashLine)
                pen.setDashPattern([5.0, 5.0])
            elif style == "Dot":
                pen.setStyle(Qt.PenStyle.DotLine)
                pen.setDashPattern([1.0, 5.0])
            elif style == "DashDot":
                pen.setStyle(Qt.PenStyle.DashDotLine)
                pen.setDashPattern([5.0, 5.0, 1.0, 5.0])
            elif style == "DashDotDot":
                pen.setStyle(Qt.PenStyle.DashDotDotLine)
                pen.setDashPattern([5.0, 5.0, 1.0, 5.0, 1.0, 5.0])
            
            line = ArrowLineItem(
                line=QLineF(start, end),
                start_arrow=start_arrow,
                end_arrow=end_arrow,
                pen=pen
            )
            self.scene.addItem(line)
            self.arrow_lines.append(line)
            
            # Add endpoint markers
            markers = self.create_endpoint_markers(start, end, color)
            self.endpoint_markers.extend(markers)
        
        self.current_line = self.arrow_lines[0] if self.arrow_lines else None
        if self.current_line:
            self.update_controls_from_line(self.current_line)
        
        self.status_label.setText(f"Created {len(self.arrow_lines)} test configurations")


def main():
    """Main function to run the test application."""
    app = QApplication(sys.argv)
    
    # Create and show the test window
    window = ArrowLineTestWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 