"""
Base Shape Classes for CAD Geometry

This module provides the base Shape2D class and ShapeType enum that all
geometric primitives inherit from.
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .point import Point2D
    from .transform import Transform2D


class ShapeType(Enum):
    """Enumeration of all supported 2D shape types."""
    POINT = "point"
    LINE = "line"
    POLYLINE = "polyline"
    ARC = "arc"
    RECT = "rect"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"
    BEZIER = "bezier"
    POLYGON = "polygon"
    REGION = "region"
    SPUR_GEAR = "spur_gear"


class Shape2D(ABC):
    """
    Abstract base class for all 2D geometric shapes.
    
    This class defines the common interface that all geometric primitives
    must implement, including transformation, bounds calculation, and decomposition.
    """

    def __init__(self):
        """Initialize a new shape."""
        pass

    def contains_point(self, point: 'Point2D', tolerance: float = 1e-10) -> bool:
        """
        Check if a point is contained within this shape.
        
        Args:
            point: The point to test
            tolerance: Tolerance for floating point comparisons
            
        Returns:
            True if the point is contained within the shape
        """
        raise NotImplementedError("Subclasses must implement contains_point")

    @classmethod
    def from_data(cls, data: dict) -> 'Shape2D':
        """Create a shape from serialized data."""
        raise NotImplementedError("Subclasses must implement from_data")

    @classmethod
    def from_string(cls, string: str) -> 'Shape2D':
        """Create a shape from a string representation."""
        raise NotImplementedError("Subclasses must implement from_string")

    def to_string(self) -> str:
        """Convert the shape to a string representation."""
        raise NotImplementedError("Subclasses must implement to_string")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    def __str__(self) -> str:
        return self.to_string()

    def __eq__(self, other: object) -> bool:
        """Check if two shapes are equal."""
        if not isinstance(other, self.__class__):
            return False
        return self.to_string() == other.to_string()

    def __ne__(self, other: object) -> bool:
        """Check if two shapes are not equal."""
        return not self.__eq__(other)

    def translate(self, vector: 'Point2D') -> 'Shape2D':
        """Translate the shape by a vector."""
        raise NotImplementedError("Subclasses must implement translate")

    def scale(self, scale: float, center: 'Point2D') -> Optional['Shape2D']:
        """Scale the shape around a center point."""
        raise NotImplementedError("Subclasses must implement scale")

    def rotate(self, angle: float, center: 'Point2D') -> 'Shape2D':
        """Rotate the shape around a center point."""
        raise NotImplementedError("Subclasses must implement rotate")

    def transform(self, transform: 'Transform2D') -> Optional['Shape2D']:
        """Transform the shape using a transformation matrix."""
        raise NotImplementedError("Subclasses must implement transform")

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """
        Get the bounding box of the shape.
        
        Returns:
            Tuple of (min_x, min_y, max_x, max_y)
        """
        raise NotImplementedError("Subclasses must implement get_bounds")

    def decompose(self, into: List[ShapeType] = [], tolerance: float = 0.001) -> List['Shape2D']:
        """
        Decompose this shape into other shape types.
        
        Args:
            into: List of target shape types to decompose into
            tolerance: Maximum deviation allowed when approximating curves
            
        Returns:
            List of shapes of the requested types
        """
        raise NotImplementedError("Subclasses must implement decompose") 