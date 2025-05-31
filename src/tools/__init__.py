"""
Tools Package

Provides drawing and editing tools for the pyTkCAD application.
"""

from .base import Tool, ToolManager, ToolState, ToolCategory, ToolDefinition
from .line import LineTool
from .circle import CircleTool
from .selector import SelectorTool
from .bezier import BezierTool
from .arc import ArcCenterTool, Arc3PointTool
from .ellipse import EllipseCenterTool, EllipseDiagonalTool
from .polygon import RectangleTool, RegularPolygonTool
from .text import TextTool
from .point import PointTool
from .dimension import (
    HorizontalDimensionTool,
    VerticalDimensionTool,
    LinearDimensionTool
)
from .image import ImageTool

# A list of all available tools for easy registration
available_tools = [
    SelectorTool,  # Always list selector first as it's the default tool
    LineTool,
    CircleTool,
    BezierTool,
    ArcCenterTool,
    Arc3PointTool,
    EllipseCenterTool,
    EllipseDiagonalTool,
    RectangleTool,
    RegularPolygonTool,
    TextTool,
    PointTool,
    HorizontalDimensionTool,
    VerticalDimensionTool,
    LinearDimensionTool,
    ImageTool
]