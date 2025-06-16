"""
Feed Wizard Implementation

This module implements the feed wizard functionality based on the original TCL
feedwiz.tcl implementation. It provides a dialog for calculating speeds and feeds
for CNC machining operations.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
import math

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QComboBox, QCheckBox, QFrame, QLineEdit,
                              QScrollBar, QListWidget, QPushButton)
from PySide6.QtCore import Qt, Signal

from BelfryCAD.gui.feedwiz import MillDefinition, StockDefinition, ToolDefinition


@dataclass
class FeedWizardInfo:
    """Configuration for the feed wizard"""
    stock_material: str = "Aluminum"
    tool_material: str = "Carbide"
    tool_diameter: str = "1/8\""
    tool_flutes: str = "4"
    mill_horsepower: str = "0.20"
    mill_speeds_discrete: bool = True
    mill_speed_min: int = 1100
    mill_speed_max: int = 10500
    mill_speed_list: List[int] = field(default_factory=lambda: [1100, 1900, 2900, 4300, 6500, 10500])


class FeedWizardDialog(QDialog):
    """Dialog for calculating speeds and feeds"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.info = FeedWizardInfo()
        self._setup_ui()
        self._connect_signals()
        self._update_calculations()

    def _setup_ui(self):
        """Set up the dialog UI"""
        self.setWindowTitle("Speed and Feed Wizard")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # Material selection
        material_layout = QHBoxLayout()
        material_label = QLabel("Material to Mill:")
        self.material_combo = QComboBox()
        self.material_combo.addItems(self._get_stock_types())
        self.material_combo.setCurrentText(self.info.stock_material)
        self.material_combo.setMinimumWidth(200)
        material_layout.addWidget(material_label)
        material_layout.addWidget(self.material_combo)
        layout.addLayout(material_layout)

        # Tool type selection
        tool_layout = QHBoxLayout()
        tool_label = QLabel("Tool Type:")
        self.tool_combo = QComboBox()
        self.tool_combo.addItems(["HSS", "Carbide"])
        self.tool_combo.setCurrentText(self.info.tool_material)
        self.tool_combo.setMinimumWidth(200)
        tool_layout.addWidget(tool_label)
        tool_layout.addWidget(self.tool_combo)
        layout.addLayout(tool_layout)

        # Tool diameter selection
        diameter_layout = QHBoxLayout()
        diameter_label = QLabel("Tool Diameter:")
        self.diameter_combo = QComboBox()
        self.diameter_combo.addItems([
            "1/32\"", "1/16\"", "1/8\"", "3/16\"", "1/4\"", "5/16\"",
            "3/8\"", "7/16\"", "1/2\"", "9/16\"", "5/8\"", "11/16\"",
            "3/4\"", "13/16\"", "7/8\"", "15/16\"", "1\""
        ])
        self.diameter_combo.setCurrentText(self.info.tool_diameter)
        self.diameter_combo.setMinimumWidth(100)
        diameter_layout.addWidget(diameter_label)
        diameter_layout.addWidget(self.diameter_combo)
        layout.addLayout(diameter_layout)

        # Tool flutes selection
        flutes_layout = QHBoxLayout()
        flutes_label = QLabel("Tool Flutes:")
        self.flutes_combo = QComboBox()
        self.flutes_combo.addItems([str(i) for i in range(1, 9)])
        self.flutes_combo.setCurrentText(self.info.tool_flutes)
        self.flutes_combo.setMinimumWidth(100)
        flutes_layout.addWidget(flutes_label)
        flutes_layout.addWidget(self.flutes_combo)
        layout.addLayout(flutes_layout)

        # Mill horsepower selection
        hp_layout = QHBoxLayout()
        hp_label = QLabel("Mill HorsePower:")
        self.hp_combo = QComboBox()
        self.hp_combo.addItems([
            "1/8", "1/6", "1/5", "1/4", "1/3", "1/2", "2/3", "3/4",
            "1", "1.5", "2.0", "3.0"
        ])
        self.hp_combo.setCurrentText(self.info.mill_horsepower)
        self.hp_combo.setMinimumWidth(100)
        hp_layout.addWidget(hp_label)
        hp_layout.addWidget(self.hp_combo)
        layout.addLayout(hp_layout)

        # Mill speeds section
        speeds_layout = QHBoxLayout()
        speeds_label = QLabel("Mill Speeds:")
        self.discrete_check = QCheckBox("Discrete")
        self.discrete_check.setChecked(self.info.mill_speeds_discrete)
        speeds_layout.addWidget(speeds_label)
        speeds_layout.addWidget(self.discrete_check)
        layout.addLayout(speeds_layout)

        # Speed range frame
        self.speed_frame = QFrame()
        speed_layout = QVBoxLayout(self.speed_frame)

        # Min/Max speed inputs
        minmax_layout = QHBoxLayout()
        min_label = QLabel("Min:")
        min_label.setObjectName("min_label")
        self.min_speed = QLineEdit(str(self.info.mill_speed_min))
        self.min_speed.setFixedWidth(80)
        max_label = QLabel("Max:")
        max_label.setObjectName("max_label")
        self.max_speed = QLineEdit(str(self.info.mill_speed_max))
        self.max_speed.setFixedWidth(80)
        minmax_layout.addWidget(min_label)
        minmax_layout.addWidget(self.min_speed)
        minmax_layout.addWidget(max_label)
        minmax_layout.addWidget(self.max_speed)
        speed_layout.addLayout(minmax_layout)

        # Discrete speeds list
        self.speeds_list = QListWidget()
        self.speeds_list.addItems([str(s) for s in self.info.mill_speed_list])
        self.speeds_list.setFixedHeight(100)
        speed_layout.addWidget(self.speeds_list)

        layout.addWidget(self.speed_frame)

        # Results frame
        results_frame = QFrame()
        results_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        results_layout = QVBoxLayout(results_frame)

        self.rpm_label = QLabel("RPM Speed: ")
        self.plunge_label = QLabel("Plunge Rate: ")
        self.feed_label = QLabel("Feed Rate: ")
        self.depth_label = QLabel("Cut Depth: ")

        results_layout.addWidget(self.rpm_label)
        results_layout.addWidget(self.plunge_label)
        results_layout.addWidget(self.feed_label)
        results_layout.addWidget(self.depth_label)

        layout.addWidget(results_frame)

        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Initial visibility
        self._update_speed_visibility()

    def _connect_signals(self):
        """Connect UI signals to handlers"""
        self.material_combo.currentTextChanged.connect(self._on_material_changed)
        self.tool_combo.currentTextChanged.connect(self._on_tool_changed)
        self.diameter_combo.currentTextChanged.connect(self._on_diameter_changed)
        self.flutes_combo.currentTextChanged.connect(self._on_flutes_changed)
        self.hp_combo.currentTextChanged.connect(self._on_hp_changed)
        self.discrete_check.toggled.connect(self._on_discrete_toggled)
        self.min_speed.textChanged.connect(self._on_speed_changed)
        self.max_speed.textChanged.connect(self._on_speed_changed)
        self.speeds_list.itemChanged.connect(self._on_speed_list_changed)

    def _get_stock_types(self) -> List[str]:
        """Get available stock material types"""
        # This would come from the mill configuration
        return ["Aluminum", "Steel", "Brass", "Plastic", "Wood"]

    def _update_speed_visibility(self):
        """Update visibility of speed controls based on discrete setting"""
        if self.info.mill_speeds_discrete:
            # Hide min/max controls and show speeds list
            self.min_speed.setVisible(False)
            self.max_speed.setVisible(False)
            min_label = self.min_speed.parent().findChild(QLabel, "min_label")
            max_label = self.max_speed.parent().findChild(QLabel, "max_label")
            if min_label:
                min_label.setVisible(False)
            if max_label:
                max_label.setVisible(False)
            self.speeds_list.setVisible(True)
        else:
            # Show min/max controls and hide speeds list
            self.min_speed.setVisible(True)
            self.max_speed.setVisible(True)
            min_label = self.min_speed.parent().findChild(QLabel, "min_label")
            max_label = self.max_speed.parent().findChild(QLabel, "max_label")
            if min_label:
                min_label.setVisible(True)
            if max_label:
                max_label.setVisible(True)
            self.speeds_list.setVisible(False)

    def _on_material_changed(self, material: str):
        """Handle material selection change"""
        self.info.stock_material = material
        self._update_calculations()

    def _on_tool_changed(self, tool: str):
        """Handle tool material change"""
        self.info.tool_material = tool
        self._update_calculations()

    def _on_diameter_changed(self, diameter: str):
        """Handle tool diameter change"""
        self.info.tool_diameter = diameter
        self._update_calculations()

    def _on_flutes_changed(self, flutes: str):
        """Handle tool flutes change"""
        self.info.tool_flutes = flutes
        self._update_calculations()

    def _on_hp_changed(self, hp: str):
        """Handle horsepower change"""
        self.info.mill_horsepower = hp
        self._update_calculations()

    def _on_discrete_toggled(self, discrete: bool):
        """Handle discrete speeds toggle"""
        self.info.mill_speeds_discrete = discrete
        self._update_speed_visibility()
        self._update_calculations()

    def _on_speed_changed(self):
        """Handle speed range changes"""
        try:
            self.info.mill_speed_min = int(self.min_speed.text())
            self.info.mill_speed_max = int(self.max_speed.text())
            self._update_calculations()
        except ValueError:
            pass

    def _on_speed_list_changed(self):
        """Handle discrete speeds list changes"""
        try:
            self.info.mill_speed_list = [
                int(self.speeds_list.item(i).text())
                for i in range(self.speeds_list.count())
            ]
            self._update_calculations()
        except ValueError:
            pass

    def _update_calculations(self):
        """Update speed and feed calculations"""
        # Convert tool diameter to inches
        tool_diam = self._parse_fraction(self.info.tool_diameter)
        if tool_diam is None:
            tool_diam = 0.125  # Default to 1/8"

        # Convert horsepower to float
        try:
            hp = float(self._parse_fraction(self.info.mill_horsepower) or 0.25)
        except (ValueError, TypeError):
            hp = 0.25  # Default to 1/4 HP

        # Configure mill
        if self.info.mill_speeds_discrete:
            MillDefinition(
                discrete_speeds=True,
                rpm_list=self.info.mill_speed_list.copy(),  # Create a copy to avoid modifying the original
                fixed_rpm=True,
                auto_toolchanger=False,
                max_feed=15.0,
                horsepower=hp
            )
        else:
            MillDefinition(
                discrete_speeds=False,
                min_rpm=self.info.mill_speed_min,
                max_rpm=self.info.mill_speed_max,
                fixed_rpm=False,
                auto_toolchanger=False,
                max_feed=15.0,
                horsepower=hp
            )

        # Configure stock
        StockDefinition(
            width=1.0,
            height=1.0,
            depth=0.5,
            material=self.info.stock_material
        )

        # Configure tool
        ToolDefinition(
            tool_id=99,
            diameter=tool_diam,
            material=self.info.tool_material,
            flutes=int(self.info.tool_flutes)
        )

        # Get calculated values
        rpm = MillDefinition.get_rpm()
        plunge_rate = MillDefinition.get_feed(plunge=True)
        feed_rate = MillDefinition.get_feed()
        cut_depth = MillDefinition.get_cut_depth(cut_width=tool_diam)

        # Update labels
        self.rpm_label.setText(f"RPM Speed:   {rpm}")
        self.plunge_label.setText(f"Plunge Rate: {plunge_rate} IPM")
        self.feed_label.setText(f"Feed Rate:   {feed_rate} IPM")
        self.depth_label.setText(f"Cut Depth:   {cut_depth}\"")

    def _parse_fraction(self, value: str) -> Optional[float]:
        """Parse a fraction string to float"""
        try:
            if "/" in value:
                num, denom = value.split("/")
                return float(num) / float(denom)
            return float(value)
        except (ValueError, ZeroDivisionError):
            return None 