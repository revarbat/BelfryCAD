"""
Cutting Parameter Calculator

This module provides calculations for cutting parameters based on
material properties, tool specifications, and machining operations.
Translated from the original TCL implementation.
"""

import math
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .feed_optimizer import MaterialType


class OperationType(Enum):
    """Types of machining operations."""
    ROUGHING = "Roughing"
    FINISHING = "Finishing"
    PROFILING = "Profiling"
    DRILLING = "Drilling"
    TAPPING = "Tapping"
    BORING = "Boring"
    SLOTTING = "Slotting"


class ToolGeometry(Enum):
    """CNCTool geometry types."""
    EMPTY_SLOT = "Empty Slot"
    SQUARE_END_MILL = "Square End Mill"
    BALL_END_MILL = "Ball End Mill"
    CORNER_RADIUS_END_MILL = "Corner Radius End Mill"
    FACE_MILL = "Face Mill"
    DRILL = "Drill"
    TAP = "Tap"
    BORING_BAR = "Boring Bar"
    FLY_CUTTER = "Fly Cutter"

class ToolMaterial(Enum):
    """CNCTool material types."""
    HSS = "HSS"
    CARBIDE = "Carbide"
    COBALT = "Cobalt"
    CERAMIC = "Ceramic"
    CBN = "CBN"

class ToolCoating(Enum):
    """CNCTool coating types."""
    NONE = "None"
    WC = "Tungsten Carbide (WC)"
    Al2O3 = "Aluminum Oxide (Al2O3)"
    TiN = "Titanium Nitride (TiN)"
    TiCN = "Titanium Carbonitride (TiCN)"
    TiAlN = "Titanium Aluminum Nitride (TiAlN)"
    AlTiN = "Aluminum Titanium Nitride (AlTiN)"
    AlCrN = "Aluminum Chromium Nitride (AlCrN)"
    TiB2 = "Titanium Boron Nitride (TiB2)"
    ZrN = "Zirconium Nitride (ZrN)"
    DIAMOND = "Diamond"

@dataclass
class ToolSpecification:
    """CNCTool specification parameters."""
    diameter: float
    length: float
    flute_count: int = 2
    geometry: ToolGeometry = ToolGeometry.SQUARE_END_MILL
    material: ToolMaterial = ToolMaterial.HSS
    coating: ToolCoating = ToolCoating.NONE
    corner_radius: float = 0.0
    chamfer_angle: float = 0.0
    helix_angle: Optional[float] = None
    rake_angle: Optional[float] = None
    tool_id: Optional[int] = None


@dataclass
class MachineCapabilities:
    """CNC Machine tool capabilities."""
    max_spindle_speed: float
    max_feed_rate: float
    max_power: float  # HP or kW
    spindle_taper: str  # BT40, CAT40, etc.
    positioning_accuracy: float
    repeatability: float
    max_tool_diameter: float
    max_tool_length: float


@dataclass
class CuttingCondition:
    """Complete cutting condition specification."""
    tool: ToolSpecification
    material: MaterialType
    operation: OperationType
    depth_of_cut: float
    width_of_cut: float
    spindle_speed: float
    feed_rate: float
    coolant: bool = True
    cutting_direction: str = "conventional"


class CuttingParameterCalculator:
    """
    Calculator for cutting parameters and performance metrics.

    This class provides comprehensive calculations for machining
    parameters including forces, power, vibration analysis, etc.
    """

    def __init__(self):
        """Initialize the calculator."""
        self.material_database = self._load_material_database()
        self.tool_database = self._load_tool_database()

    def _load_material_database(self) -> Dict[MaterialType, Dict[str, Any]]:
        """Load comprehensive material properties database."""
        return {
            MaterialType.ALUMINUM: {
                "density": 0.0975,  # lb/in³
                "modulus": 10.0e6,   # psi
                "poisson_ratio": 0.33,
                "specific_heat": 0.214,  # BTU/lb·°F
                "melting_point": 1220,   # °F
                "chip_formation": "continuous",
                "work_hardening": 0.1,
                "cutting_force_coefficient": {
                    "Ktc": 65000,  # psi
                    "Kte": 15000,  # psi
                    "Krc": 25000,  # psi
                    "Kre": 5000    # psi
                }
            },
            MaterialType.STEEL: {
                "density": 0.284,
                "modulus": 30.0e6,
                "poisson_ratio": 0.27,
                "specific_heat": 0.12,
                "melting_point": 2750,
                "chip_formation": "discontinuous",
                "work_hardening": 0.3,
                "cutting_force_coefficient": {
                    "Ktc": 180000,
                    "Kte": 40000,
                    "Krc": 70000,
                    "Kre": 15000
                }
            },
            MaterialType.STAINLESS_STEEL: {
                "density": 0.29,
                "modulus": 28.0e6,
                "poisson_ratio": 0.30,
                "specific_heat": 0.12,
                "melting_point": 2800,
                "chip_formation": "continuous",
                "work_hardening": 0.5,
                "cutting_force_coefficient": {
                    "Ktc": 220000,
                    "Kte": 50000,
                    "Krc": 85000,
                    "Kre": 20000
                }
            },
            MaterialType.BRASS: {
                "density": 0.306,
                "modulus": 15.0e6,
                "poisson_ratio": 0.34,
                "specific_heat": 0.09,
                "melting_point": 1700,
                "chip_formation": "continuous",
                "work_hardening": 0.2,
                "cutting_force_coefficient": {
                    "Ktc": 120000,
                    "Kte": 30000,
                    "Krc": 40000,
                    "Kre": 10000
                }
            },
            MaterialType.COPPER: {
                "density": 0.323,
                "modulus": 17.0e6,
                "poisson_ratio": 0.35,
                "specific_heat": 0.09,
                "melting_point": 1981,
                "chip_formation": "continuous",
                "work_hardening": 0.15,
                "cutting_force_coefficient": {
                    "Ktc": 140000,
                    "Kte": 35000,
                    "Krc": 50000,
                    "Kre": 12000
                }
            },
            MaterialType.PLASTIC: {
                "density": 0.032,  # lb/in³
                "modulus": 0.5e6,   # psi
                "poisson_ratio": 0.35,
                "specific_heat": 0.4,  # BTU/lb·°F
                "melting_point": 350,   # °F
                "chip_formation": "continuous",
                "work_hardening": 0.05,
                "cutting_force_coefficient": {
                    "Ktc": 50000,  # psi
                    "Kte": 10000,  # psi
                    "Krc": 20000,  # psi
                    "Kre": 3000    # psi
                }
            },
            MaterialType.TITANIUM: {
                "density": 0.163,  # lb/in³
                "modulus": 16.0e6,  # psi
                "poisson_ratio": 0.32,
                "specific_heat": 0.11,  # BTU/lb·°F
                "melting_point": 3034,   # °F
                "chip_formation": "discontinuous",
                "work_hardening": 0.4,
                "cutting_force_coefficient": {
                    "Ktc": 250000,  # psi
                    "Kte": 60000,   # psi
                    "Krc": 90000,   # psi
                    "Kre": 20000    # psi
                }
            },
            MaterialType.CARBON_FIBER: {
                "density": 0.07,  # lb/in³
                "modulus": 30.0e6,  # psi
                "poisson_ratio": 0.2,
                "specific_heat": 0.2,  # BTU/lb·°F
                "melting_point": 500,   # °F
                "chip_formation": "continuous",
                "work_hardening": 0.1,
                "cutting_force_coefficient": {
                    "Ktc": 80000,  # psi
                    "Kte": 20000,  # psi
                    "Krc": 30000,  # psi
                    "Kre": 7000    # psi
                }
            },
            MaterialType.WOOD: {
                "density": 0.025,  # lb/in³
                "modulus": 1.5e6,   # psi
                "poisson_ratio": 0.4,
                "specific_heat": 0.5,  # BTU/lb·°F
                "melting_point": 500,   # °F
                "chip_formation": "continuous",
                "work_hardening": 0.05,
                "cutting_force_coefficient": {
                    "Ktc": 30000,  # psi
                    "Kte": 7000,   # psi
                    "Krc": 15000,  # psi
                    "Kre": 2000    # psi
                }
            }
        }

    def _load_tool_database(self) -> Dict[str, Dict[str, Any]]:
        """Load tool material properties database."""
        return {
            "HSS": {
                "max_temperature": 1000,  # °F
                "thermal_conductivity": 25,  # BTU/hr·ft·°F
                "wear_resistance": 0.6,
                "toughness": 0.9
            },
            "Carbide": {
                "max_temperature": 1800,
                "thermal_conductivity": 35,
                "wear_resistance": 0.9,
                "toughness": 0.6
            },
            "Ceramic": {
                "max_temperature": 2000,
                "thermal_conductivity": 15,
                "wear_resistance": 0.95,
                "toughness": 0.3
            },
            "CBN": {
                "max_temperature": 2200,
                "thermal_conductivity": 100,
                "wear_resistance": 0.98,
                "toughness": 0.4
            }
        }

    def calculate_cutting_forces(self, condition: CuttingCondition) -> Dict[str, float]:
        """
        Calculate cutting forces for given conditions.

        Args:
            condition: Complete cutting condition specification

        Returns:
            Dictionary with force components in lbf
        """
        material_props = self.material_database.get(condition.material)
        if not material_props:
            raise ValueError(f"Unknown material: {condition.material}")

        force_coeffs = material_props["cutting_force_coefficient"]

        # Calculate chip thickness
        chip_thickness = self._calculate_chip_thickness(
            condition.feed_rate, condition.tool.flute_count,
            condition.spindle_speed, condition.tool.diameter)

        # Calculate cutting area
        cutting_area = condition.depth_of_cut * condition.width_of_cut

        # Tangential force (main cutting force)
        Ft = (force_coeffs["Ktc"] * cutting_area * chip_thickness +
              force_coeffs["Kte"] * cutting_area)

        # Radial force
        Fr = (force_coeffs["Krc"] * cutting_area * chip_thickness +
              force_coeffs["Kre"] * cutting_area)

        # Axial force (thrust)
        Fa = Ft * 0.3  # Approximate relationship

        # Resultant force
        F_resultant = math.sqrt(Ft**2 + Fr**2 + Fa**2)

        return {
            "tangential": Ft,
            "radial": Fr,
            "axial": Fa,
            "resultant": F_resultant
        }

    def calculate_power_consumption(self, condition: CuttingCondition) -> Dict[str, float]:
        """
        Calculate power consumption for machining operation.

        Args:
            condition: Cutting condition specification

        Returns:
            Dictionary with power values in HP
        """
        forces = self.calculate_cutting_forces(condition)

        # Cutting speed in ft/min
        cutting_speed = (math.pi * condition.tool.diameter *
                        condition.spindle_speed) / 12

        # Cutting power (main component)
        cutting_power = (forces["tangential"] * cutting_speed) / 33000  # HP

        # Spindle power (friction and acceleration)
        spindle_power = cutting_power * 0.2

        # Feed power (usually negligible for milling)
        feed_power = cutting_power * 0.05

        # Total power with efficiency factor
        machine_efficiency = 0.85
        total_power = (cutting_power + spindle_power + feed_power) / machine_efficiency

        return {
            "cutting": cutting_power,
            "spindle": spindle_power,
            "feed": feed_power,
            "total": total_power
        }

    def calculate_material_removal_rate(self, condition: CuttingCondition) -> float:
        """
        Calculate material removal rate.

        Args:
            condition: Cutting condition specification

        Returns:
            Material removal rate in in³/min
        """
        return (condition.feed_rate * condition.depth_of_cut *
                condition.width_of_cut)

    def calculate_tool_deflection(self, condition: CuttingCondition) -> Dict[str, float]:
        """
        Calculate tool deflection under cutting forces.

        Args:
            condition: Cutting condition specification

        Returns:
            Dictionary with deflection values in inches
        """
        forces = self.calculate_cutting_forces(condition)

        # CNCTool material properties (assume steel for simplicity)
        E = 30.0e6  # psi (modulus of elasticity)

        # CNCTool geometry
        L = condition.tool.length  # length
        D = condition.tool.diameter  # diameter
        I = math.pi * D**4 / 64  # moment of inertia

        # Deflection at tip (cantilever beam with point load)
        deflection_tip = (forces["resultant"] * L**3) / (3 * E * I)

        # Maximum deflection (at 2/3 length)
        deflection_max = deflection_tip * 1.1

        return {
            "tip": deflection_tip,
            "maximum": deflection_max,
            "allowable": D * 0.001  # 0.1% of diameter
        }

    def calculate_surface_roughness(self, condition: CuttingCondition) -> Dict[str, float]:
        """
        Calculate expected surface roughness.

        Args:
            condition: Cutting condition specification

        Returns:
            Dictionary with roughness values in microinches
        """
        # Feed per tooth
        chip_load = (condition.feed_rate /
                    (condition.spindle_speed * condition.tool.flute_count))

        # CNCTool geometry factor
        if condition.tool.geometry == ToolGeometry.BALL_END_MILL:
            geometry_factor = 0.5
        elif condition.tool.corner_radius:
            geometry_factor = 0.7
        else:
            geometry_factor = 1.0

        # Theoretical roughness (based on feed marks)
        Ra_theoretical = (chip_load**2 / (8 * condition.tool.corner_radius or 0.001)) * 1e6

        # Practical roughness (includes vibration, tool wear, etc.)
        Ra_practical = Ra_theoretical * geometry_factor * 1.5

        return {
            "theoretical": Ra_theoretical,
            "practical": Ra_practical,
            "achievable": Ra_practical * 0.7
        }

    def calculate_vibration_frequency(self, condition: CuttingCondition) -> Dict[str, float]:
        """
        Calculate vibration frequencies for chatter analysis.

        Args:
            condition: Cutting condition specification

        Returns:
            Dictionary with frequency values in Hz
        """
        # Tooth passing frequency
        tooth_frequency = (condition.spindle_speed * condition.tool.flute_count) / 60

        # Spindle frequency
        spindle_frequency = condition.spindle_speed / 60

        # Natural frequency estimation (simplified)
        # Based on tool geometry and material
        E = 30.0e6  # psi
        rho = 0.284  # lb/in³ (steel)
        L = condition.tool.length
        D = condition.tool.diameter

        # First bending mode frequency
        natural_frequency = (1.875**2 / (2 * math.pi)) * math.sqrt(
            (E * math.pi * D**4 / 64) / (rho * math.pi * D**2 / 4 * L**4)
        )

        return {
            "tooth_passing": tooth_frequency,
            "spindle": spindle_frequency,
            "natural": natural_frequency,
            "chatter_risk": abs(natural_frequency - tooth_frequency) / natural_frequency
        }

    def _calculate_chip_thickness(self, feed_rate: float, flute_count: int,
                                 spindle_speed: float, tool_diameter: float) -> float:
        """Calculate average chip thickness."""
        # Feed per tooth
        fz = feed_rate / (spindle_speed * flute_count)

        # For end milling, chip thickness varies with angle
        # Use average value
        return fz / 2

    def optimize_for_constraints(self, condition: CuttingCondition,
                                machine: MachineCapabilities) -> Dict[str, Any]:
        """
        Optimize cutting parameters within machine constraints.

        Args:
            condition: Initial cutting condition
            machine: Machine capabilities

        Returns:
            Dictionary with optimized parameters and analysis
        """
        analysis = {}

        # Check power constraint
        power = self.calculate_power_consumption(condition)
        if power["total"] > machine.max_power:
            # Reduce feed rate to stay within power limit
            scale_factor = machine.max_power / power["total"]
            optimized_feed = condition.feed_rate * scale_factor
            analysis["power_limited"] = True
            analysis["suggested_feed_rate"] = optimized_feed
        else:
            analysis["power_limited"] = False
            analysis["suggested_feed_rate"] = condition.feed_rate

        # Check spindle speed constraint
        if condition.spindle_speed > machine.max_spindle_speed:
            analysis["speed_limited"] = True
            analysis["suggested_spindle_speed"] = machine.max_spindle_speed
        else:
            analysis["speed_limited"] = False
            analysis["suggested_spindle_speed"] = condition.spindle_speed

        # Check tool deflection
        deflection = self.calculate_tool_deflection(condition)
        if deflection["tip"] > deflection["allowable"]:
            analysis["deflection_excessive"] = True
            analysis["suggested_depth_reduction"] = 0.5
        else:
            analysis["deflection_excessive"] = False

        # Check vibration/chatter risk
        vibration = self.calculate_vibration_frequency(condition)
        if vibration["chatter_risk"] < 0.1:  # Too close to natural frequency
            analysis["chatter_risk"] = "high"
            analysis["suggested_speed_adjustment"] = 0.9
        else:
            analysis["chatter_risk"] = "low"

        return analysis