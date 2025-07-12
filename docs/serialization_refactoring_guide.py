"""
Serialization Refactoring for BelfryCAD

This document outlines the refactoring of serialization logic to move 
serialization responsibility into the respective classes (CADObject and Layer)
rather than handling it externally in Document and LayerManager.

CURRENT ISSUE:
- Document.py contains object serialization logic
- LayerManager contains layer serialization logic  
- This violates single responsibility principle
- Makes serialization format scattered across multiple files

SOLUTION:
Move serialization into the classes themselves:
- CADObject.serialize() / CADObject.deserialize()
- Layer.serialize() / Layer.deserialize()

This creates a cleaner, more maintainable architecture.
"""

# Example implementation for CADObject class:

class CADObject:
    """Base CAD object with self-contained serialization."""
    
    def serialize(self) -> dict:
        """
        Serialize this CAD object to a dictionary.
        
        Returns:
            Dictionary containing all object data needed for persistence
        """
        return {
            "object_id": self.object_id,
            "object_type": self.object_type.value,
            "layer": self.layer.name if self.layer else None,
            "coords": [{"x": pt.x, "y": pt.y} for pt in self.coords],
            "attributes": self.attributes.copy(),
            "selected": self.selected,
            "visible": self.visible,
            "locked": self.locked,
            # Add any subclass-specific data
            **self._serialize_specific()
        }
    
    def _serialize_specific(self) -> dict:
        """Override in subclasses to add specific data."""
        return {}
    
    @classmethod
    def deserialize(cls, data: dict, object_manager, layer_manager):
        """
        Deserialize a CAD object from dictionary data.
        
        Args:
            data: Serialized object data
            object_manager: CADObjectManager for registration
            layer_manager: LayerManager for layer lookup
            
        Returns:
            Reconstructed CADObject instance
        """
        from .cad_objects import ObjectType, Point
        
        # Get object type
        object_type_str = data.get("object_type")
        object_type = ObjectType(object_type_str)
        
        # Reconstruct coordinates
        coords_data = data.get("coords", [])
        coords = []
        for coord in coords_data:
            if isinstance(coord, dict) and "x" in coord and "y" in coord:
                coords.append(Point(coord["x"], coord["y"]))
        
        # Get layer by name
        layer_name = data.get("layer", "Layer 0")
        target_layer = None
        for layer in layer_manager.get_all_layers():
            if layer.name == layer_name:
                target_layer = layer
                break
        
        if not target_layer:
            target_layer = layer_manager.create_layer(layer_name)
        
        # Create object through object manager
        obj = object_manager.create_object(object_type, *coords, layer=target_layer)
        
        if obj:
            # Restore properties
            obj.attributes.update(data.get("attributes", {}))
            obj.selected = data.get("selected", False)
            obj.visible = data.get("visible", True)
            obj.locked = data.get("locked", False)
            
            # Let subclass handle specific deserialization
            obj._deserialize_specific(data)
        
        return obj
    
    def _deserialize_specific(self, data: dict):
        """Override in subclasses to handle specific data."""
        pass


# Example implementation for Layer class:

class Layer:
    """Layer with self-contained serialization."""
    
    def serialize(self) -> dict:
        """
        Serialize this layer to a dictionary.
        
        Returns:
            Dictionary containing all layer data needed for persistence
        """
        return {
            "name": self.name,
            "color": self.color,
            "visible": self.visible,
            "locked": self.locked,
            "cut_bit": self.cut_bit,
            "cut_depth": self.cut_depth,
            "objects": self.objects.copy(),
            # Add any additional properties
            "line_width": getattr(self, 'line_width', 1.0),
            "line_style": getattr(self, 'line_style', 'solid')
        }
    
    @classmethod
    def deserialize(cls, data: dict):
        """
        Deserialize a layer from dictionary data.
        
        Args:
            data: Serialized layer data
            
        Returns:
            Reconstructed Layer instance
        """
        layer = cls(
            name=data.get("name", "Layer"),
            visible=data.get("visible", True),
            locked=data.get("locked", False),
            color=data.get("color", "black"),
            cut_bit=data.get("cut_bit", 0),
            cut_depth=data.get("cut_depth", 0.0),
            objects=data.get("objects", [])
        )
        
        # Set additional properties if they exist
        if "line_width" in data and hasattr(layer, 'line_width'):
            layer.line_width = data["line_width"]
        if "line_style" in data and hasattr(layer, 'line_style'):
            layer.line_style = data["line_style"]
        
        return layer


# Updated Document class using object self-serialization:

class Document:
    """Document with delegated serialization."""
    
    def _serialize_native(self):
        """Serialize using object self-serialization."""
        # Let objects serialize themselves
        serialized_objects = []
        for obj in self.objects.get_all_objects():
            obj_data = obj.serialize()
            serialized_objects.append(obj_data)

        # Let layers serialize themselves
        serialized_layers = {}
        for layer in self.layers.get_all_layers():
            layer_data = layer.serialize()
            serialized_layers[layer.name] = layer_data

        current_layer = self.layers.get_current_layer()
        current_layer_name = current_layer.name if current_layer else "Layer 0"

        return {
            "objects": serialized_objects,
            "layers": {
                "layer_data": serialized_layers,
                "current_layer": current_layer_name,
                "layer_order": [layer.name for layer in self.layers.get_all_layers()]
            }
        }
    
    def _deserialize_native(self, data):
        """Deserialize using object self-deserialization."""
        # Clear existing data
        self.objects.clear_all()
        self.layers.init_layers()

        # Restore layers using their own deserialization
        layers_data = data.get("layers", {})
        if "layer_data" in layers_data:
            for layer_name, layer_info in layers_data["layer_data"].items():
                layer = Layer.deserialize(layer_info)
                if layer:
                    # Add to layer manager (need proper method)
                    self.layers._add_layer(layer)
            
            # Set current layer
            if "current_layer" in layers_data:
                current_layer_name = layers_data["current_layer"]
                for layer in self.layers.get_all_layers():
                    if layer.name == current_layer_name:
                        self.layers.set_current_layer(layer)
                        break

        # Restore objects using their own deserialization
        objects_data = data.get("objects", [])
        for obj_data in objects_data:
            try:
                obj = CADObject.deserialize(obj_data, self.objects, self.layers)
            except Exception as e:
                print(f"Failed to deserialize object: {e}")


# Benefits of this approach:

"""
ADVANTAGES:

1. SINGLE RESPONSIBILITY:
   - Each class handles its own serialization
   - Document just orchestrates the process
   - Clear separation of concerns

2. EXTENSIBILITY:
   - New object types add their own serialization
   - New layer properties handled in Layer class
   - Easy to modify serialization format

3. MAINTAINABILITY:
   - Serialization logic colocated with class definition
   - Easier to find and modify
   - Reduces coupling between classes

4. TYPE SAFETY:
   - Classes know their own structure
   - Better validation during deserialization
   - Clearer error handling

5. TESTABILITY:
   - Can unit test serialization per class
   - Mock dependencies easily
   - Isolated test scenarios

IMPLEMENTATION STEPS:

1. Add serialize() method to CADObject base class
2. Add serialize() method to Layer class
3. Add deserialize() class methods to both
4. Update Document to delegate to object methods
5. Update LayerManager to delegate to Layer methods
6. Remove serialization logic from Document/LayerManager
7. Add unit tests for each class serialization

This creates a cleaner, more maintainable architecture where each
class is responsible for its own persistence logic.
"""

print("Serialization refactoring pattern documented")
print("Classes should handle their own serialize/deserialize methods")
print("Document and LayerManager should delegate to object methods")