"""
CAD Geometry Package

This package contains all the geometric primitives and operations for BelfryCAD.
"""

from .transform import Transform2D
from .shapes import ShapeType, Shape2D
from .point import Point2D
from .line import Line2D
from .polyline import PolyLine2D
from .polygon import Polygon
from .arc import Arc
from .rect import Rect
from .circle import Circle
from .ellipse import Ellipse
from .bezier import BezierPath
from .region import Region
from .spur_gear import SpurGear

# Re-export commonly used types
__all__ = [
    'Transform2D',
    'ShapeType',
    'Shape2D', 
    'Point2D',
    'Line2D',
    'PolyLine2D',
    'Polygon',
    'Arc',
    'Rect',
    'Circle',
    'Ellipse',
    'BezierPath',
    'Region',
    'SpurGear'
] 