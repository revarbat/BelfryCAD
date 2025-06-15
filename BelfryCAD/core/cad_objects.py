"""
Core CAD Objects System

This module implements the CAD objects system based on the original TCL
cadobjects.tcl. It provides object management, drawing, selection, and
manipulation functionality. The global cadobjectsInfo dictionary pattern
from TCL is replaced with a class-based approach.
"""

import math
import logging
from typing import Dict, List, Tuple, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from BelfryCAD.gui.main_window import MainWindow
    from BelfryCAD.core.layers import Layer

logger = logging.getLogger(__name__)

# Import CADObject classes from their respective tool modules
# Note: These imports are at the end of the file to avoid circular imports


class ObjectType(Enum):
    """Enumeration of object types"""
    LINE = "line"
    ARC = "arc"
    CIRCLE = "circle"
    BEZIER = "bezier"
    BEZIERQUAD = "bezierquad"
    POLYGON = "polygon"
    TEXT = "text"
    DIMENSION = "dimension"
    POINT = "point"
    IMAGE = "image"
    SCREW_HOLE = "screw_hole"


class LayerInfo(Enum):
    """Layer information indices - mirrors TCL layerInfo structure"""
    NAME = 0
    COLOR = 1
    VISIBLE = 2
    LOCKED = 3


@dataclass
class Point:
    """2D Point with float coordinates"""
    x: float
    y: float

    def __post_init__(self):
        self.x = float(self.x)
        self.y = float(self.y)

    def distance_to(self, other: 'Point') -> float:
        """Calculate distance to another point"""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

    def __add__(self, other: 'Point') -> 'Point':
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Point') -> 'Point':
        return Point(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> 'Point':
        return Point(self.x * scalar, self.y * scalar)

@dataclass
class CADObject:
    """Base CAD object - mirrors structure from cadobjects.tcl"""
    mainwin: 'MainWindow'
    object_id: int
    object_type: ObjectType
    layer: Optional['Layer'] = None  # Changed from int to Layer reference, made optional
    coords: List[Point] = field(default_factory=list)
    stroke_width: float = 0.01
    stroke_color: str = 'black'
    stroke_opacity: float = 1.0
    stroke_style: str = 'solid'
    fill_color: str = 'transparent'
    fill_opacity: float = 0.0
    selected: bool = False
    visible: bool = True
    locked: bool = False
    attributes: Dict[str, Any] = field(default_factory=dict)

    @property
    def id(self) -> str:
        """Get object ID as string for compatibility"""
        return str(self.object_id)
        
    def __post_init__(self):
        """Initialize object after creation"""
        self.show_controls = False

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get bounding box (minx, miny, maxx, maxy)"""
        if not self.coords:
            return (0, 0, 0, 0)

        x_coords = [p.x for p in self.coords]
        y_coords = [p.y for p in self.coords]
        return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))

    def get_control_points(self) -> List[Point]:
        """Get list of control points for node selection"""
        return self.coords.copy()

    def move(self, dx: float, dy: float):
        """Move object by delta x, y"""
        for point in self.coords:
            point.x += dx
            point.y += dy
        self.redraw()

    def rotate(self, angle: float, center: Point):
        """Rotate object around center point"""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        for point in self.coords:
            # Translate to origin
            x = point.x - center.x
            y = point.y - center.y

            # Rotate
            new_x = x * cos_a - y * sin_a
            new_y = x * sin_a + y * cos_a

            # Translate back
            point.x = new_x + center.x
            point.y = new_y + center.y

        self.redraw()

    def scale(self, factor: float, center: Point):
        """Scale object around center point"""
        for point in self.coords:
            # Translate to origin
            x = point.x - center.x
            y = point.y - center.y

            # Scale
            x *= factor
            y *= factor

            # Translate back
            point.x = x + center.x
            point.y = y + center.y

        self.redraw()

    @property
    def show_controls(self) -> bool:
        """Get the show controls flag"""
        return self.show_controls

    @show_controls.setter
    def show_controls(self, value: bool):
        """Set the show controls flag"""
        self.show_controls = value
        self.redraw()

    def redraw(self):
        """Redraw the object"""
        self.draw_object()
        if self.show_controls:
            self.draw_controls()

    def draw_object(self):
        """Draw the object"""
        pass

    def draw_controls(self):
        """Draw the controls"""
        pass


class CADObjectManager:
    """
    Manages CAD objects - replaces the global cadobjectsInfo dictionary
    from TCL.

    This class handles object creation, selection, drawing, and manipulation
    based on the patterns found in the original cadobjects.tcl file.
    """

    def __init__(self):
        self.objects: Dict[int, CADObject] = {}
        self.next_id: int = 1
        self.selected_objects: List[int] = []
        self.current_layer: Optional['Layer'] = None

    def create_object(
        self, object_type: ObjectType, *args, **kwargs
    ) -> CADObject:
        """Create a new CAD object"""
        object_id = self.next_id
        self.next_id += 1

        # Set current layer if not specified
        layer = kwargs.pop('layer', self.current_layer)

        # Prepare coords for each object type
        if object_type == ObjectType.LINE:
            if len(args) >= 2:
                coords = [args[0], args[1]]
            else:
                raise ValueError("Line requires start and end points")

        elif object_type == ObjectType.ARC:
            if len(args) >= 3:
                coords = [args[0], args[1], args[2]]
            else:
                raise ValueError("Arc requires center, start, and end points")

        elif object_type == ObjectType.CIRCLE:
            if len(args) >= 2:
                coords = [args[0], args[1]]
            else:
                raise ValueError("Circle requires center and radius point")

        elif object_type == ObjectType.BEZIER:
            if len(args) >= 4:
                coords = list(args[:4])
            else:
                raise ValueError("Bezier requires 4 control points")

        elif object_type == ObjectType.BEZIERQUAD:
            if len(args) >= 3:
                coords = list(args[:3])
            else:
                raise ValueError("Quadratic Bezier requires 3 control points")

        elif object_type == ObjectType.POLYGON:
            if len(args) >= 3:
                coords = list(args)
            else:
                raise ValueError("Polygon requires at least 3 points")

        elif object_type == ObjectType.TEXT:
            if len(args) >= 2:
                coords = [args[0], args[1]]
            else:
                raise ValueError("Text requires position and text content")

        elif object_type == ObjectType.DIMENSION:
            if len(args) >= 3:
                coords = [args[0], args[1], args[2]]
            else:
                raise ValueError("Dimension requires start, end, and text position")

        else:
            coords = list(args)

        obj = CADObject(
            object_id=object_id,
            object_type=object_type,
            layer=layer,
            coords=coords,
            **kwargs
        )
        self.objects[object_id] = obj
        logger.debug(f"Created {object_type.value} object with ID {object_id}")
        return obj

    def delete_object(self, object_id: int) -> bool:
        """Delete an object"""
        if object_id in self.objects:
            del self.objects[object_id]
            if object_id in self.selected_objects:
                self.selected_objects.remove(object_id)
            logger.debug(f"Deleted object {object_id}")
            return True
        return False

    def get_object(self, object_id: int) -> Optional[CADObject]:
        """Get object by ID"""
        return self.objects.get(object_id)

    def get_all_objects(self) -> List[CADObject]:
        """Get all objects"""
        return list(self.objects.values())

    def get_next_id(self) -> int:
        """Get the next available object ID"""
        next_id = self.next_id
        self.next_id += 1
        return next_id

    def add_object(self, obj: CADObject) -> int:
        """Add a pre-created object to the manager"""
        object_id = obj.object_id
        self.objects[object_id] = obj
        logger.debug(f"Added object with ID {object_id}")
        return object_id

    def get_objects_on_layer(self, layer: 'Layer') -> List[CADObject]:
        """Get all objects on a specific layer"""
        return [obj for obj in self.objects.values() if obj.layer == layer]

    def select_object(self, object_id: int):
        """Select an object"""
        if (
            object_id in self.objects and
            object_id not in self.selected_objects
        ):
            self.selected_objects.append(object_id)
            self.objects[object_id].selected = True

    def deselect_object(self, object_id: int):
        """Deselect an object"""
        if object_id in self.selected_objects:
            self.selected_objects.remove(object_id)
            if object_id in self.objects:
                self.objects[object_id].selected = False

    def clear_selection(self):
        """Clear all selections"""
        for object_id in self.selected_objects:
            if object_id in self.objects:
                self.objects[object_id].selected = False
        self.selected_objects.clear()

    def get_selected_objects(self) -> List[CADObject]:
        """Get all selected objects"""
        return [self.objects[obj_id] for obj_id in self.selected_objects
                if obj_id in self.objects]

    def move_selected(self, dx: float, dy: float):
        """Move all selected objects"""
        for obj in self.get_selected_objects():
            obj.move(dx, dy)

    def rotate_selected(self, angle: float, center: Point):
        """Rotate all selected objects around center"""
        for obj in self.get_selected_objects():
            obj.rotate(angle, center)

    def scale_selected(self, factor: float, center: Point):
        """Scale all selected objects around center"""
        for obj in self.get_selected_objects():
            obj.scale(factor, center)

    def get_bounds_all(self) -> Tuple[float, float, float, float]:
        """Get bounding box of all objects"""
        if not self.objects:
            return (0, 0, 0, 0)

        bounds = [obj.get_bounds() for obj in self.objects.values()]
        min_x = min(b[0] for b in bounds)
        min_y = min(b[1] for b in bounds)
        max_x = max(b[2] for b in bounds)
        max_y = max(b[3] for b in bounds)

        return (min_x, min_y, max_x, max_y)

    def get_bounds_selected(self) -> Tuple[float, float, float, float]:
        """Get bounding box of selected objects"""
        selected = self.get_selected_objects()
        if not selected:
            return (0, 0, 0, 0)

        bounds = [obj.get_bounds() for obj in selected]
        min_x = min(b[0] for b in bounds)
        min_y = min(b[1] for b in bounds)
        max_x = max(b[2] for b in bounds)
        max_y = max(b[3] for b in bounds)

        return (min_x, min_y, max_x, max_y)

    def find_objects_in_area(
        self, x1: float, y1: float, x2: float, y2: float
    ) -> List[int]:
        """Find objects within a rectangular area"""
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)

        result = []
        for obj_id, obj in self.objects.items():
            bounds = obj.get_bounds()
            if (
                bounds[0] >= min_x and bounds[2] <= max_x and
                bounds[1] >= min_y and bounds[3] <= max_y
            ):
                result.append(obj_id)

        return result

    def gather_points(
        self, objects: Optional[List[int]] = None
    ) -> List[Point]:
        """
        Gather points from objects - mirrors cadobjects_gather_points from TCL.
        This was one of the most called functions (32.5% of runtime).
        """
        if objects is None:
            objects = list(self.objects.keys())

        points = []
        for obj_id in objects:
            if obj_id in self.objects:
                obj = self.objects[obj_id]
                points.extend(obj.coords)

        return points

    def get_object_count(self) -> int:
        """Get total number of objects"""
        return len(self.objects)

    def get_selected_count(self) -> int:
        """Get number of selected objects"""
        return len(self.selected_objects)

    def clear_all(self):
        """Clear all objects and reset state"""
        self.objects.clear()
        self.selected_objects.clear()
        self.next_id = 1
        logger.info("Cleared all CAD objects")
