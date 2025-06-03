"""
Tools Package

Provides drawing and editing tools for the pyTkCAD application.
"""

from .base import ToolManager
from .line import LineTool
from .circle import CircleTool, Circle2PTTool, Circle3PTTool
from .selector import SelectorTool
from .bezier import BezierTool
from .arcs import ArcCenterTool, Arc3PointTool
from .ellipse import EllipseCenterTool, EllipseDiagonalTool
from .polygon import RectangleTool, RegularPolygonTool
from .text import TextTool
from .point import PointTool
from .dimension import (
    HorizontalDimensionTool,
    VerticalDimensionTool,
    LinearDimensionTool
)
from .arc_dimension import ArcDimensionTool


# A list of all available tools for easy registration
available_tools = [
    SelectorTool,  # Always list selector first as it's the default tool
    LineTool,
    CircleTool,
    Circle2PTTool,
    Circle3PTTool,
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
    ArcDimensionTool
]
