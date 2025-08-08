"""
Rect Class for CAD Geometry

This module provides the Rect class for representing 2D rectangles
with various geometric operations and calculations.
"""

from typing import List, Optional, Tuple, Union, Iterator
import numpy as np
import math
from .shapes import Shape2D, ShapeType
from .point import Point2D
from .line import Line2D
from .transform import Transform2D
from .polygon import Polygon
from .polyline import PolyLine2D
from .bezier import BezierPath
from .region import Region

EPSILON = 1e-10

class Rect(Shape2D):
    """Rectangle with geometric operations - optimized with numpy."""

    def __init__(self, *args):
        """Initialize a rectangle."""
        if len(args) == 1:
            arg = args[0]
            try:
                self.left = arg.left
                self.bottom = arg.bottom
                self.width = arg.width
                self.height = arg.height
                return
            except:
                pass
            try:
                self.left = arg.left()
                self.bottom = arg.bottom()
                self.width = arg.width()
                self.height = arg.height()
                return
            except:
                pass
            raise ValueError("Invalid arguments for Rect")
        elif len(args) == 2:
            p1 = Point2D(args[0])
            p2 = Point2D(args[1])
            self.left = min(p1.x, p2.x)
            self.bottom = min(p1.y, p2.y)
            self.width = abs(p1.x - p2.x)
            self.height = abs(p1.y - p2.y)
            return
        elif len(args) == 4:
            self.left = float(args[0])
            self.bottom = float(args[1])
            self.width = float(args[2])
            self.height = float(args[3])
            return
        else:
            raise ValueError("Invalid arguments for Rect")

    def decompose(self, into: List[ShapeType] = [], tolerance: float = 0.001) -> List['Shape2D']:
        if ShapeType.RECT in into:
            return [self]
        p1 = Point2D(self.left, self.top)
        p2 = Point2D(self.right, self.top)
        p3 = Point2D(self.right, self.bottom)
        p4 = Point2D(self.left, self.bottom)
        if ShapeType.POLYGON in into:
            return [Polygon([p1, p2, p3, p4])]
        if ShapeType.REGION in into:
            return [Region(perimeters=[Polygon([p1, p2, p3, p4])], holes=[])]
        if ShapeType.POLYLINE in into:
            return [PolyLine2D([p1, p2, p3, p4])]
        if ShapeType.LINE in into:
            return [
                Line2D(p1, p2),
                Line2D(p2, p3),
                Line2D(p3, p4),
                Line2D(p4, p1)
            ]
        raise ValueError(f"Cannot decompose rect into any of {into}")

    @property
    def top(self) -> float:
        return float(self.bottom + self.height)
    
    @property
    def right(self) -> float:
        return float(self.left + self.width)

    @property
    def p1(self) -> Point2D:
        return Point2D(self.left, self.bottom)
    
    @property
    def p2(self) -> Point2D:
        return Point2D(self.right, self.top)
    
    @property
    def center(self) -> Point2D:
        return Point2D(self.left + self.width / 2, self.bottom + self.height / 2)
    
    def __repr__(self) -> str:
        return f"Rect({self.left}, {self.bottom}, {self.width}, {self.height})"

    def __str__(self) -> str:
        return f"Rect at ({self.left}, {self.bottom}) with width {self.width} and height {self.height}"
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Rect):
            return self.left == other.left and self.bottom == other.bottom and self.width == other.width and self.height == other.height
        return self == Rect(other)
    
    def __hash__(self) -> int:
        return hash((self.left, self.bottom, self.width, self.height))
    
    def __contains__(self, point: Point2D) -> bool:
        if not isinstance(point, Point2D):
            point = Point2D(point)
        return bool(
            self.left <= point.x <= self.left + self.width and
            self.bottom <= point.y <= self.bottom + self.height
        )
    
    def contains_point(self, point: Point2D, tolerance: float = EPSILON) -> bool:
        if not isinstance(point, Point2D):
            point = Point2D(point)
        return bool(
            self.left - tolerance <= point.x <= self.left + self.width + tolerance and
            self.bottom - tolerance <= point.y <= self.bottom + self.height + tolerance
        )
    
    def intersects_rect(self, other: 'Rect') -> bool:
        return not bool(
            self.left > other.left + other.width or
            self.left + self.width < other.left or
            self.bottom > other.bottom + other.height or
            self.bottom + self.height < other.bottom
        )
    
    def translate(self, vector) -> 'Rect':
        """Make a new rectangle, translated by vector."""
        if not isinstance(vector, Point2D):
            vector = Point2D(vector)
        return Rect(self.left + vector.x, self.bottom + vector.y, self.width, self.height)

    def scale(self, scale, center = None) -> 'Rect':
        """Make a new rectangle, scaled around a point."""
        if center is None:
            center = Point2D(0, 0)
        elif not isinstance(center, Point2D):
            center = Point2D(center)
        if isinstance(scale, (int, float, np.integer, np.floating)):
            scale = float(scale)
            return Rect(
                (self.left - center.x) * scale + center.x,
                (self.bottom - center.y) * scale + center.y,
                self.width * scale,
                self.height * scale
            )
        else:
            scale_point = Point2D(scale)
            return Rect(
                (self.left - center.x) * scale_point.x + center.x,
                (self.bottom - center.y) * scale_point.y + center.y,
                self.width * scale_point.x,
                self.height * scale_point.y
            )

    def rotate(self, angle: float, center = None) -> 'Shape2D':
        """Make a new rectangle, rotated around a point."""
        if center is None:
            center = Point2D(0, 0)
        elif not isinstance(center, Point2D):
            center = Point2D(center)
        p1 = Point2D(self.top, self.left).rotate(angle, center)
        p2 = Point2D(self.top, self.right).rotate(angle, center)
        p3 = Point2D(self.bottom, self.right).rotate(angle, center)
        p4 = Point2D(self.bottom, self.left).rotate(angle, center)
        return Polygon([p1, p2, p3, p4])

    def transform(self, transform: Transform2D) -> 'Shape2D':
        """Make a new rectangle, transformed using a transformation matrix."""
        p1 = Point2D(self.top, self.left).transform(transform)
        p2 = Point2D(self.top, self.right).transform(transform)
        p3 = Point2D(self.bottom, self.right).transform(transform)
        p4 = Point2D(self.bottom, self.left).transform(transform)
        return Polygon([p1, p2, p3, p4])

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get the bounds of the rectangle as (min_x, min_y, max_x, max_y)."""
        return (self.left, self.bottom, self.right, self.top)

    def expand(self, other):
        try:
            other_f = float(other)
            self.left -= other_f
            self.bottom -= other_f
            self.width += other_f * 2.0
            self.height += other_f * 2.0
            return
        except:
            pass
        try:
            other_p = Point2D(other)
            self.left = min(self.left, other_p.x)
            self.bottom = min(self.bottom, other_p.y)
            top = max(self.top, other_p.y)
            right = max(self.right, other_p.x)
            self.width = abs(right - self.left)
            self.height = abs(top - self.bottom)
            return
        except:
            pass
        try:
            x1, y1, x2, y2 = other.get_bounds()
            self.expand(Point2D(x1, y1))
            self.expand(Point2D(x2, y2))
            return
        except:
            pass
        try:
            self.expand(other.topLeft())
            self.expand(other.bottomRight())
            return
        except:
            pass
        raise ValueError(f"Invalid type for expansion: {type(other)}")
