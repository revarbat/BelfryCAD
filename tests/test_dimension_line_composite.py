#!/usr/bin/env python3
"""
Test script for DimensionLineComposite with view scaling of 128/2.54 and Y axis reversed.

This script tests the DimensionLineComposite graphics item with:
- View scaling: 128/2.54 (approximately 50.39)
- Y axis reversed (flipped)
- Various dimension line orientations and configurations
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox
)
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QTransform
from PySide6.QtGui import QPainter

from BelfryCAD.gui.graphics_items.dimension_line_composite import (
    DimensionLineComposite, DimensionLineOrientation
)


class DimensionLineTestWindow(QMainWindow):
    """Test window for DimensionLineComposite with scaling and Y axis reversal."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DimensionLineComposite Test - Scaled View (128/2.54) with Y Reversed")
        self.setGeometry(100, 100, 1200, 800)
        
        # View scaling factor
        self.scale_factor = 128.0 / 2.54  # Approximately 50.39
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        # Create graphics view and scene
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        
        # Apply scaling and Y axis reversal
        self.apply_view_transformation()
        
        # Create control panel
        control_panel = self.create_control_panel()
        
        # Add widgets to layout
        layout.addWidget(self.view, 3)
        layout.addWidget(control_panel, 1)
        
        # Initialize test data
        self.dimension_lines = []
        self.current_line = None
        
        # Create initial test dimension lines
        self.create_test_dimension_lines()
        
        # Connect signals
        self.connect_signals()
    
    def apply_view_transformation(self):
        """Apply the view scaling and Y axis reversal transformation."""
        # Create transform for scaling and Y axis reversal
        transform = QTransform()
        
        # Scale the view
        transform.scale(self.scale_factor, self.scale_factor)
        
        # Reverse Y axis (flip vertically)
        transform.scale(1, -1)
        
        # Apply the transform to the view
        self.view.setTransform(transform)
        
        # Set scene rect to show the transformed coordinates
        # The scene will show coordinates in the original scale
        self.scene.setSceneRect(-100, -100, 200, 200)
        
        # Center the view
        self.view.centerOn(0, 0)
    
    def create_control_panel(self):
        """Create the control panel for testing different configurations."""
        panel = QWidget()
        panel.setMaximumWidth(300)
        layout = QVBoxLayout(panel)
        
        # Title
        title = QLabel("Dimension Line Controls")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Scale info
        scale_info = QLabel(f"View Scale: {self.scale_factor:.2f}\nY Axis: Reversed")
        scale_info.setStyleSheet("color: blue;")
        layout.addWidget(scale_info)
        
        # Orientation control
        orientation_group = QGroupBox("Orientation")
        orientation_layout = QVBoxLayout(orientation_group)
        
        self.orientation_combo = QComboBox()
        self.orientation_combo.addItems([
            "ANGLED", "HORIZONTAL", "VERTICAL"
        ])
        orientation_layout.addWidget(QLabel("Orientation:"))
        orientation_layout.addWidget(self.orientation_combo)
        
        layout.addWidget(orientation_group)
        
        # Parameters control
        params_group = QGroupBox("Parameters")
        params_layout = QVBoxLayout(params_group)
        
        # Extension
        self.extension_spin = QDoubleSpinBox()
        self.extension_spin.setRange(0, 50)
        self.extension_spin.setValue(10)
        self.extension_spin.setSuffix(" units")
        params_layout.addWidget(QLabel("Extension:"))
        params_layout.addWidget(self.extension_spin)
        
        # Excess
        self.excess_spin = QDoubleSpinBox()
        self.excess_spin.setRange(0, 20)
        self.excess_spin.setValue(5)
        self.excess_spin.setSuffix(" units")
        params_layout.addWidget(QLabel("Excess:"))
        params_layout.addWidget(self.excess_spin)
        
        # Gap
        self.gap_spin = QDoubleSpinBox()
        self.gap_spin.setRange(0, 20)
        self.gap_spin.setValue(5)
        self.gap_spin.setSuffix(" units")
        params_layout.addWidget(QLabel("Gap:"))
        params_layout.addWidget(self.gap_spin)
        
        layout.addWidget(params_group)
        
        # Text control
        text_group = QGroupBox("Text")
        text_layout = QVBoxLayout(text_group)
        
        self.show_text_check = QCheckBox("Show Text")
        self.show_text_check.setChecked(True)
        text_layout.addWidget(self.show_text_check)
        
        self.opposite_side_check = QCheckBox("Opposite Side")
        text_layout.addWidget(self.opposite_side_check)
        
        layout.addWidget(text_group)
        
        # Action buttons
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        self.create_button = QPushButton("Create New Dimension")
        self.create_button.clicked.connect(self.create_new_dimension)
        actions_layout.addWidget(self.create_button)
        
        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self.clear_all_dimensions)
        actions_layout.addWidget(self.clear_button)
        
        self.test_all_button = QPushButton("Test All Orientations")
        self.test_all_button.clicked.connect(self.test_all_orientations)
        actions_layout.addWidget(self.test_all_button)
        
        layout.addWidget(actions_group)
        
        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: green;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        return panel
    
    def connect_signals(self):
        """Connect control signals to update functions."""
        self.orientation_combo.currentTextChanged.connect(self.update_current_dimension)
        self.extension_spin.valueChanged.connect(self.update_current_dimension)
        self.excess_spin.valueChanged.connect(self.update_current_dimension)
        self.gap_spin.valueChanged.connect(self.update_current_dimension)
        self.show_text_check.toggled.connect(self.update_current_dimension)
        self.opposite_side_check.toggled.connect(self.update_current_dimension)
    
    def create_test_dimension_lines(self):
        """Create initial test dimension lines."""
        # Test line 1: Horizontal dimension
        start1 = QPointF(-4, -3)
        end1 = QPointF(4, -3)
        dim1 = DimensionLineComposite(
            start_point=start1,
            end_point=end1,
            extension=1.0,
            orientation=DimensionLineOrientation.HORIZONTAL,
            excess=0.5,
            gap=0.5,
            show_text=False,
            text_format_callback=lambda d: f"{d:.1f}mm"
        )
        dim1.setPen(QPen(QColor("black"), 0.1))
        self.scene.addItem(dim1)
        self.dimension_lines.append(dim1)
        
        # Test line 2: Vertical dimension
        start2 = QPointF(5, -4)
        end2 = QPointF(5, 4)
        dim2 = DimensionLineComposite(
            start_point=start2,
            end_point=end2,
            extension=1.0,
            orientation=DimensionLineOrientation.VERTICAL,
            excess=0.5,
            gap=0.5,
            show_text=False,
            text_format_callback=lambda d: f"{d:.1f}mm"
        )
        dim2.setPen(QPen(QColor("black"), 0.1))
        self.scene.addItem(dim2)
        self.dimension_lines.append(dim2)
        
        # Test line 3: Angled dimension
        start3 = QPointF(-3, 3)
        end3 = QPointF(3, -3)
        dim3 = DimensionLineComposite(
            start_point=start3,
            end_point=end3,
            extension=1.0,
            orientation=DimensionLineOrientation.ANGLED,
            excess=0.5,
            gap=0.5,
            show_text=False,
            text_format_callback=lambda d: f"{d:.1f}mm"
        )
        dim3.setPen(QPen(QColor("black"), 0.1))
        self.scene.addItem(dim3)
        self.dimension_lines.append(dim3)
        
        # Test line 4: Opposite side
        start4 = QPointF(-2, 5)
        end4 = QPointF(2, 5)
        dim4 = DimensionLineComposite(
            start_point=start4,
            end_point=end4,
            extension=1.0,
            orientation=DimensionLineOrientation.HORIZONTAL,
            excess=0.5,
            gap=0.5,
            show_text=False,
            opposite_side=True,
            text_format_callback=lambda d: f"{d:.1f}mm"
        )
        dim4.setPen(QPen(QColor("black"), 0.1))
        self.scene.addItem(dim4)
        self.dimension_lines.append(dim4)
        
        self.current_line = dim1
        self.status_label.setText(f"Created {len(self.dimension_lines)} test dimension lines")
    
    def create_new_dimension(self):
        """Create a new dimension line with current settings."""
        # Calculate position for new dimension
        offset = len(self.dimension_lines) * 20
        start = QPointF(-30 + offset, 60 + offset)
        end = QPointF(30 + offset, 60 + offset)
        
        # Get current settings
        orientation_text = self.orientation_combo.currentText()
        orientation = DimensionLineOrientation[orientation_text]
        
        # Create new dimension line
        new_dim = DimensionLineComposite(
            start_point=start,
            end_point=end,
            extension=self.extension_spin.value(),
            orientation=orientation,
            excess=self.excess_spin.value(),
            gap=self.gap_spin.value(),
            show_text=self.show_text_check.isChecked(),
            opposite_side=self.opposite_side_check.isChecked(),
            text_format_callback=lambda d: f"{d:.1f}mm"
        )
        
        self.scene.addItem(new_dim)
        self.dimension_lines.append(new_dim)
        self.current_line = new_dim
        
        self.status_label.setText(f"Created new dimension line (total: {len(self.dimension_lines)})")
    
    def update_current_dimension(self):
        """Update the current dimension line with new settings."""
        if not self.current_line:
            return
        
        # Get current settings
        orientation_text = self.orientation_combo.currentText()
        orientation = DimensionLineOrientation[orientation_text]
        
        # Remove current line from scene
        self.scene.removeItem(self.current_line)
        
        # Create new line with updated settings
        new_dim = DimensionLineComposite(
            start_point=self.current_line._start_point,
            end_point=self.current_line._end_point,
            extension=self.extension_spin.value(),
            orientation=orientation,
            excess=self.excess_spin.value(),
            gap=self.gap_spin.value(),
            show_text=self.show_text_check.isChecked(),
            opposite_side=self.opposite_side_check.isChecked(),
            text_format_callback=lambda d: f"{d:.1f}mm"
        )
        
        # Add new line to scene
        self.scene.addItem(new_dim)
        
        # Replace in list
        index = self.dimension_lines.index(self.current_line)
        self.dimension_lines[index] = new_dim
        self.current_line = new_dim
        
        self.status_label.setText("Updated current dimension line")
    
    def clear_all_dimensions(self):
        """Clear all dimension lines from the scene."""
        for dim in self.dimension_lines:
            self.scene.removeItem(dim)
        self.dimension_lines.clear()
        self.current_line = None
        self.status_label.setText("Cleared all dimension lines")
    
    def test_all_orientations(self):
        """Test all orientations with different configurations."""
        self.clear_all_dimensions()
        
        # Test configurations
        test_configs = [
            # (start, end, orientation, opposite_side, description)
            (QPointF(-4, -4), QPointF(4, -4), DimensionLineOrientation.HORIZONTAL, False, "Horizontal"),
            (QPointF(5, -5), QPointF(5, 5), DimensionLineOrientation.VERTICAL, False, "Vertical"),
            (QPointF(-3, 3), QPointF(3, -3), DimensionLineOrientation.ANGLED, False, "Angled"),
            (QPointF(-4, 4), QPointF(4, 4), DimensionLineOrientation.HORIZONTAL, True, "Horizontal Opposite"),
            (QPointF(-5, -5), QPointF(5, 5), DimensionLineOrientation.VERTICAL, True, "Vertical Opposite"),
            (QPointF(-2.5, -2.5), QPointF(2.5, 2.5), DimensionLineOrientation.ANGLED, True, "Angled Opposite"),
        ]
        
        for i, (start, end, orientation, opposite, desc) in enumerate(test_configs):
            dim = DimensionLineComposite(
                start_point=start,
                end_point=end,
                extension=8.0,
                orientation=orientation,
                excess=3.0,
                gap=3.0,
                show_text=False,
                opposite_side=opposite,
                text_format_callback=lambda d: f"{d:.1f}mm"
            )
            self.scene.addItem(dim)
            self.dimension_lines.append(dim)
        
        self.current_line = self.dimension_lines[0] if self.dimension_lines else None
        self.status_label.setText(f"Created {len(self.dimension_lines)} test configurations")


def main():
    """Main function to run the test application."""
    app = QApplication(sys.argv)
    
    # Create and show the test window
    window = DimensionLineTestWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 