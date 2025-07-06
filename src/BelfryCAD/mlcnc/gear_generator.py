"""
Gear Generator Module

This module provides classes and functions for generating G-code for various types of gears.
"""

import math
from dataclasses import dataclass
from typing import Optional, Tuple, List
from enum import Enum

class GearType(Enum):
    """Types of gears that can be generated."""
    SPUR = "spur"
    HELICAL = "helical"
    WORM = "worm"
    WORM_GEAR = "worm_gear"

class Handedness(Enum):
    """Handedness of helical gears and worms."""
    RIGHT = "right"
    LEFT = "left"

class TableOrientation(Enum):
    """Orientation of the rotary table."""
    PLUS_X = 0.0
    PLUS_Y = 90.0
    MINUS_X = 180.0
    MINUS_Y = 270.0

@dataclass
class GearParameters:
    """Base class for gear parameters."""
    pitch: float  # Diametral pitch
    num_teeth: int  # Number of teeth
    gear_width: float  # Width of gear in inches
    table_orientation: TableOrientation  # Rotary table orientation
    helical_angle: float = 0.0  # Helical angle in degrees
    handedness: Handedness = Handedness.RIGHT  # Handedness for helical gears

@dataclass
class WormParameters(GearParameters):
    """Parameters specific to worm gears."""
    worm_threads: int = 1  # Number of threads on worm
    worm_diameter: float = 0.5  # Diameter of worm in inches

class GearGenerator:
    """Base class for gear generation."""

    def __init__(self, params: GearParameters):
        self.params = params
        self.pi = math.pi
        self.rapid_distance = 0.1  # Rapid move distance in inches
        self.mill_direction = 1.0  # Conventional = 1.0, Climb = -1.0

    def _calculate_gear_dimensions(self) -> Tuple[float, float, float, float]:
        """Calculate basic gear dimensions."""
        hel_rad = math.radians(self.params.helical_angle)
        pitch_diam = (self.params.num_teeth / self.params.pitch) / math.cos(hel_rad)
        outside_diam = pitch_diam + (2.0 / self.params.pitch)
        whole_depth = 2.157 / self.params.pitch
        circ_pitch = self.pi / self.params.pitch
        return pitch_diam, outside_diam, whole_depth, circ_pitch

    def _calculate_cutting_parameters(self) -> Tuple[float, float, Tuple[float, float, float], float]:
        """Calculate parameters for the cutting operation."""
        hel_rad = math.radians(self.params.helical_angle)
        cut_len = self.params.gear_width / math.cos(hel_rad)
        a_axis_move = (math.tan(hel_rad) * self.params.gear_width) / (self.pi * self._calculate_gear_dimensions()[0] / 360.0)

        # Calculate perpendicular distances
        perp_ang = math.radians(self.params.table_orientation.value) - self.pi
        if self.params.helical_angle < 0.0:
            approach_ang = perp_ang + self.pi/2.0
            self.mill_direction = -1.0
        else:
            approach_ang = perp_ang - self.pi/2.0

        # Calculate perpendicular distances
        perp_xd = (self.params.gear_width/2.0) * math.cos(perp_ang) * math.cos(hel_rad)
        perp_yd = (self.params.gear_width/2.0) * math.sin(perp_ang) * math.cos(hel_rad)
        perp_zd = (self.params.gear_width/2.0) * abs(math.sin(hel_rad))

        # Apply mill direction
        a_axis_move *= self.mill_direction
        perp_xd *= self.mill_direction
        perp_yd *= self.mill_direction
        perp_zd *= self.mill_direction

        return cut_len, a_axis_move, (perp_xd, perp_yd, perp_zd), approach_ang

    def generate_gcode(self) -> str:
        """Generate G-code for the gear."""
        # Calculate dimensions and parameters
        pitch_diam, outside_diam, whole_depth, circ_pitch = self._calculate_gear_dimensions()
        cut_len, a_axis_move, perp_dists, approach_ang = self._calculate_cutting_parameters()
        perp_xd, perp_yd, perp_zd = perp_dists

        # Calculate rapid positions
        rapid_xb = self.rapid_distance * math.cos(approach_ang)
        rapid_yb = self.rapid_distance * math.sin(approach_ang)
        rapid_zb = 0.0

        rapid_x1 = rapid_xb - perp_xd
        rapid_y1 = rapid_yb - perp_yd
        rapid_z1 = rapid_zb - perp_zd
        rapid_x2 = rapid_xb + perp_xd
        rapid_y2 = rapid_yb + perp_yd
        rapid_z2 = rapid_zb + perp_zd

        # Calculate feed rate factors
        rot_feed_fact = 360.0 / (self.pi * outside_diam)
        cut_depth = self._calculate_cut_depth(circ_pitch/2.0)

        # Generate G-code
        gcode = []

        # Add header comments
        if abs(self.params.helical_angle) <= 0.00001:
            gcode.append("(          SPUR GEAR           )")
        else:
            gcode.append("(         HELICAL GEAR         )")
        gcode.append("( ---------------------------- )")
        gcode.append(f"( Rotary table is on {self.params.table_orientation.name} side.  )")
        gcode.append(f"( Gear cutter is on {self._get_cut_side(approach_ang)} side.   )")
        gcode.append("( ---------------------------- )")
        gcode.append(f"( pitch         = {self.params.pitch:3.0f}          )")
        gcode.append(f"( num. of teeth = {self.params.num_teeth:3.0f} teeth    )")
        gcode.append(f"( pitch diam.   = {pitch_diam:8.4f} in  )")
        gcode.append(f"( outside diam. = {outside_diam:8.4f} in  )")
        gcode.append(f"( helical angle = {self.params.helical_angle:8.4f} deg )")
        gcode.append(f"( whole depth   = {whole_depth:8.4f} in  )")
        gcode.append(f"( gear width    = {self.params.gear_width:8.4f} in  )")
        gcode.append(f"( circ. pitch   = {circ_pitch:8.4f} in  )")
        gcode.append("")

        # Add feed rate calculations
        gcode.append("( correct feed for angular motion )")
        gcode.append(f"#1020=[#1001*SIN[ABS[{self.params.helical_angle:.5f}]]*{rot_feed_fact:.5f}]")
        gcode.append(f"#1021=[#1001*COS[ABS[{self.params.helical_angle:.5f}]]]")
        gcode.append("#1011=[SQRT[[#1020*#1020]+[#1021*#1021]]] ( angular feed )")
        gcode.append("")

        # Generate cutting moves
        cur_depth = cut_depth
        while True:
            if cur_depth > whole_depth - 0.02:
                cur_depth = whole_depth

            # Calculate cutting positions
            cutting_xb = -1.0 * cur_depth * math.cos(approach_ang)
            cutting_yb = -1.0 * cur_depth * math.sin(approach_ang)
            cutting_zb = 0.0

            cut_x1 = cutting_xb - perp_xd
            cut_y1 = cutting_yb - perp_yd
            cut_z1 = cutting_zb - perp_zd
            cut_x2 = cutting_xb + perp_xd
            cut_y2 = cutting_yb + perp_yd
            cut_z2 = cutting_zb + perp_zd

            # Generate moves for each tooth
            first = True
            for i in range(self.params.num_teeth):
                a1 = i * (360.0 / self.params.num_teeth)
                a2 = a1 + a_axis_move

                if first:
                    first = False
                    gcode.append(f"G00 X{rapid_x1:.4f} Y{rapid_y1:.4f} Z{rapid_z1:.4f}")
                    gcode.append(f"G00 A{a1:.4f}")
                else:
                    gcode.append(f"G00 X{rapid_x1:.4f} Y{rapid_y1:.4f} Z{rapid_z1:.4f} A{a1:.4f}")

                gcode.append(f"G01 X{cut_x1:.4f} Y{cut_y1:.4f} Z{cut_z1:.4f} F#1000")
                gcode.append(f"G01 X{cut_x2:.4f} Y{cut_y2:.4f} Z{cut_z2:.4f} A{a2:.4f} F#1011")
                gcode.append(f"G00 X{rapid_x2:.4f} Y{rapid_y2:.4f} Z{rapid_z2:.4f}")
                gcode.append("")

            if cur_depth == whole_depth:
                break
            cur_depth += cut_depth

        gcode.append("G00 A0.0")
        return "\n".join(gcode)

    def _calculate_cut_depth(self, cut_width: float) -> float:
        """Calculate the depth of cut based on the cut width."""
        # This is a placeholder - implement actual calculation based on tool and material
        return 0.1

    def _get_cut_side(self, approach_ang: float) -> str:
        """Get the side of the cut based on the approach angle."""
        approach_deg = math.degrees(approach_ang) % 360.0
        if abs(approach_deg - 0.0) < 0.1:
            return "+X"
        elif abs(approach_deg - 90.0) < 0.1:
            return "+Y"
        elif abs(approach_deg - 180.0) < 0.1:
            return "-X"
        elif abs(approach_deg - 270.0) < 0.1:
            return "-Y"
        else:
            return f"{approach_deg:.1f} deg"

class WormGearGenerator(GearGenerator):
    """Generator for worm gears."""

    def __init__(self, params: WormParameters):
        super().__init__(params)
        self.worm_params = params

    def _calculate_worm_parameters(self) -> Tuple[float, float, float, float]:
        """Calculate worm-specific parameters."""
        addendum = 1.0 / self.params.pitch
        worm_pitch_diam = self.worm_params.worm_diameter - (2.0 * addendum)
        axial_pitch = self.pi / self.params.pitch
        lead = self.worm_params.worm_threads * axial_pitch
        lead_angle = math.atan2(lead, self.pi * worm_pitch_diam)
        helical_angle = math.degrees(lead_angle)

        if self.worm_params.handedness == Handedness.LEFT:
            helical_angle = -helical_angle

        return helical_angle, worm_pitch_diam, axial_pitch, lead

class WormGenerator(GearGenerator):
    """Generator for worms."""

    def __init__(self, params: WormParameters):
        super().__init__(params)
        self.worm_params = params

    def _calculate_worm_parameters(self) -> Tuple[float, float, float, float]:
        """Calculate worm-specific parameters."""
        addendum = 1.0 / self.params.pitch
        pitch_diam = self.worm_params.worm_diameter - (2.0 * addendum)
        axial_pitch = self.pi / self.params.pitch
        lead = self.worm_params.worm_threads * axial_pitch
        lead_angle = math.atan2(lead, self.pi * pitch_diam)
        helical_angle = math.degrees(lead_angle)

        if self.worm_params.handedness == Handedness.LEFT:
            helical_angle = -helical_angle

        complement_angle = 90.0 - helical_angle
        return complement_angle, pitch_diam, axial_pitch, lead