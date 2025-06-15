"""
Tools Package

Provides drawing and editing tools for the pyTkCAD application.
"""

from .line import LineTool
from .linemp import LineMPTool
from .polyline import PolylineTool
from .circle import CircleTool, Circle2PTTool, Circle3PTTool
from .selector import SelectorTool
from .nodeselect import NodeSelectTool
from .bezier import BezierTool, BezierQuadTool
from .arcs import ArcCenterTool, Arc3PointTool, ArcTangentTool
from .conic import Conic2PointTool, Conic3PointTool
from .ellipse import (
    EllipseCenterTool,
    EllipseDiagonalTool,
    Ellipse3CornerTool,
    EllipseCenterTangentTool,
    EllipseOppositeTangentTool
)
from .polygon import RectangleTool, RegularPolygonTool
from .text import TextTool
from .point import PointTool
from .dimension import (
    HorizontalDimensionTool,
    VerticalDimensionTool,
    LinearDimensionTool,
    ArcDimensionTool
)
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
from .duplicators import (
    GridCopyTool,
    LinearCopyTool,
    RadialCopyTool,
    OffsetCopyTool
)
from .image import ImageTool
from .screw_hole import ScrewHoleTool
from .gear import GearTool


# A list of all available tools for easy registration
available_tools = [
    SelectorTool,  # Always list selector first as it's the default tool
    NodeSelectTool,  # Add node selector as second tool in Nodes category
    # Node tools
    NodeAddTool,
    NodeDeleteTool,
    ReorientTool,
    ConnectTool,
    # Transform tools
    TranslateTool,
    RotateTool,
    ScaleTool,
    FlipTool,
    ShearTool,
    BendTool,
    WrapTool,
    UnwrapTool,
    # Duplicator tools
    LinearCopyTool,
    RadialCopyTool,
    GridCopyTool,
    OffsetCopyTool,
    # Line & Bezier tools
    LineTool,
    LineMPTool,
    PolylineTool,
    BezierTool,
    BezierQuadTool,
    # Arc tools
    ArcCenterTool,
    Arc3PointTool,
    ArcTangentTool,
    # Conic tools
    Conic2PointTool,
    Conic3PointTool,
    # Circle tools
    CircleTool,
    Circle2PTTool,
    Circle3PTTool,
    # Ellipse tools
    EllipseCenterTool,
    EllipseDiagonalTool,
    Ellipse3CornerTool,
    EllipseCenterTangentTool,
    EllipseOppositeTangentTool,
    # Polygon tools
    RectangleTool,
    RegularPolygonTool,

    # Miscellaneous tools
    PointTool,
    TextTool,
    ImageTool,
    # CAM tools
    ScrewHoleTool,
    GearTool,
    # Dimension tools
    HorizontalDimensionTool,
    VerticalDimensionTool,
    LinearDimensionTool,
    ArcDimensionTool,
]
