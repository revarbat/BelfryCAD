"""
CNC Tool Specification Dialog

This module provides a dialog for creating and editing ToolSpecification objects.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox,
    QSpinBox, QComboBox, QPushButton, QCheckBox, QGroupBox
)
from PySide6.QtCore import Qt

from ...mlcnc.cutting_params import (
    ToolSpecification, ToolGeometry, ToolMaterial, ToolCoating
)


class ToolSpecDialog(QDialog):
    """Dialog for editing tool specifications."""

    def __init__(self, tool_spec: Optional[ToolSpecification] = None, parent=None):
        super().__init__(parent)
        self.tool_spec = tool_spec or ToolSpecification(
            diameter=0.5,
            length=3.0,
            flute_count=2
        )
        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Tool Specification")
        layout = QVBoxLayout()

        # Basic parameters
        basic_group = QGroupBox("Basic Parameters")
        basic_layout = QVBoxLayout()

        # Diameter
        diameter_layout = QHBoxLayout()
        diameter_layout.addWidget(QLabel("Diameter (inches):"))
        self.diameter_spin = QDoubleSpinBox()
        self.diameter_spin.setRange(0.001, 10.0)
        self.diameter_spin.setDecimals(3)
        self.diameter_spin.setSingleStep(0.001)
        self.diameter_spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        diameter_layout.addWidget(self.diameter_spin)
        basic_layout.addLayout(diameter_layout)

        # Length
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel("Length (inches):"))
        self.length_spin = QDoubleSpinBox()
        self.length_spin.setRange(0.1, 20.0)
        self.length_spin.setDecimals(2)
        self.length_spin.setSingleStep(0.1)
        self.length_spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        length_layout.addWidget(self.length_spin)
        basic_layout.addLayout(length_layout)

        # Flute count
        flutes_layout = QHBoxLayout()
        flutes_layout.addWidget(QLabel("Number of Flutes:"))
        self.flutes_spin = QSpinBox()
        self.flutes_spin.setRange(1, 99)
        self.flutes_spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        flutes_layout.addWidget(self.flutes_spin)
        basic_layout.addLayout(flutes_layout)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # Tool properties
        props_group = QGroupBox("Tool Properties")
        props_layout = QVBoxLayout()

        # Geometry
        geometry_layout = QHBoxLayout()
        geometry_layout.addWidget(QLabel("Geometry:"))
        self.geometry_combo = QComboBox()
        self.geometry_combo.addItems([g.value for g in ToolGeometry])
        geometry_layout.addWidget(self.geometry_combo)
        props_layout.addLayout(geometry_layout)

        # Material
        material_layout = QHBoxLayout()
        material_layout.addWidget(QLabel("Material:"))
        self.material_combo = QComboBox()
        self.material_combo.addItems([m.value for m in ToolMaterial])
        material_layout.addWidget(self.material_combo)
        props_layout.addLayout(material_layout)

        # Coating
        coating_layout = QHBoxLayout()
        coating_layout.addWidget(QLabel("Coating:"))
        self.coating_combo = QComboBox()
        self.coating_combo.addItems([c.value for c in ToolCoating])
        coating_layout.addWidget(self.coating_combo)
        props_layout.addLayout(coating_layout)

        props_group.setLayout(props_layout)
        layout.addWidget(props_group)

        # Advanced parameters
        advanced_group = QGroupBox("Advanced Parameters")
        advanced_layout = QVBoxLayout()

        # Corner radius
        corner_layout = QHBoxLayout()
        corner_layout.addWidget(QLabel("Corner Radius (inches):"))
        self.corner_spin = QDoubleSpinBox()
        self.corner_spin.setRange(0.0, 1.0)
        self.corner_spin.setDecimals(3)
        self.corner_spin.setSingleStep(0.001)
        self.corner_spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        corner_layout.addWidget(self.corner_spin)
        advanced_layout.addLayout(corner_layout)

        # Chamfer angle
        chamfer_layout = QHBoxLayout()
        chamfer_layout.addWidget(QLabel("Chamfer Angle (degrees):"))
        self.chamfer_spin = QDoubleSpinBox()
        self.chamfer_spin.setRange(0.0, 90.0)
        self.chamfer_spin.setDecimals(1)
        self.chamfer_spin.setSingleStep(0.5)
        self.chamfer_spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        chamfer_layout.addWidget(self.chamfer_spin)
        advanced_layout.addLayout(chamfer_layout)

        # Helix angle
        helix_layout = QHBoxLayout()
        helix_layout.addWidget(QLabel("Helix Angle:"))
        self.helix_check = QCheckBox("Unknown")
        self.helix_check.stateChanged.connect(self._on_helix_unknown_changed)
        helix_layout.addWidget(self.helix_check)
        self.helix_spin = QDoubleSpinBox()
        self.helix_spin.setRange(0.0, 90.0)
        self.helix_spin.setDecimals(1)
        self.helix_spin.setSingleStep(0.5)
        self.helix_spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        helix_layout.addWidget(self.helix_spin)
        advanced_layout.addLayout(helix_layout)

        # Rake angle
        rake_layout = QHBoxLayout()
        rake_layout.addWidget(QLabel("Rake Angle:"))
        self.rake_check = QCheckBox("Unknown")
        self.rake_check.stateChanged.connect(self._on_rake_unknown_changed)
        rake_layout.addWidget(self.rake_check)
        self.rake_spin = QDoubleSpinBox()
        self.rake_spin.setRange(0.0, 30.0)
        self.rake_spin.setDecimals(1)
        self.rake_spin.setSingleStep(0.5)
        self.rake_spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        rake_layout.addWidget(self.rake_spin)
        advanced_layout.addLayout(rake_layout)

        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)

        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Connect signals
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

    def _load_values(self):
        """Load values from the tool specification."""
        self.diameter_spin.setValue(self.tool_spec.diameter)
        self.length_spin.setValue(self.tool_spec.length)
        self.flutes_spin.setValue(self.tool_spec.flute_count)

        # Set geometry
        geometry_index = self.geometry_combo.findText(self.tool_spec.geometry.value)
        if geometry_index >= 0:
            self.geometry_combo.setCurrentIndex(geometry_index)

        # Set material
        material_index = self.material_combo.findText(self.tool_spec.material.value)
        if material_index >= 0:
            self.material_combo.setCurrentIndex(material_index)

        # Set coating
        coating_index = self.coating_combo.findText(self.tool_spec.coating.value)
        if coating_index >= 0:
            self.coating_combo.setCurrentIndex(coating_index)

        self.corner_spin.setValue(self.tool_spec.corner_radius)
        self.chamfer_spin.setValue(self.tool_spec.chamfer_angle)

        # Handle optional angles
        if self.tool_spec.helix_angle is None:
            self.helix_check.setChecked(True)
            self.helix_spin.setEnabled(False)
        else:
            self.helix_check.setChecked(False)
            self.helix_spin.setValue(self.tool_spec.helix_angle)
            self.helix_spin.setEnabled(True)

        if self.tool_spec.rake_angle is None:
            self.rake_check.setChecked(True)
            self.rake_spin.setEnabled(False)
        else:
            self.rake_check.setChecked(False)
            self.rake_spin.setValue(self.tool_spec.rake_angle)
            self.rake_spin.setEnabled(True)

    def _on_helix_unknown_changed(self, state):
        """Handle helix angle unknown checkbox state change."""
        self.helix_spin.setEnabled(not state)

    def _on_rake_unknown_changed(self, state):
        """Handle rake angle unknown checkbox state change."""
        self.rake_spin.setEnabled(not state)

    def get_tool_spec(self) -> ToolSpecification:
        """Get the tool specification from the dialog."""
        return ToolSpecification(
            diameter=self.diameter_spin.value(),
            length=self.length_spin.value(),
            flute_count=self.flutes_spin.value(),
            geometry=ToolGeometry(self.geometry_combo.currentText()),
            material=ToolMaterial(self.material_combo.currentText()),
            coating=ToolCoating(self.coating_combo.currentText()),
            corner_radius=self.corner_spin.value(),
            chamfer_angle=self.chamfer_spin.value(),
            helix_angle=None if self.helix_check.isChecked() else self.helix_spin.value(),
            rake_angle=None if self.rake_check.isChecked() else self.rake_spin.value(),
            tool_id=self.tool_spec.tool_id
        )