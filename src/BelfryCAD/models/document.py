"""
Document business logic model.

This module contains pure business logic for the CAD document with no UI dependencies.
"""

from typing import List, Dict, Optional, Tuple, Set
from .cad_object import CadObject
from .cad_objects.group_cad_object import GroupCadObject
from .constraints_manager import ConstraintsManager
from ..utils.constraints import Constraint
from ..cad_geometry import Point2D


class Document:
    """Pure business logic for CAD document - no UI dependencies"""
    
    def __init__(self):
        self.objects: Dict[str, CadObject] = {}
        self.root_groups: Set[str] = set()  # Set of root group IDs
        self.modified = False
        self.filename: Optional[str] = None
        self.constraints_manager = ConstraintsManager(self)
    
    def add_object(self, cad_object: CadObject) -> str:
        """Add an object to the document"""
        self.objects[cad_object.object_id] = cad_object
        cad_object.document = self
        
        # If it's a group object, add it to root groups if it has no parent
        if isinstance(cad_object, GroupCadObject) and cad_object.is_root():
            self.root_groups.add(cad_object.object_id)
        
        self.modified = True
        return cad_object.object_id
    
    def remove_object(self, object_id: str) -> bool:
        """Remove an object from the document"""
        if object_id in self.objects:
            obj = self.objects[object_id]
            
            # If it's a group, handle children and parent relationships
            if isinstance(obj, GroupCadObject):
                # Remove from parent's children list
                if obj.parent_id and obj.parent_id in self.objects:
                    parent = self.objects.get(obj.parent_id)
                    if isinstance(parent, GroupCadObject):
                        parent.remove_child(object_id)
                
                # Remove from root groups if it's a root
                if object_id in self.root_groups:
                    self.root_groups.remove(object_id)
                
                # Move all children to parent or root
                for child_id in obj.children.copy():
                    child = self.objects.get(child_id)
                    if child:
                        if isinstance(child, GroupCadObject):
                            child.set_parent(obj.parent_id)
                        if obj.parent_id and obj.parent_id in self.objects:
                            parent = self.objects.get(obj.parent_id)
                            if isinstance(parent, GroupCadObject):
                                parent.add_child(child_id)
                            elif child_id not in self.root_groups:
                                self.root_groups.add(child_id)
                        else:
                            # Move to root
                            if isinstance(child, GroupCadObject):
                                child.set_parent(None)
                            else:
                                # Clear parent_id for non-group children
                                child.set_parent(None)
                            self.root_groups.add(child_id)
            
            # If it's a child of a group, remove from parent
            elif hasattr(obj, 'parent_id') and obj.parent_id:
                parent_id_val = obj.parent_id
                parent = self.objects.get(parent_id_val) if isinstance(parent_id_val, str) else None
                if parent and isinstance(parent, GroupCadObject):
                    parent.remove_child(object_id)
            
            del self.objects[object_id]
            self.modified = True
            return True
        return False
    
    def get_object(self, object_id: str) -> Optional[CadObject]:
        """Get object by ID"""
        return self.objects.get(object_id)
    
    def get_all_objects(self) -> List[CadObject]:
        """Get all objects"""
        return list(self.objects.values())
    
    def get_visible_objects(self) -> List[CadObject]:
        """Get all visible objects"""
        visible_objects = []
        for obj in self.objects.values():
            if obj.visible:
                visible_objects.append(obj)
        return visible_objects

    def get_root_objects(self) -> List[CadObject]:
        """Get all root objects (objects not in any group)"""
        root_objects = []
        for obj in self.objects.values():
            if not hasattr(obj, 'parent_id') or obj.parent_id is None:
                root_objects.append(obj)
        return root_objects

    def get_root_groups(self) -> List[GroupCadObject]:
        """Get all root groups"""
        root_groups = []
        for group_id in self.root_groups:
            group = self.objects.get(group_id)
            if isinstance(group, GroupCadObject):
                root_groups.append(group)
        return root_groups

    def create_group(self, name: str = "Group") -> str:
        """Create a new group"""
        group = GroupCadObject(self, name=name)
        return self.add_object(group)

    def add_to_group(self, object_id: str, group_id: str) -> bool:
        """Add an object to a group"""
        obj = self.objects.get(object_id)
        group = self.objects.get(group_id)
        
        if not obj or not isinstance(group, GroupCadObject):
            return False
        
        # Remove from current parent if any
        if hasattr(obj, 'parent_id') and obj.parent_id:
            old_parent_id = obj.parent_id
            old_parent = self.objects.get(old_parent_id) if isinstance(old_parent_id, str) else None
            if old_parent and isinstance(old_parent, GroupCadObject):
                old_parent.remove_child(object_id)
        
        # Add to new group
        if group.add_child(object_id):
            if hasattr(obj, 'set_parent'):
                obj.set_parent(group_id)  # group_id is a string key
            return True
        return False

    def remove_from_group(self, object_id: str) -> bool:
        """Remove an object from its group (move to root)"""
        obj = self.objects.get(object_id)
        if not obj or not hasattr(obj, 'parent_id') or not obj.parent_id:
            return False
        
        parent_id_val = obj.parent_id
        parent = self.objects.get(parent_id_val) if isinstance(parent_id_val, str) else None
        if parent and isinstance(parent, GroupCadObject):
            parent.remove_child(object_id)
            if hasattr(obj, 'set_parent'):
                obj.set_parent(None)
            
            # Add to root groups if it's a group
            if isinstance(obj, GroupCadObject):
                self.root_groups.add(object_id)
            
            return True
        return False

    def get_group_hierarchy(self) -> Dict[str, List[str]]:
        """Get the complete group hierarchy as a dictionary"""
        hierarchy = {}
        for obj_id, obj in self.objects.items():
            if isinstance(obj, GroupCadObject):
                hierarchy[obj_id] = obj.children.copy()
        return hierarchy

    def get_object_path(self, object_id: str) -> List[str]:
        """Get the path from root to the object (list of object IDs)"""
        path: List[str] = []
        current_id: Optional[str] = object_id
        
        while current_id:
            path.insert(0, current_id)
            obj = self.objects.get(current_id)
            if obj and hasattr(obj, 'parent_id'):
                pid = getattr(obj, 'parent_id', None)
                current_id = pid if isinstance(pid, str) else None
            else:
                break
        
        return path

    def get_constraint_id(self, label: str, objid1: str, objid2: Optional[str]) -> str:
        """Make a constraint ID"""
        if objid2 is None:
            return f"{label}-{objid1}"
        else:
            return f"{label}-{objid1}-{objid2}"

    def get_constraint(self, constraint_id: str) -> Optional[Constraint]:
        """Get a constraint by ID"""
        return self.constraints_manager.constraints.get(constraint_id, None)

    def add_constraint(self, constraint_id: str, constraint: Constraint, 
                      object_id1: str, object_id2: Optional[str] = None):
        """Add a constraint to the document"""
        return self.constraints_manager.add_constraint(constraint_id, constraint, object_id1, object_id2)
    
    def select_objects_at_point(self, point: Point2D, tolerance: float = 5.0) -> List[str]:
        """Select objects at a specific point"""
        selected_ids = []
        for obj in self.objects.values():
            if obj.contains_point(point, tolerance):
                selected_ids.append(obj.object_id)
        return selected_ids
    
    def select_objects_in_rectangle(
            self,
            min_x: float,
            min_y: float, 
            max_x: float,
            max_y: float
    ) -> List[str]:
        """Select objects within a rectangle"""
        selected_ids = []
        for obj in self.objects.values():
            obj_bounds = obj.get_bounds()
            if (obj_bounds[0] <= max_x and obj_bounds[2] >= min_x and
                obj_bounds[1] <= max_y and obj_bounds[3] >= min_y):
                selected_ids.append(obj.object_id)
        return selected_ids
    
    def move_selected_objects(self, selected_ids: List[str], dx: float, dy: float):
        """Move selected objects by delta"""
        for object_id in selected_ids:
            obj = self.get_object(object_id)
            if obj:
                obj.translate(dx, dy)
        self.modified = True
    
    def delete_selected_objects(self, selected_ids: List[str]):
        """Delete selected objects"""
        for object_id in selected_ids:
            self.remove_object(object_id)
    
    def get_document_bounds(self) -> Tuple[float, float, float, float]:
        """Get bounding box of all objects"""
        if not self.objects:
            return (0, 0, 0, 0)
        
        boundslist = [obj.get_bounds() for obj in self.objects.values()]
        min_x = min(bounds[0] for bounds in boundslist)
        min_y = min(bounds[1] for bounds in boundslist)
        max_x = max(bounds[2] for bounds in boundslist)
        max_y = max(bounds[3] for bounds in boundslist)
        
        return (min_x, min_y, max_x, max_y)
    
    def create_line(self, start_point: Point2D, end_point: Point2D) -> str:
        """Create a line object"""
        from .cad_objects.line_cad_object import LineCadObject
        line = LineCadObject(self, start_point, end_point)
        return self.add_object(line)
    
    def create_circle(self, center: Point2D, radius_point: Point2D) -> str:
        """Create a circle object"""
        from .cad_objects.circle_cad_object import CircleCadObject
        circle = CircleCadObject(self, center, radius_point)
        return self.add_object(circle)
    
    def mark_modified(self):
        """Mark document as modified"""
        self.modified = True
    
    def mark_saved(self):
        """Mark document as saved"""
        self.modified = False
    
    def is_modified(self) -> bool:
        """Check if document is modified"""
        return self.modified
    
    def clear(self):
        """Clear all objects from document"""
        self.objects.clear()
        self.root_groups.clear()
        self.constraints_manager.clear_all_constraints()
        self.modified = True
    
    def solve_constraints(self) -> bool:
        """Solve all constraints in the document"""
        return self.constraints_manager.solve_constraints()
    
    def remove_constraint(self, constraint_id: str) -> bool:
        """Remove a constraint by ID"""
        return self.constraints_manager.remove_constraint(constraint_id)
    
    def get_constraints_for_object(self, object_id: str) -> List[str]:
        """Get all constraint IDs involving a specific object"""
        return self.constraints_manager.get_constraints_for_object(object_id)
    
    def get_constraints_between_objects(self, object_id1: str, object_id2: str) -> List[str]:
        """Get all constraint IDs between two specific objects"""
        return self.constraints_manager.get_constraints_between_objects(object_id1, object_id2)
    
    def remove_constraints_between_objects(self, object_id1: str, object_id2: Optional[str] = None) -> List[str]:
        """Remove all constraints between two objects"""
        return self.constraints_manager.remove_constraints_between_objects(object_id1, object_id2)
    
    def get_constraint_count(self) -> int:
        """Get the total number of constraints"""
        return self.constraints_manager.get_constraint_count()
    
    def has_constraints(self) -> bool:
        """Check if there are any constraints"""
        return self.constraints_manager.has_constraints()
