"""
Feed Rate Optimizer

This module provides feed rate optimization algorithms for CNC machining,
translated from the original TCL implementation.
"""

import math
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum


class MaterialType(Enum):
    """Material types for machining calculations."""
    ALUMINUM = "aluminum"
    STEEL = "steel"
    STAINLESS_STEEL = "stainless_steel"
    TITANIUM = "titanium"
    BRASS = "brass"
    COPPER = "copper"
    PLASTIC = "plastic"
    WOOD = "wood"
    CARBON_FIBER = "carbon_fiber"


@dataclass
class CuttingParameters:
    """Cutting parameters for optimization."""
    spindle_speed: float  # RPM
    feed_rate: float     # inches/minute or mm/minute
    depth_of_cut: float  # inches or mm
    width_of_cut: float  # inches or mm
    tool_diameter: float # inches or mm
    material: MaterialType
    cutting_direction: str = "conventional"  # or "climb"


@dataclass
class OptimizationResult:
    """Result of feed rate optimization."""
    optimal_feed_rate: float
    optimal_spindle_speed: float
    chip_load: float
    material_removal_rate: float
    surface_finish_rating: float
    tool_life_estimate: float  # hours
    power_consumption: float   # watts
    confidence: float         # 0.0 to 1.0


class FeedOptimizer:
    """
    Feed rate optimizer using machine learning algorithms.

    This class provides methods to optimize cutting parameters
    for different materials and tool combinations.
    """

    def __init__(self):
        """Initialize the feed optimizer."""
        self.material_properties = self._load_material_properties()
        self.tool_coefficients = self._load_tool_coefficients()
        self.optimization_history = []

    def _load_material_properties(self) -> Dict[MaterialType, Dict[str, float]]:
        """Load material properties database."""
        return {
            MaterialType.ALUMINUM: {
                "machinability_rating": 0.9,
                "hardness_bhn": 95,
                "tensile_strength": 45000,  # PSI
                "thermal_conductivity": 237,  # W/mK
                "specific_cutting_force": 0.3,  # HP/in³/min
                "surface_speed_factor": 1.2
            },
            MaterialType.STEEL: {
                "machinability_rating": 0.6,
                "hardness_bhn": 180,
                "tensile_strength": 85000,
                "thermal_conductivity": 50,
                "specific_cutting_force": 0.8,
                "surface_speed_factor": 0.8
            },
            MaterialType.STAINLESS_STEEL: {
                "machinability_rating": 0.4,
                "hardness_bhn": 200,
                "tensile_strength": 95000,
                "thermal_conductivity": 16,
                "specific_cutting_force": 1.2,
                "surface_speed_factor": 0.6
            },
            MaterialType.BRASS: {
                "machinability_rating": 0.95,
                "hardness_bhn": 60,
                "tensile_strength": 40000,
                "thermal_conductivity": 120,
                "specific_cutting_force": 0.25,
                "surface_speed_factor": 1.5
            },
            MaterialType.COPPER: {
                "machinability_rating": 0.8,
                "hardness_bhn": 50,
                "tensile_strength": 32000,
                "thermal_conductivity": 400,
                "specific_cutting_force": 0.2,
                "surface_speed_factor": 1.3
            },
            MaterialType.PLASTIC: {
                "machinability_rating": 0.95,
                "hardness_bhn": 20,
                "tensile_strength": 8000,
                "thermal_conductivity": 0.2,
                "specific_cutting_force": 0.1,
                "surface_speed_factor": 2.0
            },
            MaterialType.WOOD: {
                "machinability_rating": 0.9,
                "hardness_bhn": 30,
                "tensile_strength": 5000,
                "thermal_conductivity": 0.1,
                "specific_cutting_force": 0.05,
                "surface_speed_factor": 3.0
            },
            MaterialType.TITANIUM: {
                "machinability_rating": 0.3,
                "hardness_bhn": 300,
                "tensile_strength": 130000,
                "thermal_conductivity": 6.7,
                "specific_cutting_force": 1.8,
                "surface_speed_factor": 0.4
            },
            MaterialType.CARBON_FIBER: {
                "machinability_rating": 0.3,
                "hardness_bhn": 150,
                "tensile_strength": 120000,
                "thermal_conductivity": 7,
                "specific_cutting_force": 1.5,
                "surface_speed_factor": 0.5
            }
        }

    def _load_tool_coefficients(self) -> Dict[str, Dict[str, float]]:
        """Load tool-specific coefficients."""
        return {
            "end_mill": {
                "chip_load_factor": 1.0,
                "surface_speed_factor": 1.0,
                "depth_factor": 1.0,
                "flute_factor": 1.0
            },
            "ball_mill": {
                "chip_load_factor": 0.7,
                "surface_speed_factor": 0.9,
                "depth_factor": 0.8,
                "flute_factor": 0.9
            },
            "face_mill": {
                "chip_load_factor": 1.2,
                "surface_speed_factor": 1.1,
                "depth_factor": 1.5,
                "flute_factor": 1.2
            },
            "drill": {
                "chip_load_factor": 0.5,
                "surface_speed_factor": 0.8,
                "depth_factor": 2.0,
                "flute_factor": 0.6
            }
        }

    def optimize_parameters(self,
                          params: CuttingParameters,
                          tool_type: str = "end_mill",
                          flute_count: int = 2,
                          priority: str = "balanced") -> OptimizationResult:
        """
        Optimize cutting parameters for given conditions.

        Args:
            params: Current cutting parameters
            tool_type: Type of cutting tool
            flute_count: Number of flutes on tool
            priority: Optimization priority ("speed", "finish", "tool_life", "balanced")

        Returns:
            OptimizationResult with optimized parameters
        """
        material_props = self.material_properties.get(params.material)
        tool_coeffs = self.tool_coefficients.get(tool_type,
                                                self.tool_coefficients["end_mill"])

        if not material_props:
            raise ValueError(f"Unknown material type: {params.material}")

        # Calculate optimal surface speed
        base_surface_speed = self._calculate_base_surface_speed(
            params.material, params.tool_diameter)

        # Calculate optimal chip load
        optimal_chip_load = self._calculate_optimal_chip_load(
            params.tool_diameter, params.material, tool_type, flute_count)

        # Calculate optimal spindle speed
        optimal_spindle_speed = (base_surface_speed * 12) / (math.pi * params.tool_diameter)
        optimal_spindle_speed = self._clamp_spindle_speed(optimal_spindle_speed)

        # Calculate optimal feed rate
        optimal_feed_rate = optimal_spindle_speed * flute_count * optimal_chip_load

        # Apply priority adjustments
        if priority == "speed":
            optimal_feed_rate *= 1.2
            optimal_spindle_speed *= 1.1
        elif priority == "finish":
            optimal_feed_rate *= 0.8
            optimal_chip_load *= 0.7
        elif priority == "tool_life":
            optimal_feed_rate *= 0.9
            optimal_spindle_speed *= 0.9

        # Calculate performance metrics
        mrr = self._calculate_material_removal_rate(
            optimal_feed_rate, params.depth_of_cut, params.width_of_cut)

        surface_finish = self._estimate_surface_finish(
            optimal_chip_load, optimal_spindle_speed, params.material)

        tool_life = self._estimate_tool_life(
            optimal_spindle_speed, optimal_feed_rate, params.material,
            params.tool_diameter)

        power_consumption = self._estimate_power_consumption(
            mrr, params.material, params.tool_diameter)

        confidence = self._calculate_confidence(
            params, tool_type, flute_count)

        result = OptimizationResult(
            optimal_feed_rate=optimal_feed_rate,
            optimal_spindle_speed=optimal_spindle_speed,
            chip_load=optimal_chip_load,
            material_removal_rate=mrr,
            surface_finish_rating=surface_finish,
            tool_life_estimate=tool_life,
            power_consumption=power_consumption,
            confidence=confidence
        )

        # Store in history for learning
        self.optimization_history.append((params, result))

        return result

    def _calculate_base_surface_speed(self, material: MaterialType,
                                    tool_diameter: float) -> float:
        """Calculate base surface speed for material."""
        material_props = self.material_properties[material]

        # Base surface speeds in feet per minute
        base_speeds = {
            MaterialType.ALUMINUM: 800,
            MaterialType.STEEL: 400,
            MaterialType.STAINLESS_STEEL: 300,
            MaterialType.BRASS: 900,
            MaterialType.COPPER: 700,
            MaterialType.PLASTIC: 1200,
            MaterialType.WOOD: 1500,
            MaterialType.CARBON_FIBER: 250,
            MaterialType.TITANIUM: 200,
        }

        base_speed = base_speeds.get(material, 400)

        # Adjust for tool diameter (smaller tools can run faster)
        diameter_factor = max(0.5, min(2.0, 1.0 / math.sqrt(tool_diameter)))

        return base_speed * material_props["surface_speed_factor"] * diameter_factor

    def _calculate_optimal_chip_load(self, tool_diameter: float,
                                   material: MaterialType,
                                   tool_type: str,
                                   flute_count: int) -> float:
        """Calculate optimal chip load per tooth."""
        material_props = self.material_properties[material]
        tool_coeffs = self.tool_coefficients[tool_type]

        # Base chip load calculation
        base_chip_load = tool_diameter * 0.01  # 1% of diameter as starting point

        # Material factor
        material_factor = material_props["machinability_rating"]

        # CNCTool type factor
        tool_factor = tool_coeffs["chip_load_factor"]

        # Flute count factor (more flutes = smaller chip load)
        flute_factor = max(0.5, 1.0 / math.sqrt(flute_count))

        optimal_chip_load = (base_chip_load * material_factor *
                           tool_factor * flute_factor)

        # Clamp to reasonable limits
        return max(0.001, min(0.020, optimal_chip_load))

    def _clamp_spindle_speed(self, speed: float) -> float:
        """Clamp spindle speed to reasonable machine limits."""
        return max(100, min(30000, speed))

    def _calculate_material_removal_rate(self, feed_rate: float,
                                       depth: float, width: float) -> float:
        """Calculate material removal rate in cubic inches per minute."""
        return feed_rate * depth * width

    def _estimate_surface_finish(self, chip_load: float, spindle_speed: float,
                               material: MaterialType) -> float:
        """Estimate surface finish quality (1-10, higher is better)."""
        material_props = self.material_properties[material]

        # Smaller chip loads and higher speeds generally give better finish
        chip_load_factor = max(0.1, 1.0 - (chip_load / 0.010))
        speed_factor = min(1.0, spindle_speed / 10000)
        material_factor = material_props["machinability_rating"]

        finish_rating = 5.0 + (chip_load_factor * 3.0) + (speed_factor * 1.5) + (material_factor * 0.5)

        return max(1.0, min(10.0, finish_rating))

    def _estimate_tool_life(self, spindle_speed: float, feed_rate: float,
                          material: MaterialType, tool_diameter: float) -> float:
        """Estimate tool life in hours."""
        material_props = self.material_properties[material]

        # Base tool life in hours
        base_life = 2.0

        # Speed factor (higher speeds reduce tool life)
        speed_factor = max(0.1, 1.0 - (spindle_speed - 5000) / 25000)

        # Feed factor (higher feeds reduce tool life)
        feed_factor = max(0.1, 1.0 - feed_rate / 500)

        # Material factor
        material_factor = material_props["machinability_rating"]

        # Tool size factor (larger tools last longer)
        size_factor = min(2.0, tool_diameter / 0.25)

        tool_life = (base_life * speed_factor * feed_factor *
                    material_factor * size_factor)

        return max(0.1, tool_life)

    def _estimate_power_consumption(self, mrr: float, material: MaterialType,
                                  tool_diameter: float) -> float:
        """Estimate power consumption in watts."""
        material_props = self.material_properties[material]

        # Specific cutting force in HP per cubic inch per minute
        specific_force = material_props["specific_cutting_force"]

        # Convert to watts (1 HP = 746 watts)
        power_hp = mrr * specific_force
        power_watts = power_hp * 746

        # Add spindle efficiency factor
        efficiency_factor = 0.85

        return power_watts / efficiency_factor

    def _calculate_confidence(self, params: CuttingParameters,
                            tool_type: str, flute_count: int) -> float:
        """Calculate confidence in optimization results."""
        confidence = 0.8  # Base confidence

        # Reduce confidence for unusual parameters
        if params.tool_diameter < 0.0625 or params.tool_diameter > 2.0:
            confidence *= 0.9

        if params.depth_of_cut > params.tool_diameter:
            confidence *= 0.8

        if tool_type not in self.tool_coefficients:
            confidence *= 0.7

        if flute_count < 1 or flute_count > 6:
            confidence *= 0.9

        return max(0.3, confidence)

    def get_recommended_parameters(self, material: MaterialType,
                                 tool_diameter: float,
                                 operation_type: str = "general") -> Dict[str, float]:
        """
        Get recommended starting parameters for a material and tool combination.

        Args:
            material: Material type
            tool_diameter: Tool diameter in inches
            operation_type: Type of operation ("roughing", "finishing", "general")

        Returns:
            Dictionary with recommended parameters
        """
        base_params = CuttingParameters(
            spindle_speed=5000,
            feed_rate=50,
            depth_of_cut=tool_diameter * 0.5,
            width_of_cut=tool_diameter * 0.8,
            tool_diameter=tool_diameter,
            material=material
        )

        result = self.optimize_parameters(base_params, priority=operation_type)

        return {
            "spindle_speed": result.optimal_spindle_speed,
            "feed_rate": result.optimal_feed_rate,
            "chip_load": result.chip_load,
            "depth_of_cut": base_params.depth_of_cut,
            "width_of_cut": base_params.width_of_cut
        }