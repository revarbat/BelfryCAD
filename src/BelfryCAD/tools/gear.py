"""
Gear tool for BelfryCAD.

This tool allows users to create and manipulate gear objects in the CAD document.
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

from ..models.cad_object import CadObject, ObjectType
from ..cad_geometry import Point2D
from .base import Tool, ToolState, ToolCategory, ToolDefinition
from ..cad_geometry.spur_gear import SpurGear
from ..utils.logger import get_logger

if TYPE_CHECKING:
    from ..gui.document_window import DocumentWindow

logger = get_logger(__name__)


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


class GearCadObject(CadObject):
    """CAD object representing a gear."""
    
    def __init__(self, document_window: 'DocumentWindow', object_id: int, position: Point2D,
                 pitch_diameter: float, num_teeth: int, pressure_angle: float = 20.0, **kwargs):
        super().__init__(
            document_window, object_id, ObjectType.GEAR, coords=[position], **kwargs)
        self.position = position
        self.pitch_diameter = pitch_diameter
        self.num_teeth = num_teeth
        self.pressure_angle = pressure_angle
        
        # Create the spur gear geometry
        self.gear = SpurGear(
            pitch_diameter=pitch_diameter,
            num_teeth=num_teeth,
            pressure_angle=pressure_angle
        )
    
    def get_bounds(self):
        """Get the bounding box of the gear."""
        radius = self.pitch_diameter / 2
        return (
            self.position.x - radius,
            self.position.y - radius,
            self.position.x + radius,
            self.position.y + radius
        )
    
    def translate(self, dx: float, dy: float):
        """Translate the gear by the given offset."""
        self.position = Point2D(self.position.x + dx, self.position.y + dy)
    
    def scale(self, scale_factor: float, center: Point2D):
        """Scale the gear around the given center point."""
        # Scale the position relative to center
        dx = self.position.x - center.x
        dy = self.position.y - center.y
        self.position = Point2D(center.x + dx * scale_factor, center.y + dy * scale_factor)
        
        # Scale the pitch diameter
        self.pitch_diameter *= scale_factor
        
        # Update the gear geometry
        self.gear = SpurGear(
            pitch_diameter=self.pitch_diameter,
            num_teeth=self.num_teeth,
            pressure_angle=self.pressure_angle
        )
    
    def rotate(self, angle: float, center: Point2D):
        """Rotate the gear around the given center point."""
        # TODO: Implement rotation
        pass


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
            node_info=["Center Point2D", "Pitch Radius Point2D"]
        )]

    def show_dialog(self) -> Optional[GearParameters]:
        """Show gear creation dialog"""
        dialog = QDialog(self.document_window)
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

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.params = GearParameters(
                pitch=pitch_spin.value(),
                num_teeth=teeth_spin.value(),
                helical_angle=helical_spin.value(),
                gear_width=width_spin.value(),
                table_orientation=orient_combo.currentIndex() * 90.0
            )
            return self.params
        return None

    def create_gear(self, position: Point2D) -> Optional[GearCadObject]:
        """Create a gear at the specified position"""
        if not self.params:
            return None

        # Create gear object
        gear = GearCadObject(
            self.document_window,
            self.document_window.document.get_next_object_id(),
            position,
            self.params.pitch_diameter,
            self.params.num_teeth,
            pressure_angle=20.0  # Default pressure angle
        )

        # Add to document
        self.document_window.document.add_object(gear)
        return gear


# Export list for tool registration
GEAR_TOOLS = [
    GearTool,
]