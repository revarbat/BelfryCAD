"""
Mill Module

This module provides classes for defining mill parameters and calculating
speeds and feeds for CNC machining operations.
"""

from dataclasses import dataclass
from typing import List, Optional, Union, Dict
import math


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

    def __post_init__(self):
        MillDefinition._instance = self

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
        if not cls._instance:
            return 10.0  # Default feed rate

        # Basic feed rate calculation based on RPM and tool parameters
        rpm = cls.get_rpm()
        tool = ToolDefinition.get_current()
        if not tool:
            return 10.0

        # Calculate chip load based on material and tool
        chip_load = cls._get_chip_load(tool.material, tool.flutes)
        
        # Calculate feed rate
        feed_rate = rpm * chip_load * tool.flutes

        # Adjust for plunge rate if needed
        if plunge:
            feed_rate *= 0.5  # Plunge rate is typically half of feed rate

        # Ensure we don't exceed max feed rate
        return min(feed_rate, cls._instance.max_feed)

    @classmethod
    def get_cut_depth(cls, cut_width: float) -> float:
        """Get the recommended cut depth in inches"""
        if not cls._instance:
            return 0.1  # Default cut depth

        # Basic cut depth calculation based on tool diameter
        # Rule of thumb: cut depth should be 1/2 to 1/4 of tool diameter
        return cut_width * 0.5

    @classmethod
    def _get_chip_load(cls, tool_material: str, flutes: int) -> float:
        """Get the recommended chip load based on tool material and flutes"""
        # Basic chip load values in inches per tooth
        if tool_material.lower() == "carbide":
            base_load = 0.003  # Carbide tools can handle higher chip loads
        else:
            base_load = 0.002  # HSS tools need lower chip loads

        # Adjust for number of flutes
        return base_load * (4.0 / flutes)  # Normalize to 4 flutes


@dataclass
class StockDefinition:
    """Definition of stock material parameters"""
    width: float = 1.0
    height: float = 1.0
    depth: float = 0.5
    material: str = "Aluminum"

    _instance: Optional['StockDefinition'] = None

    def __post_init__(self):
        StockDefinition._instance = self

    @classmethod
    def get_current(cls) -> Optional['StockDefinition']:
        """Get the current stock definition"""
        return cls._instance


@dataclass
class ToolDefinition:
    """Definition of tool parameters"""
    tool_id: int
    diameter: float
    material: str
    flutes: int

    _current_tool: Optional['ToolDefinition'] = None
    _tools: Dict[int, 'ToolDefinition'] = None

    def __post_init__(self):
        if ToolDefinition._tools is None:
            ToolDefinition._tools = {}
        ToolDefinition._tools[self.tool_id] = self
        ToolDefinition._current_tool = self  # Set as current tool by default

    @classmethod
    def get_current(cls) -> Optional['ToolDefinition']:
        """Get the current tool definition"""
        return cls._current_tool

    @classmethod
    def select_tool(cls, tool_id: int) -> bool:
        """Select a tool by ID"""
        if tool_id in cls._tools:
            cls._current_tool = cls._tools[tool_id]
            return True
        return False 