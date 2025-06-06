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
        with open(self._filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _load_native(self, filename: str):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._deserialize_native(data)

    def _serialize_native(self):
        # Serialize all objects and the new layer system
        serialized_objects = []
        for obj in self.objects.get_all_objects():
            obj_data = {
                "object_id": obj.object_id,
                "object_type": obj.object_type.value,  # Use .value for enum
                "layer": obj.layer,
                "coords": [{"x": pt.x, "y": pt.y} for pt in obj.coords],  # Serialize Points properly
                "attributes": obj.attributes,
                "selected": obj.selected,
                "visible": obj.visible,
                "locked": obj.locked
            }
            serialized_objects.append(obj_data)

        return {
            "objects": serialized_objects,
            "layers": {
                "layer_data": {
                    layer_id: self.layers.serialize_layer(layer_id)
                    for layer_id in self.layers.get_layer_ids()
                },
                "current_layer": self.layers.get_current_layer(),
                "layer_order": self.layers.get_layer_ids()
            }
        }

    def _deserialize_native(self, data):
        # Clear and restore objects and layers
        self.objects.clear_all()
        self.layers.init_layers()  # Reset layer system

        # Restore layer system
        layers_data = data.get("layers", {})
        if "layer_data" in layers_data:
            # New format with LayerManager
            for layer_id, layer_info in layers_data["layer_data"].items():
                self.layers.deserialize_layer(layer_info)
            if "current_layer" in layers_data:
                self.layers.set_current_layer(layers_data["current_layer"])
        else:
            # Old format - convert to new system
            old_layers = data.get("layers", {0: ["Layer 0", "black", True, False]})
            for layer_id, layer_info in old_layers.items():
                if isinstance(layer_info, list) and len(layer_info) >= 4:
                    name, color, visible, locked = layer_info[:4]
                    new_layer_id = self.layers.create_layer(name)
                    self.layers.set_layer_color(new_layer_id, color)
                    self.layers.set_layer_visible(new_layer_id, visible)
                    self.layers.set_layer_locked(new_layer_id, locked)
            current_layer = data.get("current_layer", 0)
            if self.layers.layer_exists(current_layer):
                self.layers.set_current_layer(current_layer)

        # Restore objects with proper deserialization
        from .cad_objects import ObjectType, Point
        objects_data = data.get("objects", [])
        for obj_data in objects_data:
            try:
                # Get object type
                object_type_str = obj_data.get("object_type")
                if isinstance(object_type_str, str):
                    object_type = ObjectType(object_type_str)
                else:
                    object_type = object_type_str

                # Rebuild coords from proper dict format
                coords_data = obj_data.get("coords", [])
                coords = []
                for coord in coords_data:
                    if isinstance(coord, dict) and "x" in coord and "y" in coord:
                        coords.append(Point(coord["x"], coord["y"]))
                    elif hasattr(coord, 'x') and hasattr(coord, 'y'):
                        coords.append(Point(coord.x, coord.y))

                # Create object with manager (don't pass attributes as kwargs)
                obj = self.objects.create_object(
                    object_type,
                    *coords,
                    layer=obj_data.get("layer", 0)
                )

                # Set attributes after creation
                obj.attributes.update(obj_data.get("attributes", {}))

                # Set additional properties
                obj.selected = obj_data.get("selected", False)
                obj.visible = obj_data.get("visible", True)
                obj.locked = obj_data.get("locked", False)

            except Exception as e:
                print(f"Failed to deserialize object: {e}")
                continue
