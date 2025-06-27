"""
Gear Tools Implementation

This module implements gear creation tools based on the original TCL
mlcnc-gears.tcl implementation. It provides tools for creating:
- Spur and helical gears
- Worm gears
- Worms
"""

import math
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass

from PySide6.QtWidgets import (QGraphicsEllipseItem, QGraphicsPathItem,
                              QGraphicsLineItem, QDialog, QVBoxLayout,
                              QHBoxLayout, QLabel, QSpinBox, QDoubleSpinBox,
                              QComboBox, QPushButton, QGroupBox)
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QColor, QPainterPath, QBrush

from BelfryCAD.core.cad_objects import CADObject, ObjectType, Point
from BelfryCAD.tools.base import Tool, ToolState, ToolCategory, ToolDefinition

if TYPE_CHECKING:
    from BelfryCAD.gui.main_window import MainWindow

@dataclass
class GearParameters:
    """Parameters for gear creation"""
    pitch: float  # Diametral pitch
    num_teeth: int  # Number of teeth
    helical_angle: float  # Helical angle in degrees
    gear_width: float  # Width of gear
    table_orientation: float  # Table orientation in degrees

@dataclass
class WormGearParameters(GearParameters):
    """Parameters for worm gear creation"""
    worm_threads: int  # Number of worm threads
    worm_diameter: float  # Worm diameter
    worm_hand: str  # "left" or "right" handed

@dataclass
class WormParameters:
    """Parameters for worm creation"""
    pitch: float  # Diametral pitch
    threads: int  # Number of threads
    hand: str  # "left" or "right" handed
    length: float  # Length of worm
    outside_diameter: float  # Outside diameter
    table_orientation: float  # Table orientation in degrees

class GearObject(CADObject):
    """Gear object - represents a spur or helical gear"""

    def __init__(self, mainwin: 'MainWindow', object_id: int, position: Point,
                 params: GearParameters, **kwargs):
        super().__init__(
            mainwin, object_id, ObjectType.GEAR, coords=[position], **kwargs)
        self.attributes.update({
            'pitch': params.pitch,
            'num_teeth': params.num_teeth,
            'helical_angle': params.helical_angle,
            'gear_width': params.gear_width,
            'table_orientation': params.table_orientation
        })

    @property
    def position(self) -> Point:
        return self.coords[0]

    @property
    def pitch_diameter(self) -> float:
        """Calculate pitch diameter"""
        hel_rad = math.radians(self.attributes['helical_angle'])
        return ((self.attributes['num_teeth'] / self.attributes['pitch']) /
                math.cos(hel_rad))

    @property
    def outside_diameter(self) -> float:
        """Calculate outside diameter"""
        return self.pitch_diameter + (2.0 / self.attributes['pitch'])

    @property
    def whole_depth(self) -> float:
        """Calculate whole depth"""
        return 2.157 / self.attributes['pitch']

class GearTool(Tool):
    """Tool for creating spur and helical gears"""

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definition"""
        return [ToolDefinition(
            token="GEAR",
            name="Gear Tool",
            category=ToolCategory.CAM,
            icon="tool-spurgear",
            cursor="crosshair",
            is_creator=True,
            secondary_key="G",
            node_info=["Center Point", "Pitch Radius Point"]
        )]

    def show_dialog(self) -> Optional[GearParameters]:
        """Show gear creation dialog"""
        dialog = QDialog(self.mainwin)
        dialog.setWindowTitle("Create Gear")
        layout = QVBoxLayout()

        # Pitch
        pitch_layout = QHBoxLayout()
        pitch_layout.addWidget(QLabel("Diametral Pitch:"))
        pitch_spin = QDoubleSpinBox()
        pitch_spin.setRange(1, 100)
        pitch_spin.setValue(self.params.pitch)
        pitch_layout.addWidget(pitch_spin)
        layout.addLayout(pitch_layout)

        # Number of teeth
        teeth_layout = QHBoxLayout()
        teeth_layout.addWidget(QLabel("Number of Teeth:"))
        teeth_spin = QSpinBox()
        teeth_spin.setRange(8, 200)
        teeth_spin.setValue(self.params.num_teeth)
        teeth_layout.addWidget(teeth_spin)
        layout.addLayout(teeth_layout)

        # Helical angle
        helical_layout = QHBoxLayout()
        helical_layout.addWidget(QLabel("Helical Angle (degrees):"))
        helical_spin = QDoubleSpinBox()
        helical_spin.setRange(-45, 45)
        helical_spin.setValue(self.params.helical_angle)
        helical_layout.addWidget(helical_spin)
        layout.addLayout(helical_layout)

        # Gear width
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Gear Width:"))
        width_spin = QDoubleSpinBox()
        width_spin.setRange(0.1, 2.0)
        width_spin.setSingleStep(0.1)
        width_spin.setValue(self.params.gear_width)
        width_layout.addWidget(width_spin)
        layout.addLayout(width_layout)

        # Table orientation
        orient_layout = QHBoxLayout()
        orient_layout.addWidget(QLabel("Table Orientation:"))
        orient_combo = QComboBox()
        orient_combo.addItems(["0° (+X)", "90° (+Y)", "180° (-X)", "270° (-Y)"])
        orient_layout.addWidget(orient_combo)
        layout.addLayout(orient_layout)

        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)

        # Connect signals
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        if dialog.exec() == QDialog.Accepted:
            self.params = GearParameters(
                pitch=pitch_spin.value(),
                num_teeth=teeth_spin.value(),
                helical_angle=helical_spin.value(),
                gear_width=width_spin.value(),
                table_orientation=orient_combo.currentIndex() * 90.0
            )
            return self.params
        return None

    def create_gear(self, position: Point) -> Optional[GearObject]:
        """Create a gear at the specified position"""
        if not self.params:
            return None

        # Create gear object
        gear = GearObject(
            self.mainwin,
            self.mainwin.document.get_next_object_id(),
            position,
            self.params
        )

        # Add to document
        self.mainwin.document.add_object(gear)
        return gear


# Export list for tool registration
GEAR_TOOLS = [
    GearTool,
]