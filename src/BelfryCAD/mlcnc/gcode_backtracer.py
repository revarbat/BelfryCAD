"""
G-Code Backtracer

This module provides functionality to analyze and visualize G-code files,
showing the tool path and machining operations in a graphical interface.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional, Tuple, Set
import math


class GCodeCommand(Enum):
    """G-code command types."""
    RAPID_MOVE = "G0"
    LINEAR_MOVE = "G1"
    ARC_CW = "G2"
    ARC_CCW = "G3"
    DWELL = "G4"
    TOOL_CHANGE = "T"
    SPINDLE_SPEED = "S"
    FEED_RATE = "F"
    COOLANT_ON = "M8"
    COOLANT_OFF = "M9"
    SPINDLE_ON = "M3"
    SPINDLE_OFF = "M5"
    PROGRAM_END = "M30"
    UNKNOWN = "UNKNOWN"


@dataclass
class GCodePoint:
    """Point in G-code coordinate system."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    i: float = 0.0  # Arc center X offset
    j: float = 0.0  # Arc center Y offset
    k: float = 0.0  # Arc center Z offset


@dataclass
class GCodeOperation:
    """G-code operation with parameters."""
    command: GCodeCommand
    point: GCodePoint
    feed_rate: Optional[float] = None
    spindle_speed: Optional[float] = None
    tool_number: Optional[int] = None
    dwell_time: Optional[float] = None
    line_number: int = 0


class GCodeBacktracer:
    """
    G-code backtracer for analyzing and visualizing G-code files.
    """

    def __init__(self):
        """Initialize the G-code backtracer."""
        self.operations: List[GCodeOperation] = []
        self.current_point = GCodePoint()
        self.current_feed_rate = 0.0
        self.current_spindle_speed = 0.0
        self.current_tool = 0
        self.bounds = {
            'min_x': float('inf'),
            'max_x': float('-inf'),
            'min_y': float('inf'),
            'max_y': float('-inf'),
            'min_z': float('inf'),
            'max_z': float('-inf')
        }
        self.z_levels: Set[float] = set()
        self.tool_changes: List[Tuple[int, int, float]] = []  # (tool_number, line_number, z_level)

    def parse_file(self, filename: str) -> None:
        """
        Parse a G-code file and extract operations.

        Args:
            filename: Path to the G-code file
        """
        with open(filename, 'r') as f:
            for line_num, line in enumerate(f, 1):
                self._parse_line(line.strip(), line_num)

    def _parse_line(self, line: str, line_num: int) -> None:
        """
        Parse a single line of G-code.

        Args:
            line: G-code line to parse
            line_num: Line number in the file
        """
        # Skip comments and empty lines
        if not line or line.startswith(';') or line.startswith('('):
            return

        # Remove comments
        line = re.sub(r'\(.*?\)', '', line)
        line = re.sub(r';.*$', '', line)

        # Split into words
        words = line.split()
        if not words:
            return

        # Parse command
        command = self._parse_command(words[0])
        if command == GCodeCommand.UNKNOWN:
            return

        # Create operation
        operation = GCodeOperation(
            command=command,
            point=GCodePoint(),
            line_number=line_num
        )

        # Parse parameters
        for word in words[1:]:
            self._parse_parameter(word, operation)

        # Update current state
        self._update_state(operation)
        self.operations.append(operation)

    def _parse_command(self, word: str) -> GCodeCommand:
        """
        Parse a G-code command word.

        Args:
            word: Command word to parse

        Returns:
            GCodeCommand enum value
        """
        try:
            return GCodeCommand(word)
        except ValueError:
            return GCodeCommand.UNKNOWN

    def _parse_parameter(self, word: str, operation: GCodeOperation) -> None:
        """
        Parse a G-code parameter.

        Args:
            word: Parameter word to parse
            operation: Operation to update
        """
        if not word:
            return

        code = word[0].upper()
        try:
            value = float(word[1:])
        except ValueError:
            return

        if code == 'X':
            operation.point.x = value
        elif code == 'Y':
            operation.point.y = value
        elif code == 'Z':
            operation.point.z = value
        elif code == 'I':
            operation.point.i = value
        elif code == 'J':
            operation.point.j = value
        elif code == 'K':
            operation.point.k = value
        elif code == 'F':
            operation.feed_rate = value
        elif code == 'S':
            operation.spindle_speed = value
        elif code == 'T':
            operation.tool_number = int(value)
        elif code == 'P':
            operation.dwell_time = value

    def _update_state(self, operation: GCodeOperation) -> None:
        """
        Update current state based on operation.

        Args:
            operation: Operation to process
        """
        # Update current point
        if operation.command in [GCodeCommand.RAPID_MOVE, GCodeCommand.LINEAR_MOVE,
                               GCodeCommand.ARC_CW, GCodeCommand.ARC_CCW]:
            if operation.point.x is not None:
                self.current_point.x = operation.point.x
            if operation.point.y is not None:
                self.current_point.y = operation.point.y
            if operation.point.z is not None:
                self.current_point.z = operation.point.z
                self.z_levels.add(operation.point.z)

        # Update feed rate
        if operation.feed_rate is not None:
            self.current_feed_rate = operation.feed_rate

        # Update spindle speed
        if operation.spindle_speed is not None:
            self.current_spindle_speed = operation.spindle_speed

        # Update tool number and track tool changes
        if operation.tool_number is not None:
            if operation.tool_number != self.current_tool:
                self.tool_changes.append((
                    operation.tool_number,
                    operation.line_number,
                    self.current_point.z
                ))
            self.current_tool = operation.tool_number

        # Update bounds
        self._update_bounds(operation)

    def _update_bounds(self, operation: GCodeOperation) -> None:
        """
        Update coordinate bounds based on operation.

        Args:
            operation: Operation to process
        """
        if operation.point.x is not None:
            self.bounds['min_x'] = min(self.bounds['min_x'], operation.point.x)
            self.bounds['max_x'] = max(self.bounds['max_x'], operation.point.x)
        if operation.point.y is not None:
            self.bounds['min_y'] = min(self.bounds['min_y'], operation.point.y)
            self.bounds['max_y'] = max(self.bounds['max_y'], operation.point.y)
        if operation.point.z is not None:
            self.bounds['min_z'] = min(self.bounds['min_z'], operation.point.z)
            self.bounds['max_z'] = max(self.bounds['max_z'], operation.point.z)

    def get_bounds(self) -> Dict[str, float]:
        """
        Get the coordinate bounds of the G-code program.

        Returns:
            Dictionary of min/max coordinates
        """
        return self.bounds

    def get_operations(self) -> List[GCodeOperation]:
        """
        Get the list of parsed operations.

        Returns:
            List of GCodeOperation objects
        """
        return self.operations

    def get_tool_changes(self) -> List[Tuple[int, int, float]]:
        """
        Get the list of tool changes with line numbers and Z-levels.

        Returns:
            List of (tool_number, line_number, z_level) tuples
        """
        return self.tool_changes

    def get_z_levels(self) -> List[float]:
        """
        Get the list of Z-levels in the program.

        Returns:
            List of Z-levels, sorted from highest to lowest
        """
        return sorted(self.z_levels, reverse=True)

    def get_machining_time(self) -> float:
        """
        Calculate estimated machining time.

        Returns:
            Estimated machining time in minutes
        """
        total_time = 0.0
        for i, op in enumerate(self.operations):
            if op.command in [GCodeCommand.LINEAR_MOVE, GCodeCommand.ARC_CW, GCodeCommand.ARC_CCW]:
                if i > 0:
                    prev_op = self.operations[i-1]
                    distance = self._calculate_distance(prev_op.point, op.point)
                    if op.feed_rate:
                        total_time += distance / op.feed_rate
            elif op.command == GCodeCommand.DWELL:
                if op.dwell_time:
                    total_time += op.dwell_time
        return total_time / 60.0  # Convert to minutes

    def _calculate_distance(self, p1: GCodePoint, p2: GCodePoint) -> float:
        """
        Calculate distance between two points.

        Args:
            p1: First point
            p2: Second point

        Returns:
            Distance between points
        """
        return math.sqrt(
            (p2.x - p1.x) ** 2 +
            (p2.y - p1.y) ** 2 +
            (p2.z - p1.z) ** 2
        )