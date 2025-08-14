"""
Graphics items package for BelfryCAD.

This package contains all graphics-related items including:
- CAD items and their subclasses
- ControlPoints and ControlDatums
- Grid graphics items
- CAD rectangle utilities
"""

# GUI Graphics Items
from .alignable_simple_text_item import AlignableSimpleTextItem
from .cad_arc_graphics_item import CadArcGraphicsItem, CadArcArrowheadEndcaps
from .construction_circle_item import ConstructionCircleItem
from .construction_cross_item import ConstructionCrossItem
from .construction_line_item import ConstructionLineItem
from .control_points import (
    ControlPoint, ControlDatum, 
    SquareControlPoint, DiamondControlPoint
)
from .dimension_line_composite import DimensionLineComposite, DimensionLineOrientation
from .grid_graphics_items import (
    GridBackground, RulersForeground, SnapCursorItem
)

# New custom CAD graphics items with selection indication
from .cad_graphics_items_base import CadGraphicsItemBase
from .cad_line_graphics_item import CadLineGraphicsItem
from .cad_circle_graphics_item import CadCircleGraphicsItem
from .cad_ellipse_graphics_item import CadEllipseGraphicsItem
from .cad_polyline_graphics_item import CadPolylineGraphicsItem
from .cad_bezier_graphics_item import CadBezierGraphicsItem
from .cad_polygon_graphics_item import CadPolygonGraphicsItem

__all__ = [
    'AlignableSimpleTextItem',
    'CadArcGraphicsItem', 'CadArcArrowheadEndcaps',
    'ConstructionCircleItem',
    'ConstructionCrossItem', 
    'ConstructionLineItem',
    'ControlPoint', 'ControlDatum',
    'SquareControlPoint', 'DiamondControlPoint',
    'DimensionLineComposite', 'DimensionLineOrientation',
    'GridBackground', 'RulersForeground', 'SnapCursorItem',
    # New custom CAD graphics items
    'CadGraphicsItemBase',
    'CadLineGraphicsItem',
    'CadCircleGraphicsItem', 
    'CadEllipseGraphicsItem',
    'CadPolylineGraphicsItem',
    'CadBezierGraphicsItem',
    'CadPolygonGraphicsItem',
] 