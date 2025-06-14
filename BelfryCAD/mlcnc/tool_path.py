"""
Tool Path Optimizer

This module provides tool path optimization algorithms for CNC machining,
including strategies for minimizing machining time, tool wear, and
surface finish optimization. Translated from the original TCL implementation.
"""

import math
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum


class PathStrategy(Enum):
    """Tool path strategies."""
    CONVENTIONAL = "conventional"
    CLIMB = "climb"
    ADAPTIVE = "adaptive"
    TROCHOIDAL = "trochoidal"
    HIGH_SPEED = "high_speed"


class PathType(Enum):
    """Types of tool paths."""
    ROUGHING = "roughing"
    SEMI_FINISHING = "semi_finishing"
    FINISHING = "finishing"
    DRILLING = "drilling"
    PROFILING = "profiling"


@dataclass
class Point3D:
    """3D point representation."""
    x: float
    y: float
    z: float


@dataclass
class ToolPathSegment:
    """Individual tool path segment."""
    start: Point3D
    end: Point3D
    feed_rate: float
    spindle_speed: float
    path_type: PathType
    strategy: PathStrategy


@dataclass
class GeometryBounds:
    """Bounding box for geometry."""
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    min_z: float
    max_z: float


@dataclass
class MachiningParameters:
    """Machining operation parameters."""
    tool_diameter: float
    stepover: float
    stepdown: float
    finish_allowance: float
    ramp_angle: float
    entry_angle: float
    exit_angle: float


class ToolPathOptimizer:
    """
    Tool path optimizer for CNC machining operations.

    This class provides algorithms to optimize tool paths for
    various machining strategies and objectives.
    """

    def __init__(self):
        """Initialize the tool path optimizer."""
        self.optimization_history = []
        self.strategy_weights = self._load_strategy_weights()

    def _load_strategy_weights(self) -> Dict[str, Dict[str, float]]:
        """Load optimization strategy weights."""
        return {
            "time_optimal": {
                "machining_time": 1.0,
                "tool_changes": 0.3,
                "rapids": 0.2,
                "surface_finish": 0.1
            },
            "surface_optimal": {
                "surface_finish": 1.0,
                "machining_time": 0.3,
                "tool_wear": 0.4,
                "vibration": 0.6
            },
            "tool_life_optimal": {
                "tool_wear": 1.0,
                "cutting_forces": 0.8,
                "heat_generation": 0.7,
                "machining_time": 0.2
            },
            "balanced": {
                "machining_time": 0.6,
                "surface_finish": 0.7,
                "tool_wear": 0.5,
                "efficiency": 0.8
            }
        }

    def generate_roughing_path(
            self,
            geometry_bounds: GeometryBounds,
            params: MachiningParameters,
            strategy: PathStrategy = PathStrategy.CONVENTIONAL
    ) -> List[ToolPathSegment]:
        """
        Generate roughing tool path.

        Args:
            geometry_bounds: Geometry bounding box
            params: Machining parameters
            strategy: Roughing strategy

        Returns:
            List of tool path segments
        """
        segments = []

        # Calculate number of passes
        total_depth = geometry_bounds.max_z - geometry_bounds.min_z
        num_z_passes = max(1, int(math.ceil(total_depth / params.stepdown)))

        # Calculate stepover pattern
        total_width = geometry_bounds.max_x - geometry_bounds.min_x
        num_x_passes = max(1, int(math.ceil(total_width / params.stepover)))

        for z_pass in range(num_z_passes):
            current_z = geometry_bounds.max_z - (z_pass * params.stepdown)

            for x_pass in range(num_x_passes):
                current_x = (
                    geometry_bounds.min_x +
                    (x_pass * params.stepover)
                )

                if strategy == PathStrategy.CONVENTIONAL:
                    segments.extend(self._generate_conventional_pass(
                        current_x, current_z, geometry_bounds, params))
                elif strategy == PathStrategy.CLIMB:
                    segments.extend(self._generate_climb_pass(
                        current_x, current_z, geometry_bounds, params))
                elif strategy == PathStrategy.TROCHOIDAL:
                    segments.extend(self._generate_trochoidal_pass(
                        current_x, current_z, geometry_bounds, params))
                elif strategy == PathStrategy.ADAPTIVE:
                    segments.extend(self._generate_adaptive_pass(
                        current_x, current_z, geometry_bounds, params))

        return segments

    def generate_finishing_path(
            self,
            geometry_bounds: GeometryBounds,
            params: MachiningParameters,
            surface_tolerance: float = 0.001
    ) -> List[ToolPathSegment]:
        """
        Generate finishing tool path.

        Args:
            geometry_bounds: Geometry bounding box
            params: Machining parameters
            surface_tolerance: Required surface tolerance

        Returns:
            List of tool path segments
        """
        segments = []

        # Calculate finishing stepover based on surface tolerance
        finish_stepover = self._calculate_finish_stepover(
            params.tool_diameter, surface_tolerance)

        total_width = geometry_bounds.max_x - geometry_bounds.min_x
        num_passes = max(1, int(math.ceil(total_width / finish_stepover)))

        for pass_num in range(num_passes):
            current_x = geometry_bounds.min_x + (pass_num * finish_stepover)

            # Generate smooth finishing pass
            segments.extend(self._generate_finish_pass(
                current_x, geometry_bounds, params, surface_tolerance))

        return segments

    def optimize_path_order(
            self,
            segments: List[ToolPathSegment],
            optimization_target: str = "time"
    ) -> List[ToolPathSegment]:
        """
        Optimize the order of tool path segments.

        Args:
            segments: List of tool path segments
            optimization_target: Optimization objective

        Returns:
            Reordered list of segments
        """
        if optimization_target == "time":
            return self._optimize_for_time(segments)
        elif optimization_target == "surface":
            return self._optimize_for_surface(segments)
        elif optimization_target == "tool_life":
            return self._optimize_for_tool_life(segments)
        else:
            return self._optimize_balanced(segments)

    def calculate_machining_time(
            self,
            segments: List[ToolPathSegment]
    ) -> Dict[str, float]:
        """
        Calculate total machining time for tool path.

        Args:
            segments: List of tool path segments

        Returns:
            Dictionary with time breakdown
        """
        cutting_time = 0.0
        rapid_time = 0.0
        tool_change_time = 0.0

        # current_tool = None

        for i, segment in enumerate(segments):
            # Calculate segment distance
            distance = self._calculate_distance(segment.start, segment.end)

            # Calculate segment time
            if segment.feed_rate > 0:
                segment_time = distance / segment.feed_rate
                cutting_time += segment_time
            else:
                # Rapid move
                rapid_feed = 500  # Default rapid rate
                segment_time = distance / rapid_feed
                rapid_time += segment_time

            # Check for tool changes (simplified)
            if i > 0 and segments[i-1].spindle_speed != segment.spindle_speed:
                tool_change_time += 0.5  # 30 seconds per tool change

        total_time = cutting_time + rapid_time + tool_change_time

        return {
            "cutting": cutting_time,
            "rapid": rapid_time,
            "tool_change": tool_change_time,
            "total": total_time
        }

    def analyze_surface_finish(
            self,
            segments: List[ToolPathSegment],
            tool_diameter: float
    ) -> Dict[str, float]:
        """
        Analyze expected surface finish for tool path.

        Args:
            segments: List of tool path segments
            tool_diameter: Tool diameter

        Returns:
            Dictionary with surface finish metrics
        """
        finish_segments = [
            s for s in segments
            if s.path_type == PathType.FINISHING
        ]

        if not finish_segments:
            return {"average_roughness": 0, "peak_roughness": 0}

        total_roughness = 0.0
        max_roughness = 0.0

        for segment in finish_segments:
            # Calculate theoretical roughness based on feed rate
            chip_load = segment.feed_rate / (segment.spindle_speed * 2)
            theoretical_ra = (chip_load ** 2) / (8 * tool_diameter * 0.01)

            total_roughness += theoretical_ra
            max_roughness = max(max_roughness, theoretical_ra)

        average_roughness = total_roughness / len(finish_segments)

        return {
            "average_roughness": average_roughness * 1e6,  # microinches
            "peak_roughness": max_roughness * 1e6,
            "uniformity": 1.0 - (
                max_roughness - average_roughness) / max_roughness
        }

    def _generate_conventional_pass(
            self,
            x_position: float,
            z_position: float,
            bounds: GeometryBounds,
            params: MachiningParameters
    ) -> List[ToolPathSegment]:
        """Generate conventional milling pass."""
        segments = []

        start_point = Point3D(x_position, bounds.min_y, z_position)
        end_point = Point3D(x_position, bounds.max_y, z_position)

        segment = ToolPathSegment(
            start=start_point,
            end=end_point,
            feed_rate=100,  # Default feed rate
            spindle_speed=5000,  # Default spindle speed
            path_type=PathType.ROUGHING,
            strategy=PathStrategy.CONVENTIONAL
        )

        segments.append(segment)
        return segments

    def _generate_climb_pass(
            self,
            x_position: float,
            z_position: float,
            bounds: GeometryBounds,
            params: MachiningParameters
    ) -> List[ToolPathSegment]:
        """Generate climb milling pass."""
        segments = []

        start_point = Point3D(x_position, bounds.max_y, z_position)
        end_point = Point3D(x_position, bounds.min_y, z_position)

        segment = ToolPathSegment(
            start=start_point,
            end=end_point,
            feed_rate=120,  # Slightly higher for climb
            spindle_speed=5000,
            path_type=PathType.ROUGHING,
            strategy=PathStrategy.CLIMB
        )

        segments.append(segment)
        return segments

    def _generate_trochoidal_pass(
            self,
            x_position: float,
            z_position: float,
            bounds: GeometryBounds,
            params: MachiningParameters
    ) -> List[ToolPathSegment]:
        """Generate trochoidal milling pass."""
        segments = []

        # Simplified trochoidal pattern
        y_current = bounds.min_y
        troch_radius = params.tool_diameter * 0.8

        while y_current < bounds.max_y:
            # Create circular arc segments
            for angle in range(0, 360, 30):  # 30-degree increments
                angle_rad = math.radians(angle)
                x_offset = troch_radius * math.cos(angle_rad)
                y_offset = troch_radius * math.sin(angle_rad)

                point = Point3D(
                    x_position + x_offset,
                    y_current + y_offset,
                    z_position
                )

                if segments:
                    segment = ToolPathSegment(
                        start=segments[-1].end,
                        end=point,
                        feed_rate=150,  # Higher feed for trochoidal
                        spindle_speed=6000,
                        path_type=PathType.ROUGHING,
                        strategy=PathStrategy.TROCHOIDAL
                    )
                    segments.append(segment)
                else:
                    # First point - create entry segment
                    entry_point = Point3D(x_position, bounds.min_y, z_position)
                    segment = ToolPathSegment(
                        start=entry_point,
                        end=point,
                        feed_rate=50,  # Slower entry
                        spindle_speed=6000,
                        path_type=PathType.ROUGHING,
                        strategy=PathStrategy.TROCHOIDAL
                    )
                    segments.append(segment)

            y_current += troch_radius * 1.5

        return segments

    def _generate_adaptive_pass(
            self,
            x_position: float,
            z_position: float,
            bounds: GeometryBounds,
            params: MachiningParameters
    ) -> List[ToolPathSegment]:
        """Generate adaptive clearing pass."""
        segments = []

        # Adaptive strategy varies parameters based on local geometry
        # This is a simplified implementation

        segment_length = (bounds.max_y - bounds.min_y) / 3

        for i in range(3):
            y_start = bounds.min_y + i * segment_length
            y_end = bounds.min_y + (i + 1) * segment_length

            # Vary feed rate based on segment position
            feed_multiplier = 1.0 + 0.2 * i  # Increase feed as we progress

            segment = ToolPathSegment(
                start=Point3D(x_position, y_start, z_position),
                end=Point3D(x_position, y_end, z_position),
                feed_rate=100 * feed_multiplier,
                spindle_speed=5000,
                path_type=PathType.ROUGHING,
                strategy=PathStrategy.ADAPTIVE
            )
            segments.append(segment)
        return segments

    def _generate_finish_pass(
            self,
            x_position: float,
            bounds: GeometryBounds,
            params: MachiningParameters,
            tolerance: float
    ) -> List[ToolPathSegment]:
        """Generate finishing pass."""
        segments = []

        # Calculate optimal finishing parameters
        finish_feed = self._calculate_finish_feed_rate(
            params.tool_diameter, tolerance)

        start_point = Point3D(x_position, bounds.min_y, bounds.max_z)
        end_point = Point3D(x_position, bounds.max_y, bounds.max_z)

        segment = ToolPathSegment(
            start=start_point,
            end=end_point,
            feed_rate=finish_feed,
            spindle_speed=8000,  # Higher speed for finishing
            path_type=PathType.FINISHING,
            strategy=PathStrategy.CONVENTIONAL
        )

        segments.append(segment)
        return segments

    def _calculate_finish_stepover(
            self,
            tool_diameter: float,
            tolerance: float
    ) -> float:
        """Calculate optimal stepover for finishing."""
        # Scallop height formula
        stepover = 2 * math.sqrt(tolerance * tool_diameter - tolerance ** 2)
        return min(stepover, tool_diameter * 0.8)  # Maximum 80% of diameter

    def _calculate_finish_feed_rate(
            self,
            tool_diameter: float,
            tolerance: float
    ) -> float:
        """Calculate optimal feed rate for finishing."""
        # Base feed rate on tolerance requirements
        base_feed = 50  # Base feed rate
        tolerance_factor = max(0.3, tolerance / 0.001)  # Scale with tolerance
        return base_feed * tolerance_factor

    def _optimize_for_time(
            self,
            segments: List[ToolPathSegment]
    ) -> List[ToolPathSegment]:
        """Optimize path order for minimum time."""
        # Simple nearest neighbor optimization
        if not segments:
            return segments

        optimized = [segments[0]]
        remaining = segments[1:]

        while remaining:
            current_end = optimized[-1].end
            nearest_idx = 0
            min_distance = float('inf')

            for i, segment in enumerate(remaining):
                distance = self._calculate_distance(current_end, segment.start)
                if distance < min_distance:
                    min_distance = distance
                    nearest_idx = i

            optimized.append(remaining.pop(nearest_idx))
        return optimized

    def _optimize_for_surface(
            self,
            segments: List[ToolPathSegment]
    ) -> List[ToolPathSegment]:
        """Optimize path order for best surface finish."""
        # Sort by path type (finishing last) and then by feed rate
        return sorted(segments, key=lambda s: (
            s.path_type.value,
            -s.feed_rate  # Lower feed rates first for better finish
        ))

    def _optimize_for_tool_life(
            self,
            segments: List[ToolPathSegment]
    ) -> List[ToolPathSegment]:
        """Optimize path order for maximum tool life."""
        # Sort by increasing cutting load (lower speeds and feeds first)
        return sorted(segments, key=lambda s: (
            s.spindle_speed * s.feed_rate
        ))

    def _optimize_balanced(
            self,
            segments: List[ToolPathSegment]
    ) -> List[ToolPathSegment]:
        """Balanced optimization approach."""
        # Combine time and surface optimizations
        time_optimized = self._optimize_for_time(segments)
        return self._optimize_for_surface(time_optimized)

    def _calculate_distance(self, point1: Point3D, point2: Point3D) -> float:
        """Calculate 3D distance between two points."""
        return math.sqrt(
            (point2.x - point1.x) ** 2 +
            (point2.y - point1.y) ** 2 +
            (point2.z - point1.z) ** 2
        )
