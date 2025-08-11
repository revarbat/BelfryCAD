"""
CAD Object business logic model.

This module contains pure business logic for CAD objects with no UI dependencies.
"""

import uuid

from enum import Enum
from typing import List, Tuple, Optional, Dict, TYPE_CHECKING

from ..utils.constraints import (
    ConstraintSolver, Constrainable, Constraint,
    get_possible_constraints,
)
from ..cad_geometry import Point2D, Transform2D, ShapeType, Shape2D

if TYPE_CHECKING:
    from .document import Document


class ObjectType(Enum):
    """Object types for CAD objects"""
    LINE = "line"
    ARC = "arc"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"
    BEZIER = "bezier"
    GEAR = "gear"
    POLYGON = "polygon"
    GROUP = "group"


class CadObject:
    """Pure business logic for CAD objects - no UI dependencies"""
    _object_types = {}
    _max_id = 0

    def __init__(self, document: 'Document', color: str = "black", line_width: Optional[float] = None):
        CadObject._max_id += 1
        self.object_id = str(CadObject._max_id)
        self.document = document
        self.color = color
        self.line_width = line_width
        self.visible = True
        self.locked = False
        self.parent_id: Optional[str] = None  # Parent group ID, None if root
        
        # Initialize name - will be set by document when object is added
        self._name: Optional[str] = None
    
    @property
    def name(self) -> str:
        """Get the object's name."""
        if self._name is None:
            # Only generate a default name if the object is in a document
            if self.document:
                # Let the document handle the naming
                return f"object{self.object_id}"
            else:
                return f"object{self.object_id}"
        return self._name
    
    @name.setter
    def name(self, value: str):
        """Set the object's name."""
        if self.document:
            # Ensure the name is unique
            unique_name = self.document.get_unique_name(value, self.object_id)
            self._name = unique_name
        else:
            self._name = value
    
    def _generate_default_name(self) -> str:
        """Generate a default name for this object based on its type."""
        if not self.document:
            return f"object{self.object_id}"
        
        # Get the object type name
        obj_type = type(self).__name__.replace('CadObject', '').lower()
        if obj_type == 'line':
            base_name = 'line'
        elif obj_type == 'circle':
            base_name = 'circle'
        elif obj_type == 'arc':
            base_name = 'arc'
        elif obj_type == 'ellipse':
            base_name = 'ellipse'
        elif obj_type == 'bezier':
            base_name = 'bezier'
        elif obj_type == 'gear':
            base_name = 'gear'
        elif obj_type == 'polygon':
            base_name = 'polygon'
        elif obj_type == 'group':
            base_name = 'group'
        else:
            base_name = 'object'
        
        # Get a unique name from the document
        return self.document.get_unique_name(base_name, self.object_id)
    
    def set_parent(self, parent_id: Optional[str]):
        """Set the parent group ID."""
        self.parent_id = parent_id
    
    def make_constrainables(self, solver: ConstraintSolver):
        """
        Setup constraints geometry for this object.
        Overridden in subclasses.
        """
        pass

    def get_constrainables(self) -> List[Tuple[str, Constrainable]]:
        """
        Get list of constrainables for this object.
        Overridden in subclasses.
        """
        return []

    def update_constrainables_before_solving(self, solver: ConstraintSolver):
        """
        Update constrainables before solving.
        Overridden in subclasses.
        """
        pass

    def update_from_solved_constraints(self, solver: ConstraintSolver):
        """
        Update object from constraints. This is called after the constraints are solved.
        Overridden in subclasses.
        """
        pass

    def get_possible_constraints(self, other: Optional['CadObject']) -> Dict[str, Constraint]:
        """
        Get possible constraints for this object.
        """
        out = {}
        if self.document is None:
            return out
        for label, constraint in get_possible_constraints(self, other).items():
            if other is None:
                long_label = f"{self.object_id}-{label}"
            else:
                long_label = f"{self.object_id}-{label}-{other.object_id}"
            if self.document.get_constraint(long_label) is None:
                out[label] = constraint
        return out

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """
        Get bounding box (min_x, min_y, max_x, max_y).
        Overridden in subclasses.
        """
        return (0, 0, 0, 0)
    
    def translate(self, dx: float, dy: float):
        """
        Translate the object by dx and dy.
        Overridden in subclasses.
        """
        pass
    
    def scale(self, scale: float, center: Point2D):
        """
        Scale the object by scale around center.
        Overridden in subclasses.
        """
        pass
    
    def rotate(self, angle: float, center: Point2D):
        """
        Rotate the object by angle around center.
        Overridden in subclasses.
        """
        pass

    def transform(self, transform: Transform2D):
        """
        Transform the object by the given transform.
        Overridden in subclasses.
        """
        pass

    def contains_point(self, point: Point2D, tolerance: float = 5.0) -> bool:
        """
        Check if the object contains the given point.
        Overridden in subclasses.
        """
        return False

    def decompose(self, into: List[ShapeType] = []) -> List[Shape2D]:
        """
        Decompose the object into a list of simpler objects.
        The list of types to decompose into is provided.
        Overridden in subclasses.
        """
        return []

    def get_data(self) -> dict:
        """
        Get the data needed to re-create this object.
        """
        data = self.get_object_data()
        data["object_id"] = self.object_id
        data["name"] = self.name
        data["color"] = self.color
        data["line_width"] = self.line_width
        data["visible"] = self.visible
        data["locked"] = self.locked
        return data

    def get_object_data(self) -> dict:
        """
        Get the data needed to re-create this object.
        Overridden in subclasses.
        """
        return {}

    @classmethod
    def register_object_type(
            cls,
            new_cls,
            obj_type: str,
            obj_tags: Dict[str, str]
            ):
        """
        Register an object type.
        """
        cls._object_types[obj_type] = (new_cls, obj_tags)

    @classmethod
    def create_object_from_data(cls, document: 'Document', obj_type: str, data: dict) -> 'CadObject':
        """
        Create a new object from the given data.
        Overridden in subclasses.
        """
        obj_class, obj_tags = cls._object_types[obj_type]
        for tag in data:
            if tag not in obj_tags:
                del data[tag]
        for tag, dflt in obj_tags.items():
            if tag not in data:
                data[tag] = dflt
        data["color"] = data["color"].strip()
        lw = data.get("line_width", "hairline").strip().lower()
        data["line_width"] = None if lw in ["", "none", "hairline"] else float(lw)
        data["object_id"] = data["object_id"].strip()
        
        # Handle name field
        if "name" in data:
            data["name"] = data["name"].strip()
        else:
            data["name"] = None
            
        return obj_class.create_object_from_data(document, obj_type, data)

