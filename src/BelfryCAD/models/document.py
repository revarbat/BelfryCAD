"""
Document business logic model.

This module contains pure business logic for the CAD document with no UI dependencies.
"""

from typing import List, Dict, Optional, Tuple
from .cad_object import CADObject, ObjectType, Point
from .layer import Layer, LayerManager


class Document:
    """Pure business logic for CAD document - no UI dependencies"""
    
    def __init__(self):
        self.objects: Dict[str, CADObject] = {}
        self.layer_manager = LayerManager()
        self.modified = False
        self.filename: Optional[str] = None
    
    def add_object(self, cad_object: CADObject) -> str:
        """Add an object to the document"""
        self.objects[cad_object.object_id] = cad_object
        
        # Add to default layer
        default_layer = self.layer_manager.get_all_layers()[0]
        default_layer.add_object(cad_object.object_id)
        
        self.modified = True
        return cad_object.object_id
    
    def remove_object(self, object_id: str) -> bool:
        """Remove an object from the document"""
        if object_id in self.objects:
            # Remove from layer
            layer = self.layer_manager.get_layer_for_object(object_id)
            if layer:
                layer.remove_object(object_id)
            
            del self.objects[object_id]
            self.modified = True
            return True
        return False
    
    def get_object(self, object_id: str) -> Optional[CADObject]:
        """Get object by ID"""
        return self.objects.get(object_id)
    
    def get_all_objects(self) -> List[CADObject]:
        """Get all objects"""
        return list(self.objects.values())
    
    def get_visible_objects(self) -> List[CADObject]:
        """Get all visible objects"""
        visible_objects = []
        for obj in self.objects.values():
            layer = self.layer_manager.get_layer_for_object(obj.object_id)
            if layer and layer.is_visible() and obj.visible:
                visible_objects.append(obj)
        return visible_objects
    
    def get_objects_in_layer(self, layer_id: str) -> List[CADObject]:
        """Get all objects in a specific layer"""
        layer = self.layer_manager.get_layer(layer_id)
        if not layer:
            return []
        
        objects = []
        for object_id in layer.objects:
            obj = self.get_object(object_id)
            if obj:
                objects.append(obj)
        return objects
    
    def move_object_to_layer(self, object_id: str, layer_id: str) -> bool:
        """Move an object to a different layer"""
        obj = self.get_object(object_id)
        layer = self.layer_manager.get_layer(layer_id)
        
        if obj and layer:
            current_layer = self.layer_manager.get_layer_for_object(object_id)
            if current_layer:
                self.layer_manager.move_object_to_layer(
                    object_id, current_layer.layer_id, layer_id
                )
                self.modified = True
                return True
        return False
    
    def select_objects_at_point(self, point: Point, tolerance: float = 5.0) -> List[str]:
        """Select objects at a specific point"""
        selected_ids = []
        for obj in self.objects.values():
            if obj.contains_point(point, tolerance):
                selected_ids.append(obj.object_id)
        return selected_ids
    
    def select_objects_in_rectangle(self, min_x: float, min_y: float, 
                                  max_x: float, max_y: float) -> List[str]:
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
                obj.move_by(dx, dy)
        self.modified = True
    
    def delete_selected_objects(self, selected_ids: List[str]):
        """Delete selected objects"""
        for object_id in selected_ids:
            self.remove_object(object_id)
    
    def get_document_bounds(self) -> Tuple[float, float, float, float]:
        """Get bounding box of all objects"""
        if not self.objects:
            return (0, 0, 0, 0)
        
        min_x = min(obj.get_bounds()[0] for obj in self.objects.values())
        min_y = min(obj.get_bounds()[1] for obj in self.objects.values())
        max_x = max(obj.get_bounds()[2] for obj in self.objects.values())
        max_y = max(obj.get_bounds()[3] for obj in self.objects.values())
        
        return (min_x, min_y, max_x, max_y)
    
    def create_line(self, start_point: Point, end_point: Point) -> str:
        """Create a line object"""
        line = CADObject(ObjectType.LINE, [start_point, end_point])
        return self.add_object(line)
    
    def create_circle(self, center: Point, radius_point: Point) -> str:
        """Create a circle object"""
        circle = CADObject(ObjectType.CIRCLE, [center, radius_point])
        return self.add_object(circle)
    
    def create_rectangle(self, corner1: Point, corner2: Point) -> str:
        """Create a rectangle object"""
        rect = CADObject(ObjectType.RECTANGLE, [corner1, corner2])
        return self.add_object(rect)
    
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
        self.layer_manager = LayerManager()
        self.modified = True 