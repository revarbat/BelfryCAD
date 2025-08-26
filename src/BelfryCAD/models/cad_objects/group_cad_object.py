"""
GroupCadObject - A group CAD object that can contain other CAD objects.
"""

from typing import List, Optional, Tuple, Dict, TYPE_CHECKING

from ..cad_object import CadObject
from ...cad_geometry import Point2D, Transform2D

if TYPE_CHECKING:
    from ...models.document import Document


class GroupCadObject(CadObject):
    """A group CAD object that can contain other CAD objects and support nesting."""

    def __init__(
            self,
            document: 'Document',
            name: str = "Group",
            color: str = "black",
            line_width: Optional[float] = None
    ):
        super().__init__(document, color, line_width)
        self.name = name
        self.children: List[str] = []  # List of child object IDs
        self.parent_id: Optional[str] = None  # Parent group ID, None if root

    def add_child(self, child_id: str) -> bool:
        """Add a child object to this group."""
        if child_id not in self.children:
            self.children.append(child_id)
            return True
        return False

    def remove_child(self, child_id: str) -> bool:
        """Remove a child object from this group."""
        if child_id in self.children:
            self.children.remove(child_id)
            return True
        return False

    def get_children(self) -> List[str]:
        """Get list of child object IDs."""
        return self.children.copy()

    def set_parent(self, parent_id: Optional[str]):
        """Set the parent group ID."""
        self.parent_id = parent_id

    def get_parent(self) -> Optional[str]:
        """Get the parent group ID."""
        return self.parent_id

    def is_root(self) -> bool:
        """Check if this group is a root group (no parent)."""
        return self.parent_id is None

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get the bounds of all children combined."""
        if not self.children:
            return (0, 0, 0, 0)
        
        # Get bounds from all visible children
        bounds_list = []
        for child_id in self.children:
            child = self.document.get_object(child_id)
            if child and child.visible:
                bounds_list.append(child.get_bounds())
        
        if not bounds_list:
            return (0, 0, 0, 0)
        
        # Calculate combined bounds
        min_x = min(bounds[0] for bounds in bounds_list)
        min_y = min(bounds[1] for bounds in bounds_list)
        max_x = max(bounds[2] for bounds in bounds_list)
        max_y = max(bounds[3] for bounds in bounds_list)
        
        return (min_x, min_y, max_x, max_y)

    def translate(self, dx: float, dy: float):
        """Translate all children by the specified offset."""
        for child_id in self.children:
            child = self.document.get_object(child_id)
            if child:
                child.translate(dx, dy)

    def scale(self, scale: float, center: Point2D):
        """Scale all children by the specified scale factor around the center point."""
        for child_id in self.children:
            child = self.document.get_object(child_id)
            if child:
                child.scale(scale, center)

    def rotate(self, angle: float, center: Point2D):
        """Rotate all children by the specified angle around the center point."""
        for child_id in self.children:
            child = self.document.get_object(child_id)
            if child:
                child.rotate(angle, center)

    def transform(self, transform: Transform2D):
        """Transform all children by the specified transform."""
        for child_id in self.children:
            child = self.document.get_object(child_id)
            if child:
                child.transform(transform)

    def contains_point(self, point: Point2D, tolerance: float = 5.0) -> bool:
        """Check if any child contains the given point."""
        for child_id in self.children:
            child = self.document.get_object(child_id)
            if child and child.contains_point(point, tolerance):
                return True
        return False

    def get_all_descendants(self) -> List[str]:
        """Get all descendant object IDs (children and their children)."""
        descendants = []
        for child_id in self.children:
            descendants.append(child_id)
            child = self.document.get_object(child_id)
            if isinstance(child, GroupCadObject):
                descendants.extend(child.get_all_descendants())
        return descendants

    def get_visible_children(self) -> List[str]:
        """Get list of visible child object IDs."""
        visible_children = []
        for child_id in self.children:
            child = self.document.get_object(child_id)
            if child and child.visible:
                visible_children.append(child_id)
        return visible_children

    def get_object_data(self) -> dict:
        """Get the data needed to re-create this object."""
        data = {
            "name": self.name,
            "children": self.children.copy(),
            "parent_id": self.parent_id
        }
        return data

    @classmethod
    def create_object_from_data(cls, document: 'Document', obj_type: str, data: dict) -> 'GroupCadObject':
        """Create a group object from the given data."""
        return cls(document, data["name"])


# Register the group object type
CadObject.register_object_type(GroupCadObject, "group", {"name": "Group"}) 