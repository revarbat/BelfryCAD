"""
Tools Package

Provides drawing and editing tools for the pyTkCAD application.
"""

from .base import ToolManager
from .line import LineTool
from .linemp import LineMPTool
from .polyline import PolylineTool
from .circle import CircleTool, Circle2PTTool, Circle3PTTool
from .selector import SelectorTool
from .bezier import BezierTool
from .arcs import ArcCenterTool, Arc3PointTool
from .ellipse import (EllipseCenterTool, EllipseDiagonalTool,
                      Ellipse3CornerTool, EllipseCenterTangentTool,
                      EllipseOppositeTangentTool)
from .polygon import RectangleTool, RegularPolygonTool
from .text import TextTool
from .point import PointTool
from .dimension import (
    HorizontalDimensionTool,
    VerticalDimensionTool,
    LinearDimensionTool
)
from .arc_dimension import ArcDimensionTool
from .transforms import (
    NodeAddTool,
    NodeDeleteTool,
    ReorientTool,
    ConnectTool,
    TranslateTool,
    RotateTool,
    ScaleTool,
    FlipTool,
    ShearTool,
    BendTool,
    WrapTool,
    UnwrapTool
)


# A list of all available tools for easy registration
available_tools = [
    SelectorTool,  # Always list selector first as it's the default tool
    LineTool,
    LineMPTool,
    PolylineTool,
    CircleTool,
    Circle2PTTool,
    Circle3PTTool,
    BezierTool,
    ArcCenterTool,
    Arc3PointTool,
    EllipseCenterTool,
    EllipseDiagonalTool,
    Ellipse3CornerTool,
    EllipseCenterTangentTool,
    EllipseOppositeTangentTool,
    RectangleTool,
    RegularPolygonTool,
    TextTool,
    PointTool,
    HorizontalDimensionTool,
    VerticalDimensionTool,
    LinearDimensionTool,
    ArcDimensionTool,
    # Transform tools
    NodeAddTool,
    NodeDeleteTool,
    ReorientTool,
    ConnectTool,
    TranslateTool,
    RotateTool,
    ScaleTool,
    FlipTool,
    ShearTool,
    BendTool,
    WrapTool,
    UnwrapTool
]
