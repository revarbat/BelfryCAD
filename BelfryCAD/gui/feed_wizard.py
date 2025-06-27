"""
Feed Wizard Implementation

This module implements the feed wizard functionality for calculating
speeds and feeds based on tool and material parameters.
"""

import logging

from typing import Optional, List, cast, TYPE_CHECKING
from dataclasses import dataclass

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QComboBox, QCheckBox, QFrame, QLineEdit,
                              QScrollBar, QListWidget, QPushButton)
from PySide6.QtCore import Qt, Signal

from BelfryCAD.mlcnc.cutting_params import (
    ToolSpecification, ToolGeometry, ToolMaterial, ToolCoating,
    MaterialType, OperationType, CuttingParameterCalculator,
    CuttingCondition
)
from .tool_table_dialog import ToolTableDialog

if TYPE_CHECKING:
    from .main_window import MainWindow

logger = logging.getLogger(__name__)

@dataclass
class MillDefinition:
    """Definition of mill parameters"""
    discrete_speeds: bool = False
    rpm_list: Optional[List[int]] = None
    min_rpm: int = 1000
    max_rpm: int = 10000
    fixed_rpm: bool = False
    auto_toolchanger: bool = False
    max_feed: float = 15.0
    horsepower: float = 0.25

    _instance: Optional['MillDefinition'] = None
    _calculator: Optional[CuttingParameterCalculator] = None

    def __post_init__(self):
        MillDefinition._instance = self
        if not MillDefinition._calculator:
            MillDefinition._calculator = CuttingParameterCalculator()

    @classmethod
    def get_rpm(cls) -> int:
        """Get the recommended RPM for the current configuration"""
        if not cls._instance:
            return 1000  # Default RPM

        if cls._instance.discrete_speeds and cls._instance.rpm_list:
            # Use the middle RPM from the list
            return cls._instance.rpm_list[len(cls._instance.rpm_list) // 2]
        else:
            # Use the middle of the RPM range
            return (cls._instance.min_rpm + cls._instance.max_rpm) // 2

    @classmethod
    def get_feed(cls, plunge: bool = False) -> float:
        """Get the recommended feed rate in IPM"""
        if not cls._instance or not cls._calculator:
            return 10.0  # Default feed rate

        # Get current tool and material
        tool = ToolSpecification(
            diameter=0.5,  # Default tool diameter
            length=3.0,    # Default tool length
            flute_count=4, # Default flute count
            geometry=ToolGeometry.SQUARE_END_MILL,
            material=ToolMaterial.CARBIDE
        )

        # Create cutting condition
        condition = CuttingCondition(
            tool=tool,
            material=MaterialType.ALUMINUM,  # Default material
            operation=OperationType.ROUGHING,
            depth_of_cut=0.1,
            width_of_cut=0.4,
            spindle_speed=cls.get_rpm(),
            feed_rate=10.0  # Initial feed rate
        )

        # Calculate optimal feed rate
        forces = cls._calculator.calculate_cutting_forces(condition)
        power = cls._calculator.calculate_power_consumption(condition)

        # Adjust feed rate based on power and forces
        feed_rate = condition.feed_rate
        if power['total'] > cls._instance.horsepower * 746:  # Convert HP to watts
            feed_rate *= 0.8  # Reduce feed rate if power exceeds machine capacity

        # Adjust for plunge rate if needed
        if plunge:
            feed_rate *= 0.5  # Plunge rate is typically half of feed rate

        # Ensure we don't exceed max feed rate
        return min(feed_rate, cls._instance.max_feed)

    @classmethod
    def get_cut_depth(cls, cut_width: float) -> float:
        """Get the recommended cut depth in inches"""
        if not cls._instance or not cls._calculator:
            return 0.1  # Default cut depth

        # Create cutting condition for depth calculation
        tool = ToolSpecification(
            diameter=cut_width,
            length=3.0,
            flute_count=4,
            geometry=ToolGeometry.SQUARE_END_MILL,
            material=ToolMaterial.CARBIDE
        )

        condition = CuttingCondition(
            tool=tool,
            material=MaterialType.ALUMINUM,
            operation=OperationType.ROUGHING,
            depth_of_cut=cut_width * 0.5,  # Initial depth
            width_of_cut=cut_width,
            spindle_speed=cls.get_rpm(),
            feed_rate=cls.get_feed()
        )

        # Calculate forces and power
        forces = cls._calculator.calculate_cutting_forces(condition)
        power = cls._calculator.calculate_power_consumption(condition)

        # Adjust depth based on forces and power
        depth = condition.depth_of_cut
        if power['total'] > cls._instance.horsepower * 746:
            depth *= 0.8  # Reduce depth if power exceeds machine capacity

        # Ensure depth is reasonable (1/2 to 1/4 of tool diameter)
        return min(depth, cut_width * 0.5)

@dataclass
class StockDefinition:
    """Definition of stock parameters"""
    width: float = 1.0
    length: float = 1.0
    height: float = 0.5
    material: str = "Aluminum"

@dataclass
class FeedWizardInfo:
    """Configuration parameters for feed wizard"""
    stock_material: str = "Aluminum"
    tool_spec: Optional[ToolSpecification] = None
    mill_horsepower: str = "0.20"
    mill_speeds_discrete: bool = True
    mill_speed_min: int = 1100
    mill_speed_max: int = 10500
    mill_speed_list: Optional[List[int]] = None

    def __post_init__(self):
        if self.mill_speed_list is None:
            self.mill_speed_list = [1100, 1900, 2900, 4300, 6500, 10500]

class FeedWizardDialog(QDialog):
    """Dialog for feed wizard configuration."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.info = FeedWizardInfo()
        self._setup_ui()
        self._connect_signals()
        self._update_calculations()
        logger.info(f"Initialized FeedWizardDialog with parent: {parent}")

    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Speeds & Feeds Wizard")
        layout = QVBoxLayout()

        # Material selection
        material_layout = QHBoxLayout()
        material_layout.addWidget(QLabel("Material to Mill:"))
        self.material_combo = QComboBox()
        self.material_combo.addItems(["Aluminum", "Steel", "Stainless Steel", "Brass", "Copper", "Plastic", "Wood", "Titanium", "Carbon Fiber"])
        self.material_combo.setCurrentText(self.info.stock_material)
        material_layout.addWidget(self.material_combo)
        layout.addLayout(material_layout)

        # Tool selection
        tool_layout = QHBoxLayout()
        tool_layout.addWidget(QLabel("Tool:"))
        self.tool_combo = QComboBox()
        self.tool_combo.setMinimumWidth(300)  # Make it wide enough to show tool details
        self.tool_combo.currentIndexChanged.connect(self._on_tool_changed)
        tool_layout.addWidget(self.tool_combo)

        # Add tool table button
        tool_table_button = QPushButton("Tool Table...")
        tool_table_button.clicked.connect(self._open_tool_table)
        tool_layout.addWidget(tool_table_button)

        layout.addLayout(tool_layout)

        # Mill horsepower
        hp_layout = QHBoxLayout()
        hp_layout.addWidget(QLabel("Mill HorsePower:"))
        self.hp_combo = QComboBox()
        self.hp_combo.addItems(["1/8", "1/6", "1/5", "1/4", "1/3", "1/2", "2/3", "3/4", "1", "1.5", "2.0", "3.0"])
        self.hp_combo.setCurrentText(self.info.mill_horsepower)
        hp_layout.addWidget(self.hp_combo)
        layout.addLayout(hp_layout)

        # Mill speeds
        speeds_layout = QHBoxLayout()
        speeds_layout.addWidget(QLabel("Mill Speeds:"))
        self.discrete_check = QCheckBox("Discrete")
        self.discrete_check.setChecked(self.info.mill_speeds_discrete)
        speeds_layout.addWidget(self.discrete_check)
        layout.addLayout(speeds_layout)

        # Min/Max speeds frame
        self.minmax_frame = QFrame()
        minmax_layout = QHBoxLayout()
        minmax_layout.addWidget(QLabel("Min:"))
        self.min_rpm = QLineEdit(str(self.info.mill_speed_min))
        minmax_layout.addWidget(self.min_rpm)
        minmax_layout.addWidget(QLabel("Max:"))
        self.max_rpm = QLineEdit(str(self.info.mill_speed_max))
        minmax_layout.addWidget(self.max_rpm)
        self.minmax_frame.setLayout(minmax_layout)
        layout.addWidget(self.minmax_frame)

        # Speed list frame
        self.speed_list_frame = QFrame()
        speed_list_layout = QVBoxLayout()
        self.speed_list = QListWidget()
        self.speed_list.addItems([str(rpm) for rpm in (self.info.mill_speed_list or [1100, 1900, 2900, 4300, 6500, 10500])])
        speed_list_layout.addWidget(self.speed_list)
        self.speed_list_frame.setLayout(speed_list_layout)
        layout.addWidget(self.speed_list_frame)

        # Results frame
        results_frame = QFrame()
        results_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        results_layout = QVBoxLayout()
        results_layout.addWidget(QLabel("Speeds & Feeds"))
        self.rpm_label = QLabel("RPM Speed: ")
        self.plunge_label = QLabel("Plunge Rate: ")
        self.feed_label = QLabel("Feed Rate: ")
        self.depth_label = QLabel("Cut Depth: ")
        results_layout.addWidget(self.rpm_label)
        results_layout.addWidget(self.plunge_label)
        results_layout.addWidget(self.feed_label)
        results_layout.addWidget(self.depth_label)
        results_frame.setLayout(results_layout)
        layout.addWidget(results_frame)

        self.setLayout(layout)

        # Update visibility based on discrete speeds setting
        self._update_speed_visibility()

        # Load tools into combo box
        self._load_tools()

    def _connect_signals(self):
        """Connect UI signals."""
        self.material_combo.currentTextChanged.connect(self._on_material_changed)
        self.hp_combo.currentTextChanged.connect(self._on_hp_changed)
        self.discrete_check.toggled.connect(self._on_discrete_toggled)
        self.min_rpm.textChanged.connect(self._on_speed_changed)
        self.max_rpm.textChanged.connect(self._on_speed_changed)
        self.speed_list.itemChanged.connect(self._on_speed_list_changed)

    def _load_tools(self):
        """Load tools from preferences into the combo box."""
        self.tool_combo.clear()

        # Get tools from preferences
        if self.parent():
            main_window = cast('MainWindow', self.parent())
            tool_dicts = main_window.preferences.get('tool_table', [])

            # Convert tool dicts to ToolSpecification objects
            for tool_dict in tool_dicts:
                try:
                    tool_dict['geometry'] = ToolGeometry(tool_dict['geometry'])
                    tool_dict['material'] = ToolMaterial(tool_dict['material'])
                    tool_dict['coating'] = ToolCoating(tool_dict['coating'])
                    tool = ToolSpecification(**tool_dict)
                    self.tool_combo.addItem(self._format_tool_info(tool), tool)
                except (ValueError, KeyError) as e:
                    logger.error(f"Error converting tool dict to ToolSpecification: {e}")
                    continue

    def _format_tool_info(self, tool: ToolSpecification) -> str:
        """Format tool information for display in the combo box."""
        if (
            tool.diameter == 0.0 or
            tool.geometry == ToolGeometry.EMPTY_SLOT
        ):  # Empty slot
            return f"Tool {tool.tool_id:02d} - Empty Slot"
        return (f"Tool {tool.tool_id:02d} - {tool.diameter:.3f}\" {tool.geometry.value} "
                f"({tool.flute_count} flutes, {tool.material.value})")

    def _on_tool_changed(self, index: int):
        """Handle tool selection change."""
        if index >= 0:
            tool = self.tool_combo.itemData(index)
            if tool:
                self.info.tool_spec = tool
                self._update_calculations()

    def _open_tool_table(self):
        """Open the tool table dialog."""
        dialog = ToolTableDialog.load_from_preferences(parent=self.parent())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Reload tools after tool table is closed
            self._load_tools()
            # Try to select the same tool if it still exists
            if self.info.tool_spec:
                for i in range(self.tool_combo.count()):
                    tool = self.tool_combo.itemData(i)
                    if tool and tool.tool_id == self.info.tool_spec.tool_id:
                        self.tool_combo.setCurrentIndex(i)
                        break

    def _update_speed_visibility(self):
        """Update visibility of speed controls based on discrete setting."""
        if self.info.mill_speeds_discrete:
            # Hide min/max controls and show speeds list
            self.min_rpm.setVisible(False)
            self.max_rpm.setVisible(False)
            min_label = self.min_rpm.parent().findChild(QLabel, "min_label")
            max_label = self.max_rpm.parent().findChild(QLabel, "max_label")
            if min_label:
                min_label.setVisible(False)
            if max_label:
                max_label.setVisible(False)
            self.speed_list_frame.setVisible(True)
        else:
            # Show min/max controls and hide speeds list
            self.min_rpm.setVisible(True)
            self.max_rpm.setVisible(True)
            min_label = self.min_rpm.parent().findChild(QLabel, "min_label")
            max_label = self.max_rpm.parent().findChild(QLabel, "max_label")
            if min_label:
                min_label.setVisible(True)
            if max_label:
                max_label.setVisible(True)
            self.speed_list_frame.setVisible(False)

    def _on_material_changed(self, material: str):
        """Handle material change."""
        self.info.stock_material = material
        self._update_calculations()

    def _on_hp_changed(self, hp: str):
        """Handle horsepower change."""
        self.info.mill_horsepower = hp
        self._update_calculations()

    def _on_discrete_toggled(self, discrete: bool):
        """Handle discrete speeds toggle."""
        self.info.mill_speeds_discrete = discrete
        self._update_speed_visibility()
        self._update_calculations()

    def _on_speed_changed(self):
        """Handle speed range changes."""
        try:
            self.info.mill_speed_min = int(self.min_rpm.text())
            self.info.mill_speed_max = int(self.max_rpm.text())
            self._update_calculations()
        except ValueError:
            pass

    def _on_speed_list_changed(self):
        """Handle speed list changes."""
        speed_list = []
        for i in range(self.speed_list.count()):
            try:
                speed = int(self.speed_list.item(i).text())
                speed_list.append(speed)
            except ValueError:
                continue
        if speed_list:
            self.info.mill_speed_list = speed_list
            self._update_calculations()

    def _update_calculations(self):
        """Update speed and feed calculations."""
        if not self.info.tool_spec:
            # Clear results if no tool selected
            self.rpm_label.setText("RPM Speed: --")
            self.plunge_label.setText("Plunge Rate: --")
            self.feed_label.setText("Feed Rate: --")
            self.depth_label.setText("Cut Depth: --")
            return

        # Create mill definition
        mill = MillDefinition(
            discrete_speeds=self.info.mill_speeds_discrete,
            rpm_list=self.info.mill_speed_list,
            min_rpm=self.info.mill_speed_min,
            max_rpm=self.info.mill_speed_max,
            horsepower=float(self.info.mill_horsepower)
        )

        # Get material type from combo box
        material_map = {
            "Aluminum": MaterialType.ALUMINUM,
            "Steel": MaterialType.STEEL,
            "Stainless Steel": MaterialType.STAINLESS_STEEL,
            "Brass": MaterialType.BRASS,
            "Copper": MaterialType.COPPER,
            "Plastic": MaterialType.PLASTIC,
            "Wood": MaterialType.WOOD,
            "Titanium": MaterialType.TITANIUM,
            "Carbon Fiber": MaterialType.CARBON_FIBER
        }
        material = material_map.get(self.material_combo.currentText(), MaterialType.ALUMINUM)

        # Create cutting condition with selected tool and material
        condition = CuttingCondition(
            tool=self.info.tool_spec,
            material=material,
            operation=OperationType.ROUGHING,
            depth_of_cut=self.info.tool_spec.diameter * 0.5,  # Initial depth
            width_of_cut=self.info.tool_spec.diameter * 0.8,  # Initial width
            spindle_speed=mill.get_rpm(),
            feed_rate=10.0  # Initial feed rate
        )

        # Calculate optimal values
        calculator = CuttingParameterCalculator()
        forces = calculator.calculate_cutting_forces(condition)
        power = calculator.calculate_power_consumption(condition)

        # Adjust feed rate based on power and forces
        feed_rate = condition.feed_rate
        if power['total'] > mill.horsepower * 746:  # Convert HP to watts
            feed_rate *= 0.8  # Reduce feed rate if power exceeds machine capacity

        # Calculate plunge rate (typically half of feed rate)
        plunge_rate = feed_rate * 0.5

        # Calculate depth of cut (1/2 to 1/4 of tool diameter)
        depth = min(self.info.tool_spec.diameter * 0.5, self.info.tool_spec.diameter * 0.25)
        if power['total'] > mill.horsepower * 746:
            depth *= 0.8  # Reduce depth if power exceeds machine capacity

        # Update labels
        self.rpm_label.setText(f"RPM Speed: {mill.get_rpm()}")
        self.plunge_label.setText(f"Plunge Rate: {plunge_rate:.1f} IPM")
        self.feed_label.setText(f"Feed Rate: {feed_rate:.1f} IPM")
        self.depth_label.setText(f"Cut Depth: {depth:.3f}\"")