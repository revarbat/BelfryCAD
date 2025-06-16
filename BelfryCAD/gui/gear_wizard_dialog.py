"""
Gear Wizard Dialog

This module provides a dialog for generating G-code for various types of gears.
"""

from typing import Optional, cast, TYPE_CHECKING
import logging

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox,
    QSpinBox, QComboBox, QPushButton, QGroupBox, QRadioButton,
    QButtonGroup, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt

from BelfryCAD.mlcnc.gear_generator import (
    GearParameters, WormParameters, GearGenerator,
    WormGearGenerator, WormGenerator, Handedness, TableOrientation
)
from BelfryCAD.mlcnc.cutting_params import (
    ToolSpecification, ToolGeometry, ToolMaterial, ToolCoating
)
from .tool_spec_dialog import ToolSpecDialog
from .tool_table_dialog import ToolTableDialog

if TYPE_CHECKING:
    from .main_window import MainWindow

logger = logging.getLogger(__name__)

class GearWizardDialog(QDialog):
    """Dialog for generating gear G-code."""

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("Initializing GearWizardDialog")
        try:
            self.tool_spec = None
            self._setup_ui()
            logger.info("UI setup complete")
            self._connect_signals()
            logger.info("Signals connected")
            self._load_tools()
            logger.info("Tools loaded")
            self._update_stats()
            logger.info("Stats updated")
        except Exception as e:
            logger.error(f"Error initializing GearWizardDialog: {e}", exc_info=True)
            raise

    def _setup_ui(self):
        """Set up the dialog UI."""
        logger.info("Setting up GearWizardDialog UI")
        try:
            self.setWindowTitle("Gear Wizard")
            layout = QVBoxLayout()

            # Tool selection
            logger.info("Setting up tool selection")
            tool_group = QGroupBox("Tool")
            tool_layout = QHBoxLayout()
            
            # Tool dropdown
            self.tool_combo = QComboBox()
            self.tool_combo.setMinimumWidth(200)
            tool_layout.addWidget(self.tool_combo)
            
            # Tool table button
            self.tool_table_button = QPushButton("Tool Table...")
            self.tool_table_button.clicked.connect(self._open_tool_table)
            tool_layout.addWidget(self.tool_table_button)
            
            tool_group.setLayout(tool_layout)
            layout.addWidget(tool_group)

            # Gear type selection
            logger.info("Setting up gear type selection")
            type_group = QGroupBox("Gear Type")
            type_layout = QVBoxLayout()
            type_layout.addWidget(QLabel("Gear Type:"))
            self.type_combo = QComboBox()
            self.type_combo.addItems([
                "Spur Gear",
                "Helical Gear",
                "Worm",
                "Worm Gear"
            ])
            self.type_combo.currentIndexChanged.connect(self._on_gear_type_changed)
            type_layout.addWidget(self.type_combo)
            type_layout.addStretch()
            type_group.setLayout(type_layout)
            layout.addWidget(type_group)

            # Basic parameters
            logger.info("Setting up basic parameters")
            basic_group = QGroupBox("Basic Parameters")
            basic_layout = QVBoxLayout()

            # Pitch
            pitch_layout = QHBoxLayout()
            pitch_layout.addWidget(QLabel("Pitch:"))
            self.pitch_spin = QSpinBox()
            self.pitch_spin.setRange(1, 99)
            self.pitch_spin.setValue(24)
            pitch_layout.addWidget(self.pitch_spin)
            basic_layout.addLayout(pitch_layout)

            # Number of teeth
            teeth_layout = QHBoxLayout()
            teeth_layout.addWidget(QLabel("Number of Teeth:"))
            self.teeth_spin = QSpinBox()
            self.teeth_spin.setRange(1, 999)
            self.teeth_spin.setValue(24)
            teeth_layout.addWidget(self.teeth_spin)
            basic_layout.addLayout(teeth_layout)

            # Gear width
            width_layout = QHBoxLayout()
            width_layout.addWidget(QLabel("Axial Width (inches):"))
            self.width_spin = QDoubleSpinBox()
            self.width_spin.setRange(0.1, 99.9999)
            self.width_spin.setDecimals(4)
            self.width_spin.setSingleStep(0.1)
            self.width_spin.setValue(1.0)
            width_layout.addWidget(self.width_spin)
            basic_layout.addLayout(width_layout)

            # Table orientation
            orientation_layout = QHBoxLayout()
            orientation_layout.addWidget(QLabel("Rotary Table Orientation:"))
            self.orientation_combo = QComboBox()
            self.orientation_combo.addItems([
                "+X (Right)",
                "+Y (Front)",
                "-X (Left)",
                "-Y (Back)"
            ])
            self.orientation_combo.currentIndexChanged.connect(self._update_stats)
            orientation_layout.addWidget(self.orientation_combo)
            orientation_layout.addStretch()
            basic_layout.addLayout(orientation_layout)

            basic_group.setLayout(basic_layout)
            layout.addWidget(basic_group)

            # Helical parameters
            logger.info("Setting up helical parameters")
            self.helical_group = QGroupBox("Helical Parameters")
            helical_layout = QVBoxLayout()

            # Helical angle
            angle_layout = QHBoxLayout()
            angle_layout.addWidget(QLabel("Helical Angle (degrees):"))
            self.angle_spin = QDoubleSpinBox()
            self.angle_spin.setRange(-89.99, 89.99)
            self.angle_spin.setDecimals(2)
            self.angle_spin.setSingleStep(0.1)
            self.angle_spin.setValue(45.0)
            angle_layout.addWidget(self.angle_spin)
            helical_layout.addLayout(angle_layout)

            # Handedness
            hand_layout = QHBoxLayout()
            hand_layout.addWidget(QLabel("Handedness:"))
            self.hand_group = QButtonGroup()
            self.right_radio = QRadioButton("Right")
            self.left_radio = QRadioButton("Left")
            self.right_radio.setChecked(True)
            self.hand_group.addButton(self.right_radio)
            self.hand_group.addButton(self.left_radio)
            hand_layout.addWidget(self.right_radio)
            hand_layout.addWidget(self.left_radio)
            helical_layout.addLayout(hand_layout)

            self.helical_group.setLayout(helical_layout)
            layout.addWidget(self.helical_group)

            # Worm parameters
            logger.info("Setting up worm parameters")
            self.worm_group = QGroupBox("Worm Parameters")
            worm_layout = QVBoxLayout()

            # Number of threads
            threads_layout = QHBoxLayout()
            threads_layout.addWidget(QLabel("Number of Threads:"))
            self.threads_spin = QSpinBox()
            self.threads_spin.setRange(1, 9)
            self.threads_spin.setValue(1)
            threads_layout.addWidget(self.threads_spin)
            worm_layout.addLayout(threads_layout)

            # Worm diameter
            worm_diam_layout = QHBoxLayout()
            worm_diam_layout.addWidget(QLabel("Worm Diameter (inches):"))
            self.worm_diam_spin = QDoubleSpinBox()
            self.worm_diam_spin.setRange(0.1, 99.9999)
            self.worm_diam_spin.setDecimals(4)
            self.worm_diam_spin.setSingleStep(0.01)
            self.worm_diam_spin.setValue(0.5)
            worm_diam_layout.addWidget(self.worm_diam_spin)
            worm_layout.addLayout(worm_diam_layout)

            self.worm_group.setLayout(worm_layout)
            layout.addWidget(self.worm_group)

            # Statistics
            logger.info("Setting up statistics")
            stats_group = QGroupBox("Gear Statistics")
            stats_layout = QVBoxLayout()
            self.outside_diam_label = QLabel("Outside Diameter:")
            self.pitch_diam_label = QLabel("Pitch Diameter:")
            self.whole_depth_label = QLabel("Whole Depth:")
            self.cut_side_label = QLabel("Cut Side:")
            stats_layout.addWidget(self.outside_diam_label)
            stats_layout.addWidget(self.pitch_diam_label)
            stats_layout.addWidget(self.whole_depth_label)
            stats_layout.addWidget(self.cut_side_label)
            stats_group.setLayout(stats_layout)
            layout.addWidget(stats_group)

            # Buttons
            logger.info("Setting up buttons")
            button_layout = QHBoxLayout()
            self.generate_button = QPushButton("Generate G-Code")
            self.cancel_button = QPushButton("Cancel")
            button_layout.addWidget(self.generate_button)
            button_layout.addWidget(self.cancel_button)
            layout.addLayout(button_layout)

            # Set the dialog's layout
            logger.info("Setting dialog layout")
            self.setLayout(layout)

            # Set initial visibility of parameter groups
            self.helical_group.setVisible(False)
            self.worm_group.setVisible(False)
            logger.info("UI setup complete")
        except Exception as e:
            logger.error(f"Error in _setup_ui: {e}", exc_info=True)
            raise

    def _connect_signals(self):
        """Connect UI signals to slots."""
        # Tool selection
        self.tool_combo.currentIndexChanged.connect(self._on_tool_changed)
        
        # Gear type selection
        self.type_combo.currentIndexChanged.connect(self._on_gear_type_changed)

        # Parameter changes
        self.pitch_spin.valueChanged.connect(self._update_stats)
        self.teeth_spin.valueChanged.connect(self._update_stats)
        self.width_spin.valueChanged.connect(self._update_stats)
        self.angle_spin.valueChanged.connect(self._update_stats)
        self.threads_spin.valueChanged.connect(self._update_stats)
        self.worm_diam_spin.valueChanged.connect(self._update_stats)
        self.right_radio.toggled.connect(self._update_stats)
        self.left_radio.toggled.connect(self._update_stats)
        self.orientation_combo.currentIndexChanged.connect(self._update_stats)

        # Buttons
        self.generate_button.clicked.connect(self._generate_gcode)
        self.cancel_button.clicked.connect(self.reject)

    def _load_tools(self):
        """Load tools from preferences."""
        logger.info("Loading tools from preferences")
        # Get preferences from main window
        main_window = cast('MainWindow', self.parent())
        if main_window:
            tool_dicts = main_window.preferences.get('tool_table', [])
            logger.info(f"Loaded {len(tool_dicts)} tools from preferences")
            
            # Convert string values back to enums
            for tool_dict in tool_dicts:
                try:
                    tool_dict['geometry'] = ToolGeometry(tool_dict['geometry'])
                    tool_dict['material'] = ToolMaterial(tool_dict['material'])
                    tool_dict['coating'] = ToolCoating(tool_dict['coating'])
                    tool = ToolSpecification(**tool_dict)
                    self.tool_combo.addItem(
                        f"Tool {tool.tool_id:02d} - {tool.diameter:.3f}\" {tool.geometry.value} ({tool.flute_count} flutes)",
                        tool
                    )
                except (ValueError, KeyError) as e:
                    logger.error(f"Error converting tool dict to ToolSpecification: {e}")
                    continue
        else:
            logger.warning("No main window found, loading empty tool list")

    def _open_tool_table(self):
        """Open the tool table dialog."""
        dialog = ToolTableDialog.load_from_preferences(parent=self.parent())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Reload tools after tool table is closed
            self._load_tools()

    def _on_tool_changed(self, index: int):
        """Handle tool selection change."""
        if index >= 0:
            self.tool_spec = self.tool_combo.currentData()
            self._update_stats()
        else:
            self.tool_spec = None

    def _on_gear_type_changed(self):
        """Handle gear type selection change."""
        gear_type = self.type_combo.currentText()
        
        # Show/hide appropriate parameter groups
        self.helical_group.setVisible(gear_type == "Helical Gear")
        self.worm_group.setVisible(gear_type in ["Worm", "Worm Gear"])
        
        # Update stats
        self._update_stats()

    def _get_gear_parameters(self) -> GearParameters:
        """Get gear parameters from UI."""
        params = GearParameters(
            pitch=self.pitch_spin.value(),
            num_teeth=self.teeth_spin.value(),
            gear_width=self.width_spin.value(),
            table_orientation=self._get_table_orientation(),
            handedness=Handedness.LEFT if self.left_radio.isChecked() else Handedness.RIGHT
        )
        return params

    def _get_table_orientation(self) -> TableOrientation:
        """Get the selected table orientation."""
        index = self.orientation_combo.currentIndex()
        if index == 0:
            return TableOrientation.PLUS_X
        elif index == 1:
            return TableOrientation.PLUS_Y
        elif index == 2:
            return TableOrientation.MINUS_X
        else:
            return TableOrientation.MINUS_Y

    def _update_stats(self):
        """Update gear statistics display."""
        try:
            params = self._get_gear_parameters()
            if self.worm_group.isVisible():
                worm_params = WormParameters(
                    **params.__dict__,
                    worm_threads=self.threads_spin.value(),
                    worm_diameter=self.worm_diam_spin.value()
                )
                if self.type_combo.currentText() == "Worm":
                    generator = WormGenerator(worm_params)
                else:
                    generator = WormGearGenerator(worm_params)
            else:
                generator = GearGenerator(params)

            # Calculate dimensions
            pitch_diam, outside_diam, whole_depth, _ = generator._calculate_gear_dimensions()
            _, _, _, approach_ang = generator._calculate_cutting_parameters()

            # Update labels
            self.outside_diam_label.setText(f"Outside Diameter: {outside_diam:.4f}\"")
            self.pitch_diam_label.setText(f"Pitch Diameter: {pitch_diam:.4f}\"")
            self.whole_depth_label.setText(f"Whole Depth: {whole_depth:.4f}\"")
            self.cut_side_label.setText(f"Cut Side: {generator._get_cut_side(approach_ang)}")

        except Exception as e:
            logger.error(f"Error updating stats: {e}")
            self.outside_diam_label.setText("Outside Diameter: Error")
            self.pitch_diam_label.setText("Pitch Diameter: Error")
            self.whole_depth_label.setText("Whole Depth: Error")
            self.cut_side_label.setText("Cut Side: Error")

    def _generate_gcode(self):
        """Generate G-code for the gear."""
        if not self.tool_spec:
            QMessageBox.warning(
                self,
                "Warning",
                "Please select a tool first."
            )
            return

        # Get basic parameters
        params = GearParameters(
            pitch=self.pitch_spin.value(),
            num_teeth=self.teeth_spin.value(),
            gear_width=self.width_spin.value(),
            table_orientation=self._get_table_orientation(),
            handedness=Handedness.RIGHT if self.right_radio.isChecked() else Handedness.LEFT
        )

        # Get helical parameters if applicable
        if self.type_combo.currentText() == "Helical Gear":
            params.helical_angle = self.angle_spin.value()

        # Get worm parameters if applicable
        if self.type_combo.currentText() in ["Worm", "Worm Gear"]:
            worm_params = WormParameters(
                pitch=params.pitch,
                num_teeth=params.num_teeth,
                gear_width=params.gear_width,
                table_orientation=params.table_orientation,
                handedness=params.handedness,
                helical_angle=params.helical_angle,
                worm_threads=self.threads_spin.value(),
                worm_diameter=self.worm_diam_spin.value()
            )
            if self.type_combo.currentText() == "Worm":
                generator = WormGenerator(worm_params)
            else:
                generator = WormGearGenerator(worm_params)
        else:
            generator = GearGenerator(params)

        # Generate G-code
        gcode = generator.generate_gcode()

        # Save to file
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save G-Code",
            "",
            "G-Code Files (*.gcode *.nc *.tap);;All Files (*.*)"
        )

        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(gcode)
                QMessageBox.information(
                    self,
                    "Success",
                    f"G-code saved to {filename}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to save G-code: {str(e)}"
                ) 