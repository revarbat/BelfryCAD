"""
CAD Object business logic model.

This module contains pure business logic for CAD objects with no UI dependencies.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum
import uuid


class ObjectType(Enum):
    """Types of CAD objects"""
    LINE = "line"
    CIRCLE = "circle"
    ARC = "arc"
    RECTANGLE = "rectangle"
    POLYGON = "polygon"
    TEXT = "text"
    BEZIER = "bezier"
    ELLIPSE = "ellipse"
    POINT = "point"


@dataclass
class Point:
    """2D point with pure business logic"""
    x: float
    y: float
    
    def __add__(self, other: 'Point') -> 'Point':
        return Point(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Point') -> 'Point':
        return Point(self.x - other.x, self.y - other.y)
    
    def __mul__(self, other: float) -> 'Point':
        return Point(self.x * other, self.y * other)
    
    def __truediv__(self, other: float) -> 'Point':
        return Point(self.x / other, self.y / other)
    
    def __neg__(self) -> 'Point':
        return Point(-self.x, -self.y)
    
    def __abs__(self) -> float:
        return (self.x * self.x + self.y * self.y) ** 0.5
    
    def __str__(self) -> str:
        return f"Point({self.x}, {self.y})"
    
    def __repr__(self) -> str:
        return f"Point({self.x}, {self.y})"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return False
        return self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        return hash((self.x, self.y))
    
    
    def distance_to(self, other: 'Point') -> float:
        """Calculate distance to another point"""
        dx = self.x - other.x
        dy = self.y - other.y
        return (dx * dx + dy * dy) ** 0.5


class CADObject:
    """Pure business logic for CAD objects - no UI dependencies"""
    
    def __init__(self, object_type: ObjectType, points: Optional[List[Point]] = None, 
                 properties: Optional[Dict[str, Any]] = None):
        self.object_id = str(uuid.uuid4())
        self.object_type = object_type
        self.points = points or []
        self.properties = properties or {}
        self.layer_id = 0  # Default layer
        self.visible = True
        self.locked = False
    
    def add_point(self, point: Point):
        """Add a point to the object"""
        self.points.append(point)
    
    def get_point(self, index: int) -> Optional[Point]:
        """Get point at index"""
        if 0 <= index < len(self.points):
            return self.points[index]
        return None
    
    def set_point(self, index: int, point: Point):
        """Set point at index"""
        if 0 <= index < len(self.points):
            self.points[index] = point
    
    def move_by(self, dx: float, dy: float):
        """Move all points by delta"""
        delta = Point(dx, dy)
        for i in range(len(self.points)):
            self.points[i] = self.points[i] + delta
    
    def get_control_points(self) -> List[Tuple[float, float, str]]:
        """Get control point data for this object type"""
        control_points = []
        
        if self.object_type == ObjectType.LINE:
            if len(self.points) >= 2:
                # Start and end points
                control_points.append((self.points[0].x, self.points[0].y, "endpoint"))
                control_points.append((self.points[1].x, self.points[1].y, "endpoint"))
        
        elif self.object_type == ObjectType.CIRCLE:
            if len(self.points) >= 2:
                # Center and radius point
                control_points.append((self.points[0].x, self.points[0].y, "center"))
                control_points.append((self.points[1].x, self.points[1].y, "radius"))
        
        elif self.object_type == ObjectType.RECTANGLE:
            if len(self.points) >= 2:
                # Corner points
                control_points.append((self.points[0].x, self.points[0].y, "corner"))
                control_points.append((self.points[1].x, self.points[1].y, "corner"))
        
        return control_points
    
    def move_control_point(self, cp_index: int, x: float, y: float):
        """Move a specific control point"""
        control_points = self.get_control_points()
        if 0 <= cp_index < len(control_points):
            # Update the corresponding point in the object
            if self.object_type == ObjectType.LINE:
                if cp_index < len(self.points):
                    self.points[cp_index] = Point(x, y)
            elif self.object_type == ObjectType.CIRCLE:
                if cp_index < len(self.points):
                    self.points[cp_index] = Point(x, y)
            elif self.object_type == ObjectType.RECTANGLE:
                if cp_index < len(self.points):
                    self.points[cp_index] = Point(x, y)
    
    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get bounding box (min_x, min_y, max_x, max_y)"""
        if not self.points:
            return (0, 0, 0, 0)
        
        min_x = min(p.x for p in self.points)
        min_y = min(p.y for p in self.points)
        max_x = max(p.x for p in self.points)
        max_y = max(p.y for p in self.points)
        
        return (min_x, min_y, max_x, max_y)
    
    def contains_point(self, point: Point, tolerance: float = 5.0) -> bool:
        """Check if object contains point within tolerance"""
        for obj_point in self.points:
            if obj_point.distance_to(point) <= tolerance:
                return True
        return False
    
    def clone(self) -> 'CADObject':
        """Create a copy of this object"""
        new_points = [Point(p.x, p.y) for p in self.points]
        new_properties = self.properties.copy()
        return CADObject(self.object_type, new_points, new_properties) 