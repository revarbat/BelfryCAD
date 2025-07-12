import json
from pathlib import Path
from typing import Optional
from .cad_objects import CADObjectManager
from .layers import LayerManager


class Document:
    """Manages the current CAD document, file I/O, and modification state."""

    def __init__(self):
        self._filename: Optional[str] = None
        self._modified: bool = False
        self.objects = CADObjectManager()
        self.layers = LayerManager("document")
        # Initialize the layer system
        self.layers.init_layers()

    @property
    def filename(self) -> Optional[str]:
        return self._filename

    @filename.setter
    def filename(self, value: str):
        self._filename = value

    def is_modified(self) -> bool:
        return self._modified

    def mark_modified(self):
        self._modified = True

    def clear_modified(self):
        self._modified = False

    def new(self):
        self.objects.clear_all()
        self.layers.init_layers()  # Reset layer system
        self._filename = None
        self.clear_modified()

    def save(self, filename: Optional[str] = None):
        if filename:
            self._filename = filename
        if not self._filename:
            raise ValueError("No filename specified for saving.")
        ext = Path(self._filename).suffix.lower()
        if ext == ".tkcad":
            self._save_native()
        else:
            raise NotImplementedError(
                f"Saving format '{ext}' not supported yet."
            )
        self.clear_modified()

    def load(self, filename: str):
        ext = Path(filename).suffix.lower()
        if ext == ".tkcad":
            self._load_native(filename)
        else:
            raise NotImplementedError(
                f"Loading format '{ext}' not supported yet."
            )
        self._filename = filename
        self.clear_modified()

    def get_filename(self) -> Optional[str]:
        return self._filename

    def set_filename(self, filename: str):
        self._filename = filename

    def _save_native(self):
        data = self._serialize_native()
        if not self._filename:
            raise ValueError("No filename specified for saving.")
        with open(self._filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _load_native(self, filename: str):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._deserialize_native(data)

    def _serialize_native(self):
        # Serialize all objects using their own serialization methods
        serialized_objects = []
        for obj in self.objects.get_all_objects():
            # Let each CADObject handle its own serialization
            obj_data = obj.serialize()
            serialized_objects.append(obj_data)

        # Serialize layers using their own serialization methods
        serialized_layers = {}
        for layer in self.layers.get_all_layers():
            # Let each Layer handle its own serialization
            layer_data = layer.serialize()
            serialized_layers[layer.name] = layer_data

        current_layer = self.layers.get_current_layer()
        current_layer_name = current_layer.name if current_layer else "Layer 0"

        return {
            "objects": serialized_objects,
            "layers": {
                "layer_data": serialized_layers,
                "current_layer": current_layer_name,
                "layer_order": [layer.name for layer in 
                               self.layers.get_all_layers()]
            }
        }

    def _deserialize_native(self, data):
        # Clear and restore objects and layers
        self.objects.clear_all()
        self.layers.init_layers()  # Reset layer system

        # Restore layer system
        layers_data = data.get("layers", {})
        if "layer_data" in layers_data:
            # New format with Layer objects - use Layer's own deserialization
            for layer_name, layer_info in layers_data["layer_data"].items():
                # Let Layer handle its own deserialization
                layer = Layer.deserialize(layer_info)
                if layer:
                    # Add to layer manager
                    self._layers.append(layer)
            
            # Set current layer by name
            if "current_layer" in layers_data:
                current_layer_name = layers_data["current_layer"]
                # Find and set current layer
                for layer in self.layers.get_all_layers():
                    if layer.name == current_layer_name:
                        self.layers.set_current_layer(layer)
                        break
        else:
            # Old format - convert to new Layer object system
            old_layers = data.get("layers", 
                                 {0: ["Layer 0", "black", True, False]})
            for layer_id, layer_info in old_layers.items():
                if isinstance(layer_info, list) and len(layer_info) >= 4:
                    name, color, visible, locked = layer_info[:4]
                    layer = self.layers.create_layer(name)
                    if layer:
                        layer.color = color
                        layer.visible = visible
                        layer.locked = locked
            
            # Set current layer from old format
            current_layer_id = data.get("current_layer", 0)
            if isinstance(current_layer_id, int):
                # Try to find layer by old ID position or use default
                all_layers = self.layers.get_all_layers()
                if (current_layer_id < len(all_layers) and 
                    current_layer_id >= 0):
                    self.layers.current_layer = all_layers[current_layer_id]

        # Restore objects using their own deserialization methods
        objects_data = data.get("objects", [])
        for obj_data in objects_data:
            try:
                # Let CADObject handle its own deserialization
                from .cad_objects import CADObject
                obj = CADObject.deserialize(obj_data, self.objects, self.layers)
                
                if obj:
                    # CADObject.deserialize should handle adding to object manager
                    # and setting layer references correctly
                    pass

            except Exception as e:
                print(f"Failed to deserialize object: {e}")
                continue
